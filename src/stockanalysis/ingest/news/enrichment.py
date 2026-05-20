from __future__ import annotations

import json
import re
from dataclasses import dataclass

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.news.models import NewsRssEventEnrichmentCandidate, NewsRssEventEnrichmentResult
from stockanalysis.ingest.news.sql import (
    render_instrument_lookup_by_symbol_sql,
    render_news_rss_classification_bootstrap_sql,
    render_pending_news_rss_event_enrichment_candidates_sql,
)
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError
from stockanalysis.ingest.sec.sql import (
    render_event_classification_impact_upsert_sql,
    render_event_instrument_impact_upsert_sql,
)


@dataclass(frozen=True)
class _ThemeTarget:
    node_code: str
    node_type: str
    impact_direction: str
    impact_strength: float
    confidence: float
    rationale: str


@dataclass(frozen=True)
class _InstrumentLookup:
    instrument_id: int
    primary_symbol: str
    instrument_name: str


_DEFAULT_THEME = _ThemeTarget(
    node_code="MARKET_NEWS_FLOW",
    node_type="theme",
    impact_direction="watch",
    impact_strength=0.45,
    confidence=0.60,
    rationale="Free RSS item is market-relevant news flow awaiting deeper enrichment.",
)

_FEED_THEME_MAP: dict[str, _ThemeTarget] = {
    "us-market-breadth": _ThemeTarget(
        node_code="US_MARKET_BREADTH",
        node_type="subtheme",
        impact_direction="watch",
        impact_strength=0.60,
        confidence=0.82,
        rationale="RSS feed is configured for broad US market breadth and index risk appetite.",
    ),
    "ai-semiconductor-cycle": _ThemeTarget(
        node_code="AI_SEMICONDUCTOR_CYCLE",
        node_type="subtheme",
        impact_direction="watch",
        impact_strength=0.65,
        confidence=0.84,
        rationale="RSS feed is configured for AI and semiconductor cycle monitoring.",
    ),
    "macro-rates-fed": _ThemeTarget(
        node_code="MACRO_RATES_FED",
        node_type="subtheme",
        impact_direction="watch",
        impact_strength=0.65,
        confidence=0.84,
        rationale="RSS feed is configured for rates, inflation, Treasury, and Fed policy monitoring.",
    ),
    "energy-geopolitics": _ThemeTarget(
        node_code="ENERGY_GEOPOLITICS",
        node_type="subtheme",
        impact_direction="watch",
        impact_strength=0.65,
        confidence=0.84,
        rationale="RSS feed is configured for energy and geopolitical risk monitoring.",
    ),
}

_THEME_KEYWORD_TARGETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("AI_SEMICONDUCTOR_CYCLE", ("nvidia", "nvda", "gpu", "h200", "semiconductor", "chip", "artificial intelligence")),
    ("MACRO_RATES_FED", ("fed", "federal reserve", "treasury", "yield", "inflation", "interest rate", "rates")),
    ("ENERGY_GEOPOLITICS", ("oil", "energy", "crude", "opec", "geopolitic", "war")),
    ("US_MARKET_BREADTH", ("s&p 500", "spx", "nasdaq", "stock market", "futures", "wall street")),
)

_THEME_BY_CODE: dict[str, _ThemeTarget] = {
    target.node_code: target for target in (*_FEED_THEME_MAP.values(), _DEFAULT_THEME)
}

_SYMBOL_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("NVDA", ("nvidia", "nvda", "h200", "gpu")),
    ("AAPL", ("apple", "aapl", "iphone")),
    ("MSFT", ("microsoft", "msft", "azure")),
    ("TSLA", ("tesla", "tsla")),
    ("SPY", ("s&p 500", "spx", "broad market")),
    ("QQQ", ("nasdaq 100", "nasdaq futures", "nasdaq")),
    ("XOM", ("exxon", "xom", "oil prices", "crude oil")),
)

_RISK_WORDS = (
    "decline",
    "declines",
    "dip",
    "dips",
    "down",
    "fall",
    "falls",
    "fear",
    "fears",
    "pressure",
    "risk",
    "sell-off",
    "slip",
    "slips",
    "strain",
    "sticky prices",
)
_SUPPORTIVE_WORDS = (
    "advance",
    "advances",
    "deal survived",
    "gain",
    "gains",
    "higher",
    "improve",
    "improves",
    "jump",
    "jumps",
    "rally",
    "surge",
    "survived",
)


def run_news_rss_event_enrichment(
    *,
    config: RuntimeConfig,
    limit: int = 50,
    dry_run: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_pending_news_rss_event_enrichment_candidates(limit=limit, executor=sql_executor)
    if not candidates:
        return _empty_summary()

    if dry_run:
        planned_results = [
            _build_result(candidate, run_id=None, instrument_symbol=detect_instrument_symbol(candidate), status="planned").summary()
            | {"theme_code": classify_theme(candidate).node_code}
            for candidate in candidates
        ]
        return {
            **_empty_summary(),
            "requested_event_count": len(candidates),
            "planned_event_count": len(candidates),
            "results": planned_results,
        }

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="news_rss_event_enrichment",
        config_json={"limit": limit, "requested_event_count": len(candidates)},
    )
    succeeded = 0
    failed = 0
    instrument_linked = 0
    instrument_skipped = 0
    results: list[dict[str, object]] = []

    try:
        sql_executor.execute_non_query(render_news_rss_classification_bootstrap_sql())
        for candidate in candidates:
            theme_target = classify_theme(candidate)
            instrument_symbol = detect_instrument_symbol(candidate)
            try:
                direction, strength = infer_impact_direction_and_strength(candidate)
                sql_executor.execute_non_query(
                    render_event_classification_impact_upsert_sql(
                        event_id=candidate.event_id,
                        node_code=theme_target.node_code,
                        node_type=theme_target.node_type,
                        impact_direction=direction,
                        impact_strength=max(theme_target.impact_strength, strength),
                        confidence=theme_target.confidence,
                        rationale=f"{theme_target.rationale} Rule-based free RSS enrichment; no paid provider or LLM used.",
                    )
                )

                if instrument_symbol:
                    instrument = resolve_instrument_by_symbol(instrument_symbol, executor=sql_executor)
                    if instrument is not None:
                        sql_executor.execute_non_query(
                            render_event_instrument_impact_upsert_sql(
                                event_id=candidate.event_id,
                                instrument_id=instrument.instrument_id,
                                impact_direction=direction,
                                impact_strength=strength,
                                confidence=0.72,
                                rationale=(
                                    f"Rule-based free RSS enrichment matched `{instrument.primary_symbol}` from "
                                    f"title/summary keywords; no paid provider or LLM used."
                                ),
                            )
                        )
                        instrument_linked += 1
                        status = "succeeded"
                    else:
                        instrument_skipped += 1
                        status = "succeeded_instrument_missing"
                else:
                    instrument_skipped += 1
                    status = "succeeded_theme_only"
            except Exception as exc:
                failed += 1
                results.append(
                    _build_result(
                        candidate,
                        run_id=run_id,
                        theme_code=theme_target.node_code,
                        instrument_symbol=instrument_symbol,
                        status="failed",
                        error=str(exc),
                    ).summary()
                )
                continue

            succeeded += 1
            results.append(
                _build_result(
                    candidate,
                    run_id=run_id,
                    theme_code=theme_target.node_code,
                    instrument_symbol=instrument_symbol,
                    status=status,
                ).summary()
            )

        if failed:
            _mark_pipeline_run_failed(sql_executor, run_id, f"{failed} news RSS enrichment operations failed")
        else:
            _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return {
        "report_name": "news_rss_event_enrichment",
        "status": "completed" if failed == 0 else "completed_with_failures",
        "run_id": run_id,
        "requested_event_count": len(candidates),
        "succeeded_event_count": succeeded,
        "failed_event_count": failed,
        "classified_event_count": succeeded,
        "instrument_linked_event_count": instrument_linked,
        "instrument_skipped_event_count": instrument_skipped,
        "results": results,
    }


def load_pending_news_rss_event_enrichment_candidates(
    *,
    limit: int,
    executor: PsqlCommandExecutor,
) -> tuple[NewsRssEventEnrichmentCandidate, ...]:
    payload_text = executor.execute_scalar(render_pending_news_rss_event_enrichment_candidates_sql(limit=limit))
    payload = json.loads(payload_text)
    return tuple(
        NewsRssEventEnrichmentCandidate(
            event_id=int(item["event_id"]),
            event_type=str(item["event_type"]),
            dedupe_key=item.get("dedupe_key"),
            title=str(item["title"]),
            summary=str(item.get("summary") or ""),
            source_name=item.get("source_name"),
            external_document_id=item.get("external_document_id"),
        )
        for item in payload
    )


def classify_theme(candidate: NewsRssEventEnrichmentCandidate) -> _ThemeTarget:
    feed_name = _feed_name(candidate.source_name)
    if feed_name in _FEED_THEME_MAP:
        return _FEED_THEME_MAP[feed_name]

    text = _candidate_text(candidate)
    for theme_code, keywords in _THEME_KEYWORD_TARGETS:
        if any(keyword in text for keyword in keywords):
            return _THEME_BY_CODE[theme_code]
    return _DEFAULT_THEME


def detect_instrument_symbol(candidate: NewsRssEventEnrichmentCandidate) -> str | None:
    text = _candidate_text(candidate)
    for symbol, keywords in _SYMBOL_KEYWORDS:
        if any(_keyword_matches(text, keyword) for keyword in keywords):
            return symbol
    return None


def infer_impact_direction_and_strength(candidate: NewsRssEventEnrichmentCandidate) -> tuple[str, float]:
    text = _candidate_text(candidate)
    if any(word in text for word in _RISK_WORDS):
        return "risk_review", 0.68
    if any(word in text for word in _SUPPORTIVE_WORDS):
        return "supportive", 0.66
    return "watch", 0.55


def resolve_instrument_by_symbol(
    symbol: str,
    *,
    executor: PsqlCommandExecutor,
) -> _InstrumentLookup | None:
    try:
        payload_text = executor.execute_scalar(render_instrument_lookup_by_symbol_sql(symbol))
    except PsqlExecutionError:
        return None
    payload = json.loads(payload_text)
    return _InstrumentLookup(
        instrument_id=int(payload["instrument_id"]),
        primary_symbol=str(payload["primary_symbol"]).upper(),
        instrument_name=str(payload["instrument_name"]),
    )


def _candidate_text(candidate: NewsRssEventEnrichmentCandidate) -> str:
    return f"{candidate.title} {candidate.summary}".lower()


def _feed_name(source_name: str | None) -> str:
    if not source_name:
        return ""
    return source_name.removeprefix("rss_news:").strip()


def _keyword_matches(text: str, keyword: str) -> bool:
    if re.fullmatch(r"[a-z0-9.:-]+", keyword):
        return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text) is not None
    return keyword in text


def _build_result(
    candidate: NewsRssEventEnrichmentCandidate,
    *,
    run_id: int | None,
    theme_code: str | None = None,
    instrument_symbol: str | None,
    status: str,
    error: str | None = None,
) -> NewsRssEventEnrichmentResult:
    return NewsRssEventEnrichmentResult(
        event_id=candidate.event_id,
        event_type=candidate.event_type,
        theme_code=theme_code,
        instrument_symbol=instrument_symbol,
        status=status,
        run_id=run_id,
        error=error,
    )


def _empty_summary() -> dict[str, object]:
    return {
        "report_name": "news_rss_event_enrichment",
        "status": "completed",
        "run_id": None,
        "requested_event_count": 0,
        "succeeded_event_count": 0,
        "failed_event_count": 0,
        "classified_event_count": 0,
        "instrument_linked_event_count": 0,
        "instrument_skipped_event_count": 0,
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
    'ingest',
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
    truncated = error_summary.strip()[:2000] or "news RSS event enrichment failed"
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
