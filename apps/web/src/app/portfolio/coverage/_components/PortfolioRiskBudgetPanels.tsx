import type { PortfolioCoverageData, TradingReadinessData } from "@/lib/types";

import {
  formatCoveragePercent,
  orderBoundaryLabel,
  orderSubmitLabel,
  recordPresent,
  riskBudgetLabel,
  userFacingText,
} from "./portfolioCoverageFormat";

type PortfolioRiskBudgetPanelsProps = {
  readonly allocationPolicy: PortfolioCoverageData["allocation_policy"];
  readonly benchmarkActiveShare: number | null;
  readonly benchmarkCode: string;
  readonly benchmarkDriftCalculated: boolean;
  readonly benchmarkSource: string;
  readonly riskBudget: PortfolioCoverageData["risk_budget"];
  readonly riskGuardrail: TradingReadinessData["portfolio_risk_budget_guardrail"];
};

export function PortfolioRiskBudgetPanels({
  allocationPolicy,
  benchmarkActiveShare,
  benchmarkCode,
  benchmarkDriftCalculated,
  benchmarkSource,
  riskBudget,
  riskGuardrail,
}: PortfolioRiskBudgetPanelsProps) {
  return (
    <>
      <article
        id="portfolio-risk-budget"
        className="bento-card span-4"
        style={{ borderColor: riskBudget.status === "needs_position_review" ? "var(--accent-amber)" : "var(--border-light)" }}
      >
        <div className="section-heading">
          <div>
            <span className="metric-sub">위험 예산 / 포지션 크기</span>
            <h2>보유 비중과 집중 위험</h2>
          </div>
          <span className={`risk-tag ${riskBudget.status === "needs_position_review" ? "risk-medium" : "risk-low"}`}>
            {riskBudgetLabel(riskBudget.status)}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          추천 점수는 매수·매도 명령이 아닙니다. 실제 보유 비중은 단일 종목 한도, 리밸런싱 기준,
          투자 논리와 성과 측정 상태를 함께 고려해 별도로 결정합니다.
        </p>
        <div className="status-rail compact-rail" aria-label="위험 예산 요약">
          <article className="rail-cell">
            <span>단일 종목 상한</span>
            <strong>{formatCoveragePercent(allocationPolicy.max_single_position_weight)}</strong>
            <small>{userFacingText(allocationPolicy.policy_scope)} 정책</small>
          </article>
          <article className="rail-cell">
            <span>최대 보유</span>
            <strong>{riskBudget.largest_position_symbol || "없음"}</strong>
            <small>{formatCoveragePercent(riskBudget.largest_position_weight)}</small>
          </article>
          <article className="rail-cell">
            <span>한도 초과</span>
            <strong>{riskBudget.over_single_position_limit_count}</strong>
            <small>축소 검토 후보</small>
          </article>
          <article className="rail-cell">
            <span>작은 비중</span>
            <strong>{riskBudget.below_rebalance_floor_count}</strong>
            <small>{formatCoveragePercent(allocationPolicy.min_rebalance_target_weight)} 미만</small>
          </article>
          <article className="rail-cell">
            <span>투자 비중</span>
            <strong>{formatCoveragePercent(riskBudget.invested_weight)}</strong>
            <small>현금 제외</small>
          </article>
        </div>
      </article>

      <article
        className="bento-card span-4"
        style={{ borderColor: riskGuardrail.paper_validation_input_allowed ? "var(--border-light)" : "var(--accent-red)" }}
      >
        <div className="section-heading">
          <div>
            <span className="metric-sub">저장된 위험 예산 검증</span>
            <h2>가상 매매 검증 입력 가능 여부</h2>
          </div>
          <span className={`risk-tag ${riskGuardrail.paper_validation_input_allowed ? "risk-low" : "risk-high"}`}>
            {riskGuardrail.paper_validation_input_allowed ? "입력 가능" : "입력 차단"}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          서버에 저장된 위험 예산 검증 결과를 가상 매매 검증이 읽습니다. 차단 상태면 충돌 수가 0이어도
          실제 주문 전환은 닫힌 상태로 유지됩니다.
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
            <strong>{benchmarkDriftCalculated ? formatCoveragePercent(benchmarkActiveShare) : "미계산"}</strong>
            <small>
              {benchmarkDriftCalculated
                ? `${benchmarkCode} · ${benchmarkSource || "구성비 저장됨"}`
                : "구성비 없으면 추정하지 않음"}
            </small>
          </article>
        </div>
      </article>
    </>
  );
}
