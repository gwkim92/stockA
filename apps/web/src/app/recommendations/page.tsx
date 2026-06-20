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

function userFacingText(value: string | null | undefined) {
  if (!value) {
    return "";
  }
  return koCode(value)
    .replaceAll("paper validation", "가상 매매 검증")
    .replaceAll("Paper validation", "가상 매매 검증")
    .replaceAll("페이퍼 검증", "가상 매매 검증")
    .replaceAll("broker flow", "실거래 연결")
    .replaceAll("broker submit", "증권사 주문 제출")
    .replaceAll("order boundary", "실거래 제한")
    .replaceAll("read_only_no_order", "읽기 전용, 실거래 주문 차단")
    .replaceAll("source blocker", "원천 근거 부족")
    .replaceAll("AI/이벤트", "뉴스·투자 근거")
    .replaceAll("AI·이벤트", "뉴스·투자 근거")
    .replaceAll("뉴스·AI 해석", "뉴스·투자 근거")
    .replaceAll(["페", "이퍼"].join(""), "가상 매매");
}

function qualityLabel(row: RecommendationRow) {
  if (row.evidence.quality_status === "ai_review_passed" || row.evidence.quality_status === "ready_for_human_review") {
    return "품질 기준 통과";
  }
  if (row.evidence.quality_status === "blocked") {
    return "근거 부족";
  }
  return koCode(row.evidence.quality_status);
}

function qualityTone(row: RecommendationRow) {
  if (row.evidence.quality_status === "ai_review_passed" || row.evidence.quality_status === "ready_for_human_review") {
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
      ? `뉴스·공시 근거 ${row.evidence.ai_or_event_component_count}개`
      : "뉴스·공시 근거 없음";
  const macroFlowText =
    row.evidence.macro_flow_evidence_count > 0
      ? `상위 흐름 전파 ${row.evidence.macro_flow_evidence_count}개`
      : row.evidence.macro_flow_component_count > 0
        ? `상위 흐름 점수 ${row.evidence.macro_flow_component_count}개`
      : "상위 흐름 전파 없음";
  const outcomeText =
    row.outcome.label === "unmeasured"
      ? "성과 미측정"
      : `성과 ${koCode(row.outcome.label)} · 알파 ${formatPercent(row.outcome.alpha)}`;
  return `${thesisText} · ${evidenceText} · ${macroFlowText} · ${outcomeText}`;
}

function macroFlowBadge(row: RecommendationRow) {
  if (row.evidence.macro_flow_evidence_count > 0) {
    return `상위 흐름 ${row.evidence.macro_flow_evidence_count}개`;
  }
  if (row.evidence.macro_flow_component_count > 0) {
    return `흐름 점수 ${row.evidence.macro_flow_component_count}개`;
  }
  return "상위 흐름 없음";
}

function boundaryLabel(status: string) {
  if (status === "decision_review_ready") {
    return "근거 충족";
  }
  if (status === "paper_validation_pending") {
    return "가상 매매 검증 대기";
  }
  if (status === "blocked_missing_thesis") {
    return "투자 논리 차단";
  }
  if (status === "blocked_missing_score_components") {
    return "점수 근거 차단";
  }
  if (status === "blocked_missing_ai_or_event_evidence") {
    return "뉴스 근거 차단";
  }
  return koCode(status);
}

function boundaryTone(status: string) {
  if (status === "decision_review_ready") {
    return "risk-low";
  }
  if (status === "paper_validation_pending") {
    return "risk-medium";
  }
  return "risk-high";
}

function evidenceQualityLabel(row: RecommendationRow) {
  if (row.evidence_quality.status === "ready_for_review") {
    return "근거 연결";
  }
  if (row.evidence_quality.status === "source_blocked") {
    return "원천 차단";
  }
  if (row.evidence_quality.status === "paper_validation_pending") {
    return "성과 대기";
  }
  if (row.evidence_quality.status === "coverage_gap") {
    return "근거 보강";
  }
  return "근거 확인";
}

function evidenceQualityTone(row: RecommendationRow) {
  if (row.evidence_quality.status === "ready_for_review") {
    return "risk-low";
  }
  if (row.evidence_quality.status === "source_blocked") {
    return "risk-high";
  }
  return "risk-medium";
}

function evidenceQualitySummary(row: RecommendationRow) {
  const quality = row.evidence_quality;
  const coverage = formatPercent(quality.coverage_ratio);
  const missing =
    quality.missing_layer_labels.length > 0
      ? `빠진 근거: ${quality.missing_layer_labels.slice(0, 3).map(userFacingText).join(", ")}${quality.missing_layer_labels.length > 3 ? " 외" : ""}`
      : "빠진 핵심 근거 없음";
  return `근거 감사 ${coverage} · 완료 ${quality.available_layer_count}/${quality.expected_layer_count} · ${missing}`;
}

export default async function RecommendationsPage() {
  const response = await getRecommendations();
  const data = response.data;
  const topRecommendation = data.recommendations[0] ?? null;
  const recommendationCommandCards = [
    {
      index: "01",
      label: "추천 신호",
      title:
        data.recommendation_count > 0
          ? `${data.recommendation_count.toLocaleString("ko-KR")}개 신호`
          : "추천 신호 없음",
      metric:
        topRecommendation !== null
          ? `상위 신호 ${topRecommendation.symbol} · 점수 ${formatPercent(topRecommendation.score)}`
          : `평균 점수 ${formatPercent(data.summary.average_score)}`,
      body:
        data.recommendation_count > 0
          ? "중장기 확인 대상이다. 이 신호만으로 주문하지 않고 상세 근거, 보유 상태, 성과 측정창을 함께 확인한다."
          : "추천 생성 작업이 아직 신호를 만들지 않았다. 먼저 데이터 수집과 추천 배치 상태를 확인한다.",
      href: "#recommendation-list",
      cta: data.recommendation_count > 0 ? "신호 목록 보기" : "목록 확인",
      tone: data.recommendation_count > 0 ? "watch" : "block",
    },
    {
      index: "02",
      label: "가상 매매 대기",
      title:
        data.summary.paper_validation_pending_count > 0
          ? "가상 검증 대기"
          : data.summary.decision_review_ready_count > 0
            ? "근거 충족"
            : "근거 입력 부족",
      metric: `${data.summary.paper_validation_pending_count.toLocaleString("ko-KR")}개 대기 · ${data.summary.decision_review_ready_count.toLocaleString("ko-KR")}개 근거 충족`,
      body:
        data.summary.paper_validation_pending_count > 0
          ? "추천 신호가 곧바로 주문으로 가지 않고 가상 매매 검증과 보유 상태 확인을 기다리는 상태다."
          : "가상 매매 입력 대상이 없거나 근거 입력이 부족하다. 추천 상세에서 어떤 근거가 빠졌는지 본다.",
      href: "/paper-trading",
      cta: "가상 매매 상태 보기",
      tone: data.summary.paper_validation_pending_count > 0 ? "watch" : "ready",
    },
    {
      index: "03",
      label: "주문 차단",
      title:
        data.summary.order_blocked_count > 0
          ? "실제 주문은 차단"
          : "주문 전환 미개방",
      metric: `${data.summary.order_blocked_count.toLocaleString("ko-KR")}개 주문 차단`,
      body:
        data.summary.order_blocked_count > 0
          ? "목록의 추천은 읽기 전용이다. 증권사 주문 제출, 자동 주문, 추천 산식 변경은 이 화면에서 열리지 않는다."
          : "차단 수가 0이어도 이 화면에는 주문 기능이 없다. 실거래는 별도 승인된 실거래 연결에서만 다룬다.",
      href: "/trading-readiness",
      cta: "실거래 제한 보기",
      tone: data.summary.order_blocked_count > 0 ? "block" : "watch",
    },
    {
      index: "04",
      label: "전문 분석 근거",
      title:
        data.summary.evidence_quality_ready_count > 0
          ? "근거 연결됨"
          : data.summary.evidence_quality_source_blocked_count > 0
            ? "원천 차단 있음"
            : data.summary.paper_validation_pending_count > 0
              ? "성과 검증 대기"
          : "근거 보강 필요",
      metric: `완료 ${data.summary.evidence_quality_ready_count.toLocaleString("ko-KR")}개 · 보강/대기 ${data.summary.evidence_quality_gap_count.toLocaleString("ko-KR")}개 · 원천 차단 ${data.summary.evidence_quality_source_blocked_count.toLocaleString("ko-KR")}개`,
      body:
        data.summary.evidence_quality_source_blocked_count > 0
          ? "원천 차단 추천은 전문 판단과 가상 매매 입력에서 제외한다. 먼저 어떤 원천이 막혔는지 확인한다."
          : data.summary.evidence_quality_ready_count > 0
            ? "추천 상세에서 재무·밸류에이션·뉴스·사이클 근거가 어디까지 연결됐는지 확인한다."
            : data.summary.paper_validation_pending_count > 0
              ? "핵심 근거가 연결된 추천도 성과 측정창이 끝나기 전에는 weight 변경과 실거래 주문으로 넘기지 않는다."
            : "투자 논리나 근거가 연결되지 않은 신호는 전문 분석 입력으로 쓰면 안 된다.",
      href: topRecommendation ? recommendationHref(topRecommendation.recommendation_id) : "#recommendation-list",
      cta: "근거 추적",
      tone:
        data.summary.evidence_quality_source_blocked_count > 0
          ? "block"
          : data.summary.evidence_quality_ready_count > 0
            ? "ready"
            : "block",
    },
  ];

  return (
    <div className="pageStack decision-page">
      <section className="decision-brief reveal" aria-labelledby="recommendations-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">
            추천 상황실 · {data.as_of_date || "기준일 미정"} · {koCode(data.strategy_name)} · {koCode(data.horizon_type)}
          </span>
          <h1 className="decision-brief-title" id="recommendations-title">
            오늘 먼저 볼 추천: {topRecommendation ? topRecommendation.symbol : "신호 대기"}
          </h1>
          <p className="decision-brief-copy">
            추천은 주문이 아니라 중장기 검토 신호다. 점수, 투자 논리, 뉴스·투자 근거, 가상 매매 대기, 실거래 차단 상태를 분리해서 본다.
          </p>
          <div className="decision-brief-meta" aria-label="추천 목록 핵심 상태">
            <span>추천 {data.recommendation_count.toLocaleString("ko-KR")}개</span>
            <span>가상 대기 {data.summary.paper_validation_pending_count.toLocaleString("ko-KR")}개</span>
            <span>주문 차단 {data.summary.order_blocked_count.toLocaleString("ko-KR")}개</span>
            <span>원천 차단 {data.summary.evidence_quality_source_blocked_count.toLocaleString("ko-KR")}개</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          {recommendationCommandCards.map((card) => (
            <a
              className={`decision-card ${
                card.tone === "ready" ? "is-good" : card.tone === "watch" ? "is-watch" : "is-block"
              }`}
              href={card.href}
              key={card.index}
            >
              <span>{card.label}</span>
              <strong>{card.title}</strong>
              <small>{card.metric} · {card.body}</small>
              <b>{card.cta}</b>
            </a>
          ))}
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-2" id="recommendation-list" aria-labelledby="recommendation-list-title">
        <div className="section-heading">
          <div>
            <span className="metric-sub">추천 목록</span>
            <h2 id="recommendation-list-title">최신 추천 신호를 근거별로 연다</h2>
          </div>
          <div className="mini-link-stack">
            <Link href="/intelligence">뉴스·사이클 근거</Link>
            <Link href="/paper-trading">가상 매매 상태</Link>
            <Link href="/portfolio/coverage">보유 상태</Link>
          </div>
        </div>

        <div className="bento-list">
          {data.recommendations.length === 0 ? (
            <p className="empty-state">
              아직 최신 추천 신호가 없다. 가격·뉴스·사이클 수집이 끝나고 추천 신호가 생성되면 이 목록에 표시된다.
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
                    <span className={row.evidence.macro_flow_evidence_count > 0 ? "risk-tag risk-medium" : "risk-tag"}>
                      {macroFlowBadge(row)}
                    </span>
                    <span className={`risk-tag ${boundaryTone(row.decision_boundary.status)}`}>
                      {boundaryLabel(row.decision_boundary.status)}
                    </span>
                    <span className={`risk-tag ${evidenceQualityTone(row)}`}>
                      {evidenceQualityLabel(row)}
                    </span>
                    <span className="metric-sub">#{row.rank_position} · {koCode(row.bucket)} · {koCode(row.status)}</span>
                  </div>
                  <Link className="stock-symbol-link" href={recommendationHref(row.recommendation_id)}>
                    <strong>{row.symbol} 추천 상세</strong>
                    <small>{row.name}</small>
                  </Link>
                  <p style={{ color: "var(--text-secondary)", margin: "10px 0 0", lineHeight: 1.55 }}>
                    {recommendationSummary(row)}
                  </p>
                  <p style={{ color: "var(--text-secondary)", margin: "8px 0 0", lineHeight: 1.55 }}>
                    사용 가능 범위: {userFacingText(row.decision_boundary.reason)} 실거래 상태는 {userFacingText(row.decision_boundary.order_boundary)}다.
                  </p>
                  <p style={{ color: "var(--text-secondary)", margin: "8px 0 0", lineHeight: 1.55 }}>
                    {evidenceQualitySummary(row)}. {userFacingText(row.evidence_quality.summary)}
                  </p>
                  {row.evidence_quality.missing_layer_labels.length > 0 ? (
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "10px" }}>
                      {row.evidence_quality.missing_layer_labels.slice(0, 5).map((label) => (
                        <span className="risk-tag risk-medium" key={`${row.recommendation_id}-${label}`}>
                          {userFacingText(label)}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  <div className="mini-link-stack" style={{ marginTop: "12px" }}>
                    <Link href={recommendationHref(row.recommendation_id)}>추천 상세</Link>
                    <Link href={stockHref(row.symbol)}>종목 상세</Link>
                    {thesisLink ? <Link href={thesisLink}>투자 논리</Link> : <span>투자 논리 없음</span>}
                    {evidenceLink ? <Link href={evidenceLink}>뉴스·투자 근거</Link> : <span>뉴스·투자 근거 없음</span>}
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
                  <small style={{ color: "var(--text-secondary)" }}>
                    근거 {row.evidence.score_component_count}개 · 흐름 {row.evidence.macro_flow_component_count}개
                  </small>
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </div>
  );
}
