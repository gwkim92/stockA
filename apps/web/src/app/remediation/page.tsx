import { getRemediationTickets } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Remediation" };

export default async function RemediationPage() {
  const response = await getRemediationTickets();

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">Portfolio • {response.data.portfolio_name}</div>
        <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>Persistent remediation backlog.</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
          Tickets are read-only here. Status mutation stays deferred until actor identity, reason capture, and audit trail are implemented.
        </p>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Open Remediation Tickets</span>
            <h2 style={{ fontSize: "1.5rem" }}>Review Required</h2>
          </div>
          
          <div className="bento-list" style={{ gap: "8px" }}>
            <div className="bento-list-item" style={{ background: "transparent", borderBottom: "1px solid var(--border-light)", borderRadius: 0, paddingBottom: "16px" }}>
              <div style={{ flexDirection: "row", width: "100%", gap: "24px" }}>
                <span className="metric-sub" style={{ width: "80px" }}>Symbol</span>
                <span className="metric-sub" style={{ width: "120px" }}>Action</span>
                <span className="metric-sub" style={{ width: "100px" }}>Risk</span>
                <span className="metric-sub" style={{ flex: 1 }}>Required Decision</span>
              </div>
            </div>
            
            {response.data.tickets.map((ticket) => (
              <div className="bento-list-item" key={ticket.ticket_id} style={{ alignItems: "flex-start" }}>
                <div style={{ flexDirection: "row", width: "100%", gap: "24px", alignItems: "center" }}>
                  <strong style={{ width: "80px", fontSize: "1.1rem" }}>{ticket.symbol}</strong>
                  <span style={{ width: "120px", color: "var(--text-primary)", fontWeight: 500 }}>{ticket.action}</span>
                  <div style={{ width: "100px" }}>
                    <span style={{ 
                      display: "inline-block",
                      color: ticket.risk_level === 'high' ? 'var(--accent-red)' : 'var(--accent-amber)',
                      fontWeight: 700, 
                      fontSize: "0.7rem",
                      textTransform: "uppercase",
                      border: "1px solid currentColor",
                      padding: "2px 8px",
                      borderRadius: "4px"
                    }}>
                      {ticket.risk_level}
                    </span>
                  </div>
                  <span style={{ flex: 1, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                    {ticket.required_human_decision}
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
