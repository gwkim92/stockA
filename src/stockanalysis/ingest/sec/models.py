from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class SecFilingRecord:
    cik: str
    company_name: str
    accession_number: str
    form_type: str
    filing_date: date
    primary_document: str | None
    primary_doc_description: str | None
    filing_url: str
    filing_index_url: str
    items: str | None
    file_number: str | None
    film_number: str | None
    is_xbrl: bool | None
    is_inline_xbrl: bool | None


@dataclass(frozen=True)
class SecFilingsSyncResult:
    cik: str
    company_name: str
    filings: tuple[SecFilingRecord, ...]

    def summary(self) -> dict[str, object]:
        first_date = self.filings[0].filing_date.isoformat() if self.filings else None
        last_date = self.filings[-1].filing_date.isoformat() if self.filings else None
        form_types = sorted({record.form_type for record in self.filings})
        return {
            "cik": self.cik,
            "company_name": self.company_name,
            "filing_count": len(self.filings),
            "form_types": form_types,
            "latest_filing_date": first_date,
            "oldest_filing_date": last_date,
        }


@dataclass(frozen=True)
class SecSourceDocumentRecord:
    document_id: int
    external_document_id: str
    title: str
    url: str | None
    raw_storage_uri: str | None
    checksum: str | None


@dataclass(frozen=True)
class SecRawFetchResult:
    document_id: int
    external_document_id: str
    title: str
    status: str
    artifact_path: str | None
    raw_storage_uri: str | None
    checksum: str | None
    byte_count: int | None
    run_id: int | None
    skipped_reason: str | None = None

    def summary(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "external_document_id": self.external_document_id,
            "title": self.title,
            "status": self.status,
            "artifact_path": self.artifact_path,
            "raw_storage_uri": self.raw_storage_uri,
            "checksum": self.checksum,
            "byte_count": self.byte_count,
            "run_id": self.run_id,
            "skipped_reason": self.skipped_reason,
        }


@dataclass(frozen=True)
class SecEventSourceDocumentRecord:
    document_id: int
    external_document_id: str
    title: str
    summary: str | None
    published_at: datetime | None
    raw_storage_uri: str | None
    checksum: str | None


@dataclass(frozen=True)
class SecExtractedEventCandidate:
    document_id: int
    external_document_id: str
    event_type: str
    title: str
    summary: str
    event_at: datetime
    time_horizon: str | None
    impact_polarity: str | None
    significance_score: float | None
    confidence: float | None
    dedupe_key: str
    link_type: str = "source"


@dataclass(frozen=True)
class SecEventExtractionResult:
    document_id: int
    external_document_id: str
    event_type: str
    title: str
    dedupe_key: str
    status: str
    run_id: int | None

    def summary(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "external_document_id": self.external_document_id,
            "event_type": self.event_type,
            "title": self.title,
            "dedupe_key": self.dedupe_key,
            "status": self.status,
            "run_id": self.run_id,
        }


@dataclass(frozen=True)
class SecEventImpactCandidate:
    event_id: int
    event_type: str
    dedupe_key: str | None
    title: str


@dataclass(frozen=True)
class EventClassificationImpactBootstrapResult:
    event_id: int
    event_type: str
    node_code: str
    status: str
    run_id: int | None
    error: str | None = None

    def summary(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "node_code": self.node_code,
            "status": self.status,
            "run_id": self.run_id,
            "error": self.error,
        }


@dataclass(frozen=True)
class SecEventInstrumentImpactCandidate:
    event_id: int
    event_type: str
    dedupe_key: str | None
    title: str
    summary: str


@dataclass(frozen=True)
class EventInstrumentImpactBootstrapResult:
    event_id: int
    event_type: str
    instrument_id: int | None
    instrument_symbol: str | None
    status: str
    run_id: int | None
    error: str | None = None

    def summary(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "instrument_id": self.instrument_id,
            "instrument_symbol": self.instrument_symbol,
            "status": self.status,
            "run_id": self.run_id,
            "error": self.error,
        }


@dataclass(frozen=True)
class SecCompanyFactsValueRecord:
    accession_number: str | None
    statement_scope: str
    fiscal_year: int
    fiscal_quarter: int | None
    period_start: date
    period_end: date
    report_date: date | None
    currency_code: str
    is_audited: bool
    metric_code: str
    metric_value: Decimal
    unit: str


@dataclass(frozen=True)
class SecCompanyFactsSyncResult:
    cik: str
    company_name: str
    values: tuple[SecCompanyFactsValueRecord, ...]
    skipped_count: int = 0

    def summary(self) -> dict[str, object]:
        metric_codes = sorted({record.metric_code for record in self.values})
        period_keys = {
            (
                record.statement_scope,
                record.fiscal_year,
                record.fiscal_quarter,
                record.period_end.isoformat(),
            )
            for record in self.values
        }
        return {
            "cik": self.cik,
            "company_name": self.company_name,
            "fact_count": len(self.values),
            "period_count": len(period_keys),
            "metric_codes": metric_codes,
            "skipped_count": self.skipped_count,
        }
