"""Per-symbol research orchestration; no change to financial models or SQL schemas.

Input/analysis faults are isolated. Storage faults and cancellation are not.
Incomplete execution raises a ValueError-compatible exception after good items
finish, preserving nonzero exits in the existing CLI and parent pipeline.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from copy import deepcopy
from datetime import date
from dataclasses import replace
import json
import re
from typing import Any

from stockanalysis.ai_agents.prompt_contract import PromptContractError
from stockanalysis.ai.research_source_version import VERSION_KEY, validated_version, same_version, generation_policy
from stockanalysis.ai.equity_research_persistence import (
    POLICY as PERSISTENCE_POLICY, render_atomic_result_sql, parse_acknowledgement,
)


class EquityResearchBatchError(PromptContractError):
    """A failed/partial batch with structured, non-source-bearing diagnostics.

    Existing CLI prints this JSON to stderr and exits 1. Python callers can
    inspect report; do not automatically retry an ambiguous persistence failure.
    Preview/source text is deliberately excluded from the exception message.
    """

    def __init__(self, report: dict[str, Any]) -> None:
        self.report = deepcopy(report)
        diagnostic = {key: value for key, value in self.report.items() if key not in (
            "artifact_preview", "model_name", "provider",
        )}
        diagnostic["results"] = [{key: value for key, value in row.items() if key != "provider"}
                                 for row in diagnostic["results"]]
        for row in diagnostic["results"]:
            if "result_receipt" in row:
                row["result_receipt"] = {key: value for key, value in row["result_receipt"].items()
                                         if key not in ("provider", "model_name")}
        super().__init__(json.dumps(diagnostic, ensure_ascii=False, allow_nan=False))


def _context_identity(context: dict[str, Any], symbol: str, as_of: date) -> None:
    instrument, query = context.get("instrument"), context.get("query")
    if not isinstance(instrument, dict) or type(instrument.get("instrument_id")) is not int or instrument["instrument_id"] <= 0:
        raise PromptContractError("context_instrument_invalid")
    if not isinstance(query, dict) or query.get("symbol") != symbol or instrument.get("primary_symbol") != symbol:
        raise PromptContractError("context_symbol_mismatch")
    if query.get("as_of_date") != as_of.isoformat():
        raise PromptContractError("context_date_mismatch")


def _input_code(exc: PromptContractError) -> str:
    code = str(exc)
    return code if code in {
        "input_budget_exceeded", "context_instrument_invalid", "context_instrument_missing",
        "context_symbol_mismatch", "context_date_mismatch", "invalid_output_json",
        "output_not_object", "duplicate_json_key", "nonfinite_json_number",
        "non_json_or_nonfinite_value", "json_nesting_limit", "output_size_limit",
    } else "context_invalid"


def _counts(report: dict[str, Any]) -> None:
    results = report["results"]
    primary = sum(row["status"] == "reported" for row in results)
    fallback = sum(row["status"] == "reported_with_fallback" for row in results)
    report.update(
        primary_report_count=primary,
        fallback_artifact_count=fallback,
        inserted_artifact_count=primary + fallback,
        unreported_artifact_count=len(results) - primary - fallback,
        # Legacy name included failed model reports with a saved fallback.
        failed_artifact_count=sum(row["status"] in {"failed", "reported_with_fallback"} for row in results),
    )


def run_batch(
    *, config: Any, as_of_date: date, symbols: Iterable[str], limit: int,
    provider: str, model_name: str, reasoning_effort: str | None,
    max_context_chars: int, execute: bool, executor: Any,
    provider_runner: Callable[..., Any] | None,
    source_refresh_claim: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Import only on invocation, keeping the public reporting module compatible.
    from stockanalysis.ai import equity_research_reporting as equity

    if type(as_of_date) is not date:
        raise ValueError("as_of_date must be a date without a time component.")
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50.")
    if type(max_context_chars) is not int or not 2000 <= max_context_chars <= 100000:
        raise ValueError("max_context_chars must be between 2000 and 100000.")
    if provider not in {equity.FIXTURE_PROVIDER, equity.CODEX_OAUTH_PROVIDER}:
        raise ValueError("Supported equity research providers are fixture and codex_oauth.")
    if source_refresh_claim is not None:
        if (type(source_refresh_claim.get('claim_id')) is not int
            or source_refresh_claim['claim_id'] <= 0 or limit != 1 or not execute):
            raise ValueError('invalid_source_refresh_claim')
        validated_version(source_refresh_claim.get('source_version'))
    sql_executor = executor or equity.PsqlCommandExecutor.from_config(config)
    report: dict[str, Any] = {
        "report_name": equity.DEFAULT_PIPELINE_NAME, "pipeline_name": equity.DEFAULT_PIPELINE_NAME,
        "artifact_type": equity.ARTIFACT_TYPE, "status": "planned" if not execute else "running",
        "execute": execute, "as_of_date": as_of_date.isoformat(), "provider": provider,
        "model_name": model_name, "symbol_count": 0, "symbol_preview": [],
        "prepared_symbol_count": 0, "input_error_count": 0, "provider_failure_count": 0,
        "preview_error_count": 0, "artifact_preview": [], "preview_symbols": [],
        "results": [], "run_id": None, "batch_policy": "per_symbol_failure_isolation_v1",
        "recommendation_scoring_mutated": False, "broker_order_submit_enabled": False,
        "persistence_policy": PERSISTENCE_POLICY,
    }
    run_id: int | None = None
    stage, current = "symbol_lookup", None
    try:
        selected = equity._load_equity_research_symbols(
            sql_executor, as_of_date=as_of_date, symbols=symbols, limit=limit,
        )
        if any(not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,19}", symbol) for symbol in selected):
            raise PromptContractError("invalid_symbol_selection")
        # One item per selected ticker; preserve the backend's original ordering.
        selected = list(dict.fromkeys(selected))
        report.update(symbol_count=len(selected), symbol_preview=selected[:10],
                      results=[{"symbol": symbol, "status": "not_attempted", "provider_attempted": False} for symbol in selected])
        contexts: dict[int, dict[str, Any]] = {}
        for index, symbol in enumerate(selected):
            current, stage = index, "context_lookup"
            try:
                context = equity.load_equity_research_context(
                    config=config, symbol=symbol, as_of_date=as_of_date, limit=8, executor=sql_executor,
                )
                _context_identity(context, symbol, as_of_date)
                if source_refresh_claim is not None and not same_version(
                    context.get('financial_source_version'), source_refresh_claim['source_version']
                ):
                    raise PromptContractError('financial_source_changed_before_generation')
                contexts[index] = equity._bounded_context_for_prompt(context, max_context_chars=max_context_chars)
                report["results"][index]["status"] = "prepared"
                report["prepared_symbol_count"] += 1
            except PromptContractError as exc:
                report["input_error_count"] += 1
                report["results"][index].update(status="failed", stage="context", error_code=_input_code(exc), provider_attempted=False)

        if not execute:
            # Preview is not a prerequisite for real generation. In dry-run only,
            # isolate a broken deterministic preview and continue the other ones.
            for index, context in list(contexts.items())[:3]:
                current, stage = index, "preview"
                try:
                    preview = equity.build_fixture_equity_research_response(
                        deepcopy(context), model_name, reasoning_effort, max_context_chars,
                    )
                    output = equity._sanitize_output(preview.output, context=context)
                    report["artifact_preview"].append(equity._output_to_json(output))
                    report["preview_symbols"].append(selected[index])
                except (MemoryError, RecursionError):
                    raise
                except Exception:
                    report["preview_error_count"] += 1
                    report["results"][index].update(status="preview_failed", stage="preview", error_code="preview_failed")
            if report["input_error_count"] or report["preview_error_count"]:
                report["status"] = "planned_with_failures"
                raise EquityResearchBatchError(report)
            return report

        if not contexts:
            _counts(report)
            report["status"] = "failed" if selected else "completed"
            if selected:
                raise EquityResearchBatchError(report)
            return report

        current, stage = None, "pipeline_start"
        run_id = equity._create_pipeline_run(sql_executor, pipeline_name=equity.DEFAULT_PIPELINE_NAME, config_json={
            "as_of_date": as_of_date.isoformat(), "artifact_type": equity.ARTIFACT_TYPE,
            "provider": provider, "model_name": model_name, "reasoning_effort": reasoning_effort,
            "limit": limit, "symbols": selected, "max_context_chars": max_context_chars,
            "offline_batch_only": True, "recommendation_scoring_mutated": False,
            "broker_order_submit_enabled": False, "batch_policy": report["batch_policy"],
            "input_failures": [row for row in report["results"] if row["status"] == "failed"],
            VERSION_KEY: {selected[index]: validated_version(context.get('financial_source_version'))
                          for index, context in contexts.items()},
            'source_generation_policy': generation_policy(model=model_name, template=equity.DEFAULT_TEMPLATE_VERSION,
                reasoning=reasoning_effort, context_limit=max_context_chars),
            **({'source_refresh_claim_id': source_refresh_claim['claim_id']} if source_refresh_claim is not None else {}),
        })
        report["run_id"] = run_id
        stage = "prompt_registration"
        prompt_id = int(sql_executor.execute_scalar(equity.render_equity_research_prompt_template_upsert_sql()))

        def isolated_runner(context: dict[str, Any], *args: Any) -> Any:
            # A provider hook must not mutate the snapshot used for hashing,
            # fallback, output normalization, or the persisted source inventory.
            assert provider_runner is not None
            return provider_runner(deepcopy(context), *args)

        for index, context in contexts.items():
            current, stage = index, "request_hash"
            row = report["results"][index]
            row.update(status="processing")
            request_hash = equity.build_equity_research_request_hash(
                context=context, provider=provider, model_name=model_name,
                prompt_template_id=prompt_id, max_context_chars=max_context_chars,
            )
            row["request_hash"] = request_hash
            fallback = False
            try:
                stage = "provider"
                row["provider_attempted"] = True
                response = equity._invoke_provider(context, provider=provider, model_name=model_name,
                    reasoning_effort=reasoning_effort, max_context_chars=max_context_chars,
                    provider_runner=isolated_runner if provider_runner is not None else None)
            except (MemoryError, RecursionError):
                raise
            except Exception as exc:
                report["provider_failure_count"] += 1
                code = "provider_contract_invalid" if isinstance(exc, PromptContractError) else "provider_failed"
                row.update(stage="provider", error_code=code)
                # Do not swallow an audit-write failure or call it a model error.
                stage = "failure_record"
                failed_id = int(sql_executor.execute_scalar(equity.render_equity_research_model_invocation_insert_sql(
                    run_id=run_id, provider=provider, model_name=model_name, reasoning_effort=reasoning_effort,
                    prompt_template_id=prompt_id, input_token_count=None, output_token_count=None,
                    cached_input_token_count=None, estimated_cost_usd=None, latency_ms=None,
                    status="failed", error_summary=code, request_hash=request_hash,
                )))
                row["failed_invocation_id"] = failed_id
                stage = "fallback"
                try:
                    response = equity.build_fixture_equity_research_response(
                        deepcopy(context), "equity-research-fallback-v1", None, max_context_chars,
                    )
                    response = replace(response, output=equity._sanitize_output(response.output, context=context))
                    fallback = True
                except (MemoryError, RecursionError):
                    raise
                except Exception:
                    row.update(status="failed", stage="fallback", error_code="fallback_failed", provider_error_code=code)
                    continue

            # Serialize before IO; commit result/log/receipt as one SQL statement.
            # Keep the original failed model audit independent on fallback paths.
            stage = "result_serialization"
            result_sql = render_atomic_result_sql(
                context=context, response=response, as_of_date=as_of_date,
                run_id=run_id, prompt_template_id=prompt_id, request_hash=request_hash,
                failed_invocation_id=row["failed_invocation_id"] if fallback else None,
            )
            stage = "result_write"
            raw_receipt = sql_executor.execute_scalar(result_sql)
            stage = "result_acknowledgement"
            receipt = parse_acknowledgement(raw_receipt, run_id=run_id, request_hash=request_hash)
            if (receipt["instrument_id"] != context["instrument"]["instrument_id"]
                or receipt["as_of_date"] != as_of_date.isoformat()
                or receipt["provider"] != response.provider or receipt["model_name"] != response.model_name
                or receipt["outcome"] != ("fallback" if fallback else "primary")
                or receipt["failed_invocation_id"] != (row["failed_invocation_id"] if fallback else None)):
                raise PromptContractError("result_receipt_mismatch")
            row.update(status="reported_with_fallback" if fallback else "reported", stage="complete",
                       invocation_id=receipt["invocation_id"], artifact_id=receipt["artifact_id"],
                       provider=response.provider, result_receipt=receipt)

        current, stage = None, "pipeline_finish"
        _counts(report)
        if report["unreported_artifact_count"]:
            report["status"] = "completed_with_failures" if report["inserted_artifact_count"] else "failed"
            summary = f"equity_batch_incomplete: {report['unreported_artifact_count']}/{len(selected)} reports not written"
            equity._mark_pipeline_run_failed(sql_executor, run_id, summary)
            raise EquityResearchBatchError(report)
        if report["fallback_artifact_count"]:
            equity._mark_pipeline_run_succeeded_with_fallback(sql_executor, run_id, failed_report_count=report["fallback_artifact_count"])
            report["status"] = "completed_with_fallback"
        else:
            equity._mark_pipeline_run_succeeded(sql_executor, run_id)
            report["status"] = "completed"
        return report
    except EquityResearchBatchError:
        raise
    except Exception:
        if current is not None and report["results"][current]["status"] in {"processing", "prepared", "not_attempted"}:
            report["results"][current].update(status="failed", stage=stage, error_code="batch_stage_failed")
        for row in report["results"]:
            if row["status"] == "prepared":
                row["status"] = "not_attempted"
        report.update(status="failed", fatal_error={"stage": stage, "error_code": "batch_stage_failed",
            "persistence_outcome_unknown": stage in {"pipeline_start", "prompt_registration", "failure_record", "result_write", "result_acknowledgement", "pipeline_finish"}})
        if execute:
            _counts(report)
        if run_id is not None:
            equity._mark_pipeline_run_failed(sql_executor, run_id, f"equity_batch_fatal:{stage}")
        raise EquityResearchBatchError(report) from None
    except BaseException:
        # Cancellation/control exceptions are not item failures or fallback causes.
        if run_id is not None:
            equity._mark_pipeline_run_failed(sql_executor, run_id, "equity_batch_interrupted")
        raise
