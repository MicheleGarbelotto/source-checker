from __future__ import annotations

import pytest

from source_checker.bibliography import make_source_record
from source_checker.mapping import MappingResult, map_source


def source(**overrides):
    defaults = {
        "aliases": (),
        "title": "",
        "authors": (),
        "year": None,
        "doi": "",
        "local_files": (),
        "provider": "test",
    }
    defaults.update(overrides)
    return make_source_record(**defaults)


def test_normalized_doi_is_the_strongest_mapping_rule() -> None:
    by_doi = source(doi="10.1000/ABC", aliases=("other",), title="Different")
    by_alias = source(aliases=("citation",), title="Same title")

    result = map_source(
        (by_alias, by_doi), doi="https://doi.org/10.1000/abc)", identifiers=("citation",)
    )

    assert result == MappingResult(
        status="resolved",
        source_ids=(by_doi.source_id,),
        rule="doi",
        confidence_note="exact normalized DOI",
    )


def test_case_insensitive_alias_is_used_after_doi() -> None:
    record = source(aliases=("ZOTERO:AbC123", "Smith2020"))

    result = map_source((record,), identifiers=("smith2020",))

    assert result.status == "resolved"
    assert result.source_ids == (record.source_id,)
    assert result.rule == "identifier"
    assert result.confidence_note == "exact case-insensitive identifier or alias"


def test_unicode_normalized_title_family_name_and_year_form_a_fingerprint() -> None:
    record = source(
        title="Café: Social-Comparison Seeking",
        authors=("Ada García",),
        year=2024,
    )

    result = map_source(
        (record,), title="CAFE social comparison seeking", authors=("García, A.",), year=2024
    )

    assert result.status == "resolved"
    assert result.source_ids == (record.source_id,)
    assert result.rule == "title-author-year"


def test_unique_normalized_title_is_used_only_after_fingerprint() -> None:
    record = source(title="A title, with punctuation!", authors=("Someone Else",), year=1999)

    result = map_source((record,), title="a TITLE with punctuation")

    assert result.status == "resolved"
    assert result.source_ids == (record.source_id,)
    assert result.rule == "title"


def test_unique_filename_or_document_metadata_is_last_rule() -> None:
    record = source(title="Unrelated", local_files=("/corpus/Smith 2020.pdf",))

    result = map_source((record,), filenames=("smith 2020.PDF",))

    assert result.status == "resolved"
    assert result.source_ids == (record.source_id,)
    assert result.rule == "filename"


def test_stronger_alias_rule_wins_over_title_rule() -> None:
    alias_record = source(aliases=("key",), title="Other")
    title_record = source(title="Shared title")

    result = map_source((title_record, alias_record), identifiers=("KEY",), title="shared title")

    assert result.source_ids == (alias_record.source_id,)
    assert result.rule == "identifier"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"identifiers": ("duplicate",)},
        {"title": "Same", "authors": ("Jones",), "year": 2020},
        {"title": "Same"},
        {"filenames": ("same.pdf",)},
    ],
)
def test_equally_plausible_candidates_are_ambiguous_in_source_id_order(kwargs: dict) -> None:
    first = source(aliases=("duplicate",), title="Same", authors=("Ada Jones",), year=2020, local_files=("/a/same.pdf",))
    second = source(aliases=("duplicate",), title="Same", authors=("Bea Jones",), year=2020, local_files=("/b/same.pdf",))

    result = map_source((second, first), **kwargs)

    assert result.status == "ambiguous"
    assert result.source_ids == tuple(sorted((first.source_id, second.source_id)))
    assert result.rule in {"identifier", "title-author-year", "title", "filename"}


def test_absent_match_is_unresolved() -> None:
    result = map_source((source(aliases=("present",)),), identifiers=("missing",))

    assert result == MappingResult("unresolved", (), "none", "no deterministic match")


def test_mapping_result_validates_its_public_invariants() -> None:
    with pytest.raises(ValueError, match="resolved"):
        MappingResult("resolved", (), "doi", "note")
    with pytest.raises(ValueError, match="ambiguous"):
        MappingResult("ambiguous", ("one",), "doi", "note")


def test_duplicate_source_ids_merge_aliases_and_files_independently_of_input_order() -> None:
    first = source(doi="10.1000/duplicate", aliases=("a",), local_files=("/corpus/a.pdf",))
    second = source(doi="10.1000/duplicate", aliases=("b",), local_files=("/corpus/b.pdf",))

    forward = map_source((first, second), identifiers=("b",))
    backward = map_source((second, first), identifiers=("b",))
    by_file = map_source((second, first), filenames=("a.pdf",))

    assert forward == backward == MappingResult(
        "resolved", (first.source_id,), "identifier", "exact case-insensitive identifier or alias"
    )
    assert by_file.status == "resolved"
    assert by_file.source_ids == (first.source_id,)


def test_compound_comma_family_name_does_not_match_a_shorter_family_name() -> None:
    maria = source(title="Shared", authors=("Maria Garcia Marquez",), year=2020)
    john = source(title="Shared", authors=("John Garcia",), year=2020)

    result = map_source(
        (john, maria), title="Shared", authors=("Garcia Marquez, M.",), year=2020
    )

    assert result.status == "resolved"
    assert result.source_ids == (maria.source_id,)
    assert result.rule == "title-author-year"


def test_compound_particle_family_name_matches_natural_order_source_name() -> None:
    beethoven = source(title="Sonata", authors=("Ludwig van Beethoven",), year=1801)
    other = source(title="Sonata", authors=("Ada Beethoven",), year=1801)

    result = map_source(
        (other, beethoven), title="Sonata", authors=("van Beethoven, L.",), year=1801
    )

    assert result.status == "resolved"
    assert result.source_ids == (beethoven.source_id,)
    assert result.rule == "title-author-year"


def test_matching_uses_original_metadata_variants_before_deduplicating_source_ids() -> None:
    a_zed = source(doi="10.1000/a", aliases=("a",), title="Zed")
    a_alpha = source(doi="10.1000/a", aliases=("b",), title="Alpha")
    b_zed = source(doi="10.1000/b", title="Zed")

    title_result = map_source((a_zed, a_alpha, b_zed), title="Zed")
    alias_result = map_source((a_zed, a_alpha, b_zed), identifiers=("b",))

    assert title_result.status == "ambiguous"
    assert title_result.source_ids == tuple(sorted((a_zed.source_id, b_zed.source_id)))
    assert title_result.rule == "title"
    assert alias_result.status == "resolved"
    assert alias_result.source_ids == (a_zed.source_id,)


def test_ambiguous_title_uses_a_status_consistent_confidence_note() -> None:
    first = source(title="Same title", authors=("Ada",))
    second = source(title="Same title", authors=("Bea",))

    result = map_source((first, second), title="Same title")

    assert result.status == "ambiguous"
    assert "unique" not in result.confidence_note
    assert result.confidence_note == "normalized title match"


def test_ambiguous_filename_uses_a_status_consistent_confidence_note() -> None:
    first = source(local_files=("/a/same.pdf",), aliases=("first",))
    second = source(local_files=("/b/same.pdf",), aliases=("second",))

    result = map_source((first, second), filenames=("same.pdf",))

    assert result.status == "ambiguous"
    assert "unique" not in result.confidence_note
    assert result.confidence_note == "normalized filename or document metadata match"
