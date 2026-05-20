#!/usr/bin/env python3
"""Validate the secret-free frontend API alert rule reference."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


EXPECTED_ALERTS = [
    "FrontendApiDown",
    "FrontendApiNotReady",
    "FrontendApiHigh5xxRate",
    "FrontendApiTimeoutSpike",
    "FrontendApiHighLatency",
    "FrontendApiAdapterErrorSpike",
]

EXPECTED_METRICS = [
    "frontend_api_requests_total",
    "frontend_api_request_duration_seconds_bucket",
    "frontend_api_request_timeouts_total",
    "frontend_api_adapter_errors_total",
    "frontend_api_ready",
    "frontend_api_db_pool_ready",
]

ALLOWED_SELECTOR_LABELS = {
    "job",
    "route_template",
    "method",
    "status_class",
    "profile",
    "source_mode",
    "error_code",
    "le",
}

FORBIDDEN_TOKENS = [
    "receiver:",
    "slack",
    "pagerduty",
    "opsgenie",
    "webhook_configs",
    "email_configs",
    "authorization",
    "bearer",
    "password",
    "secret",
    "database_url",
    "db_url",
    "raw_sql",
    "raw_query",
    "query_string",
    "request_id",
    "ticker",
    "symbol",
    "portfolio_name",
    "document_id",
    "thesis_id",
    "recommendation_id",
]


def _alert_blocks(lines: list[str]) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in lines:
        match = re.match(r"^\s*-\s*alert:\s*([A-Za-z0-9_]+)\s*$", line)
        if match:
            if current_name is not None:
                blocks[current_name] = current_lines
            current_name = match.group(1)
            current_lines = [line]
            continue
        if current_name is not None:
            current_lines.append(line)

    if current_name is not None:
        blocks[current_name] = current_lines

    return blocks


def _selector_label_names(text: str) -> set[str]:
    labels: set[str] = set()
    for selector in re.findall(r"\{([^{}]+)\}", text):
        for part in selector.split(","):
            match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|!=|=~|!~)", part)
            if match:
                labels.add(match.group(1))
    return labels


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not text.startswith("groups:\n"):
        errors.append("alert rule file must start with groups:")

    if "\t" in text:
        errors.append("tabs are not allowed in alert rule YAML")

    lower_text = text.lower()
    for token in FORBIDDEN_TOKENS:
        if token in lower_text:
            errors.append(f"forbidden token found: {token}")

    blocks = _alert_blocks(lines)
    alert_names = list(blocks)
    if alert_names != EXPECTED_ALERTS:
        errors.append(f"expected alert order {EXPECTED_ALERTS}, got {alert_names}")

    for metric in EXPECTED_METRICS:
        if metric not in text:
            errors.append(f"missing expected metric: {metric}")

    for label in sorted(_selector_label_names(text) - ALLOWED_SELECTOR_LABELS):
        errors.append(f"forbidden PromQL selector label: {label}")

    for alert_name, block_lines in blocks.items():
        block_text = "\n".join(block_lines)
        if "expr: |" not in block_text:
            errors.append(f"{alert_name} must use a multiline expr block")
        if re.search(r"^\s*for:\s*(5m|10m)\s*$", block_text, flags=re.MULTILINE) is None:
            errors.append(f"{alert_name} must have a 5m or 10m duration")
        if "severity:" not in block_text:
            errors.append(f"{alert_name} must set severity")
        if "service: stockanalysis-frontend-api" not in block_text:
            errors.append(f"{alert_name} must set the static service label")
        if "runbook_url:" not in block_text:
            errors.append(f"{alert_name} must include a runbook URL")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    errors = validate(args.path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"validated {args.path} with {len(EXPECTED_ALERTS)} alert rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
