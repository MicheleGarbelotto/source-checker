"""Immutable, format-neutral document model."""

from dataclasses import asdict, dataclass
from typing import Any


def _require_locator(locator_type: str, locator_value: str) -> None:
    if (
        not isinstance(locator_type, str)
        or not isinstance(locator_value, str)
        or not locator_type.strip()
        or not locator_value.strip()
    ):
        raise ValueError("locator_type and locator_value must be non-empty")


@dataclass(frozen=True)
class TextBlock:
    block_id: str
    text_original: str
    text_normalized: str
    locator_type: str
    locator_value: str
    heading: str

    def __post_init__(self) -> None:
        _require_locator(self.locator_type, self.locator_value)


@dataclass(frozen=True)
class CitationMention:
    raw_text: str
    citation_keys: tuple[str, ...]
    locator_type: str
    locator_value: str
    mapping_status: str

    def __post_init__(self) -> None:
        _require_locator(self.locator_type, self.locator_value)
        if self.mapping_status not in {"resolved", "ambiguous", "unresolved", "not-applicable"}:
            raise ValueError("invalid mapping_status")
        object.__setattr__(self, "citation_keys", tuple(self.citation_keys))


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    role: str
    path: str
    media_type: str
    sha256: str
    extraction_method: str
    extraction_status: str
    text_quality: str
    conversion_note: str
    blocks: tuple[TextBlock, ...]
    citations: tuple[CitationMention, ...]

    def __post_init__(self) -> None:
        if self.role not in {"target", "source"}:
            raise ValueError("role must be 'target' or 'source'")
        blocks = tuple(self.blocks)
        if len({block.block_id for block in blocks}) != len(blocks):
            raise ValueError("block_id values must be unique within a document")
        object.__setattr__(self, "blocks", blocks)
        object.__setattr__(self, "citations", tuple(self.citations))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
