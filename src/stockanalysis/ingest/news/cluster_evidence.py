from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.news.models import NewsRssClusterEvidenceEvent, NewsRssClusterEvidenceResult
from stockanalysis.ingest.news.sql import (
    render_existing_news_rss_cluster_artifact_lookup_sql,
    render_news_rss_cluster_evidence_event_candidates_sql,
    render_news_rss_cluster_extraction_artifact_insert_sql,
    render_news_rss_cluster_model_invocation_insert_sql,
)
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError


DEFAULT_CLUSTER_EVIDENCE_EVENT_LIMIT = 100
DEFAULT_CLUSTER_EVIDENCE_MAX_CLUSTERS = 4
DEFAULT_CLUSTER_EVIDENCE_PIPELINE_NAME = "news_rss_cluster_evidence"
BROAD_STORY_THEME_KEYS = frozenset({"MARKET_NEWS_FLOW", "US_MARKET_BREADTH", "UNCLASSIFIED"})
STORY_TOKEN_LIMIT = 8
STORY_LABEL_TOKEN_LIMIT = 5
MIN_BROAD_STORY_EVENTS_WITHOUT_SYMBOL = 2
_STORY_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{2,}")
_STORY_STOP_WORDS = frozenset(
    {
        "about",
        "after",
        "again",
        "against",
        "ahead",
        "and",
        "amid",
        "among",
        "are",
        "around",
        "before",
        "behind",
        "being",
        "between",
        "but",
        "could",
        "for",
        "from",
        "have",
        "into",
        "its",
        "latest",
        "market",
        "markets",
        "more",
        "new",
        "news",
        "not",
        "over",
        "says",
        "said",
        "shares",
        "stock",
        "stocks",
        "that",
        "the",
        "their",
        "this",
        "through",
        "under",
        "wall",
        "what",
        "when",
        "where",
        "while",
        "with",
        "would",
    }
)


@dataclass(frozen=True)
class _StoryFingerprint:
    story_key: str
    story_label: str


@dataclass(frozen=True)
class NewsRssClusterEvidence:
    theme_key: str
    theme_name: str
    as_of_date: date
    events: tuple[NewsRssClusterEvidenceEvent, ...]
    story_key: str = "theme"
    story_label: str = ""

    @property
    def representative_event(self) -> NewsRssClusterEvidenceEvent:
        return self.events[0]

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(sorted({event.symbol for event in self.events if event.symbol}))

    @property
    def request_hash(self) -> str:
        payload = {
            "as_of_date": self.as_of_date.isoformat(),
            "events": [
                {
                    "event_id": event.event_id,
                    "impact_direction": event.impact_direction,
                    "impact_score": event.impact_score,
                    "symbol": event.symbol,
                    "korean_title": event.korean_title,
                    "korean_summary": event.korean_summary,
                }
                for event in self.events
            ],
            "story_key": self.story_key,
            "theme_key": self.theme_key,
            "translation_payload_version": "2026-05-23",
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @property
    def confidence(self) -> float:
        event_bonus = min(len(self.events), 8) * 0.035
        symbol_bonus = 0.050 if self.symbols else 0.0
        return min(0.92, 0.58 + event_bonus + symbol_bonus)

    def output_json(self) -> str:
        direction_counts = Counter(event.impact_direction for event in self.events)
        story_label = self.story_label or self.theme_name
        payload = {
            "source": "local_rules",
            "event": {
                "title": f"News cluster summary: {self.theme_key} / {story_label}",
                "event_type": "news_cluster_summary",
                "event_at": self.representative_event.event_at,
                "confidence": self.confidence,
            },
            "cluster": {
                "as_of_date": self.as_of_date.isoformat(),
                "theme_key": self.theme_key,
                "theme_name": self.theme_name,
                "story_key": self.story_key,
                "story_label": story_label,
                "event_count": len(self.events),
                "symbols": list(self.symbols),
                "direction_counts": dict(sorted(direction_counts.items())),
                "representative_event_id": self.representative_event.event_id,
                "request_hash": self.request_hash,
            },
            "extracted_fields": [
                {
                    "field": "analysis_method",
                    "value": "free_local_rules",
                    "confidence": 1.0,
                    "source_chunk_id": "news-cluster-local-rules",
                },
                {
                    "field": "theme_mapping",
                    "value": self.theme_key,
                    "confidence": self.confidence,
                    "source_chunk_id": "news-cluster-theme",
                },
                {
                    "field": "story_mapping",
                    "value": self.story_key,
                    "confidence": self.confidence,
                    "source_chunk_id": "news-cluster-story",
                },
                {
                    "field": "event_count",
                    "value": str(len(self.events)),
                    "confidence": 1.0,
                    "source_chunk_id": "news-cluster-events",
                },
                {
                    "field": "linked_symbols",
                    "value": ", ".join(self.symbols) if self.symbols else "none",
                    "confidence": 0.82 if self.symbols else 0.60,
                    "source_chunk_id": "news-cluster-symbols",
                },
            ],
            "events": [
                {
                    "event_id": event.event_id,
                    "title": event.title,
                    "event_at": event.event_at,
                    "symbol": event.symbol,
                    "impact_direction": event.impact_direction,
                    "impact_score": event.impact_score,
                    "source_document_id": event.external_document_id,
                    "korean_title": event.korean_title,
                    "korean_summary": event.korean_summary,
                    "translation_confidence": event.translation_confidence,
                }
                for event in self.events[:10]
            ],
            "audit_notes": [
                "No paid provider or LLM was called.",
                "This artifact is evidence for AI validator review, not an automatic recommendation.",
            ],
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def run_news_rss_cluster_evidence(
    *,
    config: RuntimeConfig,
    as_of_date: date | None = None,
    event_limit: int = DEFAULT_CLUSTER_EVIDENCE_EVENT_LIMIT,
    max_clusters: int = DEFAULT_CLUSTER_EVIDENCE_MAX_CLUSTERS,
    dry_run: bool = False,
    pipeline_name: str = DEFAULT_CLUSTER_EVIDENCE_PIPELINE_NAME,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    if not pipeline_name.strip():
        raise ValueError("pipeline_name must not be empty")
    target_date = as_of_date or date.today()
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    events = load_news_rss_cluster_evidence_events(as_of_date=target_date, limit=event_limit, executor=sql_executor)
    clusters = build_news_rss_clusters(events, as_of_date=target_date, max_clusters=max_clusters)

    if dry_run:
        return {
            **_empty_summary(as_of_date=target_date, pipeline_name=pipeline_name),
            "status": "planned",
            "requested_event_count": len(events),
            "cluster_count": len(clusters),
            "planned_cluster_count": len(clusters),
            "results": [_planned_result(cluster).summary() for cluster in clusters],
        }

    if not clusters:
        return _empty_summary(as_of_date=target_date, pipeline_name=pipeline_name)

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=pipeline_name,
        config_json={
            "as_of_date": target_date.isoformat(),
            "event_limit": event_limit,
            "max_clusters": max_clusters,
            "runner": DEFAULT_CLUSTER_EVIDENCE_PIPELINE_NAME,
            "requested_event_count": len(events),
        },
    )
    inserted = 0
    skipped = 0
    failed = 0
    results: list[dict[str, object]] = []

    try:
        for cluster in clusters:
            try:
                existing_artifact_id = _lookup_existing_artifact(sql_executor, request_hash=cluster.request_hash)
                if existing_artifact_id is not None:
                    skipped += 1
                    results.append(
                        NewsRssClusterEvidenceResult(
                            theme_key=cluster.theme_key,
                            theme_name=cluster.theme_name,
                            status="skipped_existing",
                            event_count=len(cluster.events),
                            symbols=cluster.symbols,
                            representative_event_id=cluster.representative_event.event_id,
                            story_key=cluster.story_key,
                            story_label=cluster.story_label,
                            artifact_id=existing_artifact_id,
                            run_id=run_id,
                            request_hash=cluster.request_hash,
                        ).summary()
                    )
                    continue

                invocation_id = int(
                    sql_executor.execute_scalar(
                        render_news_rss_cluster_model_invocation_insert_sql(
                            run_id=run_id,
                            request_hash=cluster.request_hash,
                        )
                    )
                )
                artifact_id = int(
                    sql_executor.execute_scalar(
                        render_news_rss_cluster_extraction_artifact_insert_sql(
                            invocation_id=invocation_id,
                            document_id=cluster.representative_event.document_id,
                            event_id=cluster.representative_event.event_id,
                            output_json=cluster.output_json(),
                            confidence=cluster.confidence,
                        )
                    )
                )
                inserted += 1
                results.append(
                    NewsRssClusterEvidenceResult(
                        theme_key=cluster.theme_key,
                        theme_name=cluster.theme_name,
                        status="inserted",
                        event_count=len(cluster.events),
                        symbols=cluster.symbols,
                        representative_event_id=cluster.representative_event.event_id,
                        story_key=cluster.story_key,
                        story_label=cluster.story_label,
                        artifact_id=artifact_id,
                        invocation_id=invocation_id,
                        run_id=run_id,
                        request_hash=cluster.request_hash,
                    ).summary()
                )
            except Exception as exc:
                failed += 1
                results.append(
                    NewsRssClusterEvidenceResult(
                        theme_key=cluster.theme_key,
                        theme_name=cluster.theme_name,
                        status="failed",
                        event_count=len(cluster.events),
                        symbols=cluster.symbols,
                        representative_event_id=cluster.representative_event.event_id,
                        story_key=cluster.story_key,
                        story_label=cluster.story_label,
                        run_id=run_id,
                        request_hash=cluster.request_hash,
                        error=str(exc),
                    ).summary()
                )

        if failed:
            _mark_pipeline_run_failed(sql_executor, run_id, f"{failed} news cluster evidence artifacts failed")
        else:
            _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        "report_name": "news_rss_cluster_evidence",
        "status": "completed" if failed == 0 else "completed_with_failures",
        "pipeline_name": pipeline_name,
        "as_of_date": target_date.isoformat(),
        "run_id": run_id,
        "requested_event_count": len(events),
        "cluster_count": len(clusters),
        "inserted_artifact_count": inserted,
        "skipped_existing_count": skipped,
        "failed_cluster_count": failed,
        "results": results,
    }


def load_news_rss_cluster_evidence_events(
    *,
    as_of_date: date,
    limit: int,
    executor: PsqlCommandExecutor,
) -> tuple[NewsRssClusterEvidenceEvent, ...]:
    payload_text = executor.execute_scalar(
        render_news_rss_cluster_evidence_event_candidates_sql(as_of_date=as_of_date, limit=limit)
    )
    payload = json.loads(payload_text)
    return tuple(
        NewsRssClusterEvidenceEvent(
            event_id=int(item["event_id"]),
            document_id=int(item["document_id"]) if item.get("document_id") is not None else None,
            event_type=str(item["event_type"]),
            title=str(item["title"]),
            summary=str(item.get("summary") or ""),
            event_at=str(item["event_at"]),
            source_name=item.get("source_name"),
            external_document_id=item.get("external_document_id"),
            theme_key=str(item["theme_key"]),
            theme_name=str(item["theme_name"]),
            impact_direction=str(item.get("impact_direction") or "watch"),
            impact_score=float(item["impact_score"]) if item.get("impact_score") is not None else None,
            symbol=str(item["symbol"]).upper() if item.get("symbol") else None,
            korean_title=item.get("korean_title"),
            korean_summary=item.get("korean_summary"),
            translation_confidence=float(item["translation_confidence"])
            if item.get("translation_confidence") is not None
            else None,
        )
        for item in payload
    )


def build_news_rss_clusters(
    events: tuple[NewsRssClusterEvidenceEvent, ...],
    *,
    as_of_date: date,
    max_clusters: int,
) -> tuple[NewsRssClusterEvidence, ...]:
    if max_clusters <= 0:
        raise ValueError("max_clusters must be greater than 0")

    grouped: dict[tuple[str, str], list[NewsRssClusterEvidenceEvent]] = {}
    cluster_labels: dict[tuple[str, str], str] = {}
    theme_names: dict[tuple[str, str], str] = {}
    seen_event_ids: set[int] = set()
    for event in events:
        if event.event_id in seen_event_ids:
            continue
        seen_event_ids.add(event.event_id)
        fingerprint = _cluster_story_fingerprint(event)
        group_key = (event.theme_key, fingerprint.story_key)
        grouped.setdefault(group_key, []).append(event)
        theme_names.setdefault(group_key, event.theme_name)
        cluster_labels.setdefault(group_key, fingerprint.story_label)

    clusters = [
        NewsRssClusterEvidence(
            theme_key=theme_key,
            theme_name=theme_names[(theme_key, story_key)],
            as_of_date=as_of_date,
            events=tuple(sorted(items, key=lambda item: (item.event_at, item.event_id), reverse=True)),
            story_key=story_key,
            story_label=cluster_labels[(theme_key, story_key)],
        )
        for (theme_key, story_key), items in grouped.items()
        if _should_keep_cluster(theme_key=theme_key, events=items)
    ]
    return tuple(
        sorted(
            clusters,
            key=lambda cluster: (len(cluster.events), cluster.representative_event.event_at, cluster.theme_key),
            reverse=True,
        )[:max_clusters]
    )


def _planned_result(cluster: NewsRssClusterEvidence) -> NewsRssClusterEvidenceResult:
    return NewsRssClusterEvidenceResult(
        theme_key=cluster.theme_key,
        theme_name=cluster.theme_name,
        status="planned",
        event_count=len(cluster.events),
        symbols=cluster.symbols,
        representative_event_id=cluster.representative_event.event_id,
        story_key=cluster.story_key,
        story_label=cluster.story_label,
        request_hash=cluster.request_hash,
    )


def _cluster_story_fingerprint(event: NewsRssClusterEvidenceEvent) -> _StoryFingerprint:
    if event.theme_key not in BROAD_STORY_THEME_KEYS:
        return _StoryFingerprint(story_key="theme", story_label=event.theme_name)

    text = f"{event.title} {event.summary}".lower()
    tokens = [
        token.strip("-")
        for token in _STORY_TOKEN_PATTERN.findall(text)
        if token.strip("-") and token.strip("-") not in _STORY_STOP_WORDS
    ]
    unique_tokens = list(dict.fromkeys(tokens))
    if len(unique_tokens) < 2:
        return _StoryFingerprint(story_key=f"event-{event.event_id}", story_label=event.title[:72] or event.theme_name)

    story_tokens = unique_tokens[:STORY_TOKEN_LIMIT]
    label_tokens = unique_tokens[:STORY_LABEL_TOKEN_LIMIT]
    return _StoryFingerprint(
        story_key="story-" + "-".join(story_tokens),
        story_label=" ".join(label_tokens).title(),
    )


def _should_keep_cluster(*, theme_key: str, events: list[NewsRssClusterEvidenceEvent]) -> bool:
    if theme_key not in BROAD_STORY_THEME_KEYS:
        return True
    if any(event.symbol for event in events):
        return True
    return len(events) >= MIN_BROAD_STORY_EVENTS_WITHOUT_SYMBOL


def _lookup_existing_artifact(executor: PsqlCommandExecutor, *, request_hash: str) -> int | None:
    try:
        return int(executor.execute_scalar(render_existing_news_rss_cluster_artifact_lookup_sql(request_hash=request_hash)))
    except PsqlExecutionError:
        return None


def _empty_summary(*, as_of_date: date, pipeline_name: str = DEFAULT_CLUSTER_EVIDENCE_PIPELINE_NAME) -> dict[str, object]:
    return {
        "report_name": "news_rss_cluster_evidence",
        "status": "completed",
        "pipeline_name": pipeline_name,
        "as_of_date": as_of_date.isoformat(),
        "run_id": None,
        "requested_event_count": 0,
        "cluster_count": 0,
        "inserted_artifact_count": 0,
        "skipped_existing_count": 0,
        "failed_cluster_count": 0,
        "results": [],
    }


def _create_pipeline_run(
    executor: PsqlCommandExecutor,
    *,
    pipeline_name: str,
    config_json: dict[str, object],
) -> int:
    payload = json.dumps(config_json, ensure_ascii=False, sort_keys=True)
    sql = f"""insert into ops.pipeline_run (
    run_kind,
    pipeline_name,
    status,
    config_json
)
values (
    'ai',
    {sql_literal(pipeline_name)},
    'running',
    {sql_literal(payload)}::jsonb
)
returning run_id;"""
    return int(executor.execute_scalar(sql))


def _mark_pipeline_run_succeeded(executor: PsqlCommandExecutor, run_id: int) -> None:
    executor.execute_non_query(
        f"""update ops.pipeline_run
set
    status = 'succeeded',
    ended_at = now(),
    error_summary = null
where run_id = {run_id};"""
    )


def _mark_pipeline_run_failed(executor: PsqlCommandExecutor, run_id: int, error_summary: str) -> None:
    truncated = error_summary.strip()[:2000] or "news RSS cluster evidence failed"
    try:
        executor.execute_non_query(
            f"""update ops.pipeline_run
set
    status = 'failed',
    ended_at = now(),
    error_summary = {sql_literal(truncated)}
where run_id = {run_id};"""
        )
    except Exception:
        return
