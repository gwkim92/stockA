# System Flow Map

## Purpose

This project is a long-term investment operating system. It continuously collects market, macro, news, filing, broker, portfolio, and performance data; validates quality; structures evidence with AI where useful; then produces explainable recommendation, holding-review, paper-validation, and outcome-feedback records.

It is not a realtime trading bot and it is not a news-summary site.

## Fixed Operating Flow

```text
source collection
  -> normalization and provenance
  -> quality validation
  -> AI structuring and research artifacts
  -> cycle/company/ETF analysis
  -> recommendation, holding, and paper validation
  -> outcome and attribution feedback
  -> weight review only after mature evidence
```

## Runtime Boundaries

| Layer | Runtime | Responsibility | Boundary |
| --- | --- | --- | --- |
| Data operations | `stockanalysis-operations` Python CLI/services | Collect, normalize, validate, and write canonical data. | Owns writes through controlled runners and `ops.pipeline_run`. |
| API | FastAPI read-only server | Serves frontend DTOs from Postgres. | Read-only; protected by read auth/RBAC; no broker submit. |
| UI | Next.js | Presents investor and operator workflows. | Does not perform realtime AI calls or write trading state. |
| Database | Postgres | Canonical facts, ontology-lite graph, events, signals, research artifacts, portfolio, performance. | Canonical truth plus provenance; no synthetic missing financial facts. |
| Scheduler | EC2 `systemd` profile timers | Runs separated profiles by cadence. | Profiles are split by news, market, Toss, cross-asset, decision, macro, and performance. |
| AI | Agents SDK/OpenAI, Codex OAuth, local rules | Translation, event structuring, research summary, contradiction review. | AI does not own final recommendation score, position sizing, or order submission. |

## Deterministic Code Versus AI

| Responsibility | Owner | Reason |
| --- | --- | --- |
| Raw collection and dedupe | Deterministic code | Must be replayable and auditable. |
| Provider budget and freshness | Deterministic code | Prevents quota exhaustion and stale data pollution. |
| News translation and event extraction | AI batch with validator | Unstructured language requires interpretation, but output must be schema checked. |
| Theme/instrument acceptance | Deterministic validator | Blocks unknown nodes, hallucinated tickers, and low-confidence candidates. |
| Cycle and cross-asset snapshots | Deterministic code | Keeps scoring stable and backtestable. |
| Equity research narrative | AI batch with source guardrails | Produces Korean explanation, catalysts, risks, and invalidation notes. |
| Recommendation score and components | Deterministic code | Must be reproducible; new components can be zero-weight until evaluated. |
| Paper validation and order boundary | Deterministic code | Safety boundary must not depend on LLM output. |
| Outcome feedback and weight review | Deterministic code plus reports | Weight changes require mature samples and separate approval. |

## Operating Profiles

| Profile | Cadence | Inputs | Outputs | Must Precede |
| --- | --- | --- | --- | --- |
| `news-intraday` | Every 30-60 minutes during market/news hours | RSS feeds, existing instruments, ontology-lite graph, AI provider status | Source documents, Korean translations, events, AI artifacts, validator results | Intelligence pages, cycle evidence, recommendation evidence |
| `market-daily` | After US close | Watchlist, free market provider budget | Analysis price bars | Cycle snapshots, performance, recommendation refresh |
| Toss reference/candle/microdata/account profiles | KR/US close and intraday windows | Toss broker endpoints | Broker reality data, warnings, microdata, read-only account state | Paper readiness and broker reality cards |
| `cross-asset-daily` | After `market-daily` | FRED, CBOE, Twelve Data, market bars, news links | Indicator observations, cross-asset regimes, zero-weight recommendation evidence | Cycle map, market map, decision detail |
| `decision-daily` | After market and cross-asset data | Prices, events, cycles, fundamentals, portfolio | Recommendations, thesis/holding review inputs, paper validation audit | Investor dashboard and recommendation pages |
| `macro-weekly` | Weekly | FRED macro series, SEC/source metadata, fundamentals | Macro observations, company facts, professional analysis refresh | Longer-term cycle and equity analysis |
| `performance-monthly` | Monthly/when horizons mature | Recommendation history and price outcomes | Outcome rows, attribution, calibration evidence | Manual weight review only after maturity |

## UI Separation

| UI Area | Audience | Primary Question | Internal Terms Allowed |
| --- | --- | --- | --- |
| `/`, `/market-map`, `/cycle-map`, `/intelligence`, `/stocks`, `/recommendations`, `/portfolio/coverage`, `/paper-trading` | Investor | What should I review and why? | No. |
| `/data-health`, `/admin/ai-agents`, `/trading-readiness`, `/remediation` | Operator | Which collection, AI, safety, or data-quality boundary needs attention? | Yes, but with Korean explanation and user impact. |

## Safety Rules

- Recommendation weight changes remain blocked until outcome/evaluation evidence matures.
- Broker submit and live order automation remain blocked.
- Toss broker data can support account reality, paper readiness, and source comparison, but does not replace analysis price inputs without explicit promotion criteria.
- Source-limited instruments are not filled with synthetic financial data.
- External paid RAG/graph/vector services are not part of the current runtime.

