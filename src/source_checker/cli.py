"""Build source manifests and generalized incremental source caches."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Collection, Iterable, Sequence
from dataclasses import replace
from pathlib import Path

from source_checker.bibliography import SourceRecord, make_source_record
from source_checker.cache import CacheResult, cache_source
from source_checker.extractors import SUPPORTED_SUFFIXES, extract_document, media_type_for
from source_checker.manifest import ManifestRow, SourceArtifact, build_manifest, write_manifest
from source_checker.mapping import coalesce_source_records, map_source
from source_checker.resolvers.exports import load_export
from source_checker.resolvers.zotero import ZoteroLocalClient, ZoteroResolution, resolve_zotero


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("manifest", "cache"):
        current = subparsers.add_parser(command)
        current.add_argument("--target", action="append", default=[], type=Path)
        current.add_argument("--source", action="append", default=[], type=Path)
        current.add_argument("--bibliography", action="append", default=[], type=Path)
        current.add_argument("--manifest", action="append", default=[], type=Path)
        current.add_argument("--cache-dir", type=Path, default=Path("text-cache"))
        current.add_argument("--output", type=Path)
        current.add_argument("--zotero-live", action="store_true")
        current.add_argument("--require-zotero", action="store_true")
        current.add_argument("--fail-on-missing", action="store_true")
        current.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "manifest" and not args.target:
        parser.error("manifest requires at least one --target")
    if args.require_zotero and not args.zotero_live:
        parser.error("--require-zotero requires --zotero-live")
    target_documents, target_diagnostics = _extract_targets(args.target)
    sources, imported_rows = _collect_sources(args.source, args.bibliography, args.manifest, args.cache_dir)
    zotero_resolutions: dict[str, ZoteroResolution] = {}
    if args.zotero_live:
        if args.require_zotero:
            _check_zotero_available()
        live_sources, zotero_resolutions = _resolve_zotero_sources(target_documents, args.require_zotero)
        sources.extend(live_sources)
    current_resolutions = _current_citation_resolutions(target_documents, sources)
    artifacts, cache_results = _cache_source_documents(sources, args.cache_dir, args.force)
    generated_rows = build_manifest(target_documents, sources, artifacts)
    rows = _apply_zotero_resolutions(
        _merge_manifest_rows(imported_rows, generated_rows, current_resolutions), zotero_resolutions
    )
    if args.command == "manifest" or args.output is not None:
        output = args.output or Path("source-manifest.csv")
        write_manifest(output, rows)
    summary = _summary(rows, cache_results)
    output_summary: dict[str, object] = dict(summary)
    if target_diagnostics:
        output_summary.update(
            {
                "target_diagnostics": target_diagnostics,
                "target_unusable": len(target_diagnostics),
            }
        )
    print(json.dumps(output_summary, ensure_ascii=False, sort_keys=True))
    if target_diagnostics:
        return 2
    return 2 if args.fail_on_missing and _has_required_gap(summary) else 0


def _extract_targets(paths: Iterable[Path]) -> tuple[list, list[dict[str, object]]]:
    documents = []
    diagnostics: list[dict[str, object]] = []
    for raw_path in paths:
        expanded_paths = _expand_paths((raw_path,), SUPPORTED_SUFFIXES)
        if not expanded_paths:
            diagnostics.append(
                {
                    "block_count": 0,
                    "error": "No supported target files were found for the supplied input.",
                    "extraction_method": "",
                    "extraction_status": "error:NoSupportedTargets",
                    "path": str(Path(raw_path).expanduser().resolve()),
                    "text_quality": "unknown",
                }
            )
            continue
        for path in expanded_paths:
            try:
                document = extract_document(path, "target")
            except Exception as error:  # noqa: BLE001 - target failures become diagnostics
                diagnostics.append(
                    {
                        "block_count": 0,
                        "error": str(error),
                        "extraction_method": "",
                        "extraction_status": f"error:{type(error).__name__}",
                        "path": str(path),
                        "text_quality": "unknown",
                    }
                )
                continue
            status = document.extraction_status
            quality = document.text_quality
            if not document.blocks and status == "extracted" and quality == "good":
                status = "unusable"
                quality = "empty"
            if _is_unusable(status, quality):
                diagnostics.append(
                    {
                        "block_count": len(document.blocks),
                        "extraction_method": document.extraction_method,
                        "extraction_status": status,
                        "path": document.path,
                        "text_quality": quality,
                    }
                )
                continue
            documents.append(document)
    return documents, diagnostics


def _collect_sources(
    source_paths: Iterable[Path],
    bibliography_paths: Iterable[Path],
    manifest_paths: Iterable[Path],
    cache_dir: Path,
) -> tuple[list[SourceRecord], tuple[ManifestRow, ...]]:
    records: list[SourceRecord] = []
    preserved: list[ManifestRow] = []
    for path in _explicit_source_paths(source_paths, cache_dir):
        records.append(
            make_source_record(
                aliases=(path.stem,),
                local_files=(str(path),),
                provider="local",
            )
        )
    for path in bibliography_paths:
        records.extend(load_export(path))
    for path in _expand_paths(manifest_paths, {".csv"}):
        manifest_records, manifest_rows = _load_compatible_manifest(path)
        records.extend(manifest_records)
        preserved.extend(manifest_rows)
    return records, _coalesce_imported_rows(preserved)


def _load_compatible_manifest(path: Path) -> tuple[list[SourceRecord], tuple[ManifestRow, ...]]:
    records: list[SourceRecord] = []
    rows: list[ManifestRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw_row in csv.DictReader(handle):
            row = _manifest_row(raw_row, path)
            if not row.source_id and row.source_path and row.bibliography_key:
                generated = make_source_record(
                    aliases=(*row.aliases, row.bibliography_key),
                    title=row.title,
                    authors=row.authors,
                    year=row.year,
                    doi=row.doi,
                    local_files=(row.source_path,),
                    provider=row.provider or "manifest",
                )
                row = replace(
                    row,
                    source_id=generated.source_id,
                    aliases=generated.aliases,
                    mapping_status=(
                        row.mapping_status
                        if _has_explicit_mapping_status(raw_row)
                        else "not-applicable"
                    ),
                    mapping_rule=(row.mapping_rule if _has_explicit_mapping_status(raw_row) else "explicit-corpus"),
                )
            rows.append(row)
            if row.source_id:
                records.append(
                    SourceRecord(
                        row.source_id,
                        row.aliases,
                        row.title,
                        row.authors,
                        row.year,
                        row.doi,
                        "",
                        (row.source_path,) if row.source_path else (),
                        row.provider or "manifest",
                    )
                )
    return records, _coalesce_imported_rows(rows)


def _resolve_zotero_sources(
    target_documents: Iterable, require_zotero: bool
) -> tuple[list[SourceRecord], dict[str, ZoteroResolution]]:
    keys = sorted({key for document in target_documents for mention in document.citations for key in mention.citation_keys})
    records: list[SourceRecord] = []
    resolutions: dict[str, ZoteroResolution] = {}
    for key in keys:
        outcome = resolve_zotero(key, require_zotero=require_zotero)
        resolutions[key] = outcome
        if outcome.status in {"enriched", "attachment_unresolved"} and outcome.source is not None:
            records.append(outcome.source)
    return records, resolutions


def _check_zotero_available() -> None:
    try:
        ZoteroLocalClient().status()
    except (OSError, ValueError, json.JSONDecodeError):
        raise RuntimeError("Zotero Desktop local API is unavailable") from None


def _apply_zotero_resolutions(rows: Iterable, resolutions: dict[str, ZoteroResolution]) -> tuple:
    updated = []
    for row in rows:
        outcome = resolutions.get(row.bibliography_key)
        if outcome is None:
            updated.append(row)
            continue
        current_conflicts = tuple(
            conflict
            for conflict in row.conflicts
            if not conflict.startswith("Zotero live resolution:")
        )
        current_row = replace(row, conflicts=current_conflicts)
        weak_unresolved_mapping = (
            not row.source_id
            and row.mapping_status == "unresolved"
            and not row.candidate_source_ids
            and row.mapping_rule in {"", "none"}
        )
        replaceable_live_mapping = not row.source_id and row.mapping_rule == "zotero-live"
        replaceable_mapping = weak_unresolved_mapping or replaceable_live_mapping
        if outcome.status == "enriched":
            updated.append(current_row)
        elif outcome.status == "attachment_unresolved" and row.source_id:
            updated.append(
                replace(
                    current_row,
                    conflicts=_sorted_unique(
                        (*current_conflicts, "Zotero live resolution: attachment_unresolved")
                    ),
                )
            )
        elif outcome.status == "ambiguous":
            candidate_detail = (
                f"; candidates: {' | '.join(outcome.candidates)}" if outcome.candidates else ""
            )
            diagnostic = f"Zotero live resolution: {outcome.status}{candidate_detail}"
            mapping_changes = (
                {
                    "mapping_status": "ambiguous",
                    "mapping_rule": "zotero-live",
                    "candidate_source_ids": outcome.candidates,
                }
                if replaceable_mapping
                else {}
            )
            updated.append(
                replace(
                    current_row,
                    **mapping_changes,
                    conflicts=_sorted_unique((*current_conflicts, diagnostic)),
                )
            )
        else:
            diagnostic = f"Zotero live resolution: {outcome.status}"
            mapping_changes = (
                {
                    "mapping_status": "unresolved",
                    "mapping_rule": "zotero-live",
                    "candidate_source_ids": (),
                }
                if replaceable_mapping
                else {}
            )
            updated.append(
                replace(
                    current_row,
                    **mapping_changes,
                    conflicts=_sorted_unique((*current_conflicts, diagnostic)),
                )
            )
    return tuple(updated)


def _merge_manifest_rows(
    imported: Iterable[ManifestRow],
    generated: Iterable[ManifestRow],
    current_resolutions: dict[str, str | None],
) -> tuple[ManifestRow, ...]:
    generated_rows = tuple(generated)
    generated_by_source = {row.source_id: row for row in generated_rows if row.source_id}
    merged: list[ManifestRow] = []
    seen_sources: set[str] = set()
    for row in imported:
        replacement = generated_by_source.get(row.source_id) if row.source_id else None
        if replacement is None:
            merged.append(row)
            continue
        seen_sources.add(row.source_id)
        merged.append(_merge_source_row(row, replacement))
    for row in generated_rows:
        if row.source_id and row.source_id in seen_sources:
            continue
        if not row.source_id:
            _merge_incomplete_row(merged, row)
        else:
            merged.append(_merge_matching_incomplete_into_source(merged, row))
    return tuple(_reconcile_incomplete_rows(merged, current_resolutions))


def _coalesce_imported_rows(rows: Iterable[ManifestRow]) -> tuple[ManifestRow, ...]:
    grouped: dict[str, list[ManifestRow]] = {}
    unbound: list[ManifestRow] = []
    for row in rows:
        if row.source_id:
            grouped.setdefault(row.source_id, []).append(row)
        else:
            unbound.append(row)
    combined = [_coalesce_source_rows(group) for _, group in sorted(grouped.items())]
    return (*combined, *unbound)


def _coalesce_source_rows(rows: list[ManifestRow]) -> ManifestRow:
    ordered = sorted(
        rows,
        key=lambda row: (not bool(row.source_path), _sort_value(row.source_path), _sort_value(row.bibliography_key)),
    )
    canonical = ordered[0]
    paths = tuple(dict.fromkeys(row.source_path for row in ordered if row.source_path))
    conflicts = [conflict for row in ordered for conflict in row.conflicts]
    if len(paths) > 1:
        conflicts.append(f"source_path: {' <> '.join(paths)}")
    strongest = min(ordered, key=lambda row: _mapping_priority(row.mapping_status))
    if paths and not any(row.bibliography_key for row in ordered):
        strongest = replace(canonical, mapping_status="not-applicable", mapping_rule="explicit-corpus")
    return replace(
        canonical,
        aliases=_sorted_unique(alias for row in ordered for alias in row.aliases),
        target_files=_merged_pairs(ordered)[0],
        target_locators=_merged_pairs(ordered)[1],
        mapping_status=strongest.mapping_status,
        mapping_rule=strongest.mapping_rule,
        candidate_source_ids=_sorted_unique(
            candidate for row in ordered for candidate in row.candidate_source_ids
        ),
        conflicts=_sorted_unique(conflicts),
    )


def _merge_source_row(imported: ManifestRow, current: ManifestRow) -> ManifestRow:
    use_current_mapping = current.mapping_status == "resolved" or (
        imported.mapping_status in {"not-applicable", "unresolved"}
        and current.mapping_status != "not-applicable"
    )
    mapping = current if use_current_mapping else imported
    pairs = _merged_pairs((imported, current))
    return replace(
        imported,
        bibliography_key=mapping.bibliography_key,
        aliases=_sorted_unique((*imported.aliases, *current.aliases)),
        target_files=pairs[0],
        target_locators=pairs[1],
        mapping_status=mapping.mapping_status,
        mapping_rule=mapping.mapping_rule,
        candidate_source_ids=_sorted_unique(
            (*imported.candidate_source_ids, *current.candidate_source_ids)
        ),
        source_path=current.source_path,
        media_type=current.media_type,
        source_sha256=current.source_sha256,
        extraction_status=current.extraction_status,
        text_quality=current.text_quality,
        cache_path=current.cache_path,
        conflicts=_sorted_unique((*imported.conflicts, *current.conflicts)),
    )


def _merge_incomplete_row(rows: list[ManifestRow], current: ManifestRow) -> None:
    for index, existing in enumerate(rows):
        if not existing.source_id and existing.bibliography_key == current.bibliography_key:
            pairs = _merged_pairs((existing, current))
            stronger = min((existing, current), key=lambda row: _mapping_priority(row.mapping_status))
            rows[index] = replace(
                existing,
                aliases=_sorted_unique((*existing.aliases, *current.aliases)),
                target_files=pairs[0],
                target_locators=pairs[1],
                mapping_status=stronger.mapping_status,
                mapping_rule=stronger.mapping_rule,
                candidate_source_ids=_sorted_unique(
                    (*existing.candidate_source_ids, *current.candidate_source_ids)
                ),
                conflicts=_sorted_unique((*existing.conflicts, *current.conflicts)),
            )
            return
    rows.append(current)


def _merge_matching_incomplete_into_source(rows: list[ManifestRow], current: ManifestRow) -> ManifestRow:
    matches = [
        row for row in rows if not row.source_id and row.bibliography_key == current.bibliography_key
    ]
    if not matches:
        return current
    rows[:] = [row for row in rows if row not in matches]
    return _absorb_incomplete_rows(current, matches)


def _current_citation_resolutions(
    target_documents: Iterable, sources: Iterable[SourceRecord]
) -> dict[str, str | None]:
    outcomes: dict[str, str | None] = {}
    current_sources = tuple(group.source for group in coalesce_source_records(sources))
    for document in target_documents:
        for mention in document.citations:
            for key in mention.citation_keys:
                result = map_source(current_sources, identifiers=(key,))
                outcomes[key] = result.source_ids[0] if result.status == "resolved" else None
    return outcomes


def _reconcile_incomplete_rows(
    rows: list[ManifestRow], current_resolutions: dict[str, str | None]
) -> list[ManifestRow]:
    sources_by_id = {row.source_id: index for index, row in enumerate(rows) if row.source_id}
    replacements: dict[int, ManifestRow] = {}
    absorbed: set[int] = set()
    for index, row in enumerate(rows):
        current_source_id = current_resolutions.get(row.bibliography_key)
        source_index = sources_by_id.get(current_source_id) if current_source_id is not None else None
        if (
            row.source_id
            or not row.bibliography_key
            or source_index is None
        ):
            continue
        current = replacements.get(source_index, rows[source_index])
        replacements[source_index] = _absorb_incomplete_rows(current, (row,))
        absorbed.add(index)
    return [
        replacements.get(index, row)
        for index, row in enumerate(rows)
        if index not in absorbed
    ]


def _absorb_incomplete_rows(
    source: ManifestRow, incomplete_rows: Iterable[ManifestRow]
) -> ManifestRow:
    rows = (*incomplete_rows, source)
    pairs = _merged_pairs(rows)
    return replace(
        source,
        aliases=_sorted_unique(alias for row in rows for alias in row.aliases),
        target_files=pairs[0],
        target_locators=pairs[1],
        candidate_source_ids=_sorted_unique(
            candidate for row in rows for candidate in row.candidate_source_ids
        ),
        conflicts=_sorted_unique(conflict for row in rows for conflict in row.conflicts),
    )


def _merged_pairs(rows: Iterable[ManifestRow]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    pairs = {
        pair
        for row in rows
        for pair in zip(row.target_files, row.target_locators, strict=True)
    }
    ordered = tuple(sorted(pairs, key=lambda pair: (_sort_value(pair[0]), _sort_value(pair[1]))))
    return tuple(pair[0] for pair in ordered), tuple(pair[1] for pair in ordered)


def _mapping_priority(status: str) -> int:
    return {"resolved": 0, "ambiguous": 1, "unresolved": 2, "not-applicable": 3}.get(status, 4)


def _sorted_unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values), key=_sort_value))


def _sort_value(value: str) -> tuple[str, str]:
    return value.casefold(), value


def _manifest_row(raw_row: dict[str, str], manifest_path: Path) -> ManifestRow:
    source_path = raw_row.get("source_path") or raw_row.get("canonical_pdf_path") or ""
    if source_path:
        candidate = Path(source_path).expanduser()
        source_path = str((candidate if candidate.is_absolute() else manifest_path.parent / candidate).resolve())
    return ManifestRow(
        source_id=raw_row.get("source_id", "").strip(),
        provider=raw_row.get("provider", "").strip(),
        bibliography_key=raw_row.get("bibliography_key", "").strip(),
        aliases=_json_sequence(raw_row.get("aliases", "")),
        title=raw_row.get("title", ""),
        authors=_json_sequence(raw_row.get("authors", "")),
        year=_year(raw_row.get("year", "")),
        doi=raw_row.get("doi", ""),
        source_path=source_path,
        media_type=raw_row.get("media_type", ""),
        source_sha256=raw_row.get("source_sha256") or raw_row.get("pdf_sha256", ""),
        target_files=_json_sequence(raw_row.get("target_files", "")),
        target_locators=_json_sequence(raw_row.get("target_locators", "")),
        mapping_status=(
            raw_row.get("mapping_status")
            or raw_row.get("manifest_status")
            or ("not-applicable" if raw_row.get("source_id") else "unresolved")
        ),
        mapping_rule=raw_row.get("mapping_rule", "none"),
        candidate_source_ids=_json_sequence(raw_row.get("candidate_source_ids", "")),
        extraction_status=raw_row.get("extraction_status", "not_run"),
        text_quality=raw_row.get("text_quality", "unknown"),
        cache_path=raw_row.get("cache_path") or raw_row.get("text_cache_path", ""),
        conflicts=_json_sequence(raw_row.get("conflicts", "")),
    )


def _has_explicit_mapping_status(row: dict[str, str]) -> bool:
    return bool((row.get("mapping_status") or row.get("manifest_status") or "").strip())


def _cache_source_documents(
    sources: Iterable[SourceRecord], cache_dir: Path, force: bool
) -> tuple[list[SourceArtifact], dict[str, CacheResult]]:
    artifacts: list[SourceArtifact] = []
    results: dict[str, CacheResult] = {}
    for group in coalesce_source_records(sources):
        source = group.source
        if source.local_files:
            attempted: list[CacheResult] = []
            result: CacheResult | None = None
            for source_path in source.local_files:
                attempt = cache_source(
                    source.source_id,
                    source_path,
                    cache_dir,
                    extractor=extract_document,
                    force=force,
                )
                attempted.append(attempt)
                if _is_currently_analyzed(attempt):
                    result = attempt
                    break
            if result is None:
                result = attempted[0]
            failed_attempts = tuple(
                f"attachment attempt: {attempt.source_path} [{attempt.extraction_status}]"
                for attempt in attempted
                if not _is_currently_analyzed(attempt)
            )
            results[source.source_id] = result
            artifacts.append(
                SourceArtifact(
                    source.source_id,
                    result.source_path,
                    media_type_for(result.source_path),
                    result.document_hash,
                    result.extraction_status,
                    result.text_quality,
                    str(result.cache_path) if _is_currently_analyzed(result) else "",
                    (*group.conflicts, *failed_attempts),
                )
            )
        else:
            artifacts.append(
                SourceArtifact(source.source_id, "", "", "", "missing", "unknown", "", group.conflicts)
            )
    return artifacts, results


def _summary(
    rows: Iterable, cache_results: dict[str, CacheResult]
) -> dict[str, int | float | None]:
    entries = tuple(rows)
    missing = sum(row.mapping_status == "unresolved" for row in entries)
    ambiguous = sum(row.mapping_status == "ambiguous" for row in entries)
    unusable = sum(_is_unusable(row.extraction_status, row.text_quality) for row in entries)
    missing += sum(
        row.mapping_status != "unresolved" and row.extraction_status == "missing" for row in entries
    )
    analyzed = sum(
        row.source_id in cache_results and _is_currently_analyzed(cache_results[row.source_id])
        for row in entries
    )
    extracted = sum(
        not result.reused and _is_currently_analyzed(result) for result in cache_results.values()
    )
    expected = len(entries)
    resolved = sum(
        row.mapping_status in {"resolved", "not-applicable"}
        and row.extraction_status != "missing"
        for row in entries
    )
    return {
        "expected": expected,
        "resolved": resolved,
        "extracted": extracted,
        "analyzed": analyzed,
        "missing": missing,
        "ambiguous": ambiguous,
        "unusable": unusable,
        "coverage_percent": round(100 * analyzed / expected, 2) if expected else None,
    }


def _has_required_gap(summary: dict[str, int | float | None]) -> bool:
    return bool(
        summary["expected"] == 0
        or summary["missing"]
        or summary["ambiguous"]
        or summary["unusable"]
    )


def _is_unusable(extraction_status: str, text_quality: str = "") -> bool:
    return text_quality == "empty" or extraction_status.startswith("error:") or extraction_status in {
        "empty",
        "needs_ocr",
        "needs_review",
        "unusable",
    }


def _is_currently_analyzed(result: CacheResult) -> bool:
    return result.extraction_status != "missing" and not _is_unusable(
        result.extraction_status, result.text_quality
    )


def _explicit_source_paths(paths: Iterable[Path], cache_dir: Path) -> list[Path]:
    expanded: set[Path] = set()
    excluded = Path(cache_dir).expanduser().resolve()
    for raw in paths:
        path = Path(raw).expanduser()
        try:
            if path.is_dir():
                expanded.update(
                    child.resolve()
                    for child in path.rglob("*")
                    if child.is_file()
                    and child.suffix.casefold() in SUPPORTED_SUFFIXES
                    and not _is_within(child.resolve(), excluded)
                )
            else:
                expanded.add(path.resolve())
        except OSError:
            expanded.add(path.absolute())
    return sorted(expanded, key=lambda item: (str(item).casefold(), str(item)))


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _expand_paths(paths: Iterable[Path], suffixes: Collection[str]) -> list[Path]:
    expanded: set[Path] = set()
    for raw in paths:
        path = Path(raw).expanduser()
        if path.is_file() and path.suffix.casefold() in suffixes:
            expanded.add(path.resolve())
        elif path.is_dir():
            expanded.update(
                child.resolve()
                for child in path.rglob("*")
                if child.is_file() and child.suffix.casefold() in suffixes
            )
        else:
            raise FileNotFoundError(f"Input path does not exist or has an unsupported suffix: {path}")
    return sorted(expanded, key=lambda item: (str(item).casefold(), str(item)))


def _json_sequence(value: str) -> tuple[str, ...]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return tuple(part.strip() for part in value.split("|") if part.strip())
    return tuple(item for item in parsed if isinstance(item, str)) if isinstance(parsed, list) else ()


def _year(value: str) -> int | None:
    try:
        return int(value) if value.strip() else None
    except ValueError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
