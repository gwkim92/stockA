# Data Catalog

## Usage Legend

- `collected`: source is fetched or generated.
- `normalized`: stored in canonical or structured tables.
- `ai_input`: used as context for AI batch jobs.
- `recommendation_input`: used by deterministic recommendation, review, or paper validation logic.
- `screen`: visible in investor or operator UI.
- `zero_weight`: stored as evidence/component but not allowed to affect final score yet.
- `blocked`: intentionally excluded from investment decisions until source, quality, or maturity conditions are met.

## Current Data Sources

| Data Area | Main Sources | Storage/Surface | Usage | Notes |
| --- | --- | --- | --- | --- |
| News ledger | RSS/Atom feeds, GDELT candidate scope where enabled | `ingest.source_document`, `event.event`, AI evidence pages | collected, normalized, ai_input, recommendation_input, screen | Important news is translated and structured by batch AI; validator blocks low-quality extraction. |
| News AI artifacts | Codex OAuth, Agents SDK/OpenAI where available, local rules fallback | `ai.model_invocation`, `ai.extraction_artifact`, event impact tables | collected, normalized, recommendation_input, screen | AI output becomes canonical only after schema and grounding validation. |
| SEC filings and company facts | SEC EDGAR/companyfacts | `ingest.source_document`, financial statement and research tables | collected, normalized, ai_input, recommendation_input, screen | Missing standard facts are source blockers, not values to invent. |
| Macro data | FRED | `macro.observation`, cross-asset indicators | collected, normalized, ai_input, recommendation_input, screen | Weekly macro and daily cross-asset roles are separated. |
| Market prices | Free provider budget, Twelve Data where configured | `market.daily_price_bar` | collected, normalized, recommendation_input, screen | This is the analysis reference price for cycles, performance, and recommendations. |
| Cross-asset indicators | FRED, CBOE CSV, Twelve Data, market bars | `market.market_indicator_observation`, `signal.market_indicator_snapshot`, `signal.cross_asset_regime_snapshot` | collected, normalized, ai_input, recommendation_input, screen, zero_weight | Regime components are visible but score impact stays zero until evaluated. |
| Toss broker data | TossInvest read-only/reference/candle/microdata/account endpoints | Toss market/account snapshots, provider comparison, paper views | collected, normalized, screen, zero_weight | Broker reality data supports account and paper readiness; US candles remain validation/reference unless promoted. |
| ETF/fund data | Official ETF provider pages/files, market bars | fund analysis payloads and metric snapshots | collected, normalized, recommendation_input, screen | ETF/fund analysis uses holdings, cost, NAV premium/discount, liquidity, and tracking data instead of company financial model. |
| Financial metrics | SEC facts, filings, deterministic transforms | normalized financial metrics, financial models | collected, normalized, ai_input, recommendation_input, screen | Missing facts create source limits and professional coverage gaps. |
| Valuation | Deterministic DCF-lite, relative/method snapshots, SOTP inputs | `market.valuation_snapshot`, target range payloads | collected, normalized, recommendation_input, screen, zero_weight where not mature | Recommendation weight changes remain blocked until outcome evidence matures. |
| Portfolio positions | Local portfolio snapshots, Toss account read-only where available | `portfolio.position_snapshot`, portfolio coverage pages | collected, normalized, recommendation_input, screen | Used for holding review, concentration, average cost, unrealized P/L, and paper validation context. |
| Paper validation | Deterministic risk/order boundary checks | paper validation audit payloads | normalized, recommendation_input, screen, blocked | Failed validation is often safety block, not system error. |
| Performance and attribution | Recommendation history, price outcomes, portfolio snapshots | `performance.*`, `ai.eval_run`, data-health | normalized, recommendation_input, screen | Weight review stays blocked until outcome sample maturity gates pass. |

## Data Gaps And Policy

| Gap | Priority | Free Path | Investment Use Before Remediation |
| --- | --- | --- | --- |
| Corporate actions | Immediately free where provider/source allows | SEC/company source and market provider metadata | Show as data limitation; do not adjust performance manually without source. |
| Earnings calendar | Free but quality-limited | SEC filing dates, exchange/provider calendars | Use as screen context, not score input until quality measured. |
| Guidance/transcripts | Free but fragmented | SEC filings, company IR links where available | AI context only when source document is stored. |
| SEC ownership/13F | Free but slower cadence | SEC structured filings | Portfolio/peer context only after deterministic parser. |
| Insider transactions | Free via SEC | SEC Forms 3/4/5 parser candidate | Zero-weight evidence until parser/eval exists. |
| Sector breadth | Free from ETF constituents and market bars | ETF holdings plus price bars | Market/cycle context; no weight change before evaluation. |
| Credit/liquidity | FRED/free market proxies | FRED spreads, rates, dollar/liquidity proxies | Cross-asset regime context and zero-weight component. |
| ETF holdings freshness | Official fund pages/files | Provider-specific importers | Source-limited if stale; no synthetic holdings. |
| Toss fills/account history | Toss read-only endpoints | Broker account sync | Paper/broker reality only; no live order submit. |

## Screen Mapping

| Screen | Primary Data Used |
| --- | --- |
| `/` | Market regime, new evidence, recommendation changes, holding risk, system attention. |
| `/market-map` | Cross-asset indicators, market bars, regimes, indicator-news links. |
| `/cycle-map` | Ontology-lite graph, cycle snapshots, event heat, cross-asset impact. |
| `/intelligence` and `/ai-evidence` | News ledger, Korean translations, AI artifacts, validator results, evidence paths. |
| `/stocks/[symbol]` | Price bars, broker reality, company/ETF analysis, news, cycles, thesis, recommendation, portfolio position. |
| `/recommendations/[id]` | Recommendation score components, professional evidence audit, thesis, paper validation, order boundary. |
| `/portfolio/coverage` | Positions, average cost, unrealized P/L, concentration, benchmark drift, thesis coverage. |
| `/paper-trading` | Paper validation, risk budget, Toss broker reality, read-only order boundary. |
| `/data-health` | Collection freshness, AI/eval status, provider quota, scheduler, source limits, outcome maturity. |
| `/admin/ai-agents` | Agent registry, prompt versions, model policy, fallback path, cost/quota, Codex OAuth state. |
