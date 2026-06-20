import type { Route } from "next";
import Link from "next/link";

import { getPortfolioCoverage, getTradingReadiness } from "@/lib/frontend-api";
import { koCode, koLabel, koReason } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "보유·리스크 상태" };

const USER_FACING_REPLACEMENTS: Array<[string, string]> = [
  ["read_only_no_order", "읽기 전용, 실거래 주문 차단"],
  ["broker submit", "증권사 주문 제출"],
  ["broker", "증권사"],
  ["order boundary", "실거래 상태"],
  ["order_boundary", "실거래 상태"],
  ["eval_run_id", "검증 기록"],
  ["source_cadence_eval_run_id", "실행 주기 기록"],
  ["active share", "벤치마크와 다른 비중"],
  ["drift", "벤치마크 괴리"],
  ["benchmark", "벤치마크"],
  ["runner", "실행 기록"],
  ["child runner", "후속 실행 기록"],
  ["artifact", "결과 기록"],
  ["paper validation", "가상 매매 검증"],
  ["Paper validation", "가상 매매 검증"],
  ["blocked", "차단"],
  ["pending", "대기"],
  ["no_op", "대기"],
  ["weight review", "추천 산식 변경 여부"],
  ["weight", "비중"],
  ["가중치", "추천 산식 반영 비중"],
  ["주문 경계", "실거래 상태"],
  [["페", "이퍼"].join(""), "가상 매매"],
  ["가상 거래", "가상 매매"],
  ["커버리지", "연결 상태"],
  ["커버됨", "연결됨"],
];

const USER_FACING_CODES: Record<string, string> = {
  add_blocked_until_evidence: "근거 보강 전 증액 금지",
  benchmark_drift_review: "벤치마크 괴리 확인",
  contradicted: "반박됨",
  execute_calibration: "누적평가 실행",
  execute_feedback: "사후평가 실행",
  has_contradictions: "반박 근거 있음",
  hold_with_thesis: "투자 논리 유지",
  needs_more_data: "추가 성과 필요",
  needs_position_review: "비중 확인 필요",
  needs_thesis_update: "투자 논리 보강",
  no_op_wait_for_outcome_window: "성과 관찰 기간 대기",
  reduce_review: "축소 필요성 확인",
  reduce_watch: "축소 관찰",
  review_required: "확인 필요",
  run_calibration_now: "누적평가 실행 필요",
  run_feedback_now: "사후평가 실행 필요",
  too_early: "관찰 기간 부족",
  validated: "검증됨",
  watch_small_position: "작은 비중 관찰",
  within_budget: "한도 내",
};

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function recordString(record: Record<string, unknown> | undefined, key: string) {
  const value = record?.[key];
  return typeof value === "string" ? value : "";
}

function recordNumber(record: Record<string, unknown> | undefined, key: string) {
  const value = record?.[key];
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function userFacingText(value: string | number | boolean | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  if (typeof value === "number") {
    return value.toLocaleString("ko-KR");
  }
  if (typeof value === "boolean") {
    return value ? "예" : "아니오";
  }
  if (USER_FACING_CODES[value]) {
    return USER_FACING_CODES[value];
  }
  let text = koReason(koLabel(koCode(value)));
  for (const [from, to] of USER_FACING_REPLACEMENTS) {
    text = text.replaceAll(from, to);
  }
  return text;
}

function recordPresent(value: string | null | undefined) {
  return value ? "기록 있음" : "기록 없음";
}

function orderBoundaryLabel(value: string | null | undefined) {
  if (!value) {
    return "실거래 상태 미기록";
  }
  if (value === "read_only_no_order") {
    return "읽기 전용, 실거래 주문 차단";
  }
  return userFacingText(value);
}

function riskBudgetLabel(status: string) {
  if (status === "within_budget") {
    return "한도 내";
  }
  if (status === "needs_position_review") {
    return "비중 확인 필요";
  }
  if (status === "missing_position_snapshot") {
    return "스냅샷 없음";
  }
  return userFacingText(status);
}

function sizeStatusLabel(status: string) {
  if (status === "within_budget") {
    return "한도 내";
  }
  if (status === "below_rebalance_floor") {
    return "작은 비중";
  }
  if (status === "over_single_position_limit") {
    return "한도 초과";
  }
  if (status === "missing_weight") {
    return "비중 없음";
  }
  return userFacingText(status);
}

function sizeStatusClass(status: string) {
  if (status === "over_single_position_limit") {
    return "risk-high";
  }
  if (status === "below_rebalance_floor" || status === "missing_weight") {
    return "risk-medium";
  }
  return "risk-low";
}

function concentrationStatusLabel(status: string) {
  if (status === "within_budget") {
    return "집중도 한도 내";
  }
  if (status === "needs_concentration_review") {
    return "집중도 확인 필요";
  }
  if (status === "classification_gap") {
    return "분류 보강 필요";
  }
  if (status === "missing_position_snapshot") {
    return "스냅샷 없음";
  }
  return userFacingText(status);
}

function concentrationStatusClass(status: string) {
  if (status === "needs_concentration_review") {
    return "risk-high";
  }
  if (status === "classification_gap" || status === "missing_position_snapshot") {
    return "risk-medium";
  }
  return "risk-low";
}

function exposureStatusLabel(status: string) {
  if (status === "over_limit") {
    return "한도 초과";
  }
  if (status === "within_limit") {
    return "한도 내";
  }
  return userFacingText(status);
}

function candidateSeverityClass(severity: string) {
  if (severity === "high") {
    return "risk-high";
  }
  if (severity === "medium") {
    return "risk-medium";
  }
  return "risk-low";
}

function candidateDirectionLabel(direction: string) {
  if (direction === "overweight") {
    return "과대 보유";
  }
  if (direction === "underweight") {
    return "과소 보유";
  }
  return userFacingText(direction);
}

function sizingBandClass(reviewBand: string) {
  if (reviewBand === "reduce_review") {
    return "risk-high";
  }
  if (reviewBand === "add_blocked_until_evidence") {
    return "risk-medium";
  }
  return "risk-low";
}

function feedbackStatusClass(status: string) {
  if (status === "has_contradictions" || status === "contradicted") {
    return "risk-high";
  }
  if (status === "needs_more_data" || status === "too_early" || status === "missing" || status === "missing_history") {
    return "risk-medium";
  }
  return "risk-low";
}

function calibrationStatusClass(status: string) {
  if (status === "contradiction_review_required") {
    return "risk-high";
  }
  if (
    status === "insufficient_history"
    || status === "collect_more_feedback"
    || status === "missing"
  ) {
    return "risk-medium";
  }
  return "risk-low";
}

function cadenceStatusClass(status: string) {
  if (status === "missing_evidence_review_required") {
    return "risk-high";
  }
  if (status === "run_feedback_now" || status === "run_calibration_now" || status === "missing") {
    return "risk-medium";
  }
  return "risk-low";
}

function actionRouterStatusClass(status: string) {
  if (status.startsWith("blocked_")) {
    return "risk-high";
  }
  if (status === "missing" || status.endsWith("_ready")) {
    return "risk-medium";
  }
  return "risk-low";
}

function actionRouterLabel(status: string, executed: boolean, routeAction: string) {
  if (executed) {
    return routeAction === "execute_calibration" ? "누적평가 실행됨" : "사후평가 실행됨";
  }
  if (status === "no_op_wait_for_outcome_window") {
    return "성과 관찰 기간 대기";
  }
  if (status.startsWith("blocked_")) {
    return "가드레일 차단";
  }
  return userFacingText(status);
}

function orderSubmitLabel(allowed: boolean) {
  return `실거래 주문 ${allowed ? "허용" : "금지"}`;
}

function formatScore(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "없음";
  }
  return `${Math.round(value * 100)}점`;
}

type ExposureRow = {
  exposure_key: string;
  exposure_name: string;
  exposure_weight: number;
  position_count: number;
  symbols: string[];
  limit: number;
  excess_weight: number;
  status: string;
};

function ExposureList({ empty, items }: { empty: string; items: ExposureRow[] }) {
  if (items.length === 0) {
    return <p className="empty-state" style={{ margin: 0 }}>{empty}</p>;
  }

  return (
    <div className="bento-list" style={{ gap: "8px" }}>
      {items.map((item) => (
        <div className="bento-list-item" key={item.exposure_key}>
          <div>
            <span className={`risk-tag ${item.status === "over_limit" ? "risk-high" : "risk-low"}`}>
              {exposureStatusLabel(item.status)}
            </span>
            <strong>{userFacingText(item.exposure_name)}</strong>
            <span>
              {item.symbols.join(", ") || "심볼 없음"} · {item.position_count}개 포지션
            </span>
          </div>
          <div style={{ textAlign: "right", minWidth: "120px" }}>
            <strong>{formatPercent(item.exposure_weight)}</strong>
            <small style={{ display: "block", color: "var(--text-secondary)" }}>
              한도 {formatPercent(item.limit)}
            </small>
          </div>
        </div>
      ))}
    </div>
  );
}

export default async function PortfolioCoveragePage() {
  const [response, tradingResponse] = await Promise.all([getPortfolioCoverage(), getTradingReadiness()]);
  const data = response.data;
  const riskGuardrail = tradingResponse.data.portfolio_risk_budget_guardrail;
  const benchmarkDrift = riskGuardrail.benchmark_drift;
  const benchmarkDriftCalculated = benchmarkDrift?.drift_calculated === true;
  const benchmarkCode = recordString(benchmarkDrift, "benchmark_code") || "벤치마크";
  const benchmarkActiveShare = recordNumber(benchmarkDrift, "active_share");
  const benchmarkSource = recordString(benchmarkDrift, "benchmark_source") || recordString(benchmarkDrift, "source_type");
  const allocationPolicy = data.allocation_policy;
  const riskBudget = data.risk_budget;
  const candidateReview = riskBudget.rebalance_candidate_review;
  const candidateDecisionCounts = candidateReview.decision_counts ?? {};
  const positionSizingReview = riskBudget.position_sizing_review;
  const reviewHistory = riskBudget.review_decision_history;
  const reviewFeedback = riskBudget.review_decision_feedback;
  const reviewCalibration = riskBudget.review_feedback_calibration;
  const reviewCadence = riskBudget.review_feedback_cadence;
  const reviewActionRouter = riskBudget.review_feedback_action_router;
  const concentration = riskBudget.concentration;
  const hasPositions = data.positions.length > 0;
  const investedWeight = Math.max(0, 1 - (data.summary.cash_weight ?? 0));
  const thesisCoverageRatio = investedWeight > 0
    ? Math.max(0, Math.min(1, (investedWeight - data.summary.missing_thesis_weight) / investedWeight))
    : 0;
  const thesisReady = hasPositions && data.summary.missing_thesis_count === 0;
  const outcomeCoverageRatio = data.summary.weight_coverage_ratio;
  const reviewCandidateTotal = candidateReview.candidate_count + positionSizingReview.review_required_count;
  const portfolioCommandCards = [
    {
      index: "01",
      label: "보유 상태",
      title: hasPositions ? `${data.summary.position_count}개 보유` : "보유 스냅샷 없음",
      metric: `투자 논리 연결률 ${formatPercent(thesisCoverageRatio)} · 성과 측정 ${formatPercent(outcomeCoverageRatio)}`,
      body: hasPositions
        ? "보유 종목마다 투자 논리와 성과 측정 상태가 연결됐는지 먼저 본다. 논리 누락 종목은 보유 근거가 약하다."
        : "이 기준일에는 포지션 스냅샷이 없어 보유 상태를 만들 수 없다. 포지션 수집 상태를 먼저 확인한다.",
      href: "#portfolio-position-map",
      cta: "보유 지도 보기",
      tone: thesisReady ? "ready" : "watch",
    },
    {
      index: "02",
      label: "리스크 예산",
      title: riskBudgetLabel(riskBudget.status),
      metric: `한도 초과 ${riskBudget.over_single_position_limit_count}개 · 집중 초과 ${concentration.over_limit_count}개`,
      body: riskBudget.status === "needs_position_review" || concentration.over_limit_count > 0
        ? "단일 종목, 섹터, 테마 노출이 정책 한도와 충돌하는지 확인한다."
        : "현재 정책 기준으로 큰 한도 초과는 없다. 그래도 비중과 집중도는 아래 카드에서 계속 확인한다.",
      href: "#portfolio-risk-budget",
      cta: "리스크 보기",
      tone: riskBudget.status === "needs_position_review" || concentration.over_limit_count > 0 ? "watch" : "ready",
    },
    {
      index: "03",
      label: "리밸런싱 확인 대상",
      title: reviewCandidateTotal > 0 ? `${reviewCandidateTotal}개 확인 대상` : "즉시 대상 없음",
      metric: `벤치마크 ${candidateReview.candidate_count}개 · 포지션 ${positionSizingReview.review_required_count}개`,
      body: reviewCandidateTotal > 0
        ? "SPY 대비 괴리나 포지션 크기 문제를 확인한다. 상세 근거부터 열어본다."
        : "현재 기준으로 리밸런싱 확인 대상이 없다.",
      href: "#portfolio-rebalance-review",
      cta: "확인 대상 보기",
      tone: reviewCandidateTotal > 0 ? "watch" : "ready",
    },
    {
      index: "04",
      label: "성과 성숙 대기",
      title: reviewCalibration.weight_review_blocked ? "추천 산식 변경 금지" : "조건 확인 가능",
      metric: `성숙일 ${reviewCalibration.estimated_maturity_date || "미정"} · ${orderBoundaryLabel(reviewCalibration.guardrails.order_boundary)}`,
      body: reviewCalibration.weight_review_blocked
        ? "성과 표본이 성숙하기 전에는 추천 산식 반영 비중을 바꾸지 않는다."
        : "조건이 열려도 자동 비중 변경은 별도 승인 대상이다.",
      href: "#portfolio-outcome-boundary",
      cta: "상태 보기",
      tone: reviewCalibration.weight_review_blocked ? "block" : "watch",
    },
  ];

  return (
    <div className="pageStack decision-page">
      <section className="decision-brief reveal" aria-labelledby="portfolio-coverage-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">
            보유·리스크 상태 · {userFacingText(data.portfolio_name)} · {userFacingText(data.strategy_name)} · {data.as_of_date}
          </span>
          <h1 className="decision-brief-title" id="portfolio-coverage-title">
            보유 위험 공백은 {reviewCandidateTotal.toLocaleString("ko-KR")}개다.
          </h1>
          <p className="decision-brief-copy">
            투자 논리 누락, 리스크 한도, 벤치마크 괴리, 성과 성숙 대기를 한 화면에서 본다. 성숙 전에는 비중 정책을 바꾸지 않는다.
          </p>
          <div className="decision-brief-meta" aria-label="포트폴리오 핵심 상태">
            <span>포지션 {data.summary.position_count.toLocaleString("ko-KR")}개</span>
            <span>투자 논리 누락 {data.summary.missing_thesis_count.toLocaleString("ko-KR")}개</span>
            <span>측정 종료 {data.coverage_measurement_end_date}</span>
            <span>실거래 {orderBoundaryLabel(reviewCalibration.guardrails.order_boundary)}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          {portfolioCommandCards.map((card) => (
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

      <section className="bento-grid reveal delay-1">
        <article className="bento-card">
          <span className="metric-label">포지션</span>
          <strong className="metric-value">{data.summary.position_count}</strong>
          <span className="metric-sub">
            {hasPositions
              ? `${data.summary.position_count - data.summary.missing_thesis_count}개 투자 논리 연결`
              : "해당 기준일 포지션 스냅샷 없음"}
          </span>
        </article>
        
        <article className="bento-card" style={{ borderColor: data.summary.missing_thesis_count > 0 ? "var(--accent-red)" : "var(--border-light)" }}>
          <span className="metric-label">투자 논리 누락</span>
          <strong className="metric-value" style={{ color: data.summary.missing_thesis_count > 0 ? "var(--accent-red)" : "var(--text-primary)" }}>
            {data.summary.missing_thesis_count}
          </strong>
          <span className="metric-sub">비중 {formatPercent(data.summary.missing_thesis_weight)}</span>
        </article>

        <article className="bento-card">
          <span className="metric-label">성과 측정 연결률</span>
          <strong className="metric-value">{formatPercent(outcomeCoverageRatio)}</strong>
          <span className="metric-sub">장기 성과 기준</span>
        </article>

        <article className="bento-card">
          <span className="metric-label">성과 측정 누락</span>
          <strong className="metric-value">{data.summary.missing_outcome_count}</strong>
          <span className="metric-sub">측정 종료 {data.coverage_measurement_end_date}</span>
        </article>

        <article className="bento-card">
          <span className="metric-label">현금 비중</span>
          <strong className="metric-value">{formatPercent(data.summary.cash_weight)}</strong>
          <span className="metric-sub">명시적 배분</span>
        </article>

        <article id="portfolio-risk-budget" className="bento-card span-4" style={{ borderColor: riskBudget.status === "needs_position_review" ? "var(--accent-amber)" : "var(--border-light)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">위험 예산 / 포지션 크기</span>
              <h2>보유 비중이 정책 한도 안에 있는지 본다</h2>
            </div>
            <span className={`risk-tag ${riskBudget.status === "needs_position_review" ? "risk-medium" : "risk-low"}`}>
              {riskBudgetLabel(riskBudget.status)}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            추천 점수는 매수·매도 명령이 아니다. 실제 보유 비중은 단일 종목 한도, 리밸런싱 기준,
            투자 논리와 성과 측정 연결 상태를 함께 보고 따로 결정한다.
          </p>
          <div className="status-rail compact-rail" aria-label="위험 예산 요약">
            <article className="rail-cell">
              <span>단일 종목 상한</span>
              <strong>{formatPercent(allocationPolicy.max_single_position_weight)}</strong>
              <small>{userFacingText(allocationPolicy.policy_scope)} 정책</small>
            </article>
            <article className="rail-cell">
              <span>최대 보유</span>
              <strong>{riskBudget.largest_position_symbol || "없음"}</strong>
              <small>{formatPercent(riskBudget.largest_position_weight)}</small>
            </article>
            <article className="rail-cell">
              <span>한도 초과</span>
              <strong>{riskBudget.over_single_position_limit_count}</strong>
              <small>축소 확인 대상</small>
            </article>
            <article className="rail-cell">
              <span>작은 비중</span>
              <strong>{riskBudget.below_rebalance_floor_count}</strong>
              <small>{formatPercent(allocationPolicy.min_rebalance_target_weight)} 미만</small>
            </article>
            <article className="rail-cell">
              <span>투자 비중</span>
              <strong>{formatPercent(riskBudget.invested_weight)}</strong>
              <small>현금 제외</small>
            </article>
          </div>
        </article>

        <article className="bento-card span-4" style={{ borderColor: riskGuardrail.paper_validation_input_allowed ? "var(--border-light)" : "var(--accent-red)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">저장된 위험 예산 검증</span>
              <h2>이 검증 결과가 가상 매매 검증을 막고 있는지 본다</h2>
            </div>
            <span className={`risk-tag ${riskGuardrail.paper_validation_input_allowed ? "risk-low" : "risk-high"}`}>
              {riskGuardrail.paper_validation_input_allowed ? "입력 가능" : "입력 차단"}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            화면에서 계산한 집중도와 별도로, 서버에 저장된 위험 예산 검증 결과를 가상 매매 검증이 읽는다.
            이 값이 차단이면 가상 매매 검증은 충돌 수가 0이어도 실패 상태로 남는다.
          </p>
          <div className="status-rail compact-rail" aria-label="저장된 위험 예산 검증 요약">
            <article className="rail-cell">
              <span>검증 기록</span>
              <strong>{recordPresent(riskGuardrail.eval_run_id)}</strong>
              <small>{userFacingText(riskGuardrail.status)}</small>
            </article>
            <article className="rail-cell">
              <span>판정</span>
              <strong>{userFacingText(riskGuardrail.risk_gate_decision)}</strong>
              <small>{riskGuardrail.effective_snapshot_date || "기준일 없음"}</small>
            </article>
            <article className="rail-cell rail-critical">
              <span>차단 사유</span>
              <strong>{riskGuardrail.blocking_reasons.length}</strong>
              <small>{riskGuardrail.blocking_reasons.map((reason) => userFacingText(reason)).join(", ") || "없음"}</small>
            </article>
            <article className="rail-cell">
              <span>벤치마크 괴리</span>
              <strong>
                {benchmarkDriftCalculated ? formatPercent(benchmarkActiveShare) : "미계산"}
              </strong>
              <small>
                {benchmarkDriftCalculated
                  ? `${benchmarkCode} · ${benchmarkSource || "구성비 저장됨"}`
                  : "구성비 없으면 추정하지 않음"}
              </small>
            </article>
          </div>
        </article>

        <article className="bento-card span-4" style={{ borderColor: reviewHistory.decision_status === "review_required" ? "var(--accent-amber)" : "var(--border-light)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">저장된 포트폴리오 결정 이력</span>
              <h2>오늘 보이는 확인 대상이 감사 이력으로 남았는지 본다</h2>
            </div>
            <span className={`risk-tag ${reviewHistory.decision_status === "review_required" ? "risk-medium" : "risk-low"}`}>
              {reviewHistory.status === "loaded" ? userFacingText(reviewHistory.decision_status) : "이력 없음"}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            리밸런싱 확인 대상과 포지션 크기 상태는 주문이 아니라 의사결정 기록이다. 이력이 없으면 같은 화면을 나중에
            다시 봤을 때 당시 근거를 추적하기 어렵다.
          </p>
          <div className="status-rail compact-rail" aria-label="포트폴리오 결정 이력 요약" style={{ marginBottom: "20px" }}>
            <article className="rail-cell">
              <span>이력 기록</span>
              <strong>{recordPresent(reviewHistory.eval_run_id)}</strong>
              <small>{reviewHistory.as_of_date || "기준일 없음"}</small>
            </article>
            <article className="rail-cell">
              <span>저장 결정</span>
              <strong>{reviewHistory.decision_count}</strong>
              <small>확인 필요 {reviewHistory.review_required_count}개</small>
            </article>
            <article className="rail-cell">
              <span>벤치마크 / 포지션</span>
              <strong>{reviewHistory.benchmark_decision_count} / {reviewHistory.position_sizing_decision_count}</strong>
              <small>상태군 분리</small>
            </article>
            <article className="rail-cell rail-critical">
              <span>실거래 상태</span>
              <strong>{orderBoundaryLabel(reviewHistory.guardrails.order_boundary)}</strong>
              <small>{orderSubmitLabel(reviewHistory.guardrails.broker_submit_allowed)}</small>
            </article>
          </div>
          {reviewHistory.latest_decisions.length > 0 ? (
            <div className="bento-list" style={{ gap: "8px" }}>
              {reviewHistory.latest_decisions.slice(0, 5).map((decision) => (
                <div className="bento-list-item" key={`${decision.decision_family}-${decision.priority}-${decision.symbol}`}>
                  <div>
                    <span className={`risk-tag ${candidateSeverityClass(decision.severity)}`}>
                      {decision.decision_label || userFacingText(decision.decision_type)}
                    </span>
                    <strong>{decision.symbol} · {userFacingText(decision.decision_family)}</strong>
                    <span>{userFacingText(decision.next_review_action)}</span>
                  </div>
                  <span style={{ color: "var(--text-secondary)", maxWidth: "520px" }}>
                    {userFacingText(decision.rationale || "저장된 설명 없음")}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state" style={{ margin: 0 }}>
              아직 저장된 결정 이력이 없다. 포트폴리오 결정 이력이 생성되면 이곳에 최신 결정이 표시된다.
            </p>
          )}
        </article>

        <article className="bento-card span-4" style={{ borderColor: reviewFeedback.feedback_status === "has_contradictions" ? "var(--accent-red)" : "var(--border-light)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">포트폴리오 결정 사후평가</span>
              <h2>저장한 결정이 이후 성과와 맞았는지 본다</h2>
            </div>
            <span className={`risk-tag ${feedbackStatusClass(reviewFeedback.feedback_status)}`}>
              {reviewFeedback.status === "loaded" ? userFacingText(reviewFeedback.feedback_status) : "평가 없음"}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            이 평가는 리밸런싱이나 추천 산식 반영 비중을 바꾸지 않는다. 이전 결정을 성과 측정,
            가상 매매 검증, 투자 논리, 가격 변화와 대조해서 다음 상태 확인의 신뢰도를 높이는 자료다.
          </p>
          <div className="status-rail compact-rail" aria-label="포트폴리오 결정 사후평가 요약" style={{ marginBottom: "20px" }}>
            <article className="rail-cell">
              <span>평가 기록</span>
              <strong>{recordPresent(reviewFeedback.eval_run_id)}</strong>
              <small>{reviewFeedback.as_of_date || "기준일 없음"}</small>
            </article>
            <article className="rail-cell">
              <span>검증 / 반박</span>
              <strong>{reviewFeedback.validated_count} / {reviewFeedback.contradicted_count}</strong>
              <small>전체 {reviewFeedback.decision_count}개</small>
            </article>
            <article className="rail-cell">
              <span>아직 이른 항목</span>
              <strong>{reviewFeedback.too_early_count}</strong>
              <small>{reviewFeedback.min_horizon_days}일 관찰 기준</small>
            </article>
            <article className="rail-cell rail-critical">
              <span>실거래 상태</span>
              <strong>{orderBoundaryLabel(reviewFeedback.guardrails.order_boundary)}</strong>
              <small>{orderSubmitLabel(reviewFeedback.guardrails.broker_submit_allowed)}</small>
            </article>
          </div>
          {reviewFeedback.latest_items.length > 0 ? (
            <div className="bento-list" style={{ gap: "8px" }}>
              {reviewFeedback.latest_items.slice(0, 5).map((item) => (
                <div className="bento-list-item" key={`${item.decision_index}-${item.symbol}-${item.feedback_status}`}>
                  <div>
                    <span className={`risk-tag ${feedbackStatusClass(item.feedback_status)}`}>
                      {userFacingText(item.feedback_status)}
                    </span>
                    <strong>{item.symbol} · {item.decision_label || userFacingText(item.decision_type)}</strong>
                    <span>{userFacingText(item.feedback_reason)}</span>
                  </div>
                  <span style={{ color: "var(--text-secondary)", maxWidth: "520px" }}>
                    성과 {userFacingText(item.evidence.recommendation_outcome.outcome_label || "미측정")} · 초과수익{" "}
                    {formatPercent(item.evidence.recommendation_outcome.alpha_pct)} · 가격{" "}
                    {formatPercent(item.evidence.price_evidence.price_return_pct)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state" style={{ margin: 0 }}>
              아직 사후평가 이력이 없다. 성과 측정 기간이 끝난 뒤 저장된 결정이 맞았는지 여기에 표시된다.
            </p>
          )}
        </article>

        <article id="portfolio-outcome-boundary" className="bento-card span-4" style={{ borderColor: reviewCalibration.calibration_status === "contradiction_review_required" ? "var(--accent-red)" : "var(--border-light)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">포트폴리오 결정 신뢰도</span>
              <h2>성과 표본이 성숙하기 전에는 추천 산식 반영 비중을 바꾸지 않는다</h2>
            </div>
            <span className={`risk-tag ${reviewCalibration.weight_review_blocked ? "risk-medium" : "risk-low"}`}>
              {reviewCalibration.status === "loaded"
                  ? reviewCalibration.weight_review_blocked ? "추천 산식 변경 금지" : "조건 확인 가능"
                : "누적평가 없음"}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            포트폴리오 비중 결정은 실제 성과 관찰 기간이 지난 뒤 평가한다. 이 카드가 보여주는 것은 추천 산식 변경
            허용이 아니라, 왜 아직 금지인지와 다음 성숙 시점이다.
          </p>
          <div className="status-rail compact-rail" aria-label="포트폴리오 결정 신뢰도 요약" style={{ marginBottom: "20px" }}>
            <article className="rail-cell">
              <span>사후평가 실행</span>
              <strong>{reviewCalibration.feedback_run_count}/{reviewCalibration.min_feedback_runs}</strong>
              <small>부족 {reviewCalibration.feedback_run_gap}회 · {reviewCalibration.lookback_days || "기간 미확인"}일 기준</small>
            </article>
            <article className="rail-cell">
              <span>성숙한 결정</span>
              <strong>{reviewCalibration.mature_decision_count}/{reviewCalibration.min_mature_decisions}</strong>
              <small>부족 {reviewCalibration.mature_decision_gap}개 · 전체 {reviewCalibration.decision_count}개</small>
            </article>
            <article className="rail-cell">
              <span>예상 성숙일</span>
              <strong>{reviewCalibration.estimated_maturity_date || "계산 불가"}</strong>
              <small>
                {reviewCalibration.days_until_maturity === null
                  ? userFacingText(reviewCalibration.maturity_status)
                  : reviewCalibration.days_until_maturity > 0
                    ? `${reviewCalibration.days_until_maturity}일 대기`
                    : "다시 평가 가능일 도달"}
              </small>
            </article>
            <article className="rail-cell">
              <span>검증 / 반박</span>
              <strong>{reviewCalibration.validated_count} / {reviewCalibration.contradicted_count}</strong>
              <small>반박률 {formatPercent(reviewCalibration.contradiction_rate)}</small>
            </article>
            <article className="rail-cell rail-critical">
              <span>실거래 상태</span>
              <strong>{orderBoundaryLabel(reviewCalibration.guardrails.order_boundary)}</strong>
              <small>{orderSubmitLabel(reviewCalibration.guardrails.broker_submit_allowed)}</small>
            </article>
          </div>
          <p className="empty-state" style={{ marginTop: 0 }}>
            <strong>차단 이유</strong>
            <span>{userFacingText(reviewCalibration.weight_review_block_reason)}</span>
          </p>
          <div className="bento-list" style={{ gap: "8px" }}>
            {reviewCalibration.family_summaries.slice(0, 3).map((summary) => (
              <div className="bento-list-item" key={`calibration-${summary.decision_family}`}>
                <div>
                  <span className="risk-tag risk-medium">결정 유형</span>
                  <strong>{userFacingText(summary.decision_family || "unknown")}</strong>
                  <span>
                    전체 {summary.decision_count}개 · 성숙 {summary.mature_decision_count}개 · 반박{" "}
                    {summary.contradicted_count}개
                  </span>
                </div>
                <span style={{ color: "var(--text-secondary)" }}>
                  반박률 {formatPercent(summary.contradiction_rate)}
                </span>
              </div>
            ))}
            {reviewCalibration.family_summaries.length === 0 ? (
              <p className="empty-state" style={{ margin: 0 }}>
                아직 누적평가 자료가 없다. 여러 사후평가가 쌓인 뒤 이곳에서 결정 유형별 신뢰도를 본다.
              </p>
            ) : null}
          </div>
        </article>

        <article className="bento-card span-4" style={{ borderColor: reviewCadence.should_run_now ? "var(--accent-red)" : "var(--border-light)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">사후평가 실행 시점</span>
              <h2>사후평가와 누적평가를 언제 다시 돌릴지 본다</h2>
            </div>
            <span className={`risk-tag ${cadenceStatusClass(reviewCadence.cadence_status)}`}>
              {reviewCadence.status === "loaded" ? userFacingText(reviewCadence.cadence_status) : "실행 주기 없음"}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            최신 결정 이력, 사후평가, 누적평가가 서로 연결되어 있는지 확인한다. 실행 필요가 떠도 주문이나 추천 산식 변경은
            자동으로 허용되지 않는다.
          </p>
          <div className="status-rail compact-rail" aria-label="사후평가 실행 시점 요약" style={{ marginBottom: "20px" }}>
            <article className="rail-cell">
              <span>실행 여부</span>
              <strong>{reviewCadence.should_run_now ? "지금 실행" : "즉시 실행 아님"}</strong>
              <small>{userFacingText(reviewCadence.reason)}</small>
            </article>
            <article className="rail-cell">
              <span>결정 이력 나이</span>
              <strong>{reviewCadence.evidence.history_age_days}일</strong>
              <small>최소 {reviewCadence.min_horizon_days}일</small>
            </article>
            <article className="rail-cell">
              <span>사후평가/누적평가</span>
              <strong>{recordPresent(reviewCadence.feedback.eval_run_id)} / {recordPresent(reviewCadence.calibration.eval_run_id)}</strong>
              <small>사후평가 {userFacingText(reviewCadence.feedback.feedback_status)}</small>
            </article>
            <article className="rail-cell rail-critical">
              <span>실거래 상태</span>
              <strong>{orderBoundaryLabel(reviewCadence.order_boundary)}</strong>
              <small>{orderSubmitLabel(reviewCadence.broker_submit_allowed)}</small>
            </article>
          </div>
          <div className="empty-state" style={{ margin: 0 }}>
            <strong>{reviewCadence.label}</strong>
            <p>{userFacingText(reviewCadence.reason)}</p>
          </div>
        </article>

        <article
          className="bento-card span-4"
          style={{
            borderColor: reviewActionRouter.action_status.startsWith("blocked_")
              ? "var(--accent-red)"
              : "var(--border-light)",
          }}
        >
          <div className="section-heading">
            <div>
              <span className="metric-sub">사후평가 실행 분기</span>
              <h2>대기, 사후평가, 누적평가 중 실제로 무엇을 했는지 본다</h2>
            </div>
            <span className={`risk-tag ${actionRouterStatusClass(reviewActionRouter.action_status)}`}>
              {actionRouterLabel(
                reviewActionRouter.action_status,
                reviewActionRouter.child_runner.executed,
                reviewActionRouter.route_action,
              )}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            실행 주기 결과가 실제 안전 작업으로 이어졌는지 확인한다. 실행 기록이 있어도 추천 산식 반영 비중,
            보유 비중, 실거래 주문 전송은 여전히 자동으로 바뀌지 않는다.
          </p>
          <div className="status-rail compact-rail" aria-label="사후평가 실행 라우터 요약" style={{ marginBottom: "20px" }}>
            <article className="rail-cell">
              <span>원천 실행 주기</span>
              <strong>{userFacingText(reviewActionRouter.cadence_status)}</strong>
              <small>{recordPresent(reviewActionRouter.source_cadence_eval_run_id)}</small>
            </article>
            <article className="rail-cell">
              <span>라우팅</span>
              <strong>{userFacingText(reviewActionRouter.route_action)}</strong>
              <small>{userFacingText(reviewActionRouter.reason)}</small>
            </article>
            <article className="rail-cell">
              <span>실행한 작업</span>
              <strong>{reviewActionRouter.child_runner.executed ? "있음" : "없음"}</strong>
              <small>
                {reviewActionRouter.child_runner.executed
                  ? `${userFacingText(reviewActionRouter.child_runner.report_name)} · ${recordPresent(reviewActionRouter.child_runner.eval_run_id)}`
                  : "후속 자동 실행 없음"}
              </small>
            </article>
            <article className="rail-cell rail-critical">
              <span>실거래 상태</span>
              <strong>{orderBoundaryLabel(reviewActionRouter.order_boundary)}</strong>
              <small>{orderSubmitLabel(reviewActionRouter.broker_submit_allowed)}</small>
            </article>
          </div>
          <div className="empty-state" style={{ margin: 0 }}>
            <strong>{userFacingText(reviewActionRouter.action_status)}</strong>
            <p>{userFacingText(reviewActionRouter.next_action)}</p>
          </div>
        </article>

        <article id="portfolio-rebalance-review" className="bento-card span-4" style={{ borderColor: candidateReview.candidate_count > 0 ? "var(--accent-red)" : "var(--border-light)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">벤치마크 대비 리밸런싱 확인</span>
              <h2>SPY와 비교해 어느 종목 비중이 과하게 다른지 본다</h2>
            </div>
            <span className={`risk-tag ${candidateReview.candidate_count > 0 ? "risk-high" : "risk-low"}`}>
              {candidateReview.candidate_count > 0 ? "확인 대상 있음" : "큰 괴리 없음"}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            이 표는 주문 지시가 아니다. {candidateReview.benchmark_code || benchmarkCode} 기준 벤치마크 대비 괴리가 큰 종목을
            투자 논리, 세금/비용, 섹터 집중도와 함께 확인하기 위한 읽기 전용 대상 목록이다.
          </p>
          <div className="status-rail compact-rail" aria-label="벤치마크 리밸런싱 확인 요약" style={{ marginBottom: "20px" }}>
            <article className="rail-cell">
              <span>전체 괴리</span>
              <strong>{formatPercent(candidateReview.active_share)}</strong>
              <small>{userFacingText(candidateReview.benchmark_source || benchmarkSource || "근거 없음")}</small>
            </article>
            <article className="rail-cell">
              <span>구성비 확인률</span>
              <strong>{formatPercent(candidateReview.composition_coverage_weight)}</strong>
              <small>{candidateReview.source_as_of_date || "기준일 없음"}</small>
            </article>
            <article className="rail-cell rail-critical">
              <span>확인 대상</span>
              <strong>{candidateReview.candidate_count}</strong>
              <small>
                축소 {candidateDecisionCounts.reduce_watch ?? 0} · 미보유 확인{" "}
                {candidateDecisionCounts.needs_thesis_update ?? 0}
              </small>
            </article>
            <article className="rail-cell">
              <span>실거래 상태</span>
              <strong>{orderBoundaryLabel(candidateReview.order_boundary)}</strong>
              <small>{orderSubmitLabel(candidateReview.broker_submit_allowed)}</small>
            </article>
          </div>
          {candidateReview.candidates.length === 0 ? (
            <p className="empty-state" style={{ margin: 0 }}>
              현재 기준에서 별도 리밸런싱 확인 대상이 없다.
            </p>
          ) : (
            <div className="portfolio-review-card-grid" aria-label="벤치마크 리밸런싱 확인 후보">
              {candidateReview.candidates.map((candidate) => (
                <article className="portfolio-review-card" key={`${candidate.priority}-${candidate.symbol}-${candidate.direction}`}>
                  <div className="portfolio-review-card-head">
                    <span>우선순위 {candidate.priority.toString().padStart(2, "0")}</span>
                    <strong>{candidate.symbol}</strong>
                    <b className={`risk-tag ${candidateSeverityClass(candidate.severity)}`}>
                      {userFacingText(candidate.decision_label)}
                    </b>
                  </div>
                  <p>
                    {candidateDirectionLabel(candidate.direction)} · {userFacingText(candidate.next_review_action)}
                  </p>
                  <dl className="portfolio-review-metrics">
                    <div>
                      <dt>현재 비중</dt>
                      <dd>{formatPercent(candidate.current_weight)}</dd>
                    </div>
                    <div>
                      <dt>벤치마크</dt>
                      <dd>{formatPercent(candidate.benchmark_weight)}</dd>
                    </div>
                    <div>
                      <dt>괴리</dt>
                      <dd>{formatPercent(candidate.active_weight)}</dd>
                    </div>
                  </dl>
                  <div className="portfolio-review-evidence">
                    <div>
                      <span>연결 근거</span>
                      {candidate.related_recommendation_id && candidate.links.recommendation ? (
                        <Link href={candidate.links.recommendation as Route}>{candidate.related_recommendation_id}</Link>
                      ) : (
                        <strong>추천 연결 없음</strong>
                      )}
                      <small>
                        {candidate.related_thesis_id ? `투자 논리 ${candidate.related_thesis_id}` : "투자 논리 확인 필요"}
                      </small>
                    </div>
                    <div>
                      <span>왜 보는가</span>
                      <strong>{userFacingText(candidate.rationale)}</strong>
                      <small>{orderBoundaryLabel(candidate.order_boundary)} · {orderSubmitLabel(candidate.broker_submit_allowed)}</small>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </article>

        <article className="bento-card span-4" style={{ borderColor: positionSizingReview.review_required_count > 0 ? "var(--accent-amber)" : "var(--border-light)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">포지션 크기 상태</span>
              <h2>이 비중을 더 키워도 되는지, 줄여야 하는지 본다</h2>
            </div>
            <span className={`risk-tag ${positionSizingReview.review_required_count > 0 ? "risk-medium" : "risk-low"}`}>
              {userFacingText(positionSizingReview.status)}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            현재 보유 비중을 투자 논리, 기업 분석, 밸류에이션, 벤치마크 괴리와 함께 묶어 본다.
            여기서 나오는 값은 주문 목표가 아니라 증액 금지, 축소 필요성, 유지 상태를 구분하는 읽기 전용 상태 범위다.
          </p>
          <div className="status-rail compact-rail" aria-label="포지션 크기 상태 요약" style={{ marginBottom: "20px" }}>
            <article className="rail-cell rail-critical">
              <span>축소 필요성</span>
              <strong>{positionSizingReview.reduce_review_count}</strong>
              <small>한도 또는 벤치마크 괴리</small>
            </article>
            <article className="rail-cell">
              <span>증거 보강 전 증액 금지</span>
              <strong>{positionSizingReview.add_blocked_until_evidence_count}</strong>
              <small>논리·재무·밸류에이션 공백</small>
            </article>
            <article className="rail-cell">
              <span>작은 비중 관찰</span>
              <strong>{positionSizingReview.watch_small_position_count}</strong>
              <small>{formatPercent(positionSizingReview.min_rebalance_target_weight)} 미만</small>
            </article>
            <article className="rail-cell">
              <span>실거래 상태</span>
              <strong>{orderBoundaryLabel(positionSizingReview.order_boundary)}</strong>
              <small>{orderSubmitLabel(positionSizingReview.broker_submit_allowed)}</small>
            </article>
          </div>
          {positionSizingReview.candidates.length === 0 ? (
            <p className="empty-state" style={{ margin: 0 }}>
              보유 포지션이 없어 포지션 크기 상태를 만들 수 없다.
            </p>
          ) : (
            <div className="portfolio-review-card-grid" aria-label="포지션 크기 확인 후보">
              {positionSizingReview.candidates.map((candidate) => (
                <article className="portfolio-review-card" key={`${candidate.priority}-${candidate.symbol}-${candidate.review_band}`}>
                  <div className="portfolio-review-card-head">
                    <span>우선순위 {candidate.priority.toString().padStart(2, "0")}</span>
                    <strong>{candidate.symbol}</strong>
                    <b className={`risk-tag ${sizingBandClass(candidate.review_band)}`}>
                      {userFacingText(candidate.review_band)}
                    </b>
                  </div>
                  <p>{userFacingText(candidate.rationale)}</p>
                  <dl className="portfolio-review-metrics">
                    <div>
                      <dt>현재 비중</dt>
                      <dd>{formatPercent(candidate.current_weight)}</dd>
                    </div>
                    <div>
                      <dt>벤치마크</dt>
                      <dd>{formatPercent(candidate.benchmark_weight)}</dd>
                    </div>
                    <div>
                      <dt>확대 상한</dt>
                      <dd>{formatPercent(candidate.review_ceiling_weight)}</dd>
                    </div>
                  </dl>
                  <div className="portfolio-review-evidence">
                    <div>
                      <span>기업 근거</span>
                      <strong>
                        재무 {formatScore(candidate.fundamental_quality_score)} · 밸류 {formatScore(candidate.valuation_margin_score)}
                      </strong>
                      <small>
                        안전마진 {formatPercent(candidate.valuation_margin_of_safety)} · 기업 리서치{" "}
                        {candidate.equity_research_artifact_id ? "있음" : "없음"}
                      </small>
                    </div>
                    <div>
                      <span>판단 조건</span>
                      <strong>{userFacingText(candidate.professional_analysis_status)}</strong>
                      <small>
                        막는 이유: {candidate.blocking_factors.map((factor) => userFacingText(factor)).join(", ") || "없음"}
                      </small>
                      <small>
                        받치는 근거: {candidate.supporting_factors.map((factor) => userFacingText(factor)).join(", ") || "없음"}
                      </small>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </article>

        <article className="bento-card span-4" style={{ borderColor: concentration.status === "needs_concentration_review" ? "var(--accent-red)" : "var(--border-light)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">섹터·테마 집중도</span>
              <h2>한 종목이 아니라 같은 흐름에 얼마나 몰렸는지 본다</h2>
            </div>
            <span className={`risk-tag ${concentrationStatusClass(concentration.status)}`}>
              {concentrationStatusLabel(concentration.status)}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            같은 섹터나 테마에 여러 종목이 묶이면 종목 수가 분산되어 보여도 실제 위험은 한 방향으로 움직일 수 있다.
            이 표는 주문 지시가 아니라 포트폴리오 확인 우선순위를 정하기 위한 노출도 지도다.
          </p>
          <div className="status-rail compact-rail" aria-label="집중도 정책 요약" style={{ marginBottom: "20px" }}>
            <article className="rail-cell">
              <span>섹터 한도</span>
              <strong>{formatPercent(concentration.max_sector_weight)}</strong>
              <small>초과 시 집중도 확인</small>
            </article>
            <article className="rail-cell">
              <span>테마 한도</span>
              <strong>{formatPercent(concentration.max_theme_weight)}</strong>
              <small>상위 흐름 노출</small>
            </article>
            <article className="rail-cell">
              <span>미분류 한도</span>
              <strong>{formatPercent(concentration.max_unclassified_weight)}</strong>
              <small>데이터 품질 공백</small>
            </article>
            <article className="rail-cell">
              <span>미분류 비중</span>
              <strong>{formatPercent(concentration.unclassified_weight)}</strong>
              <small>{concentration.unclassified_symbols.join(", ") || "없음"}</small>
            </article>
            <article className="rail-cell">
              <span>초과 그룹</span>
              <strong>{concentration.over_limit_count}</strong>
              <small>섹터/테마 합산</small>
            </article>
          </div>

          <div className="bento-grid">
            <article className="bento-card span-2">
              <span className="metric-sub">섹터 노출</span>
              <h3 style={{ fontSize: "1.15rem", margin: "6px 0 12px" }}>산업 방향으로 묶인 위험</h3>
              <ExposureList empty="섹터 분류가 아직 없다. 종목 분류 데이터를 보강해야 한다." items={concentration.sector_exposures} />
            </article>
            <article className="bento-card span-2">
              <span className="metric-sub">테마 노출</span>
              <h3 style={{ fontSize: "1.15rem", margin: "6px 0 12px" }}>거시·테마 흐름으로 묶인 위험</h3>
              <ExposureList empty="테마 분류가 아직 없다. 뉴스/사이클 연결을 먼저 보강해야 한다." items={concentration.theme_exposures} />
            </article>
          </div>
        </article>

        <article id="portfolio-position-map" className="bento-card span-4">
          <div className="section-heading">
            <div>
              <span className="metric-sub">리밸런싱 우선순위</span>
              <h2>바로 주문하지 않고 무엇을 먼저 확인할지 정한다</h2>
            </div>
            <span className="risk-tag risk-medium">읽기 전용</span>
          </div>
          {riskBudget.rebalance_priorities.length === 0 ? (
            <p className="empty-state" style={{ margin: 0 }}>
              현재 정책 기준에서 우선 확인할 포지션이 없다.
            </p>
          ) : (
            <div className="bento-list">
              {riskBudget.rebalance_priorities.map((priority) => (
                <div className="bento-list-item" key={`${priority.symbol}-${priority.action}`}>
                  <div>
                    <span className="metric-sub">우선순위 {priority.priority}</span>
                    <strong>{priority.symbol} · {formatPercent(priority.current_weight)}</strong>
                    <span>{userFacingText(priority.action)}</span>
                  </div>
                  <span style={{ color: "var(--text-secondary)", maxWidth: "520px" }}>
                    {userFacingText(priority.reason)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">보유 연결 상태</span>
            <h2 style={{ fontSize: "1.5rem" }}>보유 종목 상태 지도</h2>
          </div>
          
          <div className="bento-list" style={{ gap: "8px" }}>
            <div className="bento-list-item" style={{ background: "transparent", borderBottom: "1px solid var(--border-light)", borderRadius: 0, paddingBottom: "16px" }}>
              <div style={{ flexDirection: "row", width: "100%", gap: "24px" }}>
                <span className="metric-sub" style={{ width: "100px" }}>심볼</span>
                <span className="metric-sub" style={{ width: "100px" }}>비중</span>
                <span className="metric-sub" style={{ width: "130px" }}>비중 한도</span>
                <span className="metric-sub" style={{ width: "140px" }}>투자 논리</span>
                <span className="metric-sub" style={{ width: "140px" }}>성과</span>
                <span className="metric-sub" style={{ flex: 1 }}>필요 조치</span>
              </div>
            </div>

            {!hasPositions ? (
              <p className="empty-state">
                이 기준일에 보유 포지션 스냅샷이 없어 연결 상태 표를 만들 수 없다. 포트폴리오 포지션 적재 배치가
                최신 영업일 스냅샷을 저장하면 심볼, 비중, 투자 논리, 성과 측정 상태가 여기에 표시된다.
              </p>
            ) : null}
            
            {data.positions.map((position) => (
              <div className="bento-list-item" key={position.instrument_id} style={{ alignItems: "flex-start" }}>
                <div style={{ flexDirection: "row", width: "100%", gap: "24px", alignItems: "center" }}>
                  <strong style={{ width: "100px", fontSize: "1.1rem" }}>{position.symbol}</strong>
                  <span style={{ width: "100px", color: "var(--text-primary)", fontWeight: 500 }}>{formatPercent(position.weight)}</span>
                  <span style={{ width: "130px" }}>
                    <span className={`risk-tag ${sizeStatusClass(position.position_size_status)}`}>
                      {sizeStatusLabel(position.position_size_status)}
                    </span>
                  </span>
                  <span style={{ 
                    width: "140px", 
                    color: position.active_thesis_id ? 'var(--accent-green)' : 'var(--accent-red)'
                  }}>
                    {position.active_thesis_id ? "연결됨" : "논리 누락"}
                  </span>
                  <span style={{ 
                    width: "140px", 
                    color: position.coverage_status === 'covered' ? 'var(--accent-green)' : 'var(--text-secondary)'
                  }}>
                      {position.coverage_status === "missing_outcome" ? "측정 대기" : userFacingText(position.outcome_status)}
                  </span>
                  <span style={{ flex: 1, color: "var(--text-primary)", fontWeight: 500 }}>
                    {userFacingText(position.action)}
                    <small style={{ display: "block", color: "var(--text-secondary)", fontWeight: 400, marginTop: "4px" }}>
                      {userFacingText(position.position_size_note)}
                    </small>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
