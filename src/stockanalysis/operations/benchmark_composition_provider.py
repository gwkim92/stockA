from __future__ import annotations

import csv
import re
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.benchmark_composition_import import (
    BenchmarkCompositionRow,
    DEFAULT_MIN_FULL_COVERAGE_WEIGHT,
    run_benchmark_composition_import_rows,
)


DEFAULT_SSGA_SPDR_SPY_HOLDINGS_URL = (
    "https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx"
)
DEFAULT_SSGA_PROVIDER_NAME = "State Street SPDR daily holdings"
DEFAULT_SSGA_SOURCE_NAME = "ssga_spdr_spy_daily_holdings"
DEFAULT_PIPELINE_NAME = "benchmark_composition_ssga_spdr_import"
_XLSX_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_LISTED_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9.-]*$")


@dataclass(frozen=True)
class NormalizedProviderHoldings:
    benchmark_code: str
    provider_name: str
    source_as_of_date: datetime.date
    rows: tuple[BenchmarkCompositionRow, ...]
    skipped_rows: tuple[dict[str, object], ...]

    @property
    def target_weight_total(self) -> Decimal:
        return sum((row.target_weight for row in self.rows), Decimal("0"))


def download_ssga_spdr_holdings_xlsx(*, url: str = DEFAULT_SSGA_SPDR_SPY_HOLDINGS_URL) -> bytes:
    request = Request(url, headers={"User-Agent": "stockanalysis-benchmark-holdings/0.1"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def load_ssga_spdr_holdings_xlsx(
    path: str | Path,
    *,
    benchmark_code: str,
    provider_name: str = DEFAULT_SSGA_PROVIDER_NAME,
) -> NormalizedProviderHoldings:
    rows = _xlsx_rows(Path(path))
    source_as_of_date = _parse_source_as_of_date(rows)
    header_index, header = _find_holdings_header(rows)
    required = {"name", "ticker", "weight"}
    if not required.issubset(header):
        missing = ", ".join(sorted(required - set(header)))
        raise ValueError(f"SSGA holdings XLSX missing required columns: {missing}")

    holdings: list[BenchmarkCompositionRow] = []
    skipped: list[dict[str, object]] = []
    seen_symbols: set[str] = set()
    for row_number, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        raw_symbol = str(row.get(header["ticker"]) or "").strip().upper()
        raw_name = str(row.get(header["name"]) or "").strip()
        raw_weight = row.get(header["weight"])
        if not raw_symbol and not raw_name:
            continue
        symbol = _canonical_provider_symbol(raw_symbol)
        weight = _parse_provider_weight(raw_weight)
        if not symbol or weight is None:
            skipped.append({"row_number": row_number, "symbol": raw_symbol, "name": raw_name, "reason": "not_listed_equity"})
            continue
        if symbol in seen_symbols:
            skipped.append({"row_number": row_number, "symbol": symbol, "name": raw_name, "reason": "duplicate_symbol"})
            continue
        seen_symbols.add(symbol)
        holdings.append(
            BenchmarkCompositionRow(
                symbol=symbol,
                target_weight=weight / Decimal("100"),
                name=raw_name or symbol,
                rationale=f"{provider_name} constituent weight.",
            )
        )

    if not holdings:
        raise ValueError("SSGA holdings XLSX did not contain any importable holdings.")
    return NormalizedProviderHoldings(
        benchmark_code=benchmark_code.strip().upper(),
        provider_name=provider_name,
        source_as_of_date=source_as_of_date,
        rows=tuple(holdings),
        skipped_rows=tuple(skipped),
    )


def write_normalized_holdings_csv(holdings: NormalizedProviderHoldings, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("symbol", "target_weight", "name", "rationale"))
        writer.writeheader()
        for row in holdings.rows:
            writer.writerow(
                {
                    "symbol": row.symbol,
                    "target_weight": format(row.target_weight, "f"),
                    "name": row.name or row.symbol,
                    "rationale": row.rationale or "",
                }
            )


def run_ssga_spdr_benchmark_composition_import(
    *,
    config: RuntimeConfig,
    benchmark_code: str,
    source_xlsx: str | Path | None,
    raw_xlsx_output: str | Path | None,
    normalized_csv_output: str | Path | None,
    download_url: str = DEFAULT_SSGA_SPDR_SPY_HOLDINGS_URL,
    source_name: str = DEFAULT_SSGA_SOURCE_NAME,
    execute: bool = False,
    create_missing_instruments: bool = False,
    min_full_coverage_weight: Decimal = DEFAULT_MIN_FULL_COVERAGE_WEIGHT,
    executor: PsqlCommandExecutor | None = None,
) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        xlsx_path = Path(source_xlsx).expanduser().resolve() if source_xlsx else Path(tmpdir) / "holdings.xlsx"
        if source_xlsx is None:
            content = download_ssga_spdr_holdings_xlsx(url=download_url)
            xlsx_path.write_bytes(content)
            if execute and raw_xlsx_output is not None:
                raw_path = Path(raw_xlsx_output)
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_bytes(content)

        holdings = load_ssga_spdr_holdings_xlsx(
            xlsx_path,
            benchmark_code=benchmark_code,
            provider_name=DEFAULT_SSGA_PROVIDER_NAME,
        )
        if execute and normalized_csv_output is not None:
            write_normalized_holdings_csv(holdings, normalized_csv_output)

        import_report = run_benchmark_composition_import_rows(
            config=config,
            benchmark_code=holdings.benchmark_code,
            source_type="provider_file",
            source_name=source_name,
            source_as_of_date=holdings.source_as_of_date,
            valid_from=holdings.source_as_of_date,
            rows=holdings.rows,
            execute=execute,
            min_full_coverage_weight=min_full_coverage_weight,
            create_missing_instruments=create_missing_instruments,
            executor=executor,
        )

    return {
        "report_name": DEFAULT_PIPELINE_NAME,
        "status": "completed" if execute else "planned",
        "execute": execute,
        "benchmark_code": holdings.benchmark_code,
        "provider_name": holdings.provider_name,
        "source_name": source_name,
        "source_type": "provider_file",
        "download_url": download_url,
        "source_as_of_date": holdings.source_as_of_date.isoformat(),
        "component_count": len(holdings.rows),
        "skipped_row_count": len(holdings.skipped_rows),
        "target_weight_total": format(holdings.target_weight_total, "f"),
        "coverage_status": import_report["coverage_status"],
        "full_benchmark_drift_interpretation_allowed": import_report["full_benchmark_drift_interpretation_allowed"],
        "raw_xlsx_output": str(raw_xlsx_output or source_xlsx or ""),
        "normalized_csv_output": str(normalized_csv_output or ""),
        "create_missing_instruments": create_missing_instruments,
        "recommendation_scoring_mutated": False,
        "automatic_order_allowed": False,
        "broker_submit_allowed": False,
        "skipped_rows": list(holdings.skipped_rows[:20]),
        "import_report": import_report,
    }


def _xlsx_rows(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as workbook:
        shared_strings = _shared_strings(workbook)
        sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
    rows: list[dict[str, str]] = []
    for row in sheet.findall(".//a:row", _XLSX_NS):
        cells: dict[str, str] = {}
        for cell in row.findall("a:c", _XLSX_NS):
            column = _cell_column(cell.attrib.get("r", ""))
            value_node = cell.find("a:v", _XLSX_NS)
            value = value_node.text if value_node is not None else ""
            if cell.attrib.get("t") == "s" and value:
                value = shared_strings[int(value)]
            cells[column] = value or ""
        rows.append(cells)
    return rows


def _shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []
    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root.findall("a:si", _XLSX_NS):
        strings.append("".join(node.text or "" for node in item.findall(".//a:t", _XLSX_NS)))
    return strings


def _cell_column(cell_ref: str) -> str:
    return "".join(char for char in cell_ref if char.isalpha())


def _parse_source_as_of_date(rows: list[dict[str, str]]) -> datetime.date:
    for row in rows[:10]:
        for value in row.values():
            match = re.search(r"As of ([0-9]{1,2}-[A-Za-z]{3}-[0-9]{4})", value)
            if match:
                return datetime.strptime(match.group(1), "%d-%b-%Y").date()
    raise ValueError("SSGA holdings XLSX did not expose a holdings as-of date.")


def _find_holdings_header(rows: list[dict[str, str]]) -> tuple[int, dict[str, str]]:
    for index, row in enumerate(rows):
        normalized = {str(value).strip().lower(): column for column, value in row.items()}
        if {"name", "ticker", "weight"}.issubset(normalized):
            return index, normalized
    raise ValueError("SSGA holdings XLSX did not expose a holdings header row.")


def _canonical_provider_symbol(symbol: str) -> str | None:
    if not symbol or symbol == "-":
        return None
    if not _LISTED_SYMBOL_RE.match(symbol):
        return None
    if symbol[0].isdigit():
        return None
    return symbol.replace(".", "-")


def _parse_provider_weight(value: object) -> Decimal | None:
    try:
        weight = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError):
        return None
    if weight <= 0:
        return None
    return weight
