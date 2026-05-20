from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.http import execute_request
from stockanalysis.ingest.news.models import NewsRssItem, NewsRssSyncResult
from stockanalysis.ingest.sources.rss_news import RssNewsSource


def load_news_rss_sync_result(
    *,
    feed_name: str,
    feed_url: str,
    config: RuntimeConfig,
    feed_xml_path: str | None = None,
    limit: int | None = None,
    default_language: str | None = "en",
) -> NewsRssSyncResult:
    body = Path(feed_xml_path).read_bytes() if feed_xml_path else _fetch_feed_body(feed_url, config=config)
    return parse_news_rss_feed(
        body,
        feed_name=feed_name,
        feed_url=feed_url,
        limit=limit,
        default_language=default_language,
    )


def parse_news_rss_feed(
    body: bytes | str,
    *,
    feed_name: str,
    feed_url: str,
    limit: int | None = None,
    default_language: str | None = "en",
) -> NewsRssSyncResult:
    if limit is not None and limit <= 0:
        raise ValueError("limit must be greater than 0")
    payload = body.encode("utf-8") if isinstance(body, str) else body
    root = ElementTree.fromstring(payload)
    channel = _first_child(root, "channel")
    feed_language = _clean_text(_child_text(channel, "language")) if channel is not None else None
    elements = _rss_item_elements(root) or _atom_entry_elements(root)
    records = []
    for element in elements[:limit]:
        item = _parse_item(
            element,
            feed_name=feed_name,
            feed_url=feed_url,
            default_language=feed_language or default_language,
        )
        records.append(item)
    return NewsRssSyncResult(feed_name=feed_name, feed_url=feed_url, items=tuple(records))


def _fetch_feed_body(feed_url: str, *, config: RuntimeConfig) -> bytes:
    request = RssNewsSource().build_request(
        "feed",
        {"url": feed_url},
        config=config,
        require_credentials=False,
    )
    response = execute_request(request)
    if response.status_code < 200 or response.status_code >= 300:
        raise ValueError(f"RSS feed fetch failed with status {response.status_code}.")
    return response.body


def _rss_item_elements(root: ElementTree.Element) -> list[ElementTree.Element]:
    channel = _first_child(root, "channel")
    if channel is None:
        return []
    return [child for child in list(channel) if _local_name(child.tag) == "item"]


def _atom_entry_elements(root: ElementTree.Element) -> list[ElementTree.Element]:
    if _local_name(root.tag) != "feed":
        return []
    return [child for child in list(root) if _local_name(child.tag) == "entry"]


def _parse_item(
    element: ElementTree.Element,
    *,
    feed_name: str,
    feed_url: str,
    default_language: str | None,
) -> NewsRssItem:
    title = _clean_text(_child_text(element, "title")) or "Untitled news item"
    summary = (
        _clean_text(_child_text(element, "description"))
        or _clean_text(_child_text(element, "summary"))
        or _clean_text(_child_text(element, "content"))
    )
    url = _clean_text(_child_text(element, "link")) or _atom_link_href(element)
    guid = _clean_text(_child_text(element, "guid")) or _clean_text(_child_text(element, "id"))
    published_at = _parse_datetime(
        _child_text(element, "pubDate")
        or _child_text(element, "published")
        or _child_text(element, "updated")
        or _child_text(element, "date")
    )
    language = _clean_text(_child_text(element, "language")) or default_language
    identity = guid or url or f"{title}|{published_at.isoformat() if published_at else ''}"
    external_document_id = _external_document_id(feed_name=feed_name, identity=identity)
    checksum = _checksum(
        "|".join(
            (
                feed_url,
                identity,
                title,
                summary or "",
                url or "",
                published_at.isoformat() if published_at else "",
            )
        )
    )
    return NewsRssItem(
        feed_name=feed_name,
        feed_url=feed_url,
        external_document_id=external_document_id,
        title=title,
        summary=summary,
        url=url,
        language=language,
        published_at=published_at,
        guid=guid,
        checksum=checksum,
    )


def _child_text(element: ElementTree.Element | None, local_name: str) -> str | None:
    if element is None:
        return None
    child = _first_child(element, local_name)
    if child is None:
        return None
    return "".join(child.itertext())


def _first_child(element: ElementTree.Element | None, local_name: str) -> ElementTree.Element | None:
    if element is None:
        return None
    for child in list(element):
        if _local_name(child.tag) == local_name:
            return child
    return None


def _atom_link_href(element: ElementTree.Element) -> str | None:
    for child in list(element):
        if _local_name(child.tag) != "link":
            continue
        rel = child.attrib.get("rel", "alternate")
        href = child.attrib.get("href")
        if href and rel == "alternate":
            return href
    for child in list(element):
        if _local_name(child.tag) == "link" and child.attrib.get("href"):
            return child.attrib["href"]
    return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    unescaped = html.unescape(value)
    without_tags = re.sub(r"<[^>]+>", " ", unescaped)
    cleaned = re.sub(r"\s+", " ", without_tags).strip()
    return cleaned or None


def _parse_datetime(value: str | None) -> datetime | None:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    try:
        parsed = parsedate_to_datetime(cleaned)
    except (TypeError, ValueError):
        parsed = None
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _external_document_id(*, feed_name: str, identity: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", feed_name.lower()).strip("-") or "feed"
    return f"rss:{slug}:{_checksum(identity)[:24]}"


def _checksum(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
