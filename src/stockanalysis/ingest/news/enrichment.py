from __future__ import annotations

import json
import re
from dataclasses import dataclass

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.market.universe import (
    load_market_universe_records,
    render_market_universe_bootstrap_sql,
    select_market_universe_records,
)
from stockanalysis.ingest.news.models import NewsRssEventEnrichmentCandidate, NewsRssEventEnrichmentResult
from stockanalysis.ingest.news.sql import (
    render_instrument_lookup_by_company_alias_sql,
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

_QUANTUM_THEME = _ThemeTarget(
    node_code="QUANTUM_COMPUTING_POLICY",
    node_type="subtheme",
    impact_direction="watch",
    impact_strength=0.64,
    confidence=0.82,
    rationale="News mentions quantum computing, quantum stocks, or government policy support for quantum technology.",
)

_AI_LABOR_PRODUCTIVITY_THEME = _ThemeTarget(
    node_code="AI_LABOR_PRODUCTIVITY",
    node_type="subtheme",
    impact_direction="watch",
    impact_strength=0.58,
    confidence=0.78,
    rationale="News focuses on AI adoption, labor displacement, productivity, or workplace impact rather than semiconductor supply.",
)

_THEME_KEYWORD_TARGETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "QUANTUM_COMPUTING_POLICY",
        (
            "quantum",
            "quantum computing",
            "quantum computer",
            "quantum stocks",
            "qubt",
            "rigetti",
            "ionq",
        ),
    ),
    ("AI_SEMICONDUCTOR_CYCLE", ("nvidia", "nvda", "gpu", "h200", "semiconductor", "chip", "artificial intelligence")),
    ("MACRO_RATES_FED", ("fed", "federal reserve", "treasury", "yield", "inflation", "interest rate", "rates")),
    ("ENERGY_GEOPOLITICS", ("oil", "energy", "crude", "opec", "geopolitic", "war")),
    ("US_MARKET_BREADTH", ("s&p 500", "spx", "nasdaq", "stock market", "futures", "wall street")),
)

_THEME_BY_CODE: dict[str, _ThemeTarget] = {
    target.node_code: target for target in (*_FEED_THEME_MAP.values(), _QUANTUM_THEME, _AI_LABOR_PRODUCTIVITY_THEME, _DEFAULT_THEME)
}

_SYMBOL_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("QUBT", ("qubt", "quantum computing inc", "quantum computing stock", "quantum stocks")),
    ("NVDA", ("nvidia", "nvda", "h200", "gpu")),
    ("AAPL", ("apple", "aapl", "iphone")),
    ("MSFT", ("microsoft", "msft", "azure")),
    ("TSLA", ("tesla", "tsla")),
    ("SPY", ("s&p 500", "spx", "broad market")),
    ("QQQ", ("nasdaq 100", "nasdaq futures", "nasdaq")),
    ("XOM", ("exxon", "exxon mobil", "xom")),
)

_EXPLICIT_TICKER_PATTERNS = (
    re.compile(r"\$([A-Z][A-Z0-9.-]{0,5})\b"),
    re.compile(r"\(([A-Z][A-Z0-9.-]{0,5})\)"),
    re.compile(r"\b([A-Z][A-Z0-9.-]{0,5})\s+stock\b"),
)

_TICKER_BLOCKLIST = {
    "AI",
    "API",
    "CEO",
    "CFO",
    "CIO",
    "COO",
    "CPI",
    "ETF",
    "EU",
    "FDA",
    "FED",
    "FOMC",
    "GDP",
    "IPO",
    "LLM",
    "NASDAQ",
    "NYSE",
    "OPEC",
    "PCE",
    "SEC",
    "SPX",
    "UK",
    "US",
    "USA",
    "USD",
}

_AI_LABOR_CONTEXT_TERMS = (
    "automation",
    "displacement",
    "employment",
    "job",
    "jobs",
    "labor",
    "labour",
    "layoff",
    "layoffs",
    "productivity",
    "worker",
    "workers",
    "workforce",
    "workplace",
    "worry",
    "worried",
)

_COMPANY_ALIAS_CONTEXT_TERMS = (
    " analyst ",
    " downgrade",
    " earnings",
    " guidance",
    " price target",
    " q1 ",
    " q2 ",
    " q3 ",
    " q4 ",
    " quarterly",
    " revenue",
    " shares",
    " stock ",
    " upgrade",
)

_BROAD_MARKET_STOCK_TERMS = (
    "stock futures",
    "stock market",
    "stocks are",
    "stocks fall",
    "stocks gain",
    "stocks move",
    "stocks rally",
    "stocks rise",
    "stocks slip",
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
    "funding",
    "jump",
    "jumps",
    "rally",
    "soar",
    "soars",
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
        planned_results = []
        for candidate in candidates:
            instrument_symbol, _instrument = resolve_instrument_for_candidate(candidate, executor=sql_executor)
            planned_results.append(
                _build_result(candidate, run_id=None, instrument_symbol=instrument_symbol, status="planned").summary()
                | {"theme_code": classify_theme(candidate).node_code}
            )
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
            instrument_symbol, instrument = resolve_instrument_for_candidate(candidate, executor=sql_executor)
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
                                f"title/summary keywords or instrument-name alias; no paid provider or LLM used."
                            ),
                        )
                    )
                    instrument_linked += 1
                    status = "succeeded"
                elif instrument_symbol:
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


def run_news_missing_instrument_bootstrap(
    *,
    config: RuntimeConfig,
    limit: int = 100,
    company_tickers_json_path: str | None = None,
    exchanges: list[str] | None = None,
    dry_run: bool = False,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    candidates = load_pending_news_rss_event_enrichment_candidates(limit=limit, executor=sql_executor)
    missing_symbols: list[str] = []
    symbol_event_ids: dict[str, list[int]] = {}
    for candidate in candidates:
        symbol = detect_instrument_symbol(candidate)
        if not symbol or not is_safe_news_ticker_symbol(symbol):
            continue
        if resolve_instrument_by_symbol(symbol, executor=sql_executor) is not None:
            continue
        if symbol not in symbol_event_ids:
            missing_symbols.append(symbol)
            symbol_event_ids[symbol] = []
        symbol_event_ids[symbol].append(candidate.event_id)

    if not missing_symbols:
        summary = _empty_missing_instrument_summary(
            candidate_event_count=len(candidates),
            dry_run=dry_run,
        )
        if dry_run:
            return summary
        run_id = _create_pipeline_run(
            sql_executor,
            pipeline_name="news_missing_instrument_bootstrap",
            config_json={
                "limit": limit,
                "candidate_event_count": len(candidates),
                "missing_symbols": [],
                "bootstrapped_symbols": [],
                "unmatched_symbols": [],
            },
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
        return summary | {"run_id": run_id}

    records = load_market_universe_records(
        config=config,
        company_tickers_json_path=company_tickers_json_path,
    )
    selection = select_market_universe_records(records, exchanges=exchanges)
    wanted = set(missing_symbols)
    selected_records = tuple(record for record in selection.records if record.symbol in wanted)
    bootstrapped_symbols = sorted({record.symbol for record in selected_records})
    unmatched_symbols = sorted(wanted - set(bootstrapped_symbols))

    base_summary: dict[str, object] = {
        "report_name": "news_missing_instrument_bootstrap",
        "status": "planned" if dry_run else "completed",
        "run_id": None,
        "candidate_event_count": len(candidates),
        "missing_symbol_count": len(missing_symbols),
        "sec_matched_symbol_count": len(bootstrapped_symbols),
        "bootstrapped_symbol_count": 0 if dry_run else len(bootstrapped_symbols),
        "missing_symbols": missing_symbols,
        "bootstrapped_symbols": bootstrapped_symbols,
        "unmatched_symbols": unmatched_symbols,
        "symbol_event_ids": {symbol: symbol_event_ids[symbol] for symbol in missing_symbols},
        "dry_run": dry_run,
        "requested_exchanges": list(selection.requested_exchanges),
    }
    if dry_run or not selected_records:
        if dry_run:
            return base_summary
        run_id = _create_pipeline_run(
            sql_executor,
            pipeline_name="news_missing_instrument_bootstrap",
            config_json={
                "limit": limit,
                "company_tickers_fixture_path": company_tickers_json_path,
                "requested_exchanges": list(selection.requested_exchanges),
                "missing_symbols": missing_symbols,
                "bootstrapped_symbols": bootstrapped_symbols,
                "unmatched_symbols": unmatched_symbols,
            },
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
        return base_summary | {"run_id": run_id}

    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name="news_missing_instrument_bootstrap",
        config_json={
            "limit": limit,
            "company_tickers_fixture_path": company_tickers_json_path,
            "requested_exchanges": list(selection.requested_exchanges),
            "missing_symbols": missing_symbols,
            "bootstrapped_symbols": bootstrapped_symbols,
            "unmatched_symbols": unmatched_symbols,
        },
    )
    try:
        sql_executor.execute_non_query(render_market_universe_bootstrap_sql(selected_records))
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise

    return base_summary | {"run_id": run_id}


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
    text = _candidate_text(candidate)
    if _is_ai_labor_productivity_news(text):
        return _AI_LABOR_PRODUCTIVITY_THEME

    feed_name = _feed_name(candidate.source_name)
    if feed_name in _FEED_THEME_MAP:
        return _FEED_THEME_MAP[feed_name]

    for theme_code, keywords in _THEME_KEYWORD_TARGETS:
        if any(keyword in text for keyword in keywords):
            return _THEME_BY_CODE[theme_code]
    return _DEFAULT_THEME


def detect_instrument_symbol(candidate: NewsRssEventEnrichmentCandidate) -> str | None:
    text = _candidate_text(candidate)
    for symbol, keywords in _SYMBOL_KEYWORDS:
        if any(_keyword_matches(text, keyword) for keyword in keywords):
            return symbol
    return detect_explicit_ticker_symbol(candidate)


def detect_explicit_ticker_symbol(candidate: NewsRssEventEnrichmentCandidate) -> str | None:
    text = f"{candidate.title} {candidate.summary}"
    for pattern in _EXPLICIT_TICKER_PATTERNS:
        match = pattern.search(text)
        if match is None:
            continue
        symbol = match.group(1).upper()
        if is_safe_news_ticker_symbol(symbol):
            return symbol
    return None


def is_safe_news_ticker_symbol(symbol: str) -> bool:
    cleaned = symbol.strip().upper()
    if cleaned in _TICKER_BLOCKLIST:
        return False
    if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,5}", cleaned):
        return False
    return any(char.isalpha() for char in cleaned)


def resolve_instrument_for_candidate(
    candidate: NewsRssEventEnrichmentCandidate,
    *,
    executor: PsqlCommandExecutor,
) -> tuple[str | None, _InstrumentLookup | None]:
    symbol = detect_instrument_symbol(candidate)
    if symbol:
        return symbol, resolve_instrument_by_symbol(symbol, executor=executor)
    if not should_attempt_company_alias_lookup(candidate):
        return None, None
    instrument = resolve_instrument_by_company_alias(candidate, executor=executor)
    if instrument is not None:
        return instrument.primary_symbol, instrument
    return None, None


def should_attempt_company_alias_lookup(candidate: NewsRssEventEnrichmentCandidate) -> bool:
    text = f" {_candidate_text(candidate)} "
    if any(term in text for term in _BROAD_MARKET_STOCK_TERMS):
        return False
    return any(term in text for term in _COMPANY_ALIAS_CONTEXT_TERMS)


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


def resolve_instrument_by_company_alias(
    candidate: NewsRssEventEnrichmentCandidate,
    *,
    executor: PsqlCommandExecutor,
) -> _InstrumentLookup | None:
    try:
        payload_text = executor.execute_scalar(
            render_instrument_lookup_by_company_alias_sql(title=candidate.title, summary=candidate.summary)
        )
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


def _is_ai_labor_productivity_news(text: str) -> bool:
    mentions_ai = "artificial intelligence" in text or re.search(r"(?<![a-z0-9])ai(?![a-z0-9])", text) is not None
    if not mentions_ai:
        return False
    return any(term in text for term in _AI_LABOR_CONTEXT_TERMS)


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


def _empty_missing_instrument_summary(*, candidate_event_count: int, dry_run: bool) -> dict[str, object]:
    return {
        "report_name": "news_missing_instrument_bootstrap",
        "status": "planned" if dry_run else "completed",
        "run_id": None,
        "candidate_event_count": candidate_event_count,
        "missing_symbol_count": 0,
        "sec_matched_symbol_count": 0,
        "bootstrapped_symbol_count": 0,
        "missing_symbols": [],
        "bootstrapped_symbols": [],
        "unmatched_symbols": [],
        "symbol_event_ids": {},
        "dry_run": dry_run,
        "requested_exchanges": [],
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
