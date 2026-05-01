import Link from "next/link";
import type { Route } from "next";

import { getThemeDetail } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Theme Detail" };

type ThemePageProps = {
  params: Promise<{ themeKey: string }>;
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function recommendationHref(recommendationId: string | null) {
  return recommendationId ? (`/recommendations/${recommendationId}` as Route) : null;
}

function thesisHref(thesisId: string | null) {
  return thesisId ? (`/theses/${thesisId}` as Route) : null;
}

function evidenceHref(evidenceId: string | null) {
  return evidenceId ? (`/ai-evidence/${evidenceId}` as Route) : null;
}

function sourceDocumentHref(documentId: string | null) {
  return documentId ? (`/source-documents/${documentId}` as Route) : null;
}

export default async function ThemePage({ params }: ThemePageProps) {
  const { themeKey } = await params;
  const response = await getThemeDetail(themeKey);
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          Theme • {data.strategy_name} • {data.horizon_type} • {data.as_of_date}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>{data.theme_name}</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "760px" }}>
              Theme detail connects cycle state to concrete instruments and supporting events. It is context for thesis
              review, not a standalone buy signal.
            </p>
          </div>
          <div style={{
            padding: "20px 32px",
            background: "rgba(16, 185, 129, 0.1)",
            border: "1px solid rgba(16, 185, 129, 0.2)",
            borderRadius: "var(--radius-md)",
            textAlign: "center",
          }}>
            <span className="metric-sub" style={{ color: "var(--accent-green)" }}>Cycle State</span>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0", textTransform: "uppercase" }}>
              {data.state}
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--accent-green)", fontWeight: 500 }}>
              {formatPercent(data.confidence)} confidence
            </div>
          </div>
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card">
          <span className="metric-label">Cycle Score</span>
          <strong className="metric-value">{formatPercent(data.cycle_score)}</strong>
          <span className="metric-sub">current read model</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">Event Heat</span>
          <strong className="metric-value">{formatPercent(data.features.event_intensity ?? 0)}</strong>
          <span className="metric-sub">event intensity</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">Momentum</span>
          <strong className="metric-value">{formatPercent(data.features.price_momentum ?? 0)}</strong>
          <span className="metric-sub">price feature</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">Fundamental</span>
          <strong className="metric-value">{formatPercent(data.features.fundamental_quality ?? 0)}</strong>
          <span className="metric-sub">quality feature</span>
        </article>
      </section>

      <section className="bento-grid reveal delay-2">
        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Cycle history</span>
            <h2 style={{ fontSize: "1.5rem" }}>State transitions</h2>
          </div>
          <div className="bento-list">
            {data.cycle_history.map((snapshot) => (
              <div className="bento-list-item" key={snapshot.as_of_date}>
                <div>
                  <strong>{snapshot.state}</strong>
                  <span>{snapshot.as_of_date}</span>
                </div>
                <div style={{ alignItems: "flex-end" }}>
                  <strong>{formatPercent(snapshot.confidence)}</strong>
                  <span>confidence</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Linked instruments</span>
            <h2 style={{ fontSize: "1.5rem" }}>Theme exposure</h2>
          </div>
          <div className="bento-list">
            {data.linked_instruments.map((instrument) => {
              const recommendationLink = recommendationHref(instrument.latest_recommendation_id);
              const linkedThesisHref = thesisHref(instrument.active_thesis_id);

              return (
                <div className="bento-list-item" key={instrument.instrument_id} style={{ alignItems: "flex-start" }}>
                  <div>
                    <strong>{instrument.symbol}</strong>
                    <span>{formatPercent(instrument.membership_strength)} membership</span>
                  </div>
                  <div style={{ flexDirection: "row", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                    {recommendationLink ? (
                      <Link className="btn btn-secondary" href={recommendationLink}>
                        Recommendation
                      </Link>
                    ) : null}
                    {linkedThesisHref ? (
                      <Link className="btn btn-secondary" href={linkedThesisHref}>
                        Thesis
                      </Link>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>
        </article>

        <article className="bento-card span-4">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px", gap: "16px", flexWrap: "wrap" }}>
            <div>
              <span className="metric-sub">Supporting events</span>
              <h2 style={{ fontSize: "1.5rem" }}>Evidence behind the theme</h2>
            </div>
            <Link className="btn btn-secondary" href="/events">
              Open event map
            </Link>
          </div>
          <div className="bento-list">
            {data.supporting_events.map((event) => {
              const evidenceLink = evidenceHref(event.ai_evidence_id);
              const documentLink = sourceDocumentHref(event.source_document_id);

              return (
                <div className="bento-list-item" key={event.event_id} style={{ alignItems: "flex-start" }}>
                  <div style={{ flex: 1 }}>
                    <span className="metric-sub">{event.symbol} • {event.event_at}</span>
                    <strong>{event.title}</strong>
                  </div>
                  <div style={{ alignItems: "flex-end", gap: "8px" }}>
                    <strong style={{ color: "var(--accent-green)", textTransform: "uppercase" }}>
                      {event.impact_direction}
                    </strong>
                    <span>{formatPercent(event.impact_score)} impact</span>
                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                      {evidenceLink ? (
                        <Link className="btn btn-secondary" href={evidenceLink}>
                          AI Evidence
                        </Link>
                      ) : null}
                      {documentLink ? (
                        <Link className="btn btn-secondary" href={documentLink}>
                          Source Doc
                        </Link>
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </article>

        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Operator guardrails</span>
            <h2 style={{ fontSize: "1.5rem" }}>How to read this theme</h2>
          </div>
          <ul style={{ margin: 0, paddingLeft: "20px", color: "var(--text-secondary)", display: "flex", flexDirection: "column", gap: "12px", lineHeight: 1.6 }}>
            {data.operator_notes.map((note) => (
              <li key={note} style={{ color: "var(--text-primary)" }}>{note}</li>
            ))}
          </ul>
        </article>
      </section>
    </div>
  );
}
