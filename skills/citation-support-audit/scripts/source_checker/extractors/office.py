"""Non-executing extraction for OOXML Word documents and converted legacy DOC files."""

import subprocess
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

from docx import Document  # pyright: ignore[reportMissingImports]

from source_checker.citations import VISIBLE_CITATION_RE
from source_checker.model import CitationMention, TextBlock
from source_checker.normalize import normalize_text

WORDPROCESSINGML = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NAMESPACES = {"w": WORDPROCESSINGML}
MACRO_ENABLED_MAIN_CONTENT_TYPE = b"application/vnd.ms-word.document.macroEnabled.main+xml"
DOCUMENT_MAIN_CONTENT_TYPE = b"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
_MAX_OOXML_ENTRY_COUNT = 10_000
_MAX_OOXML_ENTRY_BYTES = 50 * 1024 * 1024
_MAX_OOXML_TOTAL_BYTES = 200 * 1024 * 1024
_MAX_OOXML_COMPRESSION_RATIO = 100


def _validate_ooxml_archive(package: zipfile.ZipFile) -> None:
    """Reject oversized OOXML archives from ZIP metadata before reading any member."""
    entries = package.infolist()
    if len(entries) > _MAX_OOXML_ENTRY_COUNT:
        raise ValueError("OOXML archive has too many entries")
    entry_names: set[str] = set()
    total_bytes = 0
    for entry in entries:
        if entry.filename in entry_names:
            raise ValueError("OOXML archive contains a duplicate member name")
        entry_names.add(entry.filename)
        if entry.file_size > _MAX_OOXML_ENTRY_BYTES:
            raise ValueError("OOXML archive entry exceeds the uncompressed-size budget")
        if entry.compress_size and entry.file_size / entry.compress_size > _MAX_OOXML_COMPRESSION_RATIO:
            raise ValueError("OOXML archive entry exceeds the compression-ratio budget")
        total_bytes += entry.file_size
        if total_bytes > _MAX_OOXML_TOTAL_BYTES:
            raise ValueError("OOXML archive exceeds the aggregate uncompressed-size budget")


def _open_ooxml_document(path: Path):
    """Open DOCM through an in-memory view that only normalizes its main content type."""
    if path.suffix.lower() != ".docm":
        with zipfile.ZipFile(path) as package:
            _validate_ooxml_archive(package)
        return Document(str(path))
    with zipfile.ZipFile(path) as package:
        _validate_ooxml_archive(package)
        content_types_entry = next(
            entry for entry in package.infolist() if entry.filename == "[Content_Types].xml"
        )
        content_types = package.read(content_types_entry)
        if MACRO_ENABLED_MAIN_CONTENT_TYPE not in content_types:
            return Document(str(path))
        view = BytesIO()
        with zipfile.ZipFile(view, "w", compression=zipfile.ZIP_DEFLATED) as sanitized:
            for entry in package.infolist():
                content = package.read(entry.filename)
                if entry.filename == "[Content_Types].xml":
                    content = content.replace(
                        MACRO_ENABLED_MAIN_CONTENT_TYPE, DOCUMENT_MAIN_CONTENT_TYPE
                    )
                sanitized.writestr(entry, content)
    view.seek(0)
    return Document(view)


def _ooxml_field_result_texts(path: Path) -> dict[int, str]:
    """Return visible text for paragraphs containing Word field instructions/results.

    OOXML field instructions are intentionally ignored: they are descriptive XML,
    never commands for this extractor to execute.
    """
    with zipfile.ZipFile(path) as package:
        _validate_ooxml_archive(package)
        document_entry = next(
            entry for entry in package.infolist() if entry.filename == "word/document.xml"
        )
        document_xml = package.read(document_entry)
    root = ElementTree.fromstring(document_xml)
    paragraphs: dict[int, str] = {}
    active_fields: list[str] = []
    for index, paragraph in enumerate(root.findall(".//w:body/w:p", NAMESPACES), start=1):
        has_field_nodes = paragraph.find(".//w:fldChar", NAMESPACES) is not None or paragraph.find(
            ".//w:fldSimple", NAMESPACES
        ) is not None
        track_paragraph = bool(active_fields) or has_field_nodes
        visible_parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{{{WORDPROCESSINGML}}}fldChar":
                field_type = node.get(f"{{{WORDPROCESSINGML}}}fldCharType")
                if field_type == "begin":
                    active_fields.append("instruction")
                elif field_type == "separate" and active_fields:
                    active_fields[-1] = "result"
                elif field_type == "end" and active_fields:
                    active_fields.pop()
                continue
            if node.tag == f"{{{WORDPROCESSINGML}}}instrText":
                continue
            if active_fields and any(state != "result" for state in active_fields):
                continue
            if node.tag == f"{{{WORDPROCESSINGML}}}t":
                visible_parts.append(node.text or "")
            elif node.tag == f"{{{WORDPROCESSINGML}}}tab":
                visible_parts.append("\t")
            elif node.tag in {f"{{{WORDPROCESSINGML}}}br", f"{{{WORDPROCESSINGML}}}cr"}:
                visible_parts.append("\n")
        if track_paragraph:
            paragraphs[index] = "".join(visible_parts)
    return paragraphs


def extract_ooxml(path: Path) -> tuple[tuple[TextBlock, ...], tuple[CitationMention, ...]]:
    """Extract visible OOXML paragraphs without loading or executing macro payloads."""
    document = _open_ooxml_document(path)
    field_results = _ooxml_field_result_texts(path)
    blocks: list[TextBlock] = []
    citations: list[CitationMention] = []
    heading = "(document scope)"

    for index, paragraph in enumerate(document.paragraphs, start=1):
        text = field_results.get(index, paragraph.text or "")
        if not text.strip():
            continue
        style_name = paragraph.style.name if paragraph.style is not None else ""
        style_name = style_name or ""
        if style_name.startswith("Heading"):
            heading = text.strip() or "(document scope)"
        locator = str(index)
        blocks.append(
            TextBlock(
                block_id=f"paragraph-{index}",
                text_original=text,
                text_normalized=normalize_text(text),
                locator_type="paragraph",
                locator_value=locator,
                heading=heading,
            )
        )
        for match in VISIBLE_CITATION_RE.finditer(text):
            citations.append(
                CitationMention(
                    raw_text=match.group(0),
                    citation_keys=(),
                    locator_type="paragraph",
                    locator_value=locator,
                    mapping_status="not-applicable",
                )
            )
    return tuple(blocks), tuple(citations)


def extract_legacy_doc(path: Path) -> tuple[tuple[TextBlock, ...], tuple[CitationMention, ...]]:
    """Convert a legacy DOC in an isolated directory, then read only its DOCX output."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_directory = Path(temporary_directory)
        subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "docx",
                "--outdir",
                str(output_directory),
                str(path),
            ],
            check=True,
        )
        converted_path = output_directory / f"{path.stem}.docx"
        if not converted_path.is_file():
            raise RuntimeError(f"LibreOffice did not create converted DOCX: {converted_path}")
        return extract_ooxml(converted_path)
