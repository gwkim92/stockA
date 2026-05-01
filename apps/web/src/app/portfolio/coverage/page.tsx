import { getPortfolioCoverage } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Portfolio Coverage" };

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

export default async function PortfolioCoveragePage() {
  const response = await getPortfolioCoverage();
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          Coverage Map • {data.portfolio_name} • {data.strategy_name} • {data.as_of_date}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>Portfolio coverage gate.</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
              Attribution is blocked until every meaningful position has a thesis and measurable outcome path. Cash is shown explicitly instead of disappearing into portfolio math.
            </p>
          </div>
          
          <div style={{ 
            padding: "20px 32px", 
            background: data.attribution_readiness.is_ready ? "rgba(16, 185, 129, 0.1)" : "rgba(245, 158, 11, 0.1)", 
            border: `1px solid ${data.attribution_readiness.is_ready ? "rgba(16, 185, 129, 0.2)" : "rgba(245, 158, 11, 0.2)"}`,
            borderRadius: "var(--radius-md)",
            textAlign: "center"
          }}>
            <span className="metric-sub" style={{ color: data.attribution_readiness.is_ready ? "var(--accent-green)" : "var(--accent-amber)" }}>Weight Coverage</span>
            <div style={{ fontSize: "2.5rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0" }}>
              {formatPercent(data.summary.weight_coverage_ratio)}
            </div>
            <div style={{ fontSize: "0.85rem", color: data.attribution_readiness.is_ready ? "var(--accent-green)" : "var(--accent-amber)", fontWeight: 600, textTransform: "uppercase" }}>
              {data.attribution_readiness.is_ready ? "Ready" : "Blocked"}
            </div>
          </div>
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card">
          <span className="metric-label">Positions</span>
          <strong className="metric-value">{data.summary.position_count}</strong>
          <span className="metric-sub">{data.summary.covered_position_count} covered</span>
        </article>
        
        <article className="bento-card" style={{ borderColor: data.summary.missing_thesis_count > 0 ? "var(--accent-red)" : "var(--border-light)" }}>
          <span className="metric-label">Missing Thesis</span>
          <strong className="metric-value" style={{ color: data.summary.missing_thesis_count > 0 ? "var(--accent-red)" : "var(--text-primary)" }}>
            {data.summary.missing_thesis_count}
          </strong>
          <span className="metric-sub">{formatPercent(data.summary.missing_thesis_weight)} weight</span>
        </article>

        <article className="bento-card">
          <span className="metric-label">Cash Allocation</span>
          <strong className="metric-value">{formatPercent(data.summary.cash_weight)}</strong>
          <span className="metric-sub">explicit allocation</span>
        </article>

        <article className="bento-card">
          <span className="metric-label">Outcomes Missing</span>
          <strong className="metric-value">{data.summary.missing_outcome_count}</strong>
          <span className="metric-sub">measurement end {data.coverage_measurement_end_date}</span>
        </article>

        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Position Coverage</span>
            <h2 style={{ fontSize: "1.5rem" }}>Review Map</h2>
          </div>
          
          <div className="bento-list" style={{ gap: "8px" }}>
            <div className="bento-list-item" style={{ background: "transparent", borderBottom: "1px solid var(--border-light)", borderRadius: 0, paddingBottom: "16px" }}>
              <div style={{ flexDirection: "row", width: "100%", gap: "24px" }}>
                <span className="metric-sub" style={{ width: "100px" }}>Symbol</span>
                <span className="metric-sub" style={{ width: "100px" }}>Weight</span>
                <span className="metric-sub" style={{ width: "140px" }}>Coverage</span>
                <span className="metric-sub" style={{ width: "140px" }}>Outcome</span>
                <span className="metric-sub" style={{ flex: 1 }}>Action</span>
              </div>
            </div>
            
            {data.positions.map((position) => (
              <div className="bento-list-item" key={position.instrument_id} style={{ alignItems: "flex-start" }}>
                <div style={{ flexDirection: "row", width: "100%", gap: "24px", alignItems: "center" }}>
                  <strong style={{ width: "100px", fontSize: "1.1rem" }}>{position.symbol}</strong>
                  <span style={{ width: "100px", color: "var(--text-primary)", fontWeight: 500 }}>{formatPercent(position.weight)}</span>
                  <span style={{ 
                    width: "140px", 
                    color: position.coverage_status === 'covered' ? 'var(--accent-green)' : 'var(--accent-red)' 
                  }}>
                    {position.coverage_status}
                  </span>
                  <span style={{ 
                    width: "140px", 
                    color: position.outcome_status === 'measured' ? 'var(--accent-green)' : 'var(--text-secondary)' 
                  }}>
                    {position.outcome_status}
                  </span>
                  <span style={{ flex: 1, color: "var(--text-primary)", fontWeight: 500 }}>
                    {position.action}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
