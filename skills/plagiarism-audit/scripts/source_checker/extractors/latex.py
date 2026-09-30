"""LaTeX prose and citation extraction."""

import re
from pathlib import Path

from source_checker.citations import latex_citation_matches
from source_checker.model import CitationMention, TextBlock
from source_checker.normalize import normalize_text

SECTION_RE = re.compile(r"^\s*\\(?:part|chapter|section|subsection|subsubsection)\*?(?:\[[^\]]*\])?\{([^{}]*)\}")


def _strip_comment(line: str) -> str:
    """Remove an unescaped LaTeX comment, retaining escaped percent signs."""
    for index, character in enumerate(line):
        if character != "%":
            continue
        preceding_backslashes = 0
        cursor = index - 1
        while cursor >= 0 and line[cursor] == "\\":
            preceding_backslashes += 1
            cursor -= 1
        if preceding_backslashes % 2 == 0:
            return line[:index]
    return line


def _line_locator(start_line: int, end_line: int) -> str:
    return str(start_line) if start_line == end_line else f"{start_line}-{end_line}"


def extract_latex(path: Path) -> tuple[tuple[TextBlock, ...], tuple[CitationMention, ...]]:
    """Extract visible LaTeX lines and supported explicit citation commands."""
    blocks: list[TextBlock] = []
    citations: list[CitationMention] = []
    heading = "(document scope)"
    citation_lines: list[str] = []

    for line_number, original_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = _strip_comment(original_line)
        citation_line = line
        section = SECTION_RE.match(line)
        if section:
            heading = section.group(1).strip() or "(document scope)"
            line = line[section.end():]
            citation_line = f"{' ' * section.end()}{line}"
        citation_lines.append(citation_line)
        if not line.strip():
            continue

        visible_line = line.replace(r"\%", "%")
        locator = str(line_number)
        blocks.append(
            TextBlock(
                block_id=f"line-{line_number}",
                text_original=visible_line,
                text_normalized=normalize_text(visible_line),
                locator_type="line",
                locator_value=locator,
                heading=heading,
            )
        )
    citation_text = "\n".join(citation_lines)
    for raw_text, keys, start_offset, end_offset in latex_citation_matches(citation_text):
        start_line = citation_text.count("\n", 0, start_offset) + 1
        end_line = citation_text.count("\n", 0, end_offset) + 1
        citations.append(
            CitationMention(
                raw_text=raw_text,
                citation_keys=keys,
                locator_type="line",
                locator_value=_line_locator(start_line, end_line),
                mapping_status="unresolved",
            )
        )

    return tuple(blocks), tuple(citations)
