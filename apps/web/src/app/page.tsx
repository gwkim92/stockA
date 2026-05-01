import Link from "next/link";
import { getCockpitSnapshot } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

export default async function HomePage() {
  const { dashboard, tickets, health } = await getCockpitSnapshot();
  const data = dashboard.data;
  const firstTicket = tickets.data.tickets[0];

  return (
    <div className="bento-grid">
      
      {/* 1. Hero Module */}
      <article className="bento-card span-2 row-span-2 bento-hero reveal">
        <div>
          <div className="bento-badge">As of {data.as_of_date}</div>
          <h1>Long-term portfolio review starts with the blind spot.</h1>
          <p>
            Cycle state, remediation backlog, scheduler readiness, and thesis coverage in one unified operator view.
            AI narratives stay secondary until provenance is visible.
          </p>
        </div>
        <div className="btn-row">
          <Link className="btn btn-primary" href="/remediation">
            Review open ticket
          </Link>
          <Link className="btn btn-secondary" href="/data-health">
            Inspect data health
          </Link>
        </div>
      </article>

      {/* 2. Primary KPI */}
      <article className="bento-card reveal delay-1" style={{ borderColor: "var(--accent-red)", background: "rgba(239, 68, 68, 0.05)" }}>
        <span className="metric-label">Critical Blind Spots</span>
        <strong className="metric-value" style={{ color: "var(--accent-red)" }}>
          {data.attention_summary.critical_blind_spot_count}
        </strong>
        <span className="metric-sub">Requires human review</span>
      </article>

      {/* 3. Coverage KPI */}
      <article className="bento-card reveal delay-1">
        <span className="metric-label">Coverage Ratio</span>
        <strong className="metric-value">{formatPercent(data.latest_metrics.weight_coverage_ratio)}</strong>
        <span className="metric-sub">{formatPercent(data.latest_metrics.covered_weight)} covered weight</span>
      </article>

      {/* 4. Open Tickets */}
      <article className="bento-card reveal delay-2">
        <span className="metric-label">Open Tickets</span>
        <strong className="metric-value">{data.attention_summary.open_ticket_count}</strong>
        <span className="metric-sub">{tickets.data.status_filter} backlog</span>
      </article>

      {/* 5. System Health */}
      <article className="bento-card reveal delay-2">
        <span className="metric-label">Pipeline Failures</span>
        <strong className="metric-value">{data.attention_summary.failed_pipeline_count}</strong>
        <div className="status-indicator" style={{ marginTop: "4px" }}>
          <span className={`status-dot ${data.attention_summary.failed_pipeline_count > 0 ? 'red' : 'green'}`} />
          <span className="metric-sub" style={{ marginTop: 0 }}>{health.data.overall_status}</span>
        </div>
      </article>

      {/* 6. Top Operator Action */}
      <article className="bento-card span-2 reveal delay-3">
        <div className="bento-badge" style={{ color: "var(--accent-amber)", borderColor: "var(--accent-amber)" }}>
          Top Priority
        </div>
        <h2 style={{ fontSize: "1.5rem", marginBottom: "8px" }}>
          {firstTicket.symbol}: Thesis coverage missing
        </h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem", marginBottom: "20px" }}>
          {firstTicket.required_human_decision}
        </p>
        
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginTop: "auto" }}>
          <div>
            <span className="metric-sub">Suggested Runner</span>
            <div style={{ fontSize: "0.9rem", fontWeight: 500 }}>{firstTicket.suggested_runner}</div>
          </div>
          <div>
            <span className="metric-sub">Reason</span>
            <div style={{ fontSize: "0.9rem", fontWeight: 500 }}>{firstTicket.reason}</div>
          </div>
        </div>
      </article>

      {/* 7. Review Queue */}
      <article className="bento-card span-2 row-span-2 reveal delay-3">
        <h2 style={{ fontSize: "1.25rem", marginBottom: "16px" }}>Review Queue</h2>
        <div className="bento-list">
          {data.top_actions.map((action) => (
            <div className="bento-list-item" key={`${action.rank}-${action.symbol}`}>
              <div style={{ flexDirection: "row", alignItems: "center", gap: "12px" }}>
                <span style={{ 
                  color: action.risk_level === 'high' ? 'var(--accent-red)' : 'var(--accent-amber)',
                  fontWeight: 700, 
                  fontSize: "0.7rem",
                  textTransform: "uppercase",
                  border: "1px solid currentColor",
                  padding: "2px 6px",
                  borderRadius: "4px"
                }}>
                  {action.risk_level}
                </span>
                <strong>{action.symbol}</strong>
              </div>
              <div style={{ alignItems: "flex-end" }}>
                <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{action.action}</span>
                <span style={{ fontSize: "0.7rem" }}>{action.reason}</span>
              </div>
            </div>
          ))}
        </div>
      </article>

      {/* 8. Status Ledger */}
      <article className="bento-card span-2 reveal delay-3" style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <span className="metric-sub">Daily Automation</span>
          <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>{data.run_status.daily_automation}</div>
        </div>
        <div style={{ width: "1px", height: "40px", background: "var(--border-light)" }} />
        <div>
          <span className="metric-sub">Scheduler</span>
          <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>{data.run_status.scheduler}</div>
        </div>
        <div style={{ width: "1px", height: "40px", background: "var(--border-light)" }} />
        <div>
          <span className="metric-sub">Latest Run ID</span>
          <div style={{ fontSize: "1.1rem", fontWeight: 600, fontFamily: "monospace" }}>{data.run_status.latest_run_id}</div>
        </div>
      </article>

    </div>
  );
}
