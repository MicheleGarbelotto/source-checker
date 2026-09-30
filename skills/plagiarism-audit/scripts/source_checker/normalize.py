"""Text normalization shared by document extractors."""

import re
import unicodedata


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.casefold()
