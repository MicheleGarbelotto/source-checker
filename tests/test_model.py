from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from source_checker.model import CitationMention, DocumentRecord, TextBlock
from source_checker.normalize import normalize_text


def _block(block_id: str = "b1") -> TextBlock:
    return TextBlock(
        block_id=block_id,
        text_original="A cited claim.",
        text_normalized="a cited claim.",
        locator_type="paragraph",
        locator_value="12",
        heading="Results",
    )


def _citation(mapping_status: str = "resolved") -> CitationMention:
    return CitationMention(
        raw_text="(Alpha, 2020)",
        citation_keys=("alpha2020",),
        locator_type="paragraph",
        locator_value="12",
        mapping_status=mapping_status,
    )


def _document(*blocks: TextBlock) -> DocumentRecord:
    return DocumentRecord(
        document_id="target-1",
        role="target",
        path="draft.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        sha256="abc",
        extraction_method="python-docx",
        extraction_status="extracted",
        text_quality="good",
        conversion_note="",
        blocks=blocks,
        citations=(_citation(),),
    )


def test_document_record_serializes_format_neutral_locators():
    block = _block()
    citation = _citation()
    document = DocumentRecord(
        document_id="target-1",
        role="target",
        path="draft.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        sha256="abc",
        extraction_method="python-docx",
        extraction_status="extracted",
        text_quality="good",
        conversion_note="",
        blocks=(block,),
        citations=(citation,),
    )
    assert document.to_dict()["blocks"][0]["locator_type"] == "paragraph"


def test_normalize_text_preserves_original_only_in_caller():
    assert normalize_text("inter-\nnational  TEST") == "international test"


def test_normalize_text_applies_nfkc_and_casefold():
    assert normalize_text("Ｆｕｌｌｗｉｄｔｈ Straße") == "fullwidth strasse"


def test_records_are_frozen_and_use_immutable_sequences():
    document = _document(_block())
    assert isinstance(document.blocks, tuple)
    assert isinstance(document.citations, tuple)
    with pytest.raises(FrozenInstanceError):
        setattr(document, "role", "source")  # noqa: B010


def test_text_block_is_frozen():
    block = _block()
    with pytest.raises(FrozenInstanceError):
        setattr(block, "heading", "Discussion")  # noqa: B010


def test_citation_mention_is_frozen():
    citation = _citation()
    with pytest.raises(FrozenInstanceError):
        setattr(citation, "raw_text", "[Alpha, 2020]")  # noqa: B010


def test_sequence_inputs_are_defensively_normalized_to_tuples():
    citation_keys = cast(Any, ["alpha2020"])
    block = _block()
    blocks = cast(Any, [block])
    citations = cast(Any, [_citation()])
    citation = CitationMention("(Alpha, 2020)", citation_keys, "paragraph", "12", "resolved")
    document = DocumentRecord(
        document_id="target-1",
        role="target",
        path="draft.docx",
        media_type="text/plain",
        sha256="abc",
        extraction_method="test",
        extraction_status="extracted",
        text_quality="good",
        conversion_note="",
        blocks=blocks,
        citations=citations,
    )
    citation_keys.append("beta2021")
    blocks.clear()
    citations.clear()
    assert citation.citation_keys == ("alpha2020",)
    assert isinstance(citation.citation_keys, tuple)
    assert document.blocks == (block,)
    assert document.citations == (_citation(),)
    assert isinstance(document.blocks, tuple)
    assert isinstance(document.citations, tuple)


@pytest.mark.parametrize("role", ["invalid", "Target", ""])
def test_document_record_rejects_invalid_role(role):
    with pytest.raises(ValueError):
        DocumentRecord(
            document_id="id",
            role=role,
            path="draft.docx",
            media_type="text/plain",
            sha256="abc",
            extraction_method="test",
            extraction_status="extracted",
            text_quality="good",
            conversion_note="",
            blocks=(),
            citations=(),
        )


@pytest.mark.parametrize("mapping_status", ["invalid", "Resolved", ""])
def test_citation_mention_rejects_invalid_mapping_status(mapping_status):
    with pytest.raises(ValueError):
        _citation(mapping_status)


@pytest.mark.parametrize("factory", [
    lambda: TextBlock("b1", "original", "normalized", "", "1", "Heading"),
    lambda: TextBlock("b1", "original", "normalized", "paragraph", "", "Heading"),
    lambda: TextBlock("b1", "original", "normalized", cast(Any, None), "1", "Heading"),
    lambda: TextBlock("b1", "original", "normalized", "paragraph", cast(Any, None), "Heading"),
    lambda: CitationMention("raw", ("key",), "", "1", "resolved"),
    lambda: CitationMention("raw", ("key",), "paragraph", "", "resolved"),
    lambda: CitationMention("raw", ("key",), cast(Any, None), "1", "resolved"),
    lambda: CitationMention("raw", ("key",), "paragraph", cast(Any, None), "resolved"),
])
def test_text_blocks_and_citations_require_non_empty_locators(factory):
    with pytest.raises(ValueError):
        factory()


def test_document_record_rejects_duplicate_block_ids():
    with pytest.raises(ValueError):
        _document(_block("same"), _block("same"))
