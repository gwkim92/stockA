import Link from "next/link";
import type { Route } from "next";

import { getEvents } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "이벤트" };

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

function aiEvidenceLabel(type: string | null) {
  if (type === "news_event_candidate") {
    return "뉴스 AI 후보";
  }
  if (type === "news_cluster_summary") {
    return "뉴스 묶음 증거";
  }
  if (type) {
    return koCode(type);
  }
  return "AI 분석 대기";
}

function aiEvidenceDetail(event: { ai_evidence_provider: string | null; ai_evidence_confidence: number | null }) {
  if (!event.ai_evidence_provider) {
    return "구조화 분석이 아직 연결되지 않았다";
  }
  const confidence = event.ai_evidence_confidence === null ? "신뢰도 미제공" : `신뢰도 ${formatPercent(event.ai_evidence_confidence)}`;
  return `${koCode(event.ai_evidence_provider)} · ${confidence}`;
}

export default async function EventsPage() {
  const response = await getEvents();
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">뉴스·이벤트 원장 • {data.as_of_date} • {koCode(data.filters.event_type)}</div>
        <h1 style={{ fontSize: "clamp(2.25rem, 4vw, 4.2rem)", marginBottom: "16px" }}>뉴스가 어떤 근거로 해석됐는지 확인한다</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "760px" }}>
          무료 RSS 뉴스와 공시는 이벤트 원장에 저장되고, 중요한 뉴스는 뉴스 AI 후보로 승격된다.
          각 행의 AI 후보 링크를 열면 AI가 판단한 테마, 종목, 방향, 불확실성을 볼 수 있다.
        </p>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card">
          <span className="metric-label">이벤트</span>
          <strong className="metric-value">{data.summary.event_count}</strong>
          <span className="metric-sub">DB 이벤트 행</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">AI 해석 완료</span>
          <strong className="metric-value">{data.summary.ai_extracted_count}</strong>
          <span className="metric-sub">구조화 분석으로 승격된 건</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">원천 문서</span>
          <strong className="metric-value">{data.summary.source_document_count}</strong>
          <span className="metric-sub">증거에 연결됨</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">테마</span>
          <strong className="metric-value">{data.summary.themes_represented}</strong>
          <span className="metric-sub">연결된 테마</span>
        </article>
      </section>

      <section className="bento-grid reveal delay-2">
        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">이벤트 원장</span>
            <h2 style={{ fontSize: "1.5rem" }}>오늘 수집된 뉴스와 이벤트</h2>
          </div>

          <div className="bento-list">
            {data.events.map((event) => {
              const themeLink = themeHref(event.theme_key);
              const evidenceLink = evidenceHref(event.ai_evidence_id);
              const documentLink = sourceDocumentHref(event.source_document_id);
              const relatedEvents = event.related_events ?? [];

              return (
                <div className="bento-list-item" key={event.event_id} style={{ alignItems: "flex-start" }}>
                  <div style={{ flex: 1, gap: "8px" }}>
                    <span className="metric-sub">
                      {koCode(event.symbol)} • {koCode(event.event_type)} • {event.event_at}
                    </span>
                    <strong style={{ fontSize: "1.05rem" }}>{koLabel(event.title)}</strong>
                    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "6px" }}>
                      {themeLink ? (
                        <Link className="btn btn-secondary" href={themeLink}>
                          {koCode(event.theme_key)}
                        </Link>
                      ) : (
                        <span className="bento-badge" style={{ margin: 0 }}>{koCode(event.theme_key)}</span>
                      )}
                      {evidenceLink ? (
                        <Link className="btn btn-secondary" href={evidenceLink}>
                          {aiEvidenceLabel(event.ai_evidence_type)}
                        </Link>
                      ) : null}
                      {documentLink ? (
                        <Link className="btn btn-secondary" href={documentLink}>
                          원천 문서
                        </Link>
                      ) : null}
                    </div>
                    {relatedEvents.length > 0 ? (
                      <div className="relationship-list" aria-label={`${event.title} 관련 이벤트`}>
                        {relatedEvents.map((related) => (
                          <div className="relationship-chip" key={`${event.event_id}-${related.event_id}`}>
                            <span>{koCode(related.relation_type)}</span>
                            <strong>{koLabel(related.title)}</strong>
                            <small>
                              {koCode(related.symbol)} · {koCode(related.theme_key)} · 강도 {formatPercent(related.relation_strength)}
                            </small>
                            <small>{koLabel(related.reason)}</small>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="relationship-empty">아직 같은 종목·테마로 묶인 관련 이벤트가 없다.</p>
                    )}
                  </div>
                  <div style={{ alignItems: "flex-end", minWidth: "190px" }}>
                    <strong style={{
                      color: event.impact_direction === "supportive" ? "var(--accent-green)" : "var(--accent-amber)",
                    }}>
                      {koCode(event.impact_direction)}
                    </strong>
                    <span>영향도 {formatPercent(event.impact_score)}</span>
                    <span>{aiEvidenceDetail(event)}</span>
                    <span>{koCode(event.quality_gate)}</span>
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
