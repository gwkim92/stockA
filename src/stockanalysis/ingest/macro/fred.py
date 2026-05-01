from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.http import execute_request
from stockanalysis.ingest.macro.models import (
    MacroObservationRecord,
    MacroSeriesRecord,
    MacroSeriesSpec,
    MacroSyncResult,
)
from stockanalysis.ingest.registry import get_source


def load_macro_sync_result(
    spec: MacroSeriesSpec,
    *,
    config: RuntimeConfig,
    series_json_path: str | None = None,
    observations_json_path: str | None = None,
    observation_start: str | None = None,
    observation_end: str | None = None,
) -> MacroSyncResult:
    series_payload = _load_series_payload(
        spec.series_id,
        config=config,
        json_path=series_json_path,
    )
    observations_payload = _load_observations_payload(
        spec.series_id,
        config=config,
        json_path=observations_json_path,
        observation_start=observation_start,
        observation_end=observation_end,
    )
    series = normalize_series_payload(spec, series_payload)
    observations, skipped_count = normalize_observations_payload(spec, observations_payload)
    return MacroSyncResult(
        series=series,
        observations=tuple(observations),
        skipped_count=skipped_count,
    )


def normalize_series_payload(spec: MacroSeriesSpec, payload: dict[str, Any]) -> MacroSeriesRecord:
    entries = payload.get("seriess")
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"FRED series payload for `{spec.series_id}` does not contain `seriess` entries")
    entry = entries[0]
    return MacroSeriesRecord(
        series_code=str(entry["id"]),
        name=str(entry["title"]),
        category=spec.category,
        frequency=str(entry.get("frequency_short") or entry.get("frequency") or "unknown"),
        unit=str(entry.get("units_short") or entry.get("units") or "unknown"),
        region_code=spec.region_code,
    )


def normalize_observations_payload(
    spec: MacroSeriesSpec,
    payload: dict[str, Any],
) -> tuple[list[MacroObservationRecord], int]:
    items = payload.get("observations")
    if not isinstance(items, list):
        raise ValueError(
            f"FRED observations payload for `{spec.series_id}` does not contain `observations` entries"
        )

    records: list[MacroObservationRecord] = []
    skipped_count = 0
    for item in items:
        raw_value = str(item.get("value", "")).strip()
        if raw_value in {"", "."}:
            skipped_count += 1
            continue
        try:
            value = Decimal(raw_value)
        except InvalidOperation as exc:
            raise ValueError(
                f"Invalid numeric value `{raw_value}` in observations for `{spec.series_id}`"
            ) from exc
        records.append(
            MacroObservationRecord(
                series_code=spec.series_id,
                observation_date=date.fromisoformat(str(item["date"])),
                value=value,
                revision_number=0,
            )
        )
    records.sort(key=lambda record: record.observation_date)
    return records, skipped_count


def _load_series_payload(
    series_id: str,
    *,
    config: RuntimeConfig,
    json_path: str | None,
) -> dict[str, Any]:
    if json_path:
        return _load_json_file(json_path)
    fred = get_source("fred")
    request = fred.build_request(
        "series",
        {"series_id": series_id},
        config=config,
        require_credentials=True,
    )
    return execute_request(request).as_json()


def _load_observations_payload(
    series_id: str,
    *,
    config: RuntimeConfig,
    json_path: str | None,
    observation_start: str | None,
    observation_end: str | None,
) -> dict[str, Any]:
    if json_path:
        return _load_json_file(json_path)
    params: dict[str, str] = {"series_id": series_id}
    if observation_start:
        params["observation_start"] = observation_start
    if observation_end:
        params["observation_end"] = observation_end
    fred = get_source("fred")
    request = fred.build_request(
        "series_observations",
        params,
        config=config,
        require_credentials=True,
    )
    return execute_request(request).as_json()


def _load_json_file(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
