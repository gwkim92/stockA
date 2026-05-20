from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import urlparse

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.news.upsert import run_news_rss_upsert
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.path_policy import resolve_existing_file


NEWS_RSS_FEED_CONFIG_ENV = "STOCKANALYSIS_NEWS_RSS_FEED_CONFIG_JSON"
NEWS_RSS_FEED_CONFIG_VERSION = "news-rss-feed-config-v1"
DEFAULT_FEED_LIMIT = 25
MAX_FEED_LIMIT = 100
MAX_FEED_COUNT = 50


@dataclass(frozen=True)
class NewsRssConfiguredFeed:
    feed_name: str
    feed_url: str
    enabled: bool
    limit: int
    default_language: str | None
    feed_xml_path: str | None = None

    def safe_payload(self) -> dict[str, object]:
        parsed = urlparse(self.feed_url)
        return {
            "feed_name": self.feed_name,
            "enabled": self.enabled,
            "feed_url_host": parsed.netloc,
            "feed_url_scheme": parsed.scheme,
            "limit": self.limit,
            "default_language": self.default_language,
            "fixture_xml_configured": bool(self.feed_xml_path),
        }


def load_news_rss_feed_config(
    config_path: str | Path,
    *,
    repo_root: str | Path,
    require_repo_outside: bool = True,
) -> tuple[NewsRssConfiguredFeed, ...]:
    path = resolve_existing_file(
        config_path,
        label="news RSS feed config",
        repo_root=repo_root,
        require_repo_outside=require_repo_outside,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("news RSS feed config must be a JSON object.")
    version = str(payload.get("version", "")).strip()
    if version != NEWS_RSS_FEED_CONFIG_VERSION:
        raise ValueError(f"news RSS feed config version must be {NEWS_RSS_FEED_CONFIG_VERSION}.")
    raw_feeds = payload.get("feeds")
    if not isinstance(raw_feeds, list) or not raw_feeds:
        raise ValueError("news RSS feed config must contain a non-empty feeds list.")
    if len(raw_feeds) > MAX_FEED_COUNT:
        raise ValueError(f"news RSS feed config supports at most {MAX_FEED_COUNT} feeds.")

    feeds: list[NewsRssConfiguredFeed] = []
    seen_names: set[str] = set()
    for index, raw_feed in enumerate(raw_feeds, start=1):
        if not isinstance(raw_feed, dict):
            raise ValueError(f"news RSS feed config feeds[{index}] must be an object.")
        feed = _parse_feed(raw_feed, index=index, repo_root=repo_root)
        if feed.feed_name in seen_names:
            raise ValueError(f"duplicate news RSS feed_name: {feed.feed_name}")
        seen_names.add(feed.feed_name)
        feeds.append(feed)
    return tuple(feeds)


def build_news_rss_config_report(
    *,
    config_path: str | Path,
    repo_root: str | Path,
) -> dict[str, object]:
    feeds = load_news_rss_feed_config(config_path, repo_root=repo_root)
    return {
        "report_name": "news_rss_feed_config",
        "config_path": str(Path(config_path).expanduser().resolve()),
        "config_version": NEWS_RSS_FEED_CONFIG_VERSION,
        "feed_count": len(feeds),
        "enabled_feed_count": sum(1 for feed in feeds if feed.enabled),
        "free_provider_policy": "rss_atom_no_api_key",
        "redaction_policy": "full_feed_urls_omitted",
        "feeds": [feed.safe_payload() for feed in feeds],
    }


def run_news_rss_configured_feeds(
    *,
    config: RuntimeConfig,
    feed_config_path: str | Path,
    repo_root: str | Path,
    feed_names: Iterable[str] = (),
    dry_run: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    feeds = load_news_rss_feed_config(feed_config_path, repo_root=repo_root)
    selected_names = tuple(name.strip() for name in feed_names if name.strip())
    if selected_names:
        known_names = {feed.feed_name for feed in feeds}
        unknown = sorted(set(selected_names) - known_names)
        if unknown:
            raise ValueError(f"Unknown news RSS feed names: {', '.join(unknown)}")
        feeds = tuple(feed for feed in feeds if feed.feed_name in set(selected_names))
    enabled_feeds = tuple(feed for feed in feeds if feed.enabled)

    report: dict[str, object] = {
        "report_name": "news_rss_configured_feed_run",
        "status": "dry_run" if dry_run else "completed",
        "config_path": str(Path(feed_config_path).expanduser().resolve()),
        "feed_count": len(feeds),
        "enabled_feed_count": len(enabled_feeds),
        "selected_feed_names": list(selected_names),
        "free_provider_policy": "rss_atom_no_api_key",
        "redaction_policy": "full_feed_urls_omitted",
        "feeds": [feed.safe_payload() for feed in feeds],
        "results": [],
        "succeeded_feed_count": 0,
        "failed_feed_count": 0,
        "skipped_feed_count": len(feeds) - len(enabled_feeds),
        "requested_item_count": 0,
        "source_document_count": 0,
        "event_count": 0,
        "linked_document_count": 0,
    }
    if dry_run:
        return report

    results: list[dict[str, object]] = []
    succeeded_count = 0
    failed_count = 0
    requested_item_count = 0
    source_document_count = 0
    event_count = 0
    linked_document_count = 0

    for feed in enabled_feeds:
        try:
            summary = run_news_rss_upsert(
                feed_name=feed.feed_name,
                feed_url=feed.feed_url,
                config=config,
                feed_xml_path=feed.feed_xml_path,
                limit=feed.limit,
                default_language=feed.default_language,
                executor=executor,
            )
        except Exception as exc:
            failed_count += 1
            results.append(
                {
                    **feed.safe_payload(),
                    "status": "failed",
                    "error": str(exc)[:500],
                }
            )
            continue

        succeeded_count += 1
        requested_item_count += int(summary.get("requested_item_count", summary.get("item_count", 0)) or 0)
        source_document_count += int(summary.get("source_document_count", 0) or 0)
        event_count += int(summary.get("event_count", 0) or 0)
        linked_document_count += int(summary.get("linked_document_count", 0) or 0)
        results.append(
            {
                **feed.safe_payload(),
                "status": "succeeded",
                "run_id": summary.get("run_id"),
                "item_count": summary.get("item_count"),
                "requested_item_count": summary.get("requested_item_count", summary.get("item_count")),
                "source_document_count": summary.get("source_document_count"),
                "event_count": summary.get("event_count"),
                "linked_document_count": summary.get("linked_document_count"),
            }
        )

    report.update(
        {
            "status": "completed" if failed_count == 0 else "completed_with_failures",
            "results": results,
            "succeeded_feed_count": succeeded_count,
            "failed_feed_count": failed_count,
            "requested_item_count": requested_item_count,
            "source_document_count": source_document_count,
            "event_count": event_count,
            "linked_document_count": linked_document_count,
        }
    )
    return report


def _parse_feed(raw_feed: Mapping[str, object], *, index: int, repo_root: str | Path) -> NewsRssConfiguredFeed:
    feed_name = str(raw_feed.get("feed_name", "")).strip()
    if not _valid_feed_name(feed_name):
        raise ValueError(f"news RSS feed config feeds[{index}].feed_name is invalid.")
    feed_url = str(raw_feed.get("feed_url", "")).strip()
    _validate_feed_url(feed_url, index=index)
    enabled = bool(raw_feed.get("enabled", True))
    limit = _parse_limit(raw_feed.get("limit", DEFAULT_FEED_LIMIT), index=index)
    default_language = str(raw_feed.get("default_language", "en")).strip() or None
    feed_xml_path = raw_feed.get("feed_xml_path")
    if feed_xml_path is not None:
        feed_xml_path = str(feed_xml_path).strip() or None
    if feed_xml_path:
        feed_xml_path = str(
            resolve_existing_file(
                feed_xml_path,
                label=f"news RSS feed config feeds[{index}].feed_xml_path",
                repo_root=repo_root,
                require_repo_outside=True,
            )
        )
    return NewsRssConfiguredFeed(
        feed_name=feed_name,
        feed_url=feed_url,
        enabled=enabled,
        limit=limit,
        default_language=default_language,
        feed_xml_path=feed_xml_path,
    )


def _valid_feed_name(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value))


def _validate_feed_url(value: str, *, index: int) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"news RSS feed config feeds[{index}].feed_url must be an absolute http(s) URL.")


def _parse_limit(value: object, *, index: int) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"news RSS feed config feeds[{index}].limit must be an integer.") from exc
    if limit <= 0 or limit > MAX_FEED_LIMIT:
        raise ValueError(f"news RSS feed config feeds[{index}].limit must be between 1 and {MAX_FEED_LIMIT}.")
    return limit
