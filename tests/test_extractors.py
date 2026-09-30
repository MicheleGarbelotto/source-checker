import shutil
import subprocess
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from source_checker import extractors
from source_checker.extractors import UnsupportedFormatError, extract_document

FIXTURES = Path(__file__).parent / "fixtures" / "documents"
PDF_FIXTURES = Path(__file__).parent / "fixtures" / "pdfs"


def _replace_document_xml(path: Path, document_xml: bytes) -> None:
    with ZipFile(path) as source:
        contents = {entry.filename: source.read(entry.filename) for entry in source.infolist()}
    contents["word/document.xml"] = document_xml
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as output:
        for name, content in contents.items():
            output.writestr(name, content)


def _keys(document):
    return [key for citation in document.citations for key in citation.citation_keys]


@pytest.mark.parametrize(
    ("filename", "locator_type", "key"),
    [
        ("sample.qmd", "line", "alpha2020"),
        ("sample.tex", "line", "beta2021"),
        ("sample.html", "html-block", "gamma2022"),
    ],
)
def test_structured_formats_emit_common_blocks_and_citations(filename, locator_type, key):
    document = extract_document(FIXTURES / filename, role="target")

    assert document.blocks
    assert document.blocks[0].locator_type == locator_type
    assert key in set(_keys(document))


def test_markup_ignores_fenced_code_as_prose_and_citations(tmp_path):
    path = tmp_path / "draft.qmd"
    path.write_text(
        "# Findings\n\nVisible [@visible2020].\n\n```python\nignored = '@hidden2021'\n```\n",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert "visible2020" in _keys(document)
    assert "hidden2021" not in _keys(document)
    assert all("ignored =" not in block.text_original for block in document.blocks)


@pytest.mark.parametrize(
    ("opener", "short_closer", "invalid_closer"),
    [
        ("````", "```", "```notclosing"),
        ("~~~~", "~~~", "~~~notclosing"),
    ],
)
def test_markup_fences_require_matching_marker_length_and_blank_trailing_text(
    tmp_path, opener, short_closer, invalid_closer
):
    path = tmp_path / "fences.md"
    path.write_text(
        f"{opener}\n@inside2020\n{short_closer}\n@still_hidden2021\n"
        f"{invalid_closer}\n@also_hidden2022\n{opener}\nVisible [@outside2023].\n",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert _keys(document) == ["outside2023"]
    assert all("inside2020" not in block.text_original for block in document.blocks)
    assert all("still_hidden2021" not in block.text_original for block in document.blocks)


def test_markup_unterminated_front_matter_candidate_remains_visible(tmp_path):
    path = tmp_path / "unterminated.md"
    path.write_text("---\n\nA visible claim [@alpha2020].\n", encoding="utf-8")

    document = extract_document(path, role="target")

    assert "alpha2020" in _keys(document)
    assert any("A visible claim" in block.text_original for block in document.blocks)


def test_markup_bom_prefixed_bounded_front_matter_is_excluded(tmp_path):
    path = tmp_path / "bom.md"
    path.write_text(
        "\ufeff---\nmetadata: [@hidden2020]\n---\n# Findings\nVisible [@kept2021].\n",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert _keys(document) == ["kept2021"]
    assert all("hidden2020" not in block.text_original for block in document.blocks)


def test_markup_paired_thematic_rules_without_yaml_metadata_remain_visible(tmp_path):
    path = tmp_path / "thematic-rules.md"
    path.write_text(
        "---\n\nA visible claim [@alpha2020].\n\n---\n\nFollowing paragraph [@beta2021].\n",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert _keys(document) == ["alpha2020", "beta2021"]
    assert [block.text_original for block in document.blocks if "claim" in block.text_original or "Following" in block.text_original] == [
        "A visible claim [@alpha2020].",
        "Following paragraph [@beta2021].",
    ]


def test_latex_ignores_comments_but_not_escaped_percent(tmp_path):
    path = tmp_path / "draft.tex"
    path.write_text(
        "\\section{Results}\nVisible 50\\% with \\cite{kept2020}. % \\cite{ignored2021}\n",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert _keys(document) == ["kept2020"]
    assert "50%" in document.blocks[0].text_original
    assert "ignored2021" not in document.blocks[0].text_original


def test_html_excludes_non_content_nodes_from_blocks_and_citations(tmp_path):
    path = tmp_path / "page.html"
    path.write_text(
        """<html><body>
        <nav>Navigation <span data-cites="nav2020">Nav</span></nav>
        <script>const cited = '@script2021';</script>
        <style>.note::after { content: '@style2022'; }</style>
        <template><p data-cites="template2023">Template</p></template>
        <main><h1>Main</h1><p data-cites="kept2024">Visible evidence.</p></main>
        </body></html>""",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")
    extracted_text = " ".join(block.text_original for block in document.blocks)

    assert "Visible evidence." in extracted_text
    assert all(value not in extracted_text for value in ("Navigation", "script2021", "style2022", "Template"))
    assert _keys(document) == ["kept2024"]


def test_html_without_body_excludes_head_doctype_and_title_content(tmp_path):
    path = tmp_path / "no-body.html"
    path.write_text(
        "<!doctype html><html><head><title>Title (Alpha, 2020)</title></head>"
        "<p>Visible</p></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["Visible"]
    assert document.citations == ()


def test_html_hidden_subtrees_do_not_become_prose_or_citations(tmp_path):
    path = tmp_path / "hidden.html"
    path.write_text(
        "<html><body><p hidden>Hidden (Alpha, 2020)</p><p>Visible</p></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["Visible"]
    assert document.citations == ()


def test_html_definition_lists_preserve_structural_boundaries(tmp_path):
    path = tmp_path / "definition-list.html"
    path.write_text(
        "<html><body><dl><dt>Alpha</dt><dd>Beta</dd><dt>Gamma</dt><dd>Delta</dd></dl>"
        "</body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["Alpha", "Beta", "Gamma", "Delta"]


def test_html_data_cites_are_split_and_visible_unmapped_citations_are_retained(tmp_path):
    path = tmp_path / "page.html"
    path.write_text(
        "<html><body><p>Text <span data-cites='@alpha2020 beta2021'>citation</span> "
        "and [@visible2022].</p></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert _keys(document) == ["alpha2020", "beta2021"]
    assert any(
        citation.raw_text == "[@visible2022]" and citation.citation_keys == ()
        for citation in document.citations
    )


def test_html_mixed_blocks_preserve_generic_data_cites_without_duplicates(tmp_path):
    path = tmp_path / "mixed.html"
    path.write_text(
        "<html><body><h1>Results</h1><div data-cites='gamma2022'>(Gamma, 2022)</div>"
        "<div><p>Nested prose.</p></div></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == [
        "Results",
        "(Gamma, 2022)",
        "Nested prose.",
    ]
    assert _keys(document) == ["gamma2022"]


def test_html_visible_citation_fallback_handles_spans_and_split_descendants(tmp_path):
    path = tmp_path / "visible-citations.html"
    path.write_text(
        "<html><body><p>Text [@<em>alpha2020</em>]. "
        "<span class='citation'>(Gamma, 2022)</span> "
        "<span data-cites='beta2021'>(Beta, 2021)</span>.</p></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")
    fallback = [citation for citation in document.citations if not citation.citation_keys]

    assert _keys(document) == ["beta2021"]
    assert [(citation.raw_text, citation.citation_keys) for citation in fallback] == [
        ("[@alpha2020]", ()),
        ("(Gamma, 2022)", ()),
    ]


def test_html_mixed_container_content_has_non_overlapping_visible_blocks(tmp_path):
    path = tmp_path / "mixed-content.html"
    path.write_text(
        "<html><body><div>Before <span data-cites='alpha2020'>(Alpha, 2020)</span>"
        "<p>Paragraph.</p>After [@beta2021].</div></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")
    fallback = [citation for citation in document.citations if not citation.citation_keys]

    assert [block.text_original for block in document.blocks] == [
        "Before",
        "(Alpha, 2020)",
        "Paragraph.",
        "After [@beta2021].",
    ]
    assert _keys(document) == ["alpha2020"]
    assert [(citation.raw_text, citation.citation_keys) for citation in fallback] == [
        ("[@beta2021]", ()),
    ]


def test_html_standalone_inline_data_cites_sibling_is_retained(tmp_path):
    path = tmp_path / "inline-sibling.html"
    path.write_text(
        "<html><body><h1>Results</h1><span data-cites='gamma2022'>(Gamma, 2022)</span></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["Results", "(Gamma, 2022)"]
    assert _keys(document) == ["gamma2022"]
    assert document.blocks[1].heading == "Results"


def test_html_ancestor_data_cites_owns_descendant_prose_once(tmp_path):
    path = tmp_path / "ancestor-data-cites.html"
    path.write_text(
        "<html><body><div data-cites='gamma2022'><p>(Gamma, 2022)</p></div></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["(Gamma, 2022)"]
    assert _keys(document) == ["gamma2022"]
    assert len(document.citations) == 1


def test_html_nested_recognized_and_generic_blocks_do_not_duplicate_data_cites(tmp_path):
    path = tmp_path / "nested-blocks.html"
    path.write_text(
        "<html><body><blockquote><div data-cites='gamma2022'>(Gamma, 2022)</div></blockquote>"
        "</body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["(Gamma, 2022)"]
    assert _keys(document) == ["gamma2022"]
    assert len(document.citations) == 1


def test_html_nested_data_cites_have_distinct_non_overlapping_owners(tmp_path):
    path = tmp_path / "nested-data-cites.html"
    path.write_text(
        "<html><body><div data-cites='alpha2020'>Alpha "
        "<span data-cites='beta2021'>Beta</span></div></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["Alpha", "Beta"]
    assert _keys(document) == ["alpha2020", "beta2021"]
    assert len(document.citations) == 2


def test_html_starting_node_data_cites_is_authoritative(tmp_path):
    path = tmp_path / "root-data-cites.html"
    path.write_text(
        "<html><body data-cites='gamma2022'><p>(Gamma, 2022)</p></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["(Gamma, 2022)"]
    assert _keys(document) == ["gamma2022"]
    assert len(document.citations) == 1


def test_html_line_breaks_preserve_visible_word_boundaries(tmp_path):
    path = tmp_path / "line-breaks.html"
    path.write_text(
        "<html><body><p>First<br>second<br/>third.</p></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert document.blocks[0].text_original == "First second third."
    assert document.blocks[0].text_normalized == "first second third."


def test_html_headings_join_inline_text_without_inserting_word_breaks(tmp_path):
    path = tmp_path / "inline-heading.html"
    path.write_text(
        "<html><body><h1><em>Intro</em>duction</h1><p>Visible</p></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.heading for block in document.blocks] == ["Introduction", "Introduction"]


def test_html_metadata_scope_without_direct_text_attaches_to_nested_metadata_block(tmp_path):
    path = tmp_path / "nested-metadata-only.html"
    path.write_text(
        "<html><body><div data-cites='alpha2020'><span data-cites='beta2021'>Beta</span>"
        "</div></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["Beta"]
    assert _keys(document) == ["alpha2020", "beta2021"]
    assert len(document.citations) == 2
    assert {citation.locator_value for citation in document.citations} == {
        document.blocks[0].locator_value
    }


def test_html_empty_data_cites_does_not_suppress_visible_fallback_citation(tmp_path):
    path = tmp_path / "empty-data-cites.html"
    path.write_text(
        "<html><body><p><span data-cites=''>[@alpha2020]</span></p></body></html>",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["[@alpha2020]"]
    assert [(citation.raw_text, citation.citation_keys) for citation in document.citations] == [
        ("[@alpha2020]", ()),
    ]


@pytest.mark.parametrize(
    "command",
    [
        "cite",
        "citep",
        "citet",
        "autocite",
        "parencite",
        "textcite",
        "cite*",
        "citep*",
        "citet*",
        "autocite*",
        "parencite*",
        "textcite*",
    ],
)
def test_latex_recognizes_supported_commands_stars_and_optional_arguments(tmp_path, command):
    path = tmp_path / "commands.tex"
    path.write_text(
        f"\\section{{Citations}}\nExample \\{command}[pre-note][post-note]{{key{command.replace('*', 'star')}}}.\n",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert _keys(document) == [f"key{command.replace('*', 'star')}"]


def test_heading_provenance_and_first_seen_citekey_order_are_preserved(tmp_path):
    path = tmp_path / "headings.md"
    path.write_text(
        "# Theory {#theory}\nFirst [@alpha2020; @beta2021].\n"
        "## Extension\nSecond [@alpha2020; @gamma2022].\n",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")
    first_seen = list(dict.fromkeys(_keys(document)))

    assert first_seen == ["alpha2020", "beta2021", "gamma2022"]
    assert [block.heading for block in document.blocks] == ["Theory", "Extension"]
    assert [block.locator_value for block in document.blocks] == ["2", "4"]


def test_latex_section_provenance_is_preserved(tmp_path):
    path = tmp_path / "sections.tex"
    path.write_text(
        "\\section{Theory}\nFirst \\cite{alpha2020}.\n"
        "\\subsection{Extension}\nSecond \\cite{beta2021}.\n",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert _keys(document) == ["alpha2020", "beta2021"]
    assert [block.heading for block in document.blocks] == ["Theory", "Extension"]
    assert [block.locator_value for block in document.blocks] == ["2", "4"]


def test_latex_section_keeps_same_line_prose_and_citations(tmp_path):
    path = tmp_path / "inline-section.tex"
    path.write_text(
        "\\section{Results} Same-line prose with \\cite{alpha2020}.\n",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == [" Same-line prose with \\cite{alpha2020}."]
    assert [block.heading for block in document.blocks] == ["Results"]
    assert _keys(document) == ["alpha2020"]
    assert document.citations[0].locator_value == "1"


def test_latex_multiline_citation_has_a_deterministic_line_range(tmp_path):
    path = tmp_path / "multiline-citation.tex"
    path.write_text(
        "\\section{Results}\nText \\citep[see]\n[p. 4]{beta2021}.\n",
        encoding="utf-8",
    )

    document = extract_document(path, role="target")

    assert _keys(document) == ["beta2021"]
    assert document.citations[0].locator_type == "line"
    assert document.citations[0].locator_value == "2-3"


def test_latex_comment_continuation_does_not_insert_whitespace_into_citekeys(tmp_path):
    path = tmp_path / "continued-key.tex"
    path.write_text("\\cite{alpha% comment\n2020}\n", encoding="utf-8")

    document = extract_document(path, role="target")

    assert _keys(document) == ["alpha2020"]
    assert document.citations[0].locator_value == "1-2"


@pytest.mark.parametrize(
    ("suffix", "source_fixture", "method"),
    [
        (".md", "sample.qmd", "markup"),
        (".txt", "sample.qmd", "plain-text"),
        (".latex", "sample.tex", "latex"),
        (".htm", "sample.html", "html"),
    ],
)
def test_alias_suffixes_dispatch_to_their_adapter(tmp_path, suffix, source_fixture, method):
    path = tmp_path / f"copy{suffix}"
    path.write_bytes((FIXTURES / source_fixture).read_bytes())

    document = extract_document(path, role="source")

    assert document.extraction_method == method


def test_unsupported_suffix_names_every_supported_format(tmp_path):
    path = tmp_path / "document.rtf"
    path.write_text("Unsupported", encoding="utf-8")

    with pytest.raises(UnsupportedFormatError) as error:
        extract_document(path, role="target")

    message = str(error.value)
    for suffix in (
        ".qmd",
        ".md",
        ".txt",
        ".tex",
        ".latex",
        ".html",
        ".htm",
        ".docx",
        ".docm",
        ".doc",
        ".pdf",
    ):
        assert suffix in message


def test_extraction_rejects_file_changes_between_content_and_hash_reads(tmp_path, monkeypatch):
    path = tmp_path / "race.md"
    path.write_text("Original [@alpha2020].\n", encoding="utf-8")
    original_extract_markup = extractors.extract_markup

    def mutate_after_extraction(extraction_path):
        result = original_extract_markup(extraction_path)
        extraction_path.write_text("Changed [@beta2021].\n", encoding="utf-8")
        return result

    monkeypatch.setattr(extractors, "extract_markup", mutate_after_extraction)

    with pytest.raises(RuntimeError, match="changed during extraction"):
        extract_document(path, role="target")


@pytest.mark.parametrize("filename", ["sample.docx", "sample.docm"])
def test_ooxml_extracts_visible_paragraphs_headings_and_field_results(filename):
    document = extract_document(FIXTURES / filename, role="target")

    assert [block.locator_type for block in document.blocks] == ["paragraph"] * 3
    assert [block.locator_value for block in document.blocks] == ["1", "2", "3"]
    assert [block.heading for block in document.blocks] == ["Evidence"] * 3
    assert document.blocks[1].text_original == "Visible field result (Alpha, 2020)."
    assert document.blocks[2].text_original == "Before (Beta, 2021) after."
    assert "HYPERLINK" not in " ".join(block.text_original for block in document.blocks)
    assert [citation.raw_text for citation in document.citations] == ["(Alpha, 2020)", "(Beta, 2021)"]


def test_docm_fixture_is_macro_enabled_and_preserves_original_identity():
    path = FIXTURES / "sample.docm"
    with ZipFile(path) as package:
        content_types = package.read("[Content_Types].xml")

    document = extract_document(path, role="target")

    assert b"application/vnd.ms-word.document.macroEnabled.main+xml" in content_types
    assert document.path == str(path.resolve())
    assert document.sha256 == sha256(path.read_bytes()).hexdigest()
    assert document.media_type == "application/vnd.ms-word.document.macroEnabled.12"


def test_docm_is_read_as_ooxml_without_importing_or_executing_macros(monkeypatch):
    from source_checker.extractors import office

    calls: list[object] = []

    def unexpected_process(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("OOXML extraction must not start a process")

    monkeypatch.setattr(office.subprocess, "run", unexpected_process)

    document = extract_document(FIXTURES / "sample.docm", role="target")

    assert document.extraction_method == "ooxml"
    assert calls == []
    assert "vbaProject" not in " ".join(block.text_original for block in document.blocks)


def test_ooxml_hides_nested_field_results_inside_outer_instructions(tmp_path):
    path = tmp_path / "nested.docx"
    shutil.copyfile(FIXTURES / "sample.docx", path)
    _replace_document_xml(
        path,
        b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:r><w:t>Start </w:t></w:r><w:r><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText> HYPERLINK nested </w:instrText></w:r><w:r><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText> HYPERLINK hidden </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>
<w:r><w:t>(Hidden, 2020)</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>
<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>Visible link</w:t></w:r>
<w:r><w:fldChar w:fldCharType="end"/></w:r><w:r><w:t> end</w:t></w:r></w:p>
<w:sectPr/></w:body></w:document>""",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["Start Visible link end"]
    assert "(Hidden, 2020)" not in document.blocks[0].text_original
    assert document.citations == ()


def test_ooxml_field_result_preserves_tab_and_break_boundaries(tmp_path):
    path = tmp_path / "separators.docx"
    shutil.copyfile(FIXTURES / "sample.docx", path)
    _replace_document_xml(
        path,
        b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:r><w:t>Before</w:t></w:r><w:r><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText> HYPERLINK example </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>
<w:r><w:tab/></w:r><w:r><w:t>2026</w:t></w:r><w:r><w:br/></w:r><w:r><w:t>After</w:t></w:r>
<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p><w:sectPr/></w:body></w:document>""",
    )

    document = extract_document(path, role="target")

    assert document.blocks[0].text_original == "Before\t2026\nAfter"
    assert document.blocks[0].text_normalized == "before 2026 after"


def test_ooxml_empty_outer_field_result_does_not_fall_back_to_hidden_nested_text(
    tmp_path, monkeypatch
):
    from source_checker.extractors import office

    path = tmp_path / "empty-result.docx"
    shutil.copyfile(FIXTURES / "sample.docx", path)
    _replace_document_xml(
        path,
        b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText> HYPERLINK outer </w:instrText></w:r><w:r><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText> HYPERLINK hidden </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>
<w:r><w:t>(Hidden, 2020)</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>
<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>
</w:p><w:sectPr/></w:body></w:document>""",
    )

    class Paragraph:
        text = "(Hidden, 2020)"
        style = None

    class DocumentView:
        def __init__(self) -> None:
            self.paragraphs = [Paragraph()]

    monkeypatch.setattr(office, "_open_ooxml_document", lambda _: DocumentView())

    blocks, citations = office.extract_ooxml(path)

    assert blocks == ()
    assert citations == ()


def test_ooxml_tracks_complex_field_state_across_paragraph_boundaries(tmp_path):
    path = tmp_path / "cross-paragraph.docx"
    shutil.copyfile(FIXTURES / "sample.docx", path)
    _replace_document_xml(
        path,
        b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText> HYPERLINK outer </w:instrText></w:r>
<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText> HYPERLINK hidden </w:instrText></w:r>
<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>(Hidden, 2020)</w:t></w:r>
<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
<w:p><w:r><w:t>Instruction prose (Hidden, 2020)</w:t></w:r></w:p>
<w:p><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>Visible link</w:t></w:r>
<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p><w:sectPr/></w:body></w:document>""",
    )

    document = extract_document(path, role="target")

    assert [block.text_original for block in document.blocks] == ["Visible link"]
    assert [block.locator_value for block in document.blocks] == ["3"]
    assert document.citations == ()


def test_ooxml_rejects_duplicate_member_names_before_member_reads(tmp_path, monkeypatch):
    from source_checker.extractors import office

    path = tmp_path / "duplicate.docx"
    shutil.copyfile(FIXTURES / "sample.docx", path)
    with pytest.warns(UserWarning, match="Duplicate name"), ZipFile(
        path, "a", compression=ZIP_DEFLATED
    ) as archive:
        archive.writestr("word/document.xml", b"not a Word document")

    def unexpected_read(self, *args, **kwargs):
        raise AssertionError("duplicate archives must be rejected before member reads")

    monkeypatch.setattr(office.zipfile.ZipFile, "read", unexpected_read)

    with pytest.raises(ValueError, match="duplicate member"):
        extract_document(path, role="target")


@pytest.mark.parametrize("fixture", [FIXTURES / "sample.docx", FIXTURES / "sample.docm"])
@pytest.mark.parametrize("limit_name", ["_MAX_OOXML_ENTRY_BYTES", "_MAX_OOXML_TOTAL_BYTES"])
def test_ooxml_rejects_oversized_irrelevant_member_before_parsing(tmp_path, monkeypatch, fixture, limit_name):
    from source_checker.extractors import office

    path = tmp_path / fixture.name
    shutil.copyfile(fixture, path)
    with ZipFile(path, "a", compression=ZIP_DEFLATED) as archive:
        existing_infos = archive.infolist()
        if limit_name == "_MAX_OOXML_ENTRY_BYTES":
            limit = max(info.file_size for info in existing_infos)
            payload = b"x" * (limit + 1)
        else:
            limit = sum(info.file_size for info in existing_infos)
            payload = b"x" * 128
        archive.writestr("word/media/irrelevant.bin", payload)
    monkeypatch.setattr(office, limit_name, limit, raising=False)

    with pytest.raises(ValueError, match="OOXML archive"):
        extract_document(path, role="target")


def test_ooxml_handles_a_paragraph_style_without_a_name(monkeypatch):
    from source_checker.extractors import office

    class NamelessStyle:
        name = None

    class Paragraph:
        text = "Visible paragraph"
        style = NamelessStyle()

    class DocumentView:
        def __init__(self) -> None:
            self.paragraphs = [Paragraph()]

    monkeypatch.setattr(office, "_open_ooxml_document", lambda _: DocumentView())
    monkeypatch.setattr(office, "_ooxml_field_result_texts", lambda _: {})

    blocks, _ = office.extract_ooxml(FIXTURES / "sample.docx")

    assert blocks[0].heading == "(document scope)"


def test_legacy_doc_converts_headlessly_in_a_temporary_directory_and_cleans_up(
    tmp_path, monkeypatch
):
    from source_checker.extractors import office

    legacy_doc = tmp_path / "legacy.doc"
    legacy_doc.write_bytes(b"synthetic legacy document")
    received: list[list[str]] = []
    output_directories: list[Path] = []

    def fake_soffice(command, check):
        received.append(command)
        assert check is True
        outdir = Path(command[command.index("--outdir") + 1])
        output_directories.append(outdir)
        shutil.copyfile(FIXTURES / "sample.docx", outdir / "legacy.docx")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(office.subprocess, "run", fake_soffice)

    document = extract_document(legacy_doc, role="source")

    assert received == [
        [
            "soffice",
            "--headless",
            "--convert-to",
            "docx",
            "--outdir",
            str(output_directories[0]),
            str(legacy_doc),
        ]
    ]
    assert document.conversion_note == "Converted from .doc with LibreOffice"
    assert document.extraction_method == "libreoffice-docx"
    assert not output_directories[0].exists()


def test_pdf_prefers_pdftotext_layout_and_preserves_page_block_locators(monkeypatch):
    from source_checker.extractors import pdf

    commands: list[list[str]] = []

    def fake_pdftotext(command, check, stdout, stderr):
        commands.append(command)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=b"First page block one.\n\nFirst page block two.\fSecond page block.\f",
            stderr=b"",
        )

    monkeypatch.setattr(pdf.subprocess, "run", fake_pdftotext)

    document = extract_document(PDF_FIXTURES / "two-page.pdf", role="target")

    assert commands == [
        ["pdftotext", "-layout", "-enc", "UTF-8", str(PDF_FIXTURES / "two-page.pdf"), "-"]
    ]
    assert document.extraction_method == "pdftotext-layout"
    assert [block.locator_value for block in document.blocks] == [
        "page=1;block=1",
        "page=1;block=2",
        "page=2;block=1",
    ]


def test_pdf_falls_back_to_pypdf_when_pdftotext_is_unavailable(monkeypatch):
    from source_checker.extractors import pdf

    def missing_pdftotext(*args, **kwargs):
        raise FileNotFoundError("pdftotext")

    monkeypatch.setattr(pdf.subprocess, "run", missing_pdftotext)

    document = extract_document(PDF_FIXTURES / "two-page.pdf", role="source")

    assert document.extraction_method == "pypdf"
    assert [block.locator_value for block in document.blocks] == [
        "page=1;block=1",
        "page=2;block=1",
    ]


def test_sparse_pdf_text_is_marked_for_ocr_without_starting_ocr(monkeypatch):
    from source_checker.extractors import pdf

    commands: list[list[str]] = []

    def sparse_pdftotext(command, check, stdout, stderr):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=b"brief", stderr=b"")

    monkeypatch.setattr(pdf.subprocess, "run", sparse_pdftotext)

    document = extract_document(PDF_FIXTURES / "two-page.pdf", role="target")

    assert document.extraction_status == "needs_ocr"
    assert document.text_quality == "sparse"
    assert commands == [
        ["pdftotext", "-layout", "-enc", "UTF-8", str(PDF_FIXTURES / "two-page.pdf"), "-"]
    ]


def test_pdf_actual_replacement_characters_above_one_percent_are_degraded(monkeypatch):
    from source_checker.extractors import pdf

    def degraded_pdftotext(command, check, stdout, stderr):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=("a" * 150 + "\ufffd" * 2).encode("utf-8"),
            stderr=b"",
        )

    monkeypatch.setattr(pdf.subprocess, "run", degraded_pdftotext)

    document = extract_document(PDF_FIXTURES / "two-page.pdf", role="target")

    assert document.extraction_status == "needs_review"
    assert document.text_quality == "degraded"


@pytest.mark.parametrize(
    ("suffix", "fixture", "method"),
    [
        (".docx", FIXTURES / "sample.docx", "ooxml"),
        (".docm", FIXTURES / "sample.docm", "ooxml"),
        (".pdf", PDF_FIXTURES / "two-page.pdf", "pdftotext-layout"),
    ],
)
def test_dispatcher_supports_ooxml_and_pdf_suffixes_case_insensitively(
    tmp_path, monkeypatch, suffix, fixture, method
):
    path = tmp_path / f"copy{suffix.upper()}"
    shutil.copyfile(fixture, path)

    if suffix == ".pdf":
        from source_checker.extractors import pdf

        def missing_pdftotext(*args, **kwargs):
            raise FileNotFoundError()

        monkeypatch.setattr(pdf.subprocess, "run", missing_pdftotext)
        method = "pypdf"

    document = extract_document(path, role="target")

    assert document.extraction_method == method
    assert suffix in extractors.SUPPORTED_SUFFIXES


def test_dispatcher_supports_legacy_doc_suffix_case_insensitively(tmp_path, monkeypatch):
    path = tmp_path / "copy.DOC"
    path.write_bytes(b"synthetic legacy document")
    monkeypatch.setattr(extractors, "extract_legacy_doc", lambda _: ((), ()))

    document = extract_document(path, role="target")

    assert document.extraction_method == "libreoffice-docx"
    assert ".doc" in extractors.SUPPORTED_SUFFIXES
