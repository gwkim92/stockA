from __future__ import annotations

from stockanalysis.ingest.macro.models import MacroSeriesSpec


DEFAULT_MACRO_SERIES: tuple[MacroSeriesSpec, ...] = (
    MacroSeriesSpec("FEDFUNDS", "policy_rate", description="Effective Federal Funds Rate"),
    MacroSeriesSpec("CPIAUCSL", "inflation", description="Consumer Price Index for All Urban Consumers"),
    MacroSeriesSpec("PCEPI", "inflation", description="Personal Consumption Expenditures Price Index"),
    MacroSeriesSpec("UNRATE", "labor", description="U.S. unemployment rate"),
    MacroSeriesSpec("DGS10", "bond_yield", description="10-Year Treasury Constant Maturity Rate"),
    MacroSeriesSpec("DGS2", "bond_yield", description="2-Year Treasury Constant Maturity Rate"),
    MacroSeriesSpec("T10Y2Y", "curve", description="10-Year minus 2-Year Treasury yield spread"),
    MacroSeriesSpec("T10Y3M", "curve", description="10-Year minus 3-Month Treasury yield spread"),
    MacroSeriesSpec("DFII10", "real_rate", description="10-Year Treasury Inflation-Indexed Security rate"),
    MacroSeriesSpec("T10YIE", "inflation_expectation", description="10-Year breakeven inflation rate"),
    MacroSeriesSpec("DTWEXBGS", "dollar", description="Nominal broad U.S. dollar index"),
    MacroSeriesSpec("DCOILWTICO", "commodity", description="West Texas Intermediate crude oil spot price"),
    MacroSeriesSpec("DCOILBRENTEU", "commodity", description="Brent crude oil spot price"),
    MacroSeriesSpec("DHHNGSP", "commodity", description="Henry Hub natural gas spot price"),
    MacroSeriesSpec("VIXCLS", "volatility", description="CBOE Volatility Index close"),
    MacroSeriesSpec("BAMLH0A0HYM2", "credit", description="ICE BofA U.S. High Yield option-adjusted spread"),
    MacroSeriesSpec("BAMLC0A0CM", "credit", description="ICE BofA U.S. Corporate option-adjusted spread"),
    MacroSeriesSpec("GDPC1", "growth", description="Real Gross Domestic Product"),
)


def list_default_series() -> tuple[MacroSeriesSpec, ...]:
    return DEFAULT_MACRO_SERIES


def get_default_series(series_id: str) -> MacroSeriesSpec | None:
    normalized = series_id.upper()
    for spec in DEFAULT_MACRO_SERIES:
        if spec.series_id == normalized:
            return spec
    return None
