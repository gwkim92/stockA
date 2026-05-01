import Link from "next/link";
import type { Route } from "next";

import { getCycleStates } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Cycles" };

function formatConfidence(value: number) {
  return `${Math.round(value * 100)}%`;
}

function themeHref(themeKey: string) {
  return themeKey === "ANNUAL_REPORTING" ? (`/themes/${themeKey}` as Route) : null;
}

export default async function CyclesPage() {
  const response = await getCycleStates();
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          {data.strategy_name} • {data.horizon_type} • v{data.universe_version}
        </div>
        <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>Theme Cycle Board</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
          Cycle states are not buy signals. They are context for thesis quality, coverage gaps, and evidence review.
        </p>
      </section>

      <section className="bento-grid reveal delay-1">
        {data.cycle_states.map((cycle) => {
          const href = themeHref(cycle.theme_key);
          return (
            <article className="bento-card span-2" key={cycle.theme_key}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
                <div>
                  <span className="metric-sub" style={{ textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    {cycle.theme_key}
                  </span>
                  <h2 style={{ fontSize: "1.5rem", marginTop: "4px" }}>{cycle.theme_name}</h2>
                </div>
                <div className="bento-badge" style={{ margin: 0, background: "rgba(59, 130, 246, 0.1)", color: "var(--accent-blue)", borderColor: "rgba(59, 130, 246, 0.2)" }}>
                  {formatConfidence(cycle.confidence)} Confidence
                </div>
              </div>

              <div style={{
                margin: "0 -24px",
                padding: "20px 24px",
                background: "rgba(255, 255, 255, 0.02)",
                borderTop: "1px solid var(--border-light)",
                borderBottom: "1px solid var(--border-light)"
              }}>
                <span className="metric-sub">Current State</span>
                <div style={{ fontSize: "2rem", fontWeight: 700, fontFamily: "var(--font-display)", color: "var(--text-primary)" }}>
                  {cycle.state}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-tertiary)", marginTop: "4px" }}>
                  Transitioned from {cycle.previous_state}
                </div>
              </div>

              <div style={{ display: "flex", gap: "24px", marginTop: "24px", flexWrap: "wrap" }}>
                <div>
                  <span className="metric-sub">Instruments</span>
                  <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>{cycle.instrument_count}</div>
                </div>
                <div>
                  <span className="metric-sub">Top Symbols</span>
                  <div style={{ fontSize: "1rem", fontWeight: 500, color: "var(--text-secondary)" }}>
                    {cycle.top_symbols.join(", ")}
                  </div>
                </div>
                {href ? (
                  <Link className="btn btn-secondary" href={href} style={{ marginLeft: "auto" }}>
                    Open Theme
                  </Link>
                ) : (
                  <span className="metric-sub" style={{ marginLeft: "auto", alignSelf: "center" }}>
                    detail pending
                  </span>
                )}
              </div>
            </article>
          );
        })}
      </section>
    </div>
  );
}
