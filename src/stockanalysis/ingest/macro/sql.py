from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from decimal import Decimal

from stockanalysis.ingest.macro.models import MacroObservationRecord, MacroSyncResult


def render_macro_sync_sql(
    result: MacroSyncResult,
    *,
    chunk_size: int = 500,
    source_run_id: int | None = None,
) -> str:
    lines = [
        "begin;",
        "",
        _render_series_upsert(result),
    ]
    for chunk in _chunk(result.observations, chunk_size):
        lines.extend(
            [
                "",
                _render_observation_upsert(
                    result.series.series_code,
                    chunk,
                    source_run_id=source_run_id,
                ),
            ]
        )
    lines.extend(["", "commit;"])
    return "\n".join(lines) + "\n"


def _render_series_upsert(result: MacroSyncResult) -> str:
    series = result.series
    return f"""insert into macro.series (
    series_code,
    name,
    category,
    frequency,
    unit,
    region_code,
    data_source_id,
    is_active
)
values (
    {sql_literal(series.series_code)},
    {sql_literal(series.name)},
    {sql_literal(series.category)},
    {sql_literal(series.frequency)},
    {sql_literal(series.unit)},
    {sql_literal(series.region_code)},
    (select data_source_id from ingest.data_source where source_name = {sql_literal(series.source_name)}),
    {sql_literal(series.is_active)}
)
on conflict (series_code) do update
set
    name = excluded.name,
    category = excluded.category,
    frequency = excluded.frequency,
    unit = excluded.unit,
    region_code = excluded.region_code,
    data_source_id = excluded.data_source_id,
    is_active = excluded.is_active;"""


def _render_observation_upsert(
    series_code: str,
    records: list[MacroObservationRecord],
    *,
    source_run_id: int | None,
) -> str:
    value_rows = ",\n        ".join(
        _render_observation_value_tuple(record) for record in records
    )
    source_run_literal = "null::bigint" if source_run_id is None else f"{source_run_id}::bigint"
    return f"""with input_rows(observation_date, value, revision_number) as (
    values
        {value_rows}
)
insert into macro.observation (
    series_id,
    observation_date,
    value,
    released_at,
    revision_number,
    source_run_id
)
select
    s.series_id,
    i.observation_date,
    i.value,
    null::timestamptz,
    i.revision_number,
    {source_run_literal}
from macro.series s
join input_rows i on true
where s.series_code = {sql_literal(series_code)}
on conflict (series_id, observation_date, revision_number) do update
set
    value = excluded.value,
    released_at = excluded.released_at,
    source_run_id = excluded.source_run_id;"""


def _render_observation_value_tuple(record: MacroObservationRecord) -> str:
    return (
        f"({sql_date(record.observation_date)}, "
        f"{sql_numeric(record.value)}, "
        f"{record.revision_number})"
    )


def sql_literal(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, Decimal)):
        return str(value)
    if isinstance(value, float):
        return format(value, "f")
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def sql_date(value: date) -> str:
    return f"{sql_literal(value.isoformat())}::date"


def sql_numeric(value: Decimal) -> str:
    return f"{value}::numeric"


def _chunk(records: tuple[MacroObservationRecord, ...], size: int) -> Iterable[list[MacroObservationRecord]]:
    for index in range(0, len(records), size):
        yield list(records[index : index + size])
