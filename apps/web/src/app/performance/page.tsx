import Link from "next/link";
import type { Route } from "next";

import { getPerformanceOutcomes } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Performance Outcomes" };

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function formatBps(value: number) {
  const rounded = Math.round(value * 10) / 10;
  return `${rounded > 0 ? "+" : ""}${rounded} bps`;
}

function recommendationHref(recommendationId: string) {
  return `/recommendations/${recommendationId}` as Route;
}

function thesisHref(thesisId: string) {
  return `/theses/${thesisId}` as Route;
}

function themeHref(themeKey: string | null) {
  return themeKey === "ANNUAL_REPORTING" ? (`/themes/${themeKey}` as Route) : null;
}

function gateColor(status: string) {
  if (status === "passed") {
    return "var(--accent-green)";
  }
  if (status === "blocked") {
    return "var(--accent-amber)";
  }
  return "var(--text-secondary)";
}

export default async function PerformancePage() {
  const response = await getPerformanceOutcomes();
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          Outcome Ledger • {data.portfolio_name} • {data.measurement_end_date}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>
              Performance outcome review
            </h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "760px" }}>
              This is the accountability layer for long-term recommendations. It shows what was measured, what beat
              the benchmark, and what remains excluded before attribution can be trusted.
            </p>
          </div>

          <div style={{
            padding: "20px 32px",
            background: "rgba(16, 185, 129, 0.1)",
            border: "1px solid rgba(16, 185, 129, 0.2)",
            borderRadius: "var(--radius-md)",
            textAlign: "center",
          }}>
            <span className="metric-sub" style={{ color: "var(--accent-green)" }}>Average Alpha</span>
            <div style={{ fontSize: "2.5rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0" }}>
              {formatPercent(data.summary.average_alpha)}
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--accent-green)", fontWeight: 600, textTransform: "uppercase" }}>
              vs {data.benchmark_code}
            </div>
          </div>
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card">
          <span className="metric-label">Hit Rate</span>
          <strong className="metric-value">{formatPercent(data.summary.hit_rate)}</strong>
          <span className="metric-sub">
            {data.summary.outperform_count} outperform / {data.summary.underperform_count} underperform
          </span>
        </article>
        <article className="bento-card">
          <span className="metric-label">Measured Theses</span>
          <strong className="metric-value">{data.summary.measured_thesis_count}</strong>
          <span className="metric-sub">{data.summary.measured_recommendation_count} recommendations</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">Security Lens</span>
          <strong className="metric-value">{formatBps(data.summary.security_lens_contribution_bps)}</strong>
          <span className="metric-sub">{data.methodology}</span>
        </article>
        <article className="bento-card" style={{ borderColor: data.summary.excluded_position_count > 0 ? "rgba(245, 158, 11, 0.45)" : "var(--border-light)" }}>
          <span className="metric-label">Excluded Weight</span>
          <strong className="metric-value" style={{ color: data.summary.excluded_position_count > 0 ? "var(--accent-amber)" : "var(--text-primary)" }}>
            {formatPercent(data.summary.excluded_weight)}
          </strong>
          <span className="metric-sub">{data.summary.excluded_position_count} positions need coverage</span>
        </article>
      </section>

      <section className="bento-grid reveal delay-2">
        <article className="bento-card span-4">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px", gap: "16px", flexWrap: "wrap" }}>
            <div>
              <span className="metric-sub">Measured outcomes</span>
              <h2 style={{ fontSize: "1.5rem" }}>Recommendation accountability</h2>
            </div>
            <Link className="btn btn-secondary" href="/portfolio/coverage">
              Open coverage gate
            </Link>
          </div>
          <div className="bento-list">
            {data.outcomes.map((outcome) => (
              <div className="bento-list-item" key={outcome.outcome_id} style={{ alignItems: "flex-start" }}>
                <div style={{ flex: 1 }}>
                  <span className="metric-sub">
                    {outcome.symbol} • {outcome.horizon_days}d • {data.measurement_start_date} to {data.measurement_end_date}
                  </span>
                  <strong style={{ fontSize: "1.05rem" }}>{outcome.recommendation.toUpperCase()} / {outcome.label}</strong>
                  <span>source run {outcome.source_run_id}</span>
                  <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "8px" }}>
                    <Link className="btn btn-secondary" href={recommendationHref(outcome.recommendation_id)}>
                      Recommendation
                    </Link>
                    <Link className="btn btn-secondary" href={thesisHref(outcome.thesis_id)}>
                      Thesis
                    </Link>
                  </div>
                </div>
                <div style={{ alignItems: "flex-end", minWidth: "220px" }}>
                  <strong style={{ color: outcome.alpha >= 0 ? "var(--accent-green)" : "var(--accent-red)", fontSize: "1.25rem" }}>
                    {formatPercent(outcome.alpha)} alpha
                  </strong>
                  <span>{formatPercent(outcome.absolute_return)} absolute</span>
                  <span>{formatPercent(outcome.benchmark_return)} benchmark</span>
                  <span>{formatBps(outcome.security_contribution_bps)} contribution</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Attribution components</span>
            <h2 style={{ fontSize: "1.5rem" }}>Lenses, not additive totals</h2>
          </div>
          <div className="bento-list">
            {data.attribution_components.map((component) => {
              const href = themeHref(component.theme_key);
              return (
                <div className="bento-list-item" key={component.component_id} style={{ alignItems: "flex-start" }}>
                  <div style={{ flex: 1 }}>
                    <span className="metric-sub">{component.component_type}</span>
                    <strong>{component.label}</strong>
                    <span>{component.interpretation}</span>
                    {href ? (
                      <Link href={href} style={{ color: "var(--accent-blue)", fontSize: "0.75rem", textDecoration: "underline", textUnderlineOffset: "3px", marginTop: "4px" }}>
                        Open theme
                      </Link>
                    ) : null}
                  </div>
                  <div style={{ alignItems: "flex-end", minWidth: "92px" }}>
                    <strong style={{ color: component.contribution_bps > 0 ? "var(--accent-green)" : "var(--text-primary)" }}>
                      {formatBps(component.contribution_bps)}
                    </strong>
                    <span>{formatPercent(component.weight)} weight</span>
                  </div>
                </div>
              );
            })}
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Coverage exclusions</span>
            <h2 style={{ fontSize: "1.5rem" }}>What is not trusted yet</h2>
          </div>
          <div className="bento-list">
            {data.coverage_exclusions.map((exclusion) => (
              <div className="bento-list-item" key={exclusion.instrument_id}>
                <div>
                  <strong>{exclusion.symbol}</strong>
                  <span>{exclusion.reason}</span>
                </div>
                <div style={{ alignItems: "flex-end" }}>
                  <strong style={{ color: "var(--accent-amber)" }}>{formatPercent(exclusion.weight)}</strong>
                  <span>{exclusion.required_action}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="btn-row">
            <Link className="btn btn-secondary" href="/remediation">
              Open remediation
            </Link>
          </div>
        </article>

        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Quality gates</span>
            <h2 style={{ fontSize: "1.5rem" }}>Do not overread performance</h2>
          </div>
          <div className="bento-list">
            {data.quality_gates.map((gate) => (
              <div className="bento-list-item" key={gate.gate}>
                <div>
                  <strong>{gate.gate}</strong>
                  <span>{gate.reason}</span>
                </div>
                <strong style={{ color: gateColor(gate.status), textTransform: "uppercase" }}>{gate.status}</strong>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
