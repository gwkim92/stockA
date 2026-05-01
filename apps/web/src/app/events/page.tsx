import Link from "next/link";
import type { Route } from "next";

import { getEvents } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Events" };

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function themeHref(themeKey: string) {
  return themeKey === "ANNUAL_REPORTING" ? (`/themes/${themeKey}` as Route) : null;
}

function evidenceHref(evidenceId: string | null) {
  return evidenceId ? (`/ai-evidence/${evidenceId}` as Route) : null;
}

function sourceDocumentHref(documentId: string | null) {
  return documentId ? (`/source-documents/${documentId}` as Route) : null;
}

export default async function EventsPage() {
  const response = await getEvents();
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">Events • {data.as_of_date} • {data.filters.event_type}</div>
        <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>Event Evidence Map</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "760px" }}>
          Events are the bridge between raw documents, theme cycle changes, and thesis review. This page keeps the
          evidence chain visible before any recommendation or portfolio action.
        </p>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card">
          <span className="metric-label">Events</span>
          <strong className="metric-value">{data.summary.event_count}</strong>
          <span className="metric-sub">read model rows</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">AI Extracted</span>
          <strong className="metric-value">{data.summary.ai_extracted_count}</strong>
          <span className="metric-sub">with stored provenance</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">Source Docs</span>
          <strong className="metric-value">{data.summary.source_document_count}</strong>
          <span className="metric-sub">linked to evidence</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">Themes</span>
          <strong className="metric-value">{data.summary.themes_represented}</strong>
          <span className="metric-sub">represented</span>
        </article>
      </section>

      <section className="bento-grid reveal delay-2">
        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Event ledger</span>
            <h2 style={{ fontSize: "1.5rem" }}>Traceable event inputs</h2>
          </div>

          <div className="bento-list">
            {data.events.map((event) => {
              const themeLink = themeHref(event.theme_key);
              const evidenceLink = evidenceHref(event.ai_evidence_id);
              const documentLink = sourceDocumentHref(event.source_document_id);

              return (
                <div className="bento-list-item" key={event.event_id} style={{ alignItems: "flex-start" }}>
                  <div style={{ flex: 1, gap: "8px" }}>
                    <span className="metric-sub">
                      {event.symbol} • {event.event_type} • {event.event_at}
                    </span>
                    <strong style={{ fontSize: "1.05rem" }}>{event.title}</strong>
                    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "6px" }}>
                      {themeLink ? (
                        <Link className="btn btn-secondary" href={themeLink}>
                          {event.theme_key}
                        </Link>
                      ) : (
                        <span className="bento-badge" style={{ margin: 0 }}>{event.theme_key}</span>
                      )}
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
                  <div style={{ alignItems: "flex-end", minWidth: "190px" }}>
                    <strong style={{
                      color: event.impact_direction === "supportive" ? "var(--accent-green)" : "var(--accent-amber)",
                      textTransform: "uppercase",
                    }}>
                      {event.impact_direction}
                    </strong>
                    <span>{formatPercent(event.impact_score)} impact</span>
                    <span>{event.quality_gate}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </article>
      </section>
    </div>
  );
}
