"""Optional, read-only enrichment through Zotero Desktop's local HTTP API."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from source_checker.bibliography import SourceRecord, make_source_record, resolve_local_path

DEFAULT_ZOTERO_BASE = "http://127.0.0.1:23119"
_Opener = Callable[[urllib.request.Request, float], Any]


@dataclass(frozen=True)
class ZoteroResolution:
    status: str
    source: SourceRecord | None = None
    candidates: tuple[str, ...] = ()


class ZoteroLocalClient:
    """A small injectable GET-only client for the Zotero Desktop local API."""

    def __init__(
        self,
        base_url: str = DEFAULT_ZOTERO_BASE,
        timeout: float = 5.0,
        opener: _Opener | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._opener = opener or (lambda request, timeout: urllib.request.urlopen(request, timeout=timeout))

    def _get(self, route: str) -> Any:
        request = urllib.request.Request(
            f"{self.base_url}{route}",
            headers={"Accept": "application/json", "Zotero-API-Version": "3"},
            method="GET",
        )
        with self._opener(request, self.timeout) as response:
            payload = response.read().decode("utf-8", errors="replace")
            content_type = response.headers.get("Content-Type", "")
        if "json" in content_type or payload[:1] in "[{":
            return json.loads(payload)
        return payload

    def status(self) -> bool:
        self._get("/api/users/0/items?limit=1")
        return True

    @staticmethod
    def _data(item: Mapping[str, Any]) -> Mapping[str, Any]:
        data = item.get("data", item)
        return data if isinstance(data, Mapping) else {}

    @classmethod
    def _citation_key(cls, item: Mapping[str, Any]) -> str:
        data = cls._data(item)
        if data.get("citationKey"):
            return str(data["citationKey"]).strip()
        match = re.search(r"(?im)^\s*Citation Key\s*:\s*(\S+)\s*$", str(data.get("extra", "")))
        return match.group(1) if match else ""

    def resolve(self, citation_key: str, item_key: str = "", attachment_key: str = "") -> ZoteroResolution:
        if item_key:
            item = self._get(f"/api/users/0/items/{item_key}")
            if not isinstance(item, Mapping):
                return ZoteroResolution("not_found")
        else:
            query = urllib.parse.urlencode({"q": citation_key, "limit": 25})
            payload = self._get(f"/api/users/0/items?{query}")
            matches = [item for item in payload if isinstance(item, Mapping) and self._citation_key(item) == citation_key] if isinstance(payload, list) else []
            keys = tuple(dict.fromkeys(str(self._data(item).get("key", "")) for item in matches if self._data(item).get("key")))
            if not keys:
                return ZoteroResolution("not_found")
            if len(keys) != 1:
                return ZoteroResolution("ambiguous", candidates=keys)
            item = matches[0]
        data = self._data(item)
        resolved_item_key = item_key or str(data.get("key", ""))
        resolved_attachment_keys, local_path, attachment_error = self._attachment(
            resolved_item_key, attachment_key
        )
        aliases = [citation_key, resolved_item_key, *resolved_attachment_keys]
        return ZoteroResolution(
            "attachment_unresolved" if attachment_error else "enriched",
            make_source_record(
                aliases=aliases,
                title=_text(data.get("title")),
                authors=_authors(data.get("creators", [])),
                year=_year(_text(data.get("date"))),
                doi=_text(data.get("DOI")),
                url=_text(data.get("url")),
                local_files=[local_path] if local_path else [],
                provider="zotero",
                preserve_author_order=True,
            ),
        )

    def _attachment(self, item_key: str, attachment_key: str) -> tuple[tuple[str, ...], str, bool]:
        attempted_keys: list[str] = []
        attachment_error = False
        if attachment_key:
            attempted_keys.append(attachment_key)
            path, error = self._attachment_path(attachment_key)
            attachment_error = attachment_error or error
            if path:
                return tuple(attempted_keys), path, False
        try:
            children = self._get(f"/api/users/0/items/{item_key}/children")
        except (OSError, ValueError, json.JSONDecodeError):
            return tuple(attempted_keys), "", True
        candidates = [self._data(child) for child in children if isinstance(child, Mapping) and _is_pdf(self._data(child))] if isinstance(children, list) else []
        if not candidates:
            return tuple(attempted_keys), "", attachment_error
        candidates.sort(key=lambda child: str(child.get("dateModified", "")), reverse=True)
        for candidate in candidates:
            key = str(candidate.get("key", ""))
            if not key or key in attempted_keys:
                continue
            attempted_keys.append(key)
            path, error = self._attachment_path(key)
            attachment_error = attachment_error or error
            if path:
                return tuple(attempted_keys), path, False
        return tuple(attempted_keys), "", attachment_error or bool(candidates)

    def _attachment_path(self, attachment_key: str) -> tuple[str, bool]:
        if not attachment_key:
            return "", False
        try:
            payload = self._get(f"/api/users/0/items/{attachment_key}/file/view/url")
        except (OSError, ValueError, json.JSONDecodeError):
            return "", True
        values = [payload] if isinstance(payload, str) else [_text(payload.get(key)) for key in ("path", "url", "file")] if isinstance(payload, Mapping) else []
        for value in values:
            if not value:
                continue
            path = Path(resolve_local_path(value, Path.cwd()))
            if path.is_file():
                return str(path), False
        return "", bool(values)


def resolve_zotero(
    citation_key: str,
    *,
    item_key: str = "",
    attachment_key: str = "",
    client: ZoteroLocalClient | None = None,
    require_zotero: bool = False,
) -> ZoteroResolution:
    """Resolve only an exact key; an unavailable optional service is non-fatal."""
    active_client = client or ZoteroLocalClient()
    try:
        active_client.status()
    except (OSError, ValueError, json.JSONDecodeError):
        if require_zotero:
            raise RuntimeError("Zotero Desktop local API is unavailable") from None
        return ZoteroResolution("unavailable")
    try:
        return active_client.resolve(citation_key, item_key, attachment_key)
    except urllib.error.HTTPError as error:
        return ZoteroResolution("not_found" if error.code == 404 else f"error:http_{error.code}")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return ZoteroResolution(f"error:{type(error).__name__}")


def _is_pdf(data: Mapping[str, Any]) -> bool:
    return str(data.get("contentType", "")).casefold() == "application/pdf" or str(data.get("filename", "")).casefold().endswith(".pdf")


def _authors(creators: Any) -> list[str]:
    if not isinstance(creators, list):
        return []
    authors: list[str] = []
    for creator in creators:
        if not isinstance(creator, Mapping) or creator.get("creatorType") not in {"author", "bookAuthor"}:
            continue
        name = _text(creator.get("name"))
        if not name:
            name = " ".join(_text(creator.get(key)) for key in ("firstName", "lastName") if creator.get(key))
        if name:
            authors.append(name)
    return authors


def _year(value: str) -> int | None:
    match = re.search(r"\b(\d{4})\b", value)
    return int(match.group(1)) if match else None


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""
