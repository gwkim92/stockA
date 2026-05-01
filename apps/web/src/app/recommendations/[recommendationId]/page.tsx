import Link from "next/link";
import type { Route } from "next";
import { getRecommendationDetail } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Recommendation Detail" };

type RecommendationPageProps = {
  params: Promise<{ recommendationId: string }>;
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function evidenceHref(evidenceId: string) {
  return evidenceId.startsWith("sec-event-") ? (`/ai-evidence/${evidenceId}` as Route) : null;
}

export default async function RecommendationPage({ params }: RecommendationPageProps) {
  const { recommendationId } = await params;
  const response = await getRecommendationDetail(recommendationId);
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          REC • {data.strategy_name} • {data.horizon_type} • {data.as_of_date}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>{data.symbol} Recommendation Dossier</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
              The recommendation is presented as a scored thesis input, not an autonomous trade command. Outcome and evidence links remain visible before any portfolio action.
            </p>
          </div>
          
          <div style={{ 
            padding: "20px 32px", 
            background: "rgba(59, 130, 246, 0.1)", 
            border: "1px solid rgba(59, 130, 246, 0.2)",
            borderRadius: "var(--radius-md)",
            textAlign: "center"
          }}>
            <span className="metric-sub" style={{ color: "var(--accent-blue)" }}>Overall Score</span>
            <div style={{ fontSize: "2.5rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0" }}>
              {formatPercent(data.score)}
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--accent-blue)", fontWeight: 600, textTransform: "uppercase" }}>
              {data.recommendation}
            </div>
          </div>
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Score Anatomy</span>
            <h2 style={{ fontSize: "1.5rem" }}>{data.score_version}</h2>
          </div>
          
          <div className="bento-list">
            {data.score_components.map((component) => {
              const href = evidenceHref(component.evidence_id);
              return (
                <div className="bento-list-item" key={component.component} style={{ alignItems: "center" }}>
                  <div style={{ width: "40%" }}>
                    <strong style={{ display: "block" }}>{component.component}</strong>
                    {href ? (
                      <Link href={href} style={{ color: "var(--accent-blue)", fontSize: "0.75rem", textDecoration: "underline", textUnderlineOffset: "3px" }}>
                        {component.evidence_id}
                      </Link>
                    ) : (
                      <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>{component.evidence_id}</span>
                    )}
                  </div>
                  <div style={{ flex: 1, textAlign: "right" }}>
                    <strong style={{ fontSize: "1.1rem", color: "var(--text-primary)" }}>{formatPercent(component.value)}</strong>
                  </div>
                  <div style={{ flex: 1, textAlign: "right" }}>
                    <span className="metric-sub">Weight {formatPercent(component.weight)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
            <div>
              <span className="metric-sub">Measured Outcome</span>
              <h2 style={{ fontSize: "1.5rem" }}>{data.outcome.label}</h2>
            </div>
            <Link className="btn btn-primary" href={`/theses/${data.linked_thesis_id}`}>
              Open Linked Thesis
            </Link>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">Alpha</span>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>{formatPercent(data.outcome.alpha)}</div>
            </div>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">Absolute Return</span>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>{formatPercent(data.outcome.absolute_return)}</div>
            </div>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">Benchmark Return</span>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>{formatPercent(data.outcome.benchmark_return)}</div>
            </div>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">Measurement End</span>
              <div style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "4px" }}>{data.outcome.measurement_end_date}</div>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}
