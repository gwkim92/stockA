from __future__ import annotations

from stockanalysis.ingest.sources.alpha_vantage import AlphaVantageSource
from stockanalysis.ingest.sources.base import IngestSource
from stockanalysis.ingest.sources.fred import FredSource
from stockanalysis.ingest.sources.rss_news import RssNewsSource
from stockanalysis.ingest.sources.sec import SecSource
from stockanalysis.ingest.sources.twelve_data import TwelveDataSource


def build_registry() -> dict[str, IngestSource]:
    return {
        source.name: source
        for source in (
            SecSource(),
            FredSource(),
            RssNewsSource(),
            AlphaVantageSource(),
            TwelveDataSource(),
        )
    }


REGISTRY = build_registry()


def get_source(name: str) -> IngestSource:
    try:
        return REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Unknown source `{name}`") from exc


def list_sources() -> list[IngestSource]:
    return [REGISTRY[name] for name in sorted(REGISTRY)]
