"""Format-neutral document records for source checking."""

from .model import CitationMention, DocumentRecord, TextBlock
from .normalize import normalize_text

__version__ = "0.1.0"

__all__ = ["CitationMention", "DocumentRecord", "TextBlock", "__version__", "normalize_text"]
