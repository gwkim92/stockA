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

function isKnownThemeEventSymbol(value: string | null | undefined) {
  return Boolean(value && value !== "UNKNOWN" && value !== "UNCLASSIFIED");
}

function themeEventSymbolLabel(value: string | null | undefined) {
  return isKnownThemeEventSymbol(value) ? koCode(value) : "시장·테마 뉴스";
}

export default async function ThemePage({ params }: ThemePageProps) {
  const { themeKey } = await params;
  const response = await getThemeDetail(themeKey);
  const data = response.data;
  const hasThemeEvidence =
    data.linked_instruments.length > 0 || data.supporting_events.length > 0 || data.cycle_history.length > 0;
  const hasCycleSnapshot =
    data.cycle_history.length > 0 && data.state !== "unknown" && data.state !== "unavailable";
  const themeDisplayName = koCode(data.theme_key);

  return (
    <div className="pageStack decision-page">
      <section className="decision-brief reveal" aria-labelledby="theme-detail-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">
            테마 · {koCode(data.strategy_name)} · {koCode(data.horizon_type)} · {data.as_of_date}
          </span>
          <h1 className="decision-brief-title" id="theme-detail-title">
            {themeDisplayName} · {hasCycleSnapshot ? koCode(data.state) : "사이클 측정 전"}
          </h1>
          <p className="decision-brief-copy">
            테마 화면은 독립 매수 신호가 아니다. 사이클 상태를 실제 종목, 이벤트, 추천, 투자 논리와 연결해 검토 맥락으로 사용한다.
          </p>
          <div className="decision-brief-meta" aria-label="테마 상세 핵심 상태">
            <span>신뢰도 {hasCycleSnapshot ? formatPercent(data.confidence) : "대기"}</span>
            <span>연결 종목 {data.linked_instruments.length.toLocaleString("ko-KR")}개</span>
            <span>이벤트 {data.supporting_events.length.toLocaleString("ko-KR")}개</span>
            <span>이력 {data.cycle_history.length.toLocaleString("ko-KR")}개</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <a className={hasCycleSnapshot ? "decision-card is-good" : "decision-card is-watch"} href="#theme-cycle-history">
            <span>사이클 상태</span>
            <strong>{hasCycleSnapshot ? koCode(data.state) : "측정 전"}</strong>
            <small>{hasCycleSnapshot ? `점수 ${formatPercent(data.cycle_score)} · 신뢰도 ${formatPercent(data.confidence)}` : "사이클 배치 완료 후 상태가 표시된다."}</small>
            <b>이력 보기</b>
          </a>
          <a className={data.linked_instruments.length > 0 ? "decision-card is-good" : "decision-card is-watch"} href="#theme-linked-instruments">
            <span>연결 종목</span>
            <strong>{data.linked_instruments.length.toLocaleString("ko-KR")}개</strong>
            <small>테마가 어떤 종목에 노출되는지 확인한다.</small>
            <b>종목 보기</b>
          </a>
          <a className={data.supporting_events.length > 0 ? "decision-card is-good" : "decision-card is-watch"} href="#theme-supporting-events">
            <span>뉴스·이벤트</span>
            <strong>{data.supporting_events.length.toLocaleString("ko-KR")}개</strong>
            <small>원천 뉴스와 AI 근거가 테마 상태를 뒷받침하는지 본다.</small>
            <b>근거 보기</b>
          </a>
          <Link className={hasThemeEvidence ? "decision-card" : "decision-card is-watch"} href={"/cycle-map" as Route}>
            <span>상위 흐름</span>
            <strong>흐름 지도</strong>
            <small>거시·도메인·테마·종목 경로를 지도에서 이어서 확인한다.</small>
            <b>지도 열기</b>
          </Link>
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

      <section className="theme-evidence-panel reveal delay-2" aria-label={`${themeDisplayName} 판단 근거 흐름`}>
        <div className="theme-evidence-head">
          <div>
            <span className="metric-sub">테마 판단 흐름</span>
            <h2>사이클 변화, 노출 종목, 근거 이벤트를 한 번에 본다</h2>
          </div>
          <p>
            이 영역은 테마가 왜 현재 상태로 해석됐는지 확인하는 곳이다. 테마 상태는 자동 매수 신호가 아니며,
            종목·추천·투자 논리와 연결해 보조 근거로만 사용한다.
          </p>
        </div>

        <div className="theme-evidence-grid">
          <article className="theme-evidence-card" id="theme-cycle-history">
            <div className="theme-evidence-card-head">
              <span>1. 사이클 변화</span>
              <strong>상태 전환 이력</strong>
            </div>
            <div className="theme-cycle-track">
              {data.cycle_history.length === 0 ? (
                <p className="theme-evidence-empty">
                  아직 이 테마의 사이클 이력이 없다. 상위 흐름이나 뉴스는 먼저 이벤트 화면에 쌓이고,
                  사이클 배치가 완료되면 상태 전환 이력이 생성된다.
                </p>
              ) : null}
              {data.cycle_history.map((snapshot) => (
                <div className="theme-cycle-step" key={snapshot.as_of_date}>
                  <span>{snapshot.as_of_date}</span>
                  <strong>{koCode(snapshot.state)}</strong>
                  <small>신뢰도 {formatPercent(snapshot.confidence)}</small>
                </div>
              ))}
            </div>
          </article>

          <article className="theme-evidence-card" id="theme-linked-instruments">
            <div className="theme-evidence-card-head">
              <span>2. 종목 노출</span>
              <strong>이 테마에 연결된 종목</strong>
            </div>
            <div className="theme-instrument-grid">
              {data.linked_instruments.length === 0 ? (
                <p className="theme-evidence-empty">
                  이 기준일에 테마와 직접 연결된 종목이 없다. 거시 뉴스라면 개별 종목을 억지로 붙이지 않고
                  상위 흐름으로 먼저 저장한다.
                </p>
              ) : null}
              {data.linked_instruments.map((instrument) => {
                const recommendationLink = recommendationHref(instrument.latest_recommendation_id);
                const linkedThesisHref = thesisHref(instrument.active_thesis_id);

                return (
                  <div className="theme-instrument-card" key={instrument.instrument_id}>
                    <div>
                      <span>노출 종목</span>
                      <strong>{instrument.symbol}</strong>
                      <small>테마 연결 강도 {formatPercent(instrument.membership_strength)}</small>
                    </div>
                    <div className="mini-link-stack">
                      {recommendationLink ? <Link href={recommendationLink}>추천</Link> : null}
                      {linkedThesisHref ? <Link href={linkedThesisHref}>투자 논리</Link> : null}
                    </div>
                  </div>
                );
              })}
            </div>
          </article>
        </div>

        <article className="theme-event-panel" id="theme-supporting-events">
          <div className="theme-evidence-card-head horizontal">
            <div>
              <span>3. 근거 이벤트</span>
              <strong>테마 상태를 뒷받침한 뉴스·공시</strong>
            </div>
            <Link className="btn btn-secondary" href="/events">
              이벤트 지도 열기
            </Link>
          </div>
          <div className="theme-event-grid">
            {data.supporting_events.length === 0 ? (
              <p className="theme-evidence-empty">
                아직 이 테마를 뒷받침하는 이벤트가 없다. 뉴스 수집과 품질 기준을 통과한 이벤트만 이 목록에 표시된다.
              </p>
            ) : null}
            {data.supporting_events.map((event) => {
              const evidenceLink = evidenceHref(event.ai_evidence_id);
              const documentLink = sourceDocumentHref(event.source_document_id);

              return (
                <div className="theme-event-card" key={event.event_id}>
                  <div>
                    <span>{themeEventSymbolLabel(event.symbol)} · {event.event_at}</span>
                    <strong>{koLabel(event.title)}</strong>
                  </div>
                  <div className="theme-event-metrics">
                    <span>{koCode(event.impact_direction)}</span>
                    <span>영향도 {formatPercent(event.impact_score)}</span>
                  </div>
                  <div className="mini-link-stack">
                    {evidenceLink ? <Link href={evidenceLink}>AI 근거</Link> : null}
                    {documentLink ? <Link href={documentLink}>원천 문서</Link> : null}
                  </div>
                </div>
              );
            })}
          </div>
        </article>

        <div className="theme-guardrail-grid">
          {data.operator_notes.map((note) => (
            <article key={note}>
              <span>사용 경계</span>
              <p>{koLabel(note)}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
