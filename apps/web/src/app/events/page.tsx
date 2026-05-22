import Link from "next/link";
import type { Route } from "next";

import { getEvents } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { EventListData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "이벤트" };

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function themeHref(themeKey: string) {
  return themeKey ? (`/themes/${themeKey}` as Route) : null;
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

type EventRow = EventListData["events"][number];

function isNewsCandidate(event: EventRow) {
  return event.ai_evidence_type === "news_event_candidate";
}

function isNewsClusterSummary(event: EventRow) {
  return event.ai_evidence_type === "news_cluster_summary";
}

function evidenceButtonLabel(event: EventRow) {
  if (isNewsCandidate(event)) {
    return "개별 AI 후보";
  }
  if (isNewsClusterSummary(event)) {
    return "뉴스 묶음 근거";
  }
  return aiEvidenceLabel(event.ai_evidence_type);
}

function evidenceDetail(event: EventRow) {
  if (!event.ai_evidence_provider) {
    return "아직 개별 AI 후보나 묶음 근거가 연결되지 않았다";
  }
  const confidence = event.ai_evidence_confidence === null ? "신뢰도 미제공" : `신뢰도 ${formatPercent(event.ai_evidence_confidence)}`;
  if (isNewsCandidate(event)) {
    return `개별 AI 후보 · ${koCode(event.ai_evidence_provider)} · ${confidence}`;
  }
  if (isNewsClusterSummary(event)) {
    return `뉴스 묶음 근거 · ${koCode(event.ai_evidence_provider)} · ${confidence}`;
  }
  return `${koCode(event.ai_evidence_type)} · ${koCode(event.ai_evidence_provider)} · ${confidence}`;
}

function evidencePurpose(event: EventRow) {
  if (isNewsCandidate(event)) {
    return "이 뉴스 한 건을 AI가 종목, 테마, 방향, 불확실성으로 구조화했다.";
  }
  if (isNewsClusterSummary(event)) {
    return "여러 뉴스를 묶은 보조 근거다. 개별 후보 분석은 아니며 큰 흐름 확인용이다.";
  }
  return "아직 AI 구조화 전이다. 원천 문서와 규칙 기반 분류만 확인한다.";
}

function EventLedgerItem({ event, compact = false }: { event: EventRow; compact?: boolean }) {
  const themeLink = themeHref(event.theme_key);
  const evidenceLink = evidenceHref(event.ai_evidence_id);
  const documentLink = sourceDocumentHref(event.source_document_id);
  const relatedEventsRaw = event.related_events ?? [];
  const relatedEvents = relatedEventsRaw
    .filter((related) => related.relation_type !== "same_theme" || related.relation_strength >= 0.7)
    .slice(0, 3);
  const hiddenBroadThemeCount = Math.max(0, relatedEventsRaw.length - relatedEvents.length);

  return (
    <div className="bento-list-item" style={{ alignItems: "flex-start" }}>
      <div style={{ flex: 1, gap: "8px" }}>
        <span className="metric-sub">
          {koCode(event.symbol)} • {koCode(event.event_type)} • {event.event_at}
        </span>
        <strong style={{ fontSize: compact ? "0.98rem" : "1.05rem" }}>{koLabel(event.title)}</strong>
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
              {evidenceButtonLabel(event)}
            </Link>
          ) : null}
          {documentLink ? (
            <Link className="btn btn-secondary" href={documentLink}>
              원천 문서
            </Link>
          ) : null}
        </div>
        {!compact && relatedEvents.length > 0 ? (
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
            {hiddenBroadThemeCount > 0 ? (
              <p className="relationship-empty">
                넓은 테마만 같은 약한 연결 {hiddenBroadThemeCount}개는 숨겼다.
              </p>
            ) : null}
          </div>
        ) : null}
        {!compact && relatedEvents.length === 0 ? (
          <p className="relationship-empty">
            직접 같은 종목이거나 충분히 강한 관련 이벤트가 아직 없다.
          </p>
        ) : null}
      </div>
      <div style={{ alignItems: "flex-end", minWidth: compact ? "150px" : "190px" }}>
        <strong style={{
          color: event.impact_direction === "supportive" ? "var(--accent-green)" : "var(--accent-amber)",
        }}>
          {koCode(event.impact_direction)}
        </strong>
        <span>영향도 {formatPercent(event.impact_score)}</span>
        <span>{evidenceDetail(event)}</span>
        <span>{compact ? "원장 행: 수집 상태 확인용이다." : evidencePurpose(event)}</span>
        <span>{koCode(event.quality_gate)}</span>
      </div>
    </div>
  );
}

export default async function EventsPage() {
  const [candidateResponse, ledgerResponse] = await Promise.all([
    getEvents({ evidenceType: "news_event_candidate", limit: 24 }),
    getEvents({ limit: 12 }),
  ]);
  const candidateData = candidateResponse.data;
  const ledgerData = ledgerResponse.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          이벤트 판단판 • {ledgerData.as_of_date} • 기본: {koCode(candidateData.filters.evidence_type)}
        </div>
        <h1 style={{ fontSize: "clamp(2.25rem, 4vw, 4.2rem)", marginBottom: "16px" }}>
          먼저 검토할 뉴스 후보부터 본다
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "800px" }}>
          첫 목록은 AI가 한 뉴스 단위로 구조화한 후보만 보여준다. 전체 수집 원장은 아래 보조 영역에 남겨,
          잡음과 원천 데이터까지 필요할 때만 확인한다.
        </p>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card">
          <span className="metric-label">판단 후보</span>
          <strong className="metric-value">{candidateData.summary.event_count}</strong>
          <span className="metric-sub">개별 AI 후보 전체</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">원장 전체</span>
          <strong className="metric-value">{ledgerData.summary.event_count}</strong>
          <span className="metric-sub">수집 이벤트 행</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">뉴스 묶음</span>
          <strong className="metric-value">{ledgerData.summary.news_cluster_summary_count}</strong>
          <span className="metric-sub">흐름 보조 근거</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">미검토</span>
          <strong className="metric-value">{ledgerData.summary.unreviewed_event_count}</strong>
          <span className="metric-sub">AI 근거 미연결</span>
        </article>
      </section>

      <section className="bento-grid reveal delay-2">
        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">기본 판단 목록</span>
            <h2 style={{ fontSize: "1.5rem" }}>AI가 구조화한 개별 뉴스 후보</h2>
            <p className="relationship-empty">
              이 목록은 추천이나 보유검토에 들어가기 전 사람이 먼저 봐야 하는 후보군이다. 뉴스 묶음 근거와 미검토 원장 행은 아래 원장 영역에서 따로 확인한다.
            </p>
          </div>

          {candidateData.events.length > 0 ? (
            <div className="bento-list">
              {candidateData.events.map((event) => (
                <EventLedgerItem event={event} key={event.event_id} />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              아직 개별 뉴스 AI 후보가 없다. 수집 원장은 아래에서 확인하고, 뉴스 AI 추출 배치가 다음 실행에서 후보를 만든다.
            </div>
          )}

          <details className="secondary-details">
            <summary>원장 전체 최신 {ledgerData.events.length}개 보기</summary>
            <p style={{ margin: "14px 0 8px", lineHeight: 1.6 }}>
              이 영역은 디버깅과 출처 확인용이다. 뉴스 묶음 근거와 미검토 row가 섞여 있으므로 투자 판단은 위 기본 목록을 우선한다.
            </p>
            <div className="bento-list">
              {ledgerData.events.map((event) => (
                <EventLedgerItem compact event={event} key={`ledger-${event.event_id}`} />
              ))}
            </div>
          </details>
        </article>
      </section>
    </div>
  );
}
