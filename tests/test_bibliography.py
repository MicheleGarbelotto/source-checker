from __future__ import annotations

import hashlib
import json
import os
from email.message import Message
from pathlib import Path
from typing import Any, Self
from urllib.error import HTTPError

import pytest

from source_checker.bibliography import bibtex as bibtex_module
from source_checker.bibliography import (
    load_bibtex,
    load_csl_json,
    load_ris,
    make_source_record,
    normalize_doi,
    resolve_local_path,
)
from source_checker.resolvers import local as local_module
from source_checker.resolvers.exports import UnsupportedExportError, load_export
from source_checker.resolvers.local import resolve_local_sources
from source_checker.resolvers.zotero import ZoteroLocalClient, resolve_zotero

FIXTURES = Path(__file__).parent / "fixtures" / "bibliographies"


@pytest.mark.parametrize(
    ("loader", "filename", "provider"),
    [
        (load_bibtex, "sample.bib", "bibtex"),
        (load_ris, "sample.ris", "ris"),
        (load_csl_json, "sample.json", "csl-json"),
    ],
)
def test_export_loaders_emit_neutral_conceptual_source(loader: Any, filename: str, provider: str):
    record = loader(FIXTURES / filename)[0]

    assert record.source_id == "doi:10.1000/abc.def"
    assert {"Theory2024", "zotero-item-ABCD1234"} <= set(record.aliases)
    assert record.title == 'Seeking Comparison: A "Conceptual" Account'
    assert record.authors == ("Jane Doe", "Ana de la Cruz")
    assert record.year == 2024
    assert record.doi == "10.1000/abc.def"
    assert record.local_files == (
        str((FIXTURES / "files" / "theory.pdf").resolve()),
        str((FIXTURES / "files" / "supplement.pdf").resolve()),
    )
    assert record.provider == provider


def test_csl_loader_represents_missing_optional_fields_safely():
    record = load_csl_json(FIXTURES / "sample.json")[1]

    assert record.title == ""
    assert record.authors == ()
    assert record.year is None
    assert record.doi == ""
    assert record.local_files == ()
    assert record.aliases == ("missing-fields",)


@pytest.mark.parametrize("filename", ["sample.BIB", "sample.RIS", "sample.JSON"])
def test_export_dispatcher_matches_extensions_case_insensitively(tmp_path: Path, filename: str):
    source = FIXTURES / f"sample.{filename.rsplit('.', 1)[1].lower()}"
    copied = tmp_path / filename
    copied.write_bytes(source.read_bytes())

    assert load_export(copied)[0].source_id == "doi:10.1000/abc.def"


def test_export_dispatcher_rejects_unsupported_exports(tmp_path: Path):
    export = tmp_path / "source.txt"
    export.write_text("not an export", encoding="utf-8")

    with pytest.raises(UnsupportedExportError, match=".txt"):
        load_export(export)


def test_local_resolver_expands_explicit_files_and_directories_deterministically(tmp_path: Path):
    first = tmp_path / "z.pdf"
    first.write_bytes(b"first")
    directory = tmp_path / "attachments"
    directory.mkdir()
    second = directory / "a.txt"
    second.write_text("second", encoding="utf-8")

    records = resolve_local_sources([first, directory])

    assert [record.path for record in records] == [str(second.resolve()), str(first.resolve())]
    assert [record.sha256 for record in records] == [
        hashlib.sha256(b"second").hexdigest(),
        hashlib.sha256(b"first").hexdigest(),
    ]
    assert records[0].media_type == "text/plain"
    assert records[1].media_type == "application/pdf"


def test_local_resolver_rejects_missing_paths_without_database_access(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        resolve_local_sources([tmp_path / "not-present.pdf"])


def test_bibtex_mendeley_file_links_preserve_drives_uris_descriptions_and_multiple_entries(
    tmp_path: Path,
):
    export = tmp_path / "library.bib"
    export.write_text(
        """@article{links,
  title = {Links},
  file = {:C:/papers/a.pdf:PDF;C:/papers/a.pdf;:file:///C:/papers/a.pdf:PDF;Description:files/a.pdf:application/pdf}
}""",
        encoding="utf-8",
    )

    record = load_bibtex(export)[0]

    assert record.local_files == (
        str(Path("C:/papers/a.pdf").resolve()),
        str((tmp_path / "files" / "a.pdf").resolve()),
    )


def test_bibtex_braced_quote_does_not_hide_following_entries(tmp_path: Path):
    export = tmp_path / "quoted.bib"
    export.write_text(
        """@article{first, title = {A 6" display}}
@article{second, title = {Second entry}}""",
        encoding="utf-8",
    )

    records = load_bibtex(export)

    assert [(record.aliases, record.title) for record in records] == [
        (("first",), 'A 6" display'),
        (("second",), "Second entry"),
    ]


def test_ris_links_keep_relative_files_and_exclude_http_urls(tmp_path: Path):
    export = tmp_path / "links.ris"
    export.write_text(
        """TY  - JOUR
TI  - Linked RIS
UR  - files/from-ur.pdf
L1  - https://example.test/full-text.pdf
L2  - file:///C:/papers/linked.pdf
ER  -""",
        encoding="utf-8",
    )

    record = load_ris(export)[0]

    assert record.url == "files/from-ur.pdf"
    assert record.local_files == (
        str((tmp_path / "files" / "from-ur.pdf").resolve()),
        str(Path("C:/papers/linked.pdf").resolve()),
    )


def test_ris_m3_work_type_is_not_used_as_a_doi_or_shared_identity(tmp_path: Path):
    export = tmp_path / "m3.ris"
    export.write_text(
        """TY  - JOUR
ID  - one
TI  - First
M3  - Journal Article
ER  -
TY  - JOUR
ID  - two
TI  - Second
M3  - Journal Article
ER  -""",
        encoding="utf-8",
    )

    first, second = load_ris(export)

    assert first.doi == second.doi == ""
    assert first.source_id != second.source_id


def test_csl_null_scalars_stay_missing_and_titled_records_do_not_collide(tmp_path: Path):
    export = tmp_path / "nulls.json"
    export.write_text(
        json.dumps(
            [
                {"id": "one", "title": "First", "DOI": None, "URL": None, "author": None},
                {"id": "two", "title": "Second", "DOI": None, "URL": None, "attachment": None},
            ]
        ),
        encoding="utf-8",
    )

    first, second = load_csl_json(export)

    assert (first.doi, first.url, first.authors) == ("", "", ())
    assert (second.doi, second.url, second.local_files) == ("", "", ())
    assert first.source_id != second.source_id


def test_non_bibtex_providers_preserve_literal_braces_and_tilde(tmp_path: Path):
    csl = tmp_path / "literal.json"
    csl.write_text(json.dumps({"id": "csl", "title": "Set {A} ~ B"}), encoding="utf-8")
    ris = tmp_path / "literal.ris"
    ris.write_text("TY  - JOUR\nID  - ris\nTI  - Set {A} ~ B\nER  -", encoding="utf-8")
    routes = {
        "/api/users/0/items?limit=1": [],
        "/api/users/0/items/DIRECT": {"data": {"key": "DIRECT", "title": "Set {A} ~ B", "DOI": None}},
        "/api/users/0/items/DIRECT/children": [],
    }
    client = ZoteroLocalClient(
        opener=lambda request, timeout: _FakeResponse(routes[request.full_url.split("23119", 1)[1]])
    )

    zotero = resolve_zotero("literal", item_key="DIRECT", client=client)

    assert load_csl_json(csl)[0].title == "Set {A} ~ B"
    assert load_ris(ris)[0].title == "Set {A} ~ B"
    assert zotero.source is not None and zotero.source.title == "Set {A} ~ B"
    assert zotero.source.doi == ""


def test_csl_attachments_keep_only_local_paths_and_file_uris(tmp_path: Path):
    export = tmp_path / "attachments.json"
    export.write_text(
        json.dumps(
            {
                "id": "attachments",
                "attachment": ["files/local.pdf", "file:///C:/papers/uri.pdf", "https://example.test/remote.pdf"],
            }
        ),
        encoding="utf-8",
    )

    record = load_csl_json(export)[0]

    assert record.local_files == (
        str((tmp_path / "files" / "local.pdf").resolve()),
        str(Path("C:/papers/uri.pdf").resolve()),
    )


def test_file_uri_authority_is_preserved_and_localhost_is_local(tmp_path: Path):
    network = resolve_local_path("file://server/share/paper.pdf", tmp_path / "export.bib")
    localhost = resolve_local_path("file://localhost/C:/papers/local.pdf", tmp_path / "export.bib")

    if os.name == "nt":
        assert network == r"\\server\share\paper.pdf"
    else:
        assert network.endswith("/server/share/paper.pdf")
    assert "localhost" not in localhost.casefold()
    expected_localhost = Path("C:/papers/local.pdf") if os.name == "nt" else Path("/C:/papers/local.pdf")
    assert localhost == str(expected_localhost.resolve())


def test_bibtex_entry_scanner_uses_a_compiled_start_pattern():
    assert bibtex_module._ENTRY_START.search("@article{key, title={Title}}") is not None


def test_local_sort_key_breaks_casefold_ties_by_original_path():
    assert local_module._path_sort_key(Path("A.pdf")) < local_module._path_sort_key(Path("a.pdf"))


def test_doi_normalization_preserves_balanced_doi_punctuation_and_stable_ids():
    resolver_form = "https://doi.org/10.1000/example(1)"
    plain_form = "doi:10.1000/example(1)."

    first = make_source_record(title="Stable", doi=resolver_form, provider="bibtex")
    second = make_source_record(title="Stable", doi=plain_form, provider="ris")

    assert normalize_doi(plain_form) == "10.1000/example(1)"
    assert first.source_id == second.source_id == "doi:10.1000/example(1)"


def test_source_identity_uses_aliases_or_files_only_when_metadata_is_absent(tmp_path: Path):
    metadata_bib = make_source_record(
        aliases=("bib-key",), title="Shared metadata", authors=("Jane Doe",), year=2024, provider="bibtex"
    )
    metadata_ris = make_source_record(
        aliases=("manager-key",), title="Shared metadata", authors=("Jane Doe",), year=2024, provider="ris"
    )
    sparse_alias = make_source_record(aliases=("alpha",), provider="bibtex")
    sparse_file = make_source_record(local_files=(str(tmp_path / "beta.pdf"),), provider="ris")

    assert metadata_bib.source_id == metadata_ris.source_id
    assert sparse_alias.source_id != sparse_file.source_id


def test_bibtex_corporate_author_does_not_split_on_braced_and(tmp_path: Path):
    export = tmp_path / "corporate.bib"
    export.write_text(
        "@report{corp, author = {{Research and Development Group}}, title = {Corporate}}",
        encoding="utf-8",
    )

    assert load_bibtex(export)[0].authors == ("Research and Development Group",)


def test_bibtex_authors_split_whitespace_and_preserve_double_braced_corporate_names(tmp_path: Path):
    export = tmp_path / "bibtex-authors.bib"
    export.write_text(
        """@article{people, author = {Doe, Jane and
Roe, John}, title = {People}}
@report{corporate, author = {{Research, Development}}, title = {Corporate}}""",
        encoding="utf-8",
    )

    people, corporate = load_bibtex(export)

    assert people.authors == ("Jane Doe", "John Roe")
    assert corporate.authors == ("Research, Development",)


def test_bibtex_protects_each_corporate_author_token_before_personal_name_normalization(
    tmp_path: Path,
):
    export = tmp_path / "mixed-authors.bib"
    export.write_text(
        """@article{corporate-first, author = {{Research, Development} and Doe, Jane}, title = {First}}
@article{corporate-last, author = {Doe, Jane and {Research, Development}}, title = {Last}}""",
        encoding="utf-8",
    )

    corporate_first, corporate_last = load_bibtex(export)

    assert corporate_first.authors == ("Research, Development", "Jane Doe")
    assert corporate_last.authors == ("Jane Doe", "Research, Development")


def test_bibtex_parenthesis_entries_ignore_quotes_inside_braced_values(tmp_path: Path):
    export = tmp_path / "parentheses.bib"
    export.write_text(
        '@article(a,title={A 6" display},year={2024})\n@article{b,title={Second},year={2025}}',
        encoding="utf-8",
    )

    records = load_bibtex(export)

    assert [(record.aliases, record.title, record.year) for record in records] == [
        (("a",), 'A 6" display', 2024),
        (("b",), "Second", 2025),
    ]


def test_bibtex_mendeley_links_decode_escaped_drives_and_supported_document_extensions(
    tmp_path: Path,
):
    export = tmp_path / "mendeley-documents.bib"
    export.write_text(
        r"@article{documents, title = {Documents}, file = {:C\:/papers/a.pdf:PDF;Description:files/a.docx:application/vnd.openxmlformats-officedocument.wordprocessingml.document;https://example.test/remote.docx}}",
        encoding="utf-8",
    )

    record = load_bibtex(export)[0]

    assert record.local_files == (
        str(Path("C:/papers/a.pdf").resolve()),
        str((tmp_path / "files" / "a.docx").resolve()),
    )


def test_csl_authors_preserve_literal_order_and_non_dropping_particle(tmp_path: Path):
    export = tmp_path / "authors.json"
    export.write_text(
        json.dumps(
            [
                {
                    "id": "authors",
                    "author": [
                        {"literal": "Research, Development"},
                        {"given": "Ludwig", "non-dropping-particle": "van", "family": "Beethoven"},
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    assert load_csl_json(export)[0].authors == ("Research, Development", "Ludwig van Beethoven")


def test_zotero_corporate_comma_name_preserves_order_and_matches_csl_identity(tmp_path: Path):
    csl = tmp_path / "corporate.json"
    csl.write_text(
        json.dumps({"id": "csl", "title": "Corporate", "author": [{"literal": "Research, Development"}]}),
        encoding="utf-8",
    )
    routes = {
        "/api/users/0/items?limit=1": [],
        "/api/users/0/items/DIRECT": {
            "data": {
                "key": "DIRECT",
                "title": "Corporate",
                "creators": [{"creatorType": "author", "name": "Research, Development"}],
            }
        },
        "/api/users/0/items/DIRECT/children": [],
    }
    client = ZoteroLocalClient(
        opener=lambda request, timeout: _FakeResponse(routes[request.full_url.split("23119", 1)[1]])
    )

    zotero = resolve_zotero("corporate", item_key="DIRECT", client=client)
    csl_record = load_csl_json(csl)[0]

    assert zotero.source is not None
    assert zotero.source.authors == ("Research, Development",)
    assert zotero.source.source_id == csl_record.source_id


def test_csl_numeric_identifiers_are_aliases_and_distinguish_sparse_records(tmp_path: Path):
    export = tmp_path / "numeric-ids.json"
    export.write_text(
        json.dumps([{"id": 123}, {"id": 0}, {"id": None}, {"id": {"invalid": True}}]),
        encoding="utf-8",
    )

    numeric, zero, null, invalid = load_csl_json(export)

    assert numeric.aliases == ("123",)
    assert zero.aliases == ("0",)
    assert null.aliases == invalid.aliases == ()
    assert numeric.source_id != zero.source_id


def test_bibtex_decodes_common_escapes_and_nonbreaking_spaces(tmp_path: Path):
    export = tmp_path / "escapes.bib"
    export.write_text(
        r"@article{escapes, title = {Costs \$5 and 10\%~today: \& \_ \# \{braces\}}}",
        encoding="utf-8",
    )

    assert load_bibtex(export)[0].title == "Costs $5 and 10% today: & _ # {braces}"


class _FakeResponse:
    def __init__(self, payload: Any):
        self.payload = payload
        self.headers = {"Content-Type": "application/json"}

    def read(self) -> bytes:
        import json

        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_zotero_http_status_probe_failure_is_only_an_availability_failure():
    def unavailable(request: Any, timeout: float) -> Any:
        raise HTTPError(request.full_url, 503, "offline", Message(), None)

    client = ZoteroLocalClient(opener=unavailable)

    assert resolve_zotero("Theory2024", client=client).status == "unavailable"
    with pytest.raises(RuntimeError, match="unavailable"):
        resolve_zotero("Theory2024", client=client, require_zotero=True)


def test_zotero_attachment_http_errors_continue_candidates_and_preserve_metadata(tmp_path: Path):
    pdf = tmp_path / "good.pdf"
    pdf.write_bytes(b"pdf")
    routes: dict[str, Any] = {
        "/api/users/0/items?limit=1": [],
        "/api/users/0/items?q=Theory2024&limit=25": [
            {"data": {"key": "ITEM", "citationKey": "Theory2024", "title": "Known item", "DOI": None}}
        ],
        "/api/users/0/items/ITEM/children": [
            {"data": {"key": "STALE", "contentType": "application/pdf", "dateModified": "2026-02-01"}},
            {"data": {"key": "GOOD", "contentType": "application/pdf", "dateModified": "2026-01-01"}},
        ],
        "/api/users/0/items/STALE/file/view/url": HTTPError("stale", 404, "missing", Message(), None),
        "/api/users/0/items/GOOD/file/view/url": f"file:///{pdf.as_posix()}",
    }
    requested: list[str] = []

    def opener(request: Any, timeout: float) -> _FakeResponse:
        route = request.full_url.split("23119", 1)[1]
        requested.append(route)
        payload = routes[route]
        if isinstance(payload, HTTPError):
            raise payload
        return _FakeResponse(payload)

    outcome = resolve_zotero("Theory2024", client=ZoteroLocalClient(opener=opener), require_zotero=True)

    assert outcome.status == "enriched"
    assert outcome.source is not None
    assert outcome.source.title == "Known item"
    assert outcome.source.doi == ""
    assert outcome.source.local_files == (str(pdf.resolve()),)
    assert requested[-2:] == ["/api/users/0/items/STALE/file/view/url", "/api/users/0/items/GOOD/file/view/url"]


def test_zotero_attachment_404_is_not_a_service_unavailability_error():
    routes: dict[str, Any] = {
        "/api/users/0/items?limit=1": [],
        "/api/users/0/items?q=Theory2024&limit=25": [
            {"data": {"key": "ITEM", "citationKey": "Theory2024", "title": "Known item"}}
        ],
        "/api/users/0/items/ITEM/children": HTTPError("children", 404, "missing", Message(), None),
    }

    def opener(request: Any, timeout: float) -> _FakeResponse:
        payload = routes[request.full_url.split("23119", 1)[1]]
        if isinstance(payload, HTTPError):
            raise payload
        return _FakeResponse(payload)

    outcome = resolve_zotero("Theory2024", client=ZoteroLocalClient(opener=opener), require_zotero=True)

    assert outcome.status == "attachment_unresolved"
    assert outcome.source is not None
    assert outcome.source.title == "Known item"
    assert outcome.source.local_files == ()


def test_zotero_creators_keep_authors_and_corporate_names_but_exclude_editors():
    routes = {
        "/api/users/0/items?limit=1": [],
        "/api/users/0/items/DIRECT": {
            "data": {
                "key": "DIRECT",
                "title": "Creators",
                "creators": [
                    {"creatorType": "author", "firstName": "Ada", "lastName": "Lovelace"},
                    {"creatorType": "editor", "firstName": "Ed", "lastName": "Itor"},
                    {"creatorType": "bookAuthor", "firstName": "Book", "lastName": "Author"},
                    {"creatorType": "author", "name": "WHO"},
                ],
            }
        },
        "/api/users/0/items/DIRECT/children": [],
    }
    client = ZoteroLocalClient(
        opener=lambda request, timeout: _FakeResponse(routes[request.full_url.split("23119", 1)[1]])
    )

    outcome = resolve_zotero("Creators", item_key="DIRECT", client=client)

    assert outcome.source is not None
    assert outcome.source.authors == ("Ada Lovelace", "Book Author", "WHO")


def test_zotero_resolves_exact_citation_key_and_pdf_child(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")
    routes = {
        "/api/users/0/items?limit=1": [],
        "/api/users/0/items?q=Theory2024&limit=25": [
            {"data": {"key": "ABCD1234", "citationKey": "Theory2024", "title": "Live title", "DOI": "10.2/LIVE"}}
        ],
        "/api/users/0/items/ABCD1234/children": [
            {"data": {"key": "ATTACH", "contentType": "application/pdf", "filename": "source.pdf"}}
        ],
        "/api/users/0/items/ATTACH/file/view/url": f"file:///{pdf.as_posix()}",
    }
    client = ZoteroLocalClient(opener=lambda request, timeout: _FakeResponse(routes[request.full_url.split("23119", 1)[1]]))

    record = resolve_zotero("Theory2024", client=client)

    assert record.status == "enriched"
    assert record.source is not None
    assert record.source.source_id == "doi:10.2/live"
    assert {"Theory2024", "ABCD1234", "ATTACH"} <= set(record.source.aliases)
    assert record.source.local_files == (str(pdf.resolve()),)
    assert record.source.provider == "zotero"


def test_zotero_never_selects_an_ambiguous_citation_key():
    routes = {
        "/api/users/0/items?limit=1": [],
        "/api/users/0/items?q=duplicate&limit=25": [
            {"data": {"key": "ONE", "citationKey": "duplicate"}},
            {"data": {"key": "TWO", "citationKey": "duplicate"}},
        ],
    }
    client = ZoteroLocalClient(opener=lambda request, timeout: _FakeResponse(routes[request.full_url.split("23119", 1)[1]]))

    outcome = resolve_zotero("duplicate", client=client)

    assert outcome.status == "ambiguous"
    assert outcome.source is None
    assert outcome.candidates == ("ONE", "TWO")


def test_zotero_uses_an_explicit_item_key_without_a_search_query():
    routes = {
        "/api/users/0/items?limit=1": [],
        "/api/users/0/items/DIRECT": {
            "data": {"key": "DIRECT", "citationKey": "not-used", "title": "Direct route"}
        },
        "/api/users/0/items/DIRECT/children": [],
    }
    client = ZoteroLocalClient(
        opener=lambda request, timeout: _FakeResponse(routes[request.full_url.split("23119", 1)[1]])
    )

    outcome = resolve_zotero("Theory2024", item_key="DIRECT", client=client)

    assert outcome.status == "enriched"
    assert outcome.source is not None
    assert outcome.source.title == "Direct route"
    assert {"Theory2024", "DIRECT"} <= set(outcome.source.aliases)


def test_zotero_unusable_explicit_attachment_falls_back_to_accessible_pdf_child(tmp_path: Path):
    accessible = tmp_path / "accessible.pdf"
    accessible.write_bytes(b"pdf")
    routes = {
        "/api/users/0/items?limit=1": [],
        "/api/users/0/items?q=Theory2024&limit=25": [
            {"data": {"key": "ITEM", "citationKey": "Theory2024", "title": "Attachment fallback"}}
        ],
        "/api/users/0/items/EXPLICIT/file/view/url": "file:///C:/missing.pdf",
        "/api/users/0/items/ITEM/children": [
            {"data": {"key": "MISSING", "contentType": "application/pdf", "dateModified": "2026-02-01"}},
            {"data": {"key": "ACCESSIBLE", "contentType": "application/pdf", "dateModified": "2026-01-01"}},
        ],
        "/api/users/0/items/MISSING/file/view/url": "file:///C:/missing.pdf",
        "/api/users/0/items/ACCESSIBLE/file/view/url": f"file:///{accessible.as_posix()}",
    }
    client = ZoteroLocalClient(
        opener=lambda request, timeout: _FakeResponse(routes[request.full_url.split("23119", 1)[1]])
    )

    outcome = resolve_zotero("Theory2024", attachment_key="EXPLICIT", client=client)

    assert outcome.status == "enriched"
    assert outcome.source is not None
    assert {"Theory2024", "ITEM", "EXPLICIT", "ACCESSIBLE"} <= set(outcome.source.aliases)
    assert outcome.source.local_files == (str(accessible.resolve()),)


def test_zotero_unavailability_is_optional_unless_required():
    def unavailable(request: Any, timeout: float) -> Any:
        raise OSError("offline")

    client = ZoteroLocalClient(opener=unavailable)

    assert resolve_zotero("Theory2024", client=client).status == "unavailable"
    with pytest.raises(RuntimeError, match="unavailable"):
        resolve_zotero("Theory2024", client=client, require_zotero=True)
