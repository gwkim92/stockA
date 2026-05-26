from __future__ import annotations

import json
import re
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.macro.sql import sql_literal
from stockanalysis.ingest.news.ai_extract import DEFAULT_MIN_CONFIDENCE, parse_news_ai_output, validate_news_ai_output
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError


DEFAULT_EVAL_NAME = "news_ai_extraction_quality"
DEFAULT_DATASET_VERSION = "news-ai-eval-v1"
DEFAULT_DATASET_PATH = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "news_ai_eval_dataset_v1.json"

DEFAULT_REFERENCE_NODES: dict[str, dict[str, object]] = {
    "AI_SEMICONDUCTOR_CYCLE": {"node_id": 21, "code": "AI_SEMICONDUCTOR_CYCLE", "node_type": "theme", "name": "AI Semiconductor Cycle"},
    "QUANTUM_COMPUTING_POLICY": {"node_id": 22, "code": "QUANTUM_COMPUTING_POLICY", "node_type": "theme", "name": "Quantum Computing Policy"},
    "ENERGY_GEOPOLITICS": {"node_id": 23, "code": "ENERGY_GEOPOLITICS", "node_type": "theme", "name": "Energy Geopolitics"},
    "MACRO_RATES_FED": {"node_id": 24, "code": "MACRO_RATES_FED", "node_type": "macro", "name": "Macro Rates and Fed"},
    "MACRO_INFLATION": {"node_id": 25, "code": "MACRO_INFLATION", "node_type": "macro", "name": "Macro Inflation"},
    "TECH_DOMAIN": {"node_id": 26, "code": "TECH_DOMAIN", "node_type": "domain", "name": "Technology Domain"},
    "MARKET_NEWS_FLOW": {"node_id": 27, "code": "MARKET_NEWS_FLOW", "node_type": "theme", "name": "Market News Flow"},
}

DEFAULT_REFERENCE_INSTRUMENTS: dict[str, dict[str, object]] = {
    "NVDA": {"instrument_id": 701, "primary_symbol": "NVDA", "instrument_name": "NVIDIA Corp"},
    "QUBT": {"instrument_id": 702, "primary_symbol": "QUBT", "instrument_name": "Quantum Computing Inc"},
    "XOM": {"instrument_id": 703, "primary_symbol": "XOM", "instrument_name": "Exxon Mobil Corporation"},
    "SPY": {"instrument_id": 704, "primary_symbol": "SPY", "instrument_name": "SPDR S&P 500 ETF Trust"},
    "QQQ": {"instrument_id": 705, "primary_symbol": "QQQ", "instrument_name": "Invesco QQQ Trust"},
    "TLT": {"instrument_id": 706, "primary_symbol": "TLT", "instrument_name": "iShares 20+ Year Treasury Bond ETF"},
    "XLE": {"instrument_id": 707, "primary_symbol": "XLE", "instrument_name": "Energy Select Sector SPDR Fund"},
}


@dataclass(frozen=True)
class NewsAiEvalCase:
    case_id: str
    category: str
    title: str
    summary: str
    korean_title: str
    korean_summary: str
    ai_output: dict[str, object]
    expected_theme_codes: tuple[str, ...]
    allowed_theme_codes: tuple[str, ...]
    forbidden_theme_codes: tuple[str, ...]
    expected_direct_symbols: tuple[str, ...]
    forbidden_direct_symbols: tuple[str, ...]
    expected_blocked_symbols: tuple[str, ...]
    expected_blocked_candidate: bool

    @property
    def source_text(self) -> str:
        return f"{self.title}\n{self.summary}"

    @property
    def has_korean_translation(self) -> bool:
        return bool(self.korean_title.strip() and self.korean_summary.strip())


@dataclass(frozen=True)
class NewsAiEvalDataset:
    dataset_version: str
    cases: tuple[NewsAiEvalCase, ...]
    reference_nodes: Mapping[str, Mapping[str, object]]
    reference_instruments: Mapping[str, Mapping[str, object]]


class NewsAiEvalReferenceExecutor:
    def __init__(self, dataset: NewsAiEvalDataset) -> None:
        self.nodes = {code.upper(): dict(row) for code, row in DEFAULT_REFERENCE_NODES.items()}
        self.nodes.update({code.upper(): dict(row) for code, row in dataset.reference_nodes.items()})
        self.instruments = {code.upper(): dict(row) for code, row in DEFAULT_REFERENCE_INSTRUMENTS.items()}
        self.instruments.update({code.upper(): dict(row) for code, row in dataset.reference_instruments.items()})

    def execute_scalar(self, sql: str) -> str:
        if "from ref.classification_node node" in sql:
            code = _lookup_sql_literal_argument(sql, "upper")
            if code and code.upper() in self.nodes:
                return json.dumps(self.nodes[code.upper()])
            raise PsqlExecutionError("psql returned no rows for scalar query")
        if "from ref.instrument i" in sql:
            symbol = _lookup_sql_literal_argument(sql, "lower")
            if symbol and symbol.upper() in self.instruments:
                return json.dumps(self.instruments[symbol.upper()])
            raise PsqlExecutionError("psql returned no rows for scalar query")
        raise AssertionError(f"Unexpected eval reference SQL: {sql[:120]}")


def load_news_ai_eval_dataset(path: str | Path | None = None) -> NewsAiEvalDataset:
    selected_path = Path(path).expanduser().resolve() if path is not None else DEFAULT_DATASET_PATH
    payload = json.loads(selected_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("News AI eval dataset must be a JSON object.")
    cases_payload = payload.get("cases")
    if not isinstance(cases_payload, list) or not cases_payload:
        raise ValueError("News AI eval dataset must contain a non-empty cases array.")
    return NewsAiEvalDataset(
        dataset_version=str(payload.get("dataset_version") or DEFAULT_DATASET_VERSION),
        cases=tuple(_parse_case(item) for item in cases_payload),
        reference_nodes=_as_mapping(payload.get("reference_nodes")),
        reference_instruments=_as_mapping(payload.get("reference_instruments")),
    )


def score_news_ai_eval_dataset(
    dataset: NewsAiEvalDataset,
    *,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> dict[str, object]:
    reference_executor = NewsAiEvalReferenceExecutor(dataset)
    case_results = []
    totals = {
        "theme_true_positive_count": 0,
        "theme_false_positive_count": 0,
        "direct_ticker_true_positive_count": 0,
        "direct_ticker_false_positive_count": 0,
        "macro_only_case_count": 0,
        "macro_only_false_ticker_count": 0,
        "blocked_expected_count": 0,
        "blocked_correct_count": 0,
        "translation_available_count": 0,
        "quantum_energy_misclassification_count": 0,
    }

    for case in dataset.cases:
        output = parse_news_ai_output(case.ai_output)
        validated = validate_news_ai_output(
            output,
            min_confidence=min_confidence,
            executor=reference_executor,  # type: ignore[arg-type]
            source_text=case.source_text,
        )
        accepted_themes = {impact.node_code for impact in validated.theme_impacts}
        accepted_symbols = {impact.primary_symbol for impact in validated.instrument_impacts}
        expected_themes = set(case.expected_theme_codes)
        allowed_themes = expected_themes | set(case.allowed_theme_codes)
        expected_symbols = set(case.expected_direct_symbols)
        forbidden_themes = set(case.forbidden_theme_codes)
        forbidden_symbols = set(case.forbidden_direct_symbols)
        blocked_symbols = set(case.expected_blocked_symbols)

        theme_false_positives = accepted_themes - allowed_themes
        direct_false_positives = accepted_symbols - expected_symbols
        missing_themes = expected_themes - accepted_themes
        missing_symbols = expected_symbols - accepted_symbols
        blocked_symbols_accepted = accepted_symbols & blocked_symbols
        forbidden_theme_hits = accepted_themes & forbidden_themes
        forbidden_symbol_hits = accepted_symbols & forbidden_symbols
        is_macro_only = case.category == "macro_only"
        if is_macro_only:
            totals["macro_only_case_count"] += 1
            totals["macro_only_false_ticker_count"] += len(accepted_symbols)
        if case.expected_blocked_candidate or blocked_symbols:
            totals["blocked_expected_count"] += 1
            if not blocked_symbols_accepted and (not case.expected_blocked_candidate or not accepted_themes and not accepted_symbols):
                totals["blocked_correct_count"] += 1
        if case.has_korean_translation:
            totals["translation_available_count"] += 1
        if case.category == "quantum_policy":
            energy_hits = forbidden_theme_hits | forbidden_symbol_hits
            totals["quantum_energy_misclassification_count"] += len(energy_hits)

        totals["theme_true_positive_count"] += len(accepted_themes & expected_themes)
        totals["theme_false_positive_count"] += len(theme_false_positives | forbidden_theme_hits)
        totals["direct_ticker_true_positive_count"] += len(accepted_symbols & expected_symbols)
        totals["direct_ticker_false_positive_count"] += len(direct_false_positives | forbidden_symbol_hits)

        case_results.append(
            {
                "case_id": case.case_id,
                "category": case.category,
                "accepted_theme_codes": sorted(accepted_themes),
                "accepted_direct_symbols": sorted(accepted_symbols),
                "missing_theme_codes": sorted(missing_themes),
                "missing_direct_symbols": sorted(missing_symbols),
                "blocked_symbols_accepted": sorted(blocked_symbols_accepted),
                "forbidden_theme_hits": sorted(forbidden_theme_hits),
                "forbidden_symbol_hits": sorted(forbidden_symbol_hits),
                "rejected_impact_count": validated.rejected_impact_count,
                "translation_available": case.has_korean_translation,
                "passed": (
                    not missing_themes
                    and not missing_symbols
                    and not theme_false_positives
                    and not direct_false_positives
                    and not blocked_symbols_accepted
                    and not forbidden_theme_hits
                    and not forbidden_symbol_hits
                    and (not case.expected_blocked_candidate or not accepted_themes and not accepted_symbols)
                ),
            }
        )

    theme_denominator = totals["theme_true_positive_count"] + totals["theme_false_positive_count"]
    direct_denominator = totals["direct_ticker_true_positive_count"] + totals["direct_ticker_false_positive_count"]
    metrics = {
        **totals,
        "case_count": len(dataset.cases),
        "passed_case_count": sum(1 for result in case_results if result["passed"]),
        "failed_case_count": sum(1 for result in case_results if not result["passed"]),
        "theme_precision": _ratio(totals["theme_true_positive_count"], theme_denominator),
        "direct_ticker_grounding_precision": _ratio(totals["direct_ticker_true_positive_count"], direct_denominator),
        "macro_only_false_ticker_rate": _ratio(totals["macro_only_false_ticker_count"], totals["macro_only_case_count"]),
        "blocked_candidate_correctness": _ratio(totals["blocked_correct_count"], totals["blocked_expected_count"]),
        "korean_translation_availability": _ratio(totals["translation_available_count"], len(dataset.cases)),
    }
    pass_thresholds = {
        "theme_precision_min": 1.0,
        "direct_ticker_grounding_precision_min": 1.0,
        "macro_only_false_ticker_count_max": 0,
        "quantum_energy_misclassification_count_max": 0,
        "korean_translation_availability_min": 1.0,
    }
    overall_pass = (
        metrics["theme_precision"] >= pass_thresholds["theme_precision_min"]
        and metrics["direct_ticker_grounding_precision"] >= pass_thresholds["direct_ticker_grounding_precision_min"]
        and metrics["macro_only_false_ticker_count"] <= pass_thresholds["macro_only_false_ticker_count_max"]
        and metrics["quantum_energy_misclassification_count"] <= pass_thresholds["quantum_energy_misclassification_count_max"]
        and metrics["korean_translation_availability"] >= pass_thresholds["korean_translation_availability_min"]
        and metrics["failed_case_count"] == 0
    )
    return {
        "dataset_version": dataset.dataset_version,
        "eval_name": DEFAULT_EVAL_NAME,
        "overall_pass": overall_pass,
        "metrics": metrics,
        "pass_thresholds": pass_thresholds,
        "case_results": case_results,
    }


def render_news_ai_eval_run_insert_sql(
    *,
    eval_name: str,
    dataset_version: str,
    provider: str,
    model_name: str,
    score_json: Mapping[str, object],
) -> str:
    score_text = json.dumps(score_json, ensure_ascii=False, sort_keys=True)
    return f"""insert into ai.eval_run (
    eval_name,
    dataset_version,
    provider,
    model_name,
    score_json
)
values (
    {sql_literal(eval_name)},
    {sql_literal(dataset_version)},
    {sql_literal(provider)},
    {sql_literal(model_name)},
    {sql_literal(score_text)}::jsonb
)
returning eval_run_id;"""


def run_news_ai_eval(
    *,
    config: RuntimeConfig,
    dataset_path: str | Path | None = None,
    provider: str = "fixture",
    model_name: str = "news-ai-eval-fixture-v1",
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    execute: bool = False,
    executor: PsqlCommandExecutor | None = None,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    if provider != "fixture":
        raise ValueError("news-ai-eval-run currently supports provider=fixture only.")
    dataset = load_news_ai_eval_dataset(dataset_path)
    score = score_news_ai_eval_dataset(dataset, min_confidence=min_confidence)
    report: dict[str, object] = {
        "report_name": "news_ai_eval_dataset_and_scoring",
        "generated_at": _format_timestamp(generated_at or datetime.now(timezone.utc)),
        "status": "planned" if not execute else "running",
        "execute": execute,
        "provider": provider,
        "model_name": model_name,
        "dataset_version": dataset.dataset_version,
        "score": score,
    }
    if not execute:
        return report

    sql_executor = executor or PsqlCommandExecutor.from_config(config)
    run_id = _create_pipeline_run(
        sql_executor,
        pipeline_name=DEFAULT_EVAL_NAME,
        config_json={
            "dataset_version": dataset.dataset_version,
            "provider": provider,
            "model_name": model_name,
            "min_confidence": min_confidence,
        },
    )
    report["run_id"] = run_id
    try:
        eval_run_id = int(
            sql_executor.execute_scalar(
                render_news_ai_eval_run_insert_sql(
                    eval_name=DEFAULT_EVAL_NAME,
                    dataset_version=dataset.dataset_version,
                    provider=provider,
                    model_name=model_name,
                    score_json=score,
                )
            )
        )
        _mark_pipeline_run_succeeded(sql_executor, run_id)
    except Exception as exc:
        _mark_pipeline_run_failed(sql_executor, run_id, str(exc))
        raise
    report["status"] = "completed"
    report["eval_run_id"] = eval_run_id
    return report


def _create_pipeline_run(
    executor: PsqlCommandExecutor,
    *,
    pipeline_name: str,
    config_json: Mapping[str, object],
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
    truncated = error_summary.strip()[:2000] or "news AI eval failed"
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


def _parse_case(payload: object) -> NewsAiEvalCase:
    if not isinstance(payload, dict):
        raise ValueError("News AI eval case must be an object.")
    ai_output = payload.get("ai_output")
    if not isinstance(ai_output, dict):
        raise ValueError("News AI eval case must contain ai_output object.")
    return NewsAiEvalCase(
        case_id=_required_text(payload, "case_id"),
        category=_required_text(payload, "category"),
        title=_required_text(payload, "title"),
        summary=_required_text(payload, "summary"),
        korean_title=_optional_text(payload.get("korean_title")),
        korean_summary=_optional_text(payload.get("korean_summary")),
        ai_output=ai_output,
        expected_theme_codes=_text_tuple(payload.get("expected_theme_codes")),
        allowed_theme_codes=_text_tuple(payload.get("allowed_theme_codes")),
        forbidden_theme_codes=_text_tuple(payload.get("forbidden_theme_codes")),
        expected_direct_symbols=_text_tuple(payload.get("expected_direct_symbols")),
        forbidden_direct_symbols=_text_tuple(payload.get("forbidden_direct_symbols")),
        expected_blocked_symbols=_text_tuple(payload.get("expected_blocked_symbols")),
        expected_blocked_candidate=payload.get("expected_blocked_candidate") is True,
    )


def _required_text(payload: Mapping[str, object], key: str) -> str:
    value = _optional_text(payload.get(key))
    if not value:
        raise ValueError(f"News AI eval case field `{key}` is required.")
    return value


def _optional_text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _text_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item).strip().upper() for item in value if str(item).strip())


def _as_mapping(value: object) -> dict[str, Mapping[str, object]]:
    if not isinstance(value, MappingABC):
        return {}
    result: dict[str, Mapping[str, object]] = {}
    for key, item in value.items():
        if isinstance(item, MappingABC):
            result[str(key).upper()] = {str(row_key): row_value for row_key, row_value in item.items()}
    return result


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 6)


def _lookup_sql_literal_argument(sql: str, function_name: str) -> str | None:
    pattern = rf"{re.escape(function_name)}\('((?:''|[^'])*)'\)"
    matches = re.findall(pattern, sql, flags=re.IGNORECASE)
    if not matches:
        return None
    return matches[-1].replace("''", "'").strip()


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
