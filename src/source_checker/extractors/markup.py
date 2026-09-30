"""Native extraction for Markdown, Quarto Markdown, and plain text."""

import re
from pathlib import Path

from source_checker.citations import pandoc_citation_keys
from source_checker.model import CitationMention, TextBlock
from source_checker.normalize import normalize_text

HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
YAML_MAPPING_RE = re.compile(r"^\s*[A-Za-z][A-Za-z0-9_-]*\s*:")


def _clean_heading(value: str) -> str:
    return re.sub(r"\s*\{[^{}]*\}\s*$", "", value).strip()


def _line_locator(start_line: int, end_line: int) -> str:
    return str(start_line) if start_line == end_line else f"{start_line}-{end_line}"


def _is_fence_closer(line: str, character: str, minimum_length: int) -> bool:
    return re.fullmatch(rf"\s*{re.escape(character)}{{{minimum_length},}}\s*", line) is not None


def _front_matter_end_line(lines: list[str]) -> int | None:
    if not lines or lines[0].lstrip("\ufeff").strip() != "---":
        return None
    for line_number, line in enumerate(lines[1:], start=2):
        if line.strip() in {"---", "..."}:
            interior = lines[1 : line_number - 1]
            return line_number if any(YAML_MAPPING_RE.match(item) for item in interior) else None
    return None


def extract_markup(path: Path) -> tuple[tuple[TextBlock, ...], tuple[CitationMention, ...]]:
    """Extract prose blocks and Pandoc citekeys while omitting YAML and fenced code."""
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[TextBlock] = []
    citations: list[CitationMention] = []
    heading = "(document scope)"
    paragraph: list[str] = []
    paragraph_start = 0
    in_fence = False
    fence_character = ""
    fence_length = 0
    front_matter_end_line = _front_matter_end_line(lines)
    if lines:
        lines[0] = lines[0].lstrip("\ufeff")

    def flush_paragraph(end_line: int) -> None:
        nonlocal paragraph, paragraph_start
        if not paragraph:
            return
        text = "\n".join(paragraph)
        locator = _line_locator(paragraph_start, end_line)
        blocks.append(
            TextBlock(
                block_id=f"line-{paragraph_start}",
                text_original=text,
                text_normalized=normalize_text(text),
                locator_type="line",
                locator_value=locator,
                heading=heading,
            )
        )
        paragraph = []
        paragraph_start = 0

    for line_number, line in enumerate(lines, start=1):
        if front_matter_end_line is not None and line_number <= front_matter_end_line:
            continue

        if in_fence:
            if _is_fence_closer(line, fence_character, fence_length):
                in_fence = False
                fence_character = ""
                fence_length = 0
            continue
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            flush_paragraph(line_number - 1)
            in_fence = True
            fence_character = marker[0]
            fence_length = len(marker)
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            flush_paragraph(line_number - 1)
            heading = _clean_heading(heading_match.group(1)) or "(document scope)"
            continue
        if not line.strip():
            flush_paragraph(line_number - 1)
            continue

        if not paragraph:
            paragraph_start = line_number
        paragraph.append(line)
        locator = _line_locator(line_number, line_number)
        for key in pandoc_citation_keys(line):
            citations.append(
                CitationMention(
                    raw_text=f"@{key}",
                    citation_keys=(key,),
                    locator_type="line",
                    locator_value=locator,
                    mapping_status="unresolved",
                )
            )

    flush_paragraph(len(lines))
    return tuple(blocks), tuple(citations)


def extract_plain_text(path: Path) -> tuple[tuple[TextBlock, ...], tuple[CitationMention, ...]]:
    """Extract non-empty text lines without applying markup-specific citation parsing."""
    blocks: list[TextBlock] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            blocks.append(
                TextBlock(
                    block_id=f"line-{line_number}",
                    text_original=line,
                    text_normalized=normalize_text(line),
                    locator_type="line",
                    locator_value=str(line_number),
                    heading="(document scope)",
                )
            )
    return tuple(blocks), ()
