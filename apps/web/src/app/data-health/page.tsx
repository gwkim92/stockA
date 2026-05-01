import { getDataHealth } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Data Health" };

export default async function DataHealthPage() {
  const response = await getDataHealth();
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">System Health • {data.as_of_date}</div>
        <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>Data health before conviction.</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
          The UI treats scheduler readiness, pipeline provenance, and stale datasets as first-class investment risk.
        </p>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Pipeline Runs</span>
            <h2 style={{ fontSize: "1.75rem", display: "flex", alignItems: "center", gap: "12px" }}>
              {data.overall_status}
              <span className={`status-dot ${data.overall_status === 'healthy' ? 'green' : 'red'}`} style={{ width: "12px", height: "12px" }} />
            </h2>
          </div>
          
          <div className="bento-list">
            {data.pipeline_runs.map((run) => (
              <div className="bento-list-item" key={run.latest_run_id}>
                <div>
                  <strong>{run.pipeline_name}</strong>
                  <span style={{ fontFamily: "monospace", fontSize: "0.75rem" }}>{run.latest_run_id}</span>
                </div>
                <div style={{ alignItems: "flex-end" }}>
                  <strong style={{ color: run.latest_status === "succeeded" ? "var(--accent-green)" : "var(--accent-red)" }}>
                    {run.latest_status}
                  </strong>
                  <span>{run.finished_at}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Open Gates</span>
            <h2 style={{ fontSize: "1.75rem" }}>{data.open_gates.length} gates remain</h2>
          </div>
          
          <div style={{ display: "flex", flexWrap: "wrap", gap: "12px" }}>
            {data.open_gates.map((gate) => (
              <div key={gate} style={{ 
                padding: "8px 16px", 
                background: "rgba(255, 255, 255, 0.05)", 
                border: "1px solid var(--border-light)",
                borderRadius: "var(--radius-sm)",
                fontSize: "0.85rem",
                fontWeight: 500
              }}>
                {gate}
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
