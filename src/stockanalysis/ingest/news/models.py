from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsRssItem:
    feed_name: str
    feed_url: str
    external_document_id: str
    title: str
    summary: str | None
    url: str | None
    language: str | None
    published_at: datetime | None
    guid: str | None
    checksum: str


@dataclass(frozen=True)
class NewsRssSyncResult:
    feed_name: str
    feed_url: str
    items: tuple[NewsRssItem, ...]

    def summary(self) -> dict[str, object]:
        first_published_at = self.items[0].published_at.isoformat() if self.items and self.items[0].published_at else None
        last_published_at = self.items[-1].published_at.isoformat() if self.items and self.items[-1].published_at else None
        return {
            "feed_name": self.feed_name,
            "feed_url": self.feed_url,
            "item_count": len(self.items),
            "first_published_at": first_published_at,
            "last_published_at": last_published_at,
        }


@dataclass(frozen=True)
class NewsRssEventEnrichmentCandidate:
    event_id: int
    event_type: str
    dedupe_key: str | None
    title: str
    summary: str
    source_name: str | None
    external_document_id: str | None


@dataclass(frozen=True)
class NewsRssEventEnrichmentResult:
    event_id: int
    event_type: str
    theme_code: str | None
    instrument_symbol: str | None
    status: str
    run_id: int | None = None
    error: str | None = None

    def summary(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "theme_code": self.theme_code,
            "instrument_symbol": self.instrument_symbol,
            "status": self.status,
            "run_id": self.run_id,
        }
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True)
class NewsRssClusterEvidenceEvent:
    event_id: int
    document_id: int | None
    event_type: str
    title: str
    summary: str
    event_at: str
    source_name: str | None
    external_document_id: str | None
    theme_key: str
    theme_name: str
    impact_direction: str
    impact_score: float | None
    symbol: str | None
    korean_title: str | None = None
    korean_summary: str | None = None
    translation_confidence: float | None = None


@dataclass(frozen=True)
class NewsRssClusterEvidenceResult:
    theme_key: str
    theme_name: str
    status: str
    event_count: int
    symbols: tuple[str, ...]
    representative_event_id: int | None
    story_key: str | None = None
    story_label: str | None = None
    artifact_id: int | None = None
    invocation_id: int | None = None
    run_id: int | None = None
    request_hash: str | None = None
    error: str | None = None

    def summary(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "theme_key": self.theme_key,
            "theme_name": self.theme_name,
            "status": self.status,
            "event_count": self.event_count,
            "symbols": list(self.symbols),
            "representative_event_id": self.representative_event_id,
            "story_key": self.story_key,
            "story_label": self.story_label,
            "artifact_id": self.artifact_id,
            "invocation_id": self.invocation_id,
            "run_id": self.run_id,
            "request_hash": self.request_hash,
        }
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True)
class NewsRssAiExtractionCandidate:
    event_id: int
    document_id: int
    title: str
    summary: str
    event_at: str
    source_name: str | None
    external_document_id: str | None
    source_url: str | None
    existing_theme_code: str | None
    existing_instrument_symbol: str | None


@dataclass(frozen=True)
class NewsRssAiExtractionResult:
    event_id: int
    status: str
    document_id: int | None = None
    artifact_id: int | None = None
    invocation_id: int | None = None
    run_id: int | None = None
    request_hash: str | None = None
    validated_theme_count: int = 0
    validated_instrument_count: int = 0
    rejected_impact_count: int = 0
    error: str | None = None

    def summary(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "event_id": self.event_id,
            "document_id": self.document_id,
            "status": self.status,
            "artifact_id": self.artifact_id,
            "invocation_id": self.invocation_id,
            "run_id": self.run_id,
            "request_hash": self.request_hash,
            "validated_theme_count": self.validated_theme_count,
            "validated_instrument_count": self.validated_instrument_count,
            "rejected_impact_count": self.rejected_impact_count,
        }
        if self.error:
            payload["error"] = self.error
        return payload
