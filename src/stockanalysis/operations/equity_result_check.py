"""Read-only operator check of a previously attempted equity report.

Use run_id/request_hash from the batch result. Never generates, retries, repairs
or marks a pipeline successful. A current database match is not model quality.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import json
import re
import subprocess
import sys
from typing import Any, Protocol, Sequence, TextIO

from stockanalysis.ai.equity_research_persistence import reconcile_result, render_reconciliation_sql
from stockanalysis.ai_agents.prompt_contract import PromptContractError
from stockanalysis.ingest.config import ConfigError, RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError

PROCESS_TIMEOUT_SECONDS = 15
EXIT_CODES = {"matching": 0, "unavailable": 1, "conflicting": 3, "not_observed": 4}
MESSAGES = {
    "matching": ("저장 기록 일치", "재생성하지 말고 확인된 실행·보고서 ID로 기존 결과를 확인하세요."),
    "conflicting": ("저장 기록 불일치", "덮어쓰기·변경된 기록과 실행 이력을 대조하세요. 자동 재시도하지 않습니다."),
    "not_observed": ("저장 확인 정보 미관측", "저장 실패가 확정된 것은 아닙니다. 진행 중 작업과 기존 기록부터 확인하세요."),
    "unavailable": ("저장 결과 확인 불가", "오류 코드를 확인하세요. 조회 실패를 미저장이나 재실행 허가로 해석하지 마세요."),
}
SAFE_RECEIPT_FIELDS = (
    "policy", "outcome", "artifact_id", "invocation_id", "failed_invocation_id",
    "instrument_id", "as_of_date", "result_fingerprint", "invocation_fingerprint",
)


class ScalarReader(Protocol):
    def execute_scalar(self, sql: str) -> str: ...


class _BoundedPsqlReader(PsqlCommandExecutor):
    """Reuse the existing configured psql command, adding a process deadline.

    The configuration is an existing trusted operator command, not user/source
    text. subprocess.run terminates its direct child on timeout; this is not a
    guarantee that arbitrary configured wrapper descendants are terminated.
    """

    def _run(self, sql: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [*self._base_command, "-v", "ON_ERROR_STOP=1", "-X", "-q", "-t", "-A", "-w"],
            input=sql, text=True, capture_output=True, check=False,
            timeout=PROCESS_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            raise PsqlExecutionError("result_check_database_error")
        return result


class _ReadOnlySnapshot:
    """Wrap the fixed reconciliation SELECT, with transaction-local safeguards."""

    def __init__(self, reader: ScalarReader) -> None:
        self.reader = reader

    def execute_scalar(self, sql: str) -> str:
        return self.reader.execute_scalar(
            "BEGIN READ ONLY;\n"
            "SET LOCAL statement_timeout = '5s';\n"
            "SET LOCAL lock_timeout = '1s';\n"
            "SET LOCAL idle_in_transaction_session_timeout = '8s';\n"
            "SET LOCAL search_path = pg_catalog;\n"
            "SET LOCAL TIME ZONE 'UTC';\n"
            "SET LOCAL DateStyle = 'ISO, YMD';\n"
            + sql + "\nROLLBACK;\n"
        )


def check_result(*, run_id: int, request_hash: str, reader: ScalarReader | None = None,
                 config: RuntimeConfig | None = None) -> dict[str, Any]:
    # Validate before configuration or any IO. Bad input is a caller error, not
    # an unavailable database or absent receipt. No raw input is echoed.
    render_reconciliation_sql(run_id=run_id, request_hash=request_hash)
    receipt = None
    error_code = None
    try:
        database = reader if reader is not None else _BoundedPsqlReader.from_config(
            config if config is not None else RuntimeConfig.from_env()
        )
        result = reconcile_result(_ReadOnlySnapshot(database), run_id=run_id, request_hash=request_hash)
        status = result["status"]
        if result["receipt"] is not None:
            receipt = {key: result["receipt"][key] for key in SAFE_RECEIPT_FIELDS}
    except ConfigError:
        status, error_code = "unavailable", "configuration_unavailable"
    except subprocess.TimeoutExpired:
        status, error_code = "unavailable", "check_timeout"
    except (OSError, PsqlExecutionError):
        status, error_code = "unavailable", "database_unavailable"
    except PromptContractError:
        status, error_code = "unavailable", "invalid_stored_result"
    message, next_step = MESSAGES[status]
    return {
        "report_name": "equity_result_check_v1", "status": status,
        "run_id": run_id, "request_hash": request_hash,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "message_ko": message, "next_step_ko": next_step,
        "receipt": receipt, "error_code": error_code,
        "read_only": True, "automatic_retry_allowed": False,
        "model_invoked": False, "pipeline_status_changed": False,
        "observation_scope": "current_database_snapshot_not_analysis_quality_or_retry_authorization",
    }


def render_text(report: dict[str, Any]) -> str:
    # Only render known structured fields, never raw SQL/provider exception text.
    lines = [f"기업 리서치 저장 확인: {report['message_ko']} ({report['status']})",
             f"실행 ID: {report['run_id']}", f"요청 해시: {report['request_hash']}"]
    receipt = report["receipt"]
    if receipt is not None:
        outcome = "정상 제공자 경로" if receipt["outcome"] == "primary" else "규칙 기반 대체 경로"
        lines.extend((f"보고서 ID: {receipt['artifact_id']} · 기업 ID: {receipt['instrument_id']}",
                      f"보고서 기준일: {receipt['as_of_date']} · {outcome}"))
        key = "invocation_id" if receipt["outcome"] == "primary" else "failed_invocation_id"
        lines.append(f"연결 호출 ID: {receipt[key]}")
    if report["error_code"] is not None:
        lines.append(f"오류 코드: {report['error_code']}")
    lines.extend((f"확인 시각(UTC): {report['checked_at_utc']}", report["next_step_ko"],
                  "읽기 전용 · 모델 호출 없음 · 상태 변경 없음 · 자동 재시도 없음",
                  "이 결과는 조회 시점의 저장 대조이며 분석 정확도·수익성을 증명하지 않습니다."))
    return "\n".join(lines) + "\n"


class _UsageError(ValueError):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        # argparse's default can echo arbitrary supplied values/unknown flags.
        raise _UsageError("invalid_arguments")


class _Once(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        marker = f"_provided_{self.dest}"
        if getattr(namespace, marker, False):
            raise argparse.ArgumentError(self, "duplicate_argument")
        setattr(namespace, marker, True)
        setattr(namespace, self.dest, values)


def _run_id(value: str) -> int:
    if not re.fullmatch(r"[1-9][0-9]{0,18}", value) or int(value) > 9223372036854775807:
        raise argparse.ArgumentTypeError("invalid_run_id")
    return int(value)


def _request_hash(value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise argparse.ArgumentTypeError("invalid_request_hash")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="stockanalysis-equity-result-check", allow_abbrev=False,
                     description="기존 실행 ID·요청 해시로 기업 리서치 저장 결과만 대조합니다. 재시도·수정하지 않습니다.")
    parser.add_argument("--run-id", required=True, type=_run_id, action=_Once)
    parser.add_argument("--request-hash", required=True, type=_request_hash, action=_Once)
    parser.add_argument("--format", choices=("text", "json"), default="text", action=_Once)
    return parser


def main(argv: Sequence[str] | None = None, *, stdout: TextIO | None = None,
         stderr: TextIO | None = None, reader: ScalarReader | None = None) -> int:
    out, err = stdout or sys.stdout, stderr or sys.stderr
    parser = build_parser()
    try:
        with redirect_stdout(out):
            args = parser.parse_args(argv)
    except _UsageError:
        parser.print_usage(file=err)
        err.write("입력 오류: 양의 실행 ID, 64자리 소문자 요청 해시와 text/json 형식을 확인하세요.\n")
        return 2
    except SystemExit as exc:
        # Help is an intentional exit before any runtime lookup.
        if exc.code == 0:
            return 0
        raise
    report = check_result(run_id=args.run_id, request_hash=args.request_hash, reader=reader)
    out.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_text(report))
    return EXIT_CODES[report["status"]]


def main_entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    main_entry()
