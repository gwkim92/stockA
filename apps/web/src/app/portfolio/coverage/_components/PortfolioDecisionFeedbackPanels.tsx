import type { PortfolioCoverageData } from "@/lib/types";

import {
  candidateSeverityClass,
  feedbackStatusClass,
  formatCoveragePercent,
  orderBoundaryLabel,
  orderSubmitLabel,
  recordPresent,
  userFacingText,
} from "./portfolioCoverageFormat";

type PortfolioDecisionFeedbackPanelsProps = {
  readonly reviewFeedback: PortfolioCoverageData["risk_budget"]["review_decision_feedback"];
  readonly reviewHistory: PortfolioCoverageData["risk_budget"]["review_decision_history"];
};

export function PortfolioDecisionFeedbackPanels({ reviewFeedback, reviewHistory }: PortfolioDecisionFeedbackPanelsProps) {
  return (
    <>
      <article
        className="bento-card span-4"
        style={{ borderColor: reviewHistory.decision_status === "review_required" ? "var(--accent-amber)" : "var(--border-light)" }}
      >
        <div className="section-heading">
          <div>
            <span className="metric-sub">저장된 포트폴리오 결정 이력</span>
            <h2>오늘 보이는 후보가 감사 이력으로 남았는지 확인</h2>
          </div>
          <span className={`risk-tag ${reviewHistory.decision_status === "review_required" ? "risk-medium" : "risk-low"}`}>
            {reviewHistory.status === "loaded" ? userFacingText(reviewHistory.decision_status) : "이력 없음"}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          리밸런싱 검토 후보와 포지션 크기 상태는 주문이 아니라 의사결정 기록입니다. 이력이 있어야 나중에
          당시 근거를 다시 추적할 수 있습니다.
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
            <small>점검 필요 {reviewHistory.review_required_count}개</small>
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
            아직 저장된 결정 이력이 없습니다. 포트폴리오 결정 이력이 생성되면 최신 결정이 표시됩니다.
          </p>
        )}
      </article>

      <article
        className="bento-card span-4"
        style={{ borderColor: reviewFeedback.feedback_status === "has_contradictions" ? "var(--accent-red)" : "var(--border-light)" }}
      >
        <div className="section-heading">
          <div>
            <span className="metric-sub">포트폴리오 결정 사후평가</span>
            <h2>저장한 결정이 이후 성과와 맞았는지 확인</h2>
          </div>
          <span className={`risk-tag ${feedbackStatusClass(reviewFeedback.feedback_status)}`}>
            {reviewFeedback.status === "loaded" ? userFacingText(reviewFeedback.feedback_status) : "평가 없음"}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          이 평가는 추천 산식 비중을 바꾸지 않습니다. 이전 결정을 성과 측정, 가상 매매 검증, 투자 논리,
          가격 변화와 대조해 다음 판단의 신뢰도를 높이는 자료입니다.
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
                  {formatCoveragePercent(item.evidence.recommendation_outcome.alpha_pct)} · 가격{" "}
                  {formatCoveragePercent(item.evidence.price_evidence.price_return_pct)}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="empty-state" style={{ margin: 0 }}>
            아직 사후평가 이력이 없습니다. 성과 측정 기간이 끝난 뒤 저장된 결정이 맞았는지 표시됩니다.
          </p>
        )}
      </article>
    </>
  );
}
