import Link from "next/link";
import type { Route } from "next";

import { getThemeDetail } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "테마 상세" };

type ThemePageProps = {
  params: Promise<{ themeKey: string }>;
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function formatOptionalPercent(value: number | null | undefined) {
  return value === null || value === undefined ? "측정 전" : formatPercent(value);
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
  const hasThemeEvidence =
    data.linked_instruments.length > 0 || data.supporting_events.length > 0 || data.cycle_history.length > 0;
  const hasCycleSnapshot =
    data.cycle_history.length > 0 && data.state !== "unknown" && data.state !== "unavailable";

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          테마 • {koCode(data.strategy_name)} • {koCode(data.horizon_type)} • {data.as_of_date}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>{koLabel(data.theme_name)}</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "760px" }}>
              테마 화면은 사이클 상태를 실제 종목과 보조 이벤트에 연결한다. 독립 매수 신호가 아니라 투자 논리
              검토를 위한 맥락이다.
            </p>
          </div>
          <div style={{
            padding: "20px 32px",
            background: "rgba(16, 185, 129, 0.1)",
            border: "1px solid rgba(16, 185, 129, 0.2)",
            borderRadius: "var(--radius-md)",
            textAlign: "center",
          }}>
            <span className="metric-sub" style={{ color: "var(--accent-green)" }}>사이클 상태</span>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0", textTransform: "uppercase" }}>
              {hasCycleSnapshot ? koCode(data.state) : "측정 전"}
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--accent-green)", fontWeight: 500 }}>
              {hasCycleSnapshot ? `신뢰도 ${formatPercent(data.confidence)}` : "사이클 스냅샷 대기"}
            </div>
          </div>
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card">
          <span className="metric-label">사이클 점수</span>
          <strong className="metric-value">{hasCycleSnapshot ? formatPercent(data.cycle_score) : "측정 전"}</strong>
          <span className="metric-sub">현재 사이클 모델</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">이벤트 강도</span>
          <strong className="metric-value">{formatOptionalPercent(data.features.event_intensity)}</strong>
          <span className="metric-sub">이벤트 강도</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">모멘텀</span>
          <strong className="metric-value">{formatOptionalPercent(data.features.price_momentum)}</strong>
          <span className="metric-sub">가격 모멘텀</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">펀더멘털</span>
          <strong className="metric-value">{formatOptionalPercent(data.features.fundamental_quality)}</strong>
          <span className="metric-sub">펀더멘털 품질</span>
        </article>
      </section>

      <section className="bento-grid reveal delay-2">
        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">사이클 이력</span>
            <h2 style={{ fontSize: "1.5rem" }}>상태 전환</h2>
          </div>
          <div className="bento-list">
            {data.cycle_history.length === 0 ? (
              <p className="empty-state">
                아직 이 테마의 사이클 이력이 없다. 상위 흐름이나 뉴스는 먼저 이벤트 화면에 쌓이고,
                사이클 배치가 완료되면 상태 전환 이력이 생성된다.
              </p>
            ) : null}
            {data.cycle_history.map((snapshot) => (
              <div className="bento-list-item" key={snapshot.as_of_date}>
                <div>
                  <strong>{koCode(snapshot.state)}</strong>
                  <span>{snapshot.as_of_date}</span>
                </div>
                <div style={{ alignItems: "flex-end" }}>
                  <strong>{formatPercent(snapshot.confidence)}</strong>
                  <span>신뢰도</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">연결 종목</span>
            <h2 style={{ fontSize: "1.5rem" }}>테마 노출</h2>
          </div>
          <div className="bento-list">
            {data.linked_instruments.length === 0 ? (
              <p className="empty-state">
                이 기준일에 테마와 직접 연결된 종목이 없다. 거시 뉴스라면 개별 종목을 억지로 붙이지 않고
                상위 흐름으로 먼저 저장한다.
              </p>
            ) : null}
            {data.linked_instruments.map((instrument) => {
              const recommendationLink = recommendationHref(instrument.latest_recommendation_id);
              const linkedThesisHref = thesisHref(instrument.active_thesis_id);

              return (
                <div className="bento-list-item" key={instrument.instrument_id} style={{ alignItems: "flex-start" }}>
                  <div>
                    <strong>{instrument.symbol}</strong>
                    <span>테마 연결 강도 {formatPercent(instrument.membership_strength)}</span>
                  </div>
                  <div style={{ flexDirection: "row", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                    {recommendationLink ? (
                      <Link className="btn btn-secondary" href={recommendationLink}>
                        추천
                      </Link>
                    ) : null}
                    {linkedThesisHref ? (
                      <Link className="btn btn-secondary" href={linkedThesisHref}>
                        투자 논리
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
              <span className="metric-sub">보조 이벤트</span>
              <h2 style={{ fontSize: "1.5rem" }}>테마 뒤의 증거</h2>
            </div>
            <Link className="btn btn-secondary" href="/events">
              이벤트 지도 열기
            </Link>
          </div>
          <div className="bento-list">
            {data.supporting_events.length === 0 ? (
              <p className="empty-state">
                아직 이 테마를 뒷받침하는 이벤트가 없다. 뉴스 수집과 AI 후보 검증을 통과한 이벤트만 이 목록에 표시된다.
              </p>
            ) : null}
            {data.supporting_events.map((event) => {
              const evidenceLink = evidenceHref(event.ai_evidence_id);
              const documentLink = sourceDocumentHref(event.source_document_id);

              return (
                <div className="bento-list-item" key={event.event_id} style={{ alignItems: "flex-start" }}>
                  <div style={{ flex: 1 }}>
                    <span className="metric-sub">{event.symbol} • {event.event_at}</span>
                    <strong>{koLabel(event.title)}</strong>
                  </div>
                  <div style={{ alignItems: "flex-end", gap: "8px" }}>
                    <strong style={{ color: "var(--accent-green)", textTransform: "uppercase" }}>
                      {koCode(event.impact_direction)}
                    </strong>
                    <span>영향도 {formatPercent(event.impact_score)}</span>
                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                      {evidenceLink ? (
                        <Link className="btn btn-secondary" href={evidenceLink}>
                          AI 증거
                        </Link>
                      ) : null}
                      {documentLink ? (
                        <Link className="btn btn-secondary" href={documentLink}>
                          원천 문서
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
            <span className="metric-sub">운영 안전장치</span>
            <h2 style={{ fontSize: "1.5rem" }}>이 테마를 읽는 방법</h2>
          </div>
          <ul style={{ margin: 0, paddingLeft: "20px", color: "var(--text-secondary)", display: "flex", flexDirection: "column", gap: "12px", lineHeight: 1.6 }}>
            {data.operator_notes.map((note) => (
              <li key={note} style={{ color: "var(--text-primary)" }}>{koLabel(note)}</li>
            ))}
          </ul>
        </article>
      </section>
    </div>
  );
}
