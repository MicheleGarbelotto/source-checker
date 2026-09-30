"""Dispatch local supported document formats to neutral extraction records."""

import hashlib
import mimetypes
from pathlib import Path

from source_checker.extractors.html import extract_html
from source_checker.extractors.latex import extract_latex
from source_checker.extractors.markup import extract_markup, extract_plain_text
from source_checker.extractors.office import extract_legacy_doc, extract_ooxml
from source_checker.extractors.pdf import extract_pdf
from source_checker.model import CitationMention, DocumentRecord, TextBlock

SUPPORTED_SUFFIXES = (
    ".qmd",
    ".md",
    ".txt",
    ".tex",
    ".latex",
    ".html",
    ".htm",
    ".docx",
    ".docm",
    ".doc",
    ".pdf",
)


class UnsupportedFormatError(ValueError):
    """Raised when no extractor is available for a local input suffix."""


class ExtractionConsistencyError(RuntimeError):
    """Raised when a local document changes while it is being extracted."""


def media_type_for(path: Path | str) -> str:
    """Return the canonical media type used by the shared document adapters."""
    path = Path(path)
    explicit = {
        ".qmd": "text/markdown",
        ".md": "text/markdown",
        ".tex": "text/x-tex",
        ".latex": "text/x-tex",
        ".html": "text/html",
        ".htm": "text/html",
        ".txt": "text/plain",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docm": "application/vnd.ms-word.document.macroEnabled.12",
        ".doc": "application/msword",
        ".pdf": "application/pdf",
    }
    return explicit.get(path.suffix.lower(), mimetypes.guess_type(path.name)[0] or "application/octet-stream")


def extract_document(path: Path | str, role: str) -> DocumentRecord:
    """Extract a supported local document into the common neutral record model."""
    document_path = Path(path)
    suffix = document_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(SUPPORTED_SUFFIXES)
        raise UnsupportedFormatError(f"Unsupported format {suffix or '(none)'}. Supported formats: {supported}")

    initial_content = document_path.read_bytes()

    blocks: tuple[TextBlock, ...]
    citations: tuple[CitationMention, ...]
    extraction_method: str
    extraction_status = "extracted"
    text_quality = "good"
    conversion_note = ""
    if suffix in {".qmd", ".md"}:
        blocks, citations = extract_markup(document_path)
        extraction_method = "markup"
    elif suffix == ".txt":
        blocks, citations = extract_plain_text(document_path)
        extraction_method = "plain-text"
    elif suffix in {".tex", ".latex"}:
        blocks, citations = extract_latex(document_path)
        extraction_method = "latex"
    elif suffix in {".docx", ".docm"}:
        blocks, citations = extract_ooxml(document_path)
        extraction_method = "ooxml"
    elif suffix == ".doc":
        blocks, citations = extract_legacy_doc(document_path)
        extraction_method = "libreoffice-docx"
        conversion_note = "Converted from .doc with LibreOffice"
    elif suffix == ".pdf":
        blocks, citations, extraction_status, text_quality, extraction_method = extract_pdf(document_path)
    else:
        blocks, citations = extract_html(document_path)
        extraction_method = "html"

    final_content = document_path.read_bytes()
    if initial_content != final_content:
        raise ExtractionConsistencyError(f"Document changed during extraction: {document_path}")
    digest = hashlib.sha256(final_content).hexdigest()
    return DocumentRecord(
        document_id=f"{role}-{digest}",
        role=role,
        path=str(document_path.resolve()),
        media_type=media_type_for(document_path),
        sha256=digest,
        extraction_method=extraction_method,
        extraction_status=extraction_status,
        text_quality=text_quality,
        conversion_note=conversion_note,
        blocks=blocks,
        citations=citations,
    )


__all__ = [
    "SUPPORTED_SUFFIXES",
    "ExtractionConsistencyError",
    "UnsupportedFormatError",
    "extract_document",
    "media_type_for",
]
