import Link from "next/link";
import type { Route } from "next";
import { getThesisDetail } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Thesis Detail" };

type ThesisPageProps = {
  params: Promise<{ thesisId: string }>;
};

function evidenceHref(evidenceId: string, evidenceType: string) {
  return evidenceType === "source_document_event" ? (`/ai-evidence/${evidenceId}` as Route) : null;
}

export default async function ThesisPage({ params }: ThesisPageProps) {
  const { thesisId } = await params;
  const response = await getThesisDetail(thesisId);
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          Thesis • {data.symbol} • {data.status} • v{data.thesis_version}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>Thesis evidence ledger.</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
              {data.summary}
            </p>
          </div>
          
          <div style={{ 
            padding: "20px 32px", 
            background: "rgba(16, 185, 129, 0.1)", 
            border: "1px solid rgba(16, 185, 129, 0.2)",
            borderRadius: "var(--radius-md)",
            textAlign: "center"
          }}>
            <span className="metric-sub" style={{ color: "var(--accent-green)" }}>Latest Review</span>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0" }}>
              {data.latest_review.action}
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--accent-green)", fontWeight: 500 }}>
              {data.latest_review.risk_level} risk
            </div>
          </div>
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Core Claims</span>
            <h2 style={{ fontSize: "1.5rem" }}>What must remain true</h2>
          </div>
          <ol style={{ 
            margin: 0, 
            paddingLeft: "20px", 
            color: "var(--text-secondary)", 
            display: "flex", 
            flexDirection: "column", 
            gap: "12px",
            lineHeight: 1.6
          }}>
            {data.core_claims.map((claim) => (
              <li key={claim} style={{ color: "var(--text-primary)" }}>{claim}</li>
            ))}
          </ol>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Invalidation</span>
            <h2 style={{ fontSize: "1.5rem" }}>Break conditions</h2>
          </div>
          <div className="bento-list">
            {data.invalidation_conditions.map((condition) => (
              <div className="bento-list-item" key={condition.condition} style={{ alignItems: "center" }}>
                <span style={{ color: "var(--text-primary)" }}>{condition.condition}</span>
                <strong style={{ 
                  color: condition.current_status === "not_triggered" ? "var(--accent-green)" : "var(--accent-red)"
                }}>
                  {condition.current_status}
                </strong>
              </div>
            ))}
          </div>
        </article>

        <article className="bento-card span-4">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
            <div>
              <span className="metric-sub">Evidence</span>
              <h2 style={{ fontSize: "1.5rem" }}>Traceable inputs</h2>
            </div>
            <Link className="btn btn-secondary" href={`/recommendations/${data.created_from_recommendation_id}`}>
              Back to recommendation
            </Link>
          </div>
          
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "16px" }}>
            {data.evidence.map((evidence) => {
              const href = evidenceHref(evidence.evidence_id, evidence.type);
              return (
                <div key={evidence.evidence_id} style={{
                  padding: "20px",
                  background: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid var(--border-light)",
                  borderRadius: "var(--radius-sm)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px"
                }}>
                  <span className="metric-sub">{evidence.type}</span>
                  <strong style={{ fontSize: "1.1rem" }}>{evidence.title}</strong>
                  {href ? (
                    <Link href={href} style={{
                      color: "var(--accent-blue)",
                      fontSize: "0.85rem",
                      textDecoration: "underline",
                      textUnderlineOffset: "4px",
                      marginTop: "8px",
                      width: "fit-content"
                    }}>
                      {evidence.evidence_id}
                    </Link>
                  ) : (
                    <span style={{ color: "var(--text-tertiary)", fontSize: "0.85rem", marginTop: "8px" }}>
                      {evidence.evidence_id}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </article>
      </section>
    </div>
  );
}
