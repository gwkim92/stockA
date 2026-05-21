import Link from "next/link";
import type { Route } from "next";

import { getRecommendations } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import type { RecommendationListData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "추천" };

type RecommendationRow = RecommendationListData["recommendations"][number];

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function recommendationHref(recommendationId: string) {
  return `/recommendations/${encodeURIComponent(recommendationId)}` as Route;
}

function stockHref(symbol: string) {
  return `/stocks/${encodeURIComponent(symbol)}` as Route;
}

function thesisHref(thesisId: string | null) {
  return thesisId ? (`/theses/${encodeURIComponent(thesisId)}` as Route) : null;
}

function evidenceHref(evidenceId: string | null) {
  return evidenceId ? (`/ai-evidence/${encodeURIComponent(evidenceId)}` as Route) : null;
}

function qualityLabel(row: RecommendationRow) {
  if (row.evidence.quality_status === "ready_for_human_review") {
    return "사람 검토 가능";
  }
  if (row.evidence.quality_status === "blocked") {
    return "근거 부족";
  }
  return koCode(row.evidence.quality_status);
}

function qualityTone(row: RecommendationRow) {
  if (row.evidence.quality_status === "ready_for_human_review") {
    return "risk-low";
  }
  if (row.evidence.quality_status === "blocked") {
    return "risk-high";
  }
  return "risk-medium";
}

function recommendationSummary(row: RecommendationRow) {
  const thesisText = row.linked_thesis_id ? "투자 논리 연결" : "투자 논리 없음";
  const evidenceText =
    row.evidence.ai_or_event_component_count > 0
      ? `AI/이벤트 근거 ${row.evidence.ai_or_event_component_count}개`
      : "AI/이벤트 근거 없음";
  const outcomeText =
    row.outcome.label === "unmeasured"
      ? "성과 미측정"
      : `성과 ${koCode(row.outcome.label)} · 알파 ${formatPercent(row.outcome.alpha)}`;
  return `${thesisText} · ${evidenceText} · ${outcomeText}`;
}

export default async function RecommendationsPage() {
  const response = await getRecommendations();
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="page-hero reveal" aria-labelledby="recommendations-title">
        <div className="bento-badge">추천 상황실 • 중장기 후보 검토</div>
        <h1 id="recommendations-title">지금 시스템이 어떤 종목을 왜 추천 후보로 보는지 확인한다.</h1>
        <p>
          이 화면은 주문 화면이 아니다. 최신 추천 배치의 점수, 근거, 투자 논리, 성과 측정 상태를 한 번에 보여주고
          사람이 상세 검토할 항목을 고르는 읽기 전용 관제 화면이다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="추천 요약">
        <div className="rail-cell">
          <span>추천 후보</span>
          <strong>{data.recommendation_count.toLocaleString("ko-KR")}</strong>
          <small>{data.as_of_date || "기준일 없음"}</small>
        </div>
        <div className="rail-cell">
          <span>검토 가능</span>
          <strong>{data.summary.reviewable_count.toLocaleString("ko-KR")}</strong>
          <small>근거와 논리가 연결됨</small>
        </div>
        <div className="rail-cell">
          <span>차단/보강</span>
          <strong>{data.summary.blocked_count.toLocaleString("ko-KR")}</strong>
          <small>근거 부족 또는 논리 미연결</small>
        </div>
        <div className="rail-cell">
          <span>평균 점수</span>
          <strong>{formatPercent(data.summary.average_score)}</strong>
          <small>{koCode(data.strategy_name)} · {koCode(data.horizon_type)}</small>
        </div>
      </section>

      <section className="bento-card reveal delay-2" aria-labelledby="recommendation-flow-title">
        <div className="section-heading">
          <div>
            <span className="metric-sub">운영 흐름</span>
            <h2 id="recommendation-flow-title">추천은 수집 데이터와 AI 근거를 사람이 검토할 형태로 묶은 결과다</h2>
          </div>
          <Link className="btn btn-secondary" href="/intelligence">
            분석 지도 보기
          </Link>
        </div>
        <div className="flow-steps">
          <article className="flow-step">
            <span>1. 수집</span>
            <strong>가격·뉴스·공시</strong>
            <p>스케줄러가 Postgres에 데이터를 쌓고 상태는 데이터 수집 화면에 남긴다.</p>
          </article>
          <article className="flow-step">
            <span>2. 구조화</span>
            <strong>테마·종목·방향</strong>
            <p>뉴스 AI 후보와 저장된 맥락 조회 결과는 검증을 통과해야 추천 근거로 연결된다.</p>
          </article>
          <article className="flow-step">
            <span>3. 추천</span>
            <strong>점수와 논리</strong>
            <p>추천은 주문이 아니라 장기 투자 후보를 검토하기 위한 입력값이다.</p>
          </article>
          <article className="flow-step">
            <span>4. 검토</span>
            <strong>보유·성과 확인</strong>
            <p>보유 검토와 성과 측정이 이어져 추천 품질을 계속 확인한다.</p>
          </article>
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-3" aria-labelledby="recommendation-list-title">
        <div className="section-heading">
          <div>
            <span className="metric-sub">추천 목록</span>
            <h2 id="recommendation-list-title">최신 추천 배치</h2>
          </div>
          <div className="mini-link-stack">
            <Link href="/paper-trading">가상 거래 검토</Link>
            <Link href="/portfolio/coverage">보유 검토</Link>
          </div>
        </div>

        <div className="bento-list">
          {data.recommendations.length === 0 ? (
            <p className="empty-state">
              아직 최신 추천 배치가 없다. 가격·뉴스·사이클 배치가 실행되고 추천 후보가 생성되면 이 목록에 표시된다.
            </p>
          ) : null}
          {data.recommendations.map((row) => {
            const thesisLink = thesisHref(row.linked_thesis_id);
            const evidenceLink = evidenceHref(row.evidence.primary_evidence_id);
            return (
              <article className="bento-list-item" key={row.recommendation_id} style={{ alignItems: "flex-start", gap: "20px" }}>
                <div style={{ flex: "1 1 420px", minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap", marginBottom: "8px" }}>
                    <span className={`risk-tag ${qualityTone(row)}`}>{qualityLabel(row)}</span>
                    <span className="metric-sub">#{row.rank_position} · {koCode(row.bucket)} · {koCode(row.status)}</span>
                  </div>
                  <Link className="stock-symbol-link" href={recommendationHref(row.recommendation_id)}>
                    <strong>{row.symbol} 추천 검토서</strong>
                    <small>{row.name}</small>
                  </Link>
                  <p style={{ color: "var(--text-secondary)", margin: "10px 0 0", lineHeight: 1.55 }}>
                    {recommendationSummary(row)}
                  </p>
                  <div className="mini-link-stack" style={{ marginTop: "12px" }}>
                    <Link href={recommendationHref(row.recommendation_id)}>추천 상세</Link>
                    <Link href={stockHref(row.symbol)}>종목 상세</Link>
                    {thesisLink ? <Link href={thesisLink}>투자 논리</Link> : <span>투자 논리 없음</span>}
                    {evidenceLink ? <Link href={evidenceLink}>AI 근거</Link> : <span>AI 근거 없음</span>}
                  </div>
                </div>
                <div style={{ flex: "0 0 150px", textAlign: "right" }}>
                  <span className="metric-sub">추천 조치</span>
                  <strong style={{ display: "block", color: "var(--text-primary)", marginTop: "4px" }}>{koCode(row.action)}</strong>
                  <small style={{ color: "var(--text-secondary)" }}>목표 비중 {formatPercent(row.recommended_weight)}</small>
                </div>
                <div style={{ flex: "0 0 120px", textAlign: "right" }}>
                  <span className="metric-sub">점수</span>
                  <strong style={{ display: "block", color: "var(--text-primary)", marginTop: "4px" }}>{formatPercent(row.score)}</strong>
                  <small style={{ color: "var(--text-secondary)" }}>근거 {row.evidence.score_component_count}개</small>
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </div>
  );
}
