"""Extraction for local static HTML snapshots."""

from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import Comment, Doctype, NavigableString, Tag

from source_checker.citations import VISIBLE_CITATION_RE
from source_checker.model import CitationMention, TextBlock
from source_checker.normalize import normalize_text

BLOCK_TAGS = {
    "caption",
    "dd",
    "dt",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "li",
    "blockquote",
    "pre",
    "td",
    "th",
}
GENERIC_BLOCK_TAGS = {
    "article",
    "div",
    "dl",
    "figure",
    "figcaption",
    "main",
    "section",
    "table",
    "tbody",
    "tfoot",
    "thead",
    "tr",
}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
EXCLUDED_TAGS = {"head", "script", "style", "nav", "template"}
STRUCTURAL_TAGS = BLOCK_TAGS | GENERIC_BLOCK_TAGS
MetadataScope = tuple[tuple[str, ...], list[bool]]
MetadataScopes = tuple[MetadataScope, ...]


def _locator(block_number: int, node: Tag) -> str:
    identifier = node.get("id")
    return f"block={block_number};id={identifier}" if identifier else f"block={block_number}"


def _visible_text(node: Tag) -> str:
    fragments: list[str] = []
    for descendant in node.descendants:
        if isinstance(descendant, (Comment, Doctype)):
            continue
        if isinstance(descendant, NavigableString):
            fragments.append(str(descendant))
        elif isinstance(descendant, Tag) and descendant.name == "br":
            fragments.append(" ")
    return " ".join("".join(fragments).split())


def extract_html(path: Path) -> tuple[tuple[TextBlock, ...], tuple[CitationMention, ...]]:
    """Extract visible static HTML content and explicit local citation metadata."""
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    for node in soup.find_all(EXCLUDED_TAGS):
        node.decompose()
    for node in soup.find_all(attrs={"hidden": True}):  # pyright: ignore[reportArgumentType]
        node.decompose()

    blocks: list[TextBlock] = []
    citations: list[CitationMention] = []
    heading = "(document scope)"
    block_number = 0

    def emit_block(text: str, node: Tag, metadata_scopes: MetadataScopes = ()) -> None:
        nonlocal block_number
        visible_text = " ".join(text.split())
        if not visible_text:
            return
        block_number += 1
        locator = _locator(block_number, node)
        blocks.append(
            TextBlock(
                block_id=f"html-block-{block_number}",
                text_original=visible_text,
                text_normalized=normalize_text(visible_text),
                locator_type="html-block",
                locator_value=locator,
                heading=heading,
            )
        )
        if metadata_scopes:
            for citation_keys, emitted in metadata_scopes:
                if citation_keys and not emitted[0]:
                    citations.append(
                        CitationMention(
                            raw_text=visible_text,
                            citation_keys=citation_keys,
                            locator_type="html-block",
                            locator_value=locator,
                            mapping_status="unresolved",
                        )
                    )
                emitted[0] = True
            return
        for match in VISIBLE_CITATION_RE.finditer(visible_text):
            citations.append(
                CitationMention(
                    raw_text=match.group(0),
                    citation_keys=(),
                    locator_type="html-block",
                    locator_value=locator,
                    mapping_status="not-applicable",
                )
            )

    def data_cites_scope(node: Tag) -> MetadataScope | None:
        keys = tuple(
            key.lstrip("@") for key in str(node["data-cites"]).split() if key.lstrip("@")
        )
        return (keys, [False]) if keys else None

    def walk(node: Tag, metadata_scopes: MetadataScopes = ()) -> None:
        fragments: list[str] = []

        def flush_fragments() -> None:
            if fragments:
                emit_block("".join(fragments), node, metadata_scopes)
                fragments.clear()

        def process_child(child: object) -> None:
            nonlocal heading
            if isinstance(child, (Comment, Doctype)):
                return
            if isinstance(child, NavigableString):
                fragments.append(str(child))
                return
            if not isinstance(child, Tag):
                return
            child_metadata_scope = data_cites_scope(child) if child.has_attr("data-cites") else None
            if child.name in HEADING_TAGS:
                flush_fragments()
                heading = _visible_text(child) or "(document scope)"
                if child_metadata_scope is not None:
                    walk(child, (*metadata_scopes, child_metadata_scope))
                else:
                    walk(child, metadata_scopes)
                return
            if child_metadata_scope is not None:
                flush_fragments()
                walk(child, (*metadata_scopes, child_metadata_scope))
                return
            if child.name == "br":
                fragments.append(" ")
                return
            if child.name in STRUCTURAL_TAGS:
                flush_fragments()
                walk(child, metadata_scopes)
                return
            for nested_child in child.children:
                process_child(nested_child)

        for child in node.children:
            process_child(child)
        flush_fragments()

    root = soup.body or soup
    root_metadata_scope = data_cites_scope(root) if root.has_attr("data-cites") else None
    walk(root, (root_metadata_scope,) if root_metadata_scope is not None else ())
    return tuple(blocks), tuple(citations)
