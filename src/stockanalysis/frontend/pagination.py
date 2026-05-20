from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit


DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 100
PAGINATION_ERROR_CODE = "FrontendPaginationInvalid"
PAGINATION_QUERY_KEYS = {"limit", "cursor"}


class FrontendPaginationError(RuntimeError):
    code = PAGINATION_ERROR_CODE


@dataclass(frozen=True)
class FrontendCollectionSpec:
    path: str
    collection_key: str
    required_query_keys: tuple[str, ...] = ()
    path_suffix: str | None = None

    def matches(self, path: str, query: dict[str, str]) -> bool:
        if self.path_suffix is not None:
            if not path.startswith(self.path) or not path.endswith(self.path_suffix):
                return False
        elif path != self.path:
            return False
        return all(query.get(key) for key in self.required_query_keys)


@dataclass(frozen=True)
class FrontendPaginationParams:
    limit: int
    cursor: str | None
    offset: int


COLLECTION_SPECS = (
    FrontendCollectionSpec(path="/api/stocks", collection_key="stocks"),
    FrontendCollectionSpec(path="/api/paper-trading/preview", collection_key="paper_actions"),
    FrontendCollectionSpec(path="/api/remediation-tickets", collection_key="tickets"),
    FrontendCollectionSpec(path="/api/cycles", collection_key="cycle_states", required_query_keys=("asOfDate",)),
    FrontendCollectionSpec(path="/api/events", collection_key="events", required_query_keys=("asOfDate",)),
    FrontendCollectionSpec(path="/api/ai/news-clusters", collection_key="clusters", required_query_keys=("asOfDate",)),
    FrontendCollectionSpec(
        path="/api/performance/",
        path_suffix="/outcomes",
        collection_key="outcomes",
        required_query_keys=("measurementEndDate",),
    ),
    FrontendCollectionSpec(
        path="/api/portfolio/",
        path_suffix="/coverage",
        collection_key="positions",
        required_query_keys=("asOfDate",),
    ),
)


def apply_frontend_pagination(api_path: str, payload: dict[str, Any]) -> dict[str, Any]:
    parsed = urlsplit(api_path)
    query = _single_value_query(parsed.query)
    spec = collection_spec_for_path(parsed.path, query)
    if spec is None:
        if PAGINATION_QUERY_KEYS.intersection(query):
            raise FrontendPaginationError("Pagination parameters are only supported on frontend list endpoints.")
        return payload

    params = parse_frontend_pagination_params(query)
    data = payload.get("data")
    if not isinstance(data, dict):
        return payload
    raw_items = data.get(spec.collection_key)
    if not isinstance(raw_items, list):
        return payload

    items = raw_items[params.offset : params.offset + params.limit]
    next_offset = params.offset + params.limit
    has_more = next_offset < len(raw_items)
    next_cursor = encode_frontend_cursor(next_offset) if has_more else None

    page_data = dict(data)
    page_data[spec.collection_key] = items
    page_payload = dict(payload)
    page_payload["data"] = page_data
    page_payload["pagination"] = {
        "limit": params.limit,
        "cursor": params.cursor,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "item_count": len(items),
    }
    return page_payload


def apply_frontend_sql_pagination(api_path: str, payload: dict[str, Any]) -> dict[str, Any]:
    parsed = urlsplit(api_path)
    query = _single_value_query(parsed.query)
    spec = collection_spec_for_path(parsed.path, query)
    if spec is None:
        if PAGINATION_QUERY_KEYS.intersection(query):
            raise FrontendPaginationError("Pagination parameters are only supported on frontend list endpoints.")
        return payload

    params = parse_frontend_pagination_params(query)
    data = payload.get("data")
    if not isinstance(data, dict):
        return payload
    raw_items = data.get(spec.collection_key)
    if not isinstance(raw_items, list):
        return payload

    items = raw_items[: params.limit]
    has_more = len(raw_items) > params.limit
    next_cursor = encode_frontend_cursor(params.offset + params.limit) if has_more else None

    page_data = dict(data)
    page_data[spec.collection_key] = items
    page_payload = dict(payload)
    page_payload["data"] = page_data
    page_payload["pagination"] = {
        "limit": params.limit,
        "cursor": params.cursor,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "item_count": len(items),
    }
    return page_payload


def frontend_sql_page_window(api_path: str) -> tuple[int, int]:
    parsed = urlsplit(api_path)
    query = _single_value_query(parsed.query)
    params = parse_frontend_pagination_params(query)
    return params.limit + 1, params.offset


def canonical_frontend_path_for_pagination(api_path: str) -> str:
    parsed = urlsplit(api_path)
    query_values = parse_qs(parsed.query, keep_blank_values=True)
    for key in PAGINATION_QUERY_KEYS:
        query_values.pop(key, None)
    query = urlencode([(key, value) for key, values in query_values.items() for value in values])
    return urlunsplit(("", "", parsed.path, query, ""))


def collection_spec_for_path(path: str, query: dict[str, str]) -> FrontendCollectionSpec | None:
    for spec in COLLECTION_SPECS:
        if spec.matches(path, query):
            return spec
    return None


def parse_frontend_pagination_params(query: dict[str, str]) -> FrontendPaginationParams:
    limit = _parse_limit(query.get("limit"))
    cursor = query.get("cursor") or None
    offset = decode_frontend_cursor(cursor) if cursor is not None else 0
    return FrontendPaginationParams(limit=limit, cursor=cursor, offset=offset)


def encode_frontend_cursor(offset: int) -> str:
    if offset < 0:
        raise ValueError("cursor offset must be non-negative")
    raw = json.dumps({"v": 1, "offset": offset}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_frontend_cursor(cursor: str) -> int:
    if not cursor:
        raise FrontendPaginationError("Pagination cursor must not be empty.")
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(f"{cursor}{padding}".encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise FrontendPaginationError("Pagination cursor is invalid.") from exc
    if not isinstance(payload, dict) or payload.get("v") != 1:
        raise FrontendPaginationError("Pagination cursor version is not supported.")
    offset = payload.get("offset")
    if not isinstance(offset, int) or offset < 0:
        raise FrontendPaginationError("Pagination cursor offset is invalid.")
    return offset


def _parse_limit(raw_limit: str | None) -> int:
    if raw_limit is None or raw_limit == "":
        return DEFAULT_PAGE_LIMIT
    if not raw_limit.isdigit():
        raise FrontendPaginationError("Pagination limit must be an integer.")
    limit = int(raw_limit)
    if limit < 1 or limit > MAX_PAGE_LIMIT:
        raise FrontendPaginationError(f"Pagination limit must be between 1 and {MAX_PAGE_LIMIT}.")
    return limit


def _single_value_query(raw_query: str) -> dict[str, str]:
    query_values = parse_qs(raw_query, keep_blank_values=True)
    query: dict[str, str] = {}
    for key, values in query_values.items():
        if values:
            query[key] = values[-1]
    return query
