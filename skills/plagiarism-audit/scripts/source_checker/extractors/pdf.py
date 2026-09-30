"""PDF text extraction with an explicit non-OCR quality state."""

import re
import subprocess
from collections.abc import Sequence
from pathlib import Path

from source_checker.citations import VISIBLE_CITATION_RE
from source_checker.model import CitationMention, TextBlock
from source_checker.normalize import normalize_text


def split_blocks(page_text: str) -> list[str]:
    """Split one physical page into visible paragraph-like text blocks."""
    page_text = page_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not page_text:
        return []
    return [block.strip() for block in re.split(r"\n\s*\n+", page_text) if block.strip()]


def extract_pdf_pages(path: Path) -> tuple[list[str], str]:
    """Extract physical PDF pages, preferring pdftotext before pypdf."""
    try:
        process = subprocess.run(  # noqa: UP022 - preserve legacy subprocess capture behavior
            ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        text = (process.stdout or b"").decode("utf-8", errors="replace")
        pages = text.split("\f")
        if pages and not pages[-1].strip():
            pages.pop()
        return pages, "pdftotext-layout"
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise RuntimeError("Neither pdftotext nor pypdf is available") from error
        reader = PdfReader(str(path))
        return [(page.extract_text() or "") for page in reader.pages], "pypdf"


def _quality(pages: Sequence[str]) -> tuple[str, str]:
    """Return the legacy text-extraction status without attempting OCR."""
    characters = sum(len(re.sub(r"\s+", "", page)) for page in pages)
    replacement = sum(page.count("\ufffd") for page in pages)
    if characters == 0:
        return "empty", "empty"
    per_page = characters / max(len(pages), 1)
    if per_page < 100:
        return "needs_ocr", "sparse"
    if replacement / characters > 0.01:
        return "needs_review", "degraded"
    return "extracted", "good"


def extract_pdf(
    path: Path,
) -> tuple[tuple[TextBlock, ...], tuple[CitationMention, ...], str, str, str]:
    """Extract PDF text blocks and report quality; this function never invokes OCR."""
    pages, extraction_method = extract_pdf_pages(path)
    extraction_status, text_quality = _quality(pages)
    blocks: list[TextBlock] = []
    citations: list[CitationMention] = []
    for page_number, page_text in enumerate(pages, start=1):
        for block_number, text in enumerate(split_blocks(page_text), start=1):
            locator = f"page={page_number};block={block_number}"
            blocks.append(
                TextBlock(
                    block_id=f"pdf-page-{page_number}-block-{block_number}",
                    text_original=text,
                    text_normalized=normalize_text(text),
                    locator_type="pdf-block",
                    locator_value=locator,
                    heading="(document scope)",
                )
            )
            for match in VISIBLE_CITATION_RE.finditer(text):
                citations.append(
                    CitationMention(
                        raw_text=match.group(0),
                        citation_keys=(),
                        locator_type="pdf-block",
                        locator_value=locator,
                        mapping_status="not-applicable",
                    )
                )
    return tuple(blocks), tuple(citations), extraction_status, text_quality, extraction_method
