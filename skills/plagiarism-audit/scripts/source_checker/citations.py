"""Citation-token helpers shared by format-specific extractors."""

import re

PANDOC_CITATION_RE = re.compile(r"(?<![\w@.])@([A-Za-z0-9][A-Za-z0-9_.:+\-]*)")
LATEX_CITATION_RE = re.compile(
    r"\\(?:cite|citep|citet|autocite|parencite|textcite)\*?(?:\s*\[[^\]]*\])*\s*\{([^{}]*)\}"
)
VISIBLE_CITATION_RE = re.compile(
    r"\[@[^\]]+\]|\([^()\n]*\b(?:18|19|20)\d{2}[a-z]?\b[^()\n]*\)"
)


def pandoc_citation_keys(text: str) -> tuple[str, ...]:
    """Return Pandoc-style citekeys from *text* in encounter order."""
    return tuple(match.group(1).rstrip(".,;:!?") for match in PANDOC_CITATION_RE.finditer(text))


def latex_citation_matches(text: str) -> tuple[tuple[str, tuple[str, ...], int, int], ...]:
    """Return supported LaTeX citation commands, citekeys, and source offsets."""
    matches: list[tuple[str, tuple[str, ...], int, int]] = []
    for match in LATEX_CITATION_RE.finditer(text):
        keys = tuple(
            re.sub(r"\s+", "", key) for key in match.group(1).split(",") if key.strip()
        )
        if keys:
            matches.append((match.group(0), keys, match.start(), match.end()))
    return tuple(matches)
