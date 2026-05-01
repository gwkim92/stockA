from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class MacroSeriesSpec:
    series_id: str
    category: str
    region_code: str = "US"
    description: str | None = None


@dataclass(frozen=True)
class MacroSeriesRecord:
    series_code: str
    name: str
    category: str
    frequency: str
    unit: str
    region_code: str
    source_name: str = "fred"
    is_active: bool = True


@dataclass(frozen=True)
class MacroObservationRecord:
    series_code: str
    observation_date: date
    value: Decimal
    revision_number: int = 0


@dataclass(frozen=True)
class MacroSyncResult:
    series: MacroSeriesRecord
    observations: tuple[MacroObservationRecord, ...]
    skipped_count: int

    def summary(self) -> dict[str, object]:
        first_date = self.observations[0].observation_date.isoformat() if self.observations else None
        last_date = self.observations[-1].observation_date.isoformat() if self.observations else None
        return {
            "series_code": self.series.series_code,
            "series_name": self.series.name,
            "category": self.series.category,
            "frequency": self.series.frequency,
            "unit": self.series.unit,
            "observation_count": len(self.observations),
            "skipped_count": self.skipped_count,
            "first_observation_date": first_date,
            "last_observation_date": last_date,
        }
