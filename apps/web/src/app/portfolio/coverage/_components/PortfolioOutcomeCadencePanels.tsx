import type { PortfolioCoverageData } from "@/lib/types";

import {
  actionRouterLabel,
  actionRouterStatusClass,
  cadenceStatusClass,
  formatCoveragePercent,
  orderBoundaryLabel,
  orderSubmitLabel,
  recordPresent,
  userFacingText,
} from "./portfolioCoverageFormat";

type PortfolioOutcomeCadencePanelsProps = {
  readonly reviewActionRouter: PortfolioCoverageData["risk_budget"]["review_feedback_action_router"];
  readonly reviewCadence: PortfolioCoverageData["risk_budget"]["review_feedback_cadence"];
  readonly reviewCalibration: PortfolioCoverageData["risk_budget"]["review_feedback_calibration"];
};

export function PortfolioOutcomeCadencePanels({
  reviewActionRouter,
  reviewCadence,
  reviewCalibration,
}: PortfolioOutcomeCadencePanelsProps) {
  return (
    <>
      <article
        id="portfolio-outcome-boundary"
        className="bento-card span-4"
        style={{ borderColor: reviewCalibration.calibration_status === "contradiction_review_required" ? "var(--accent-red)" : "var(--border-light)" }}
      >
        <div className="section-heading">
          <div>
            <span className="metric-sub">포트폴리오 결정 신뢰도</span>
            <h2>성과 표본이 성숙하기 전에는 추천 산식 비중을 바꾸지 않는다</h2>
          </div>
          <span className={`risk-tag ${reviewCalibration.weight_review_blocked ? "risk-medium" : "risk-low"}`}>
            {reviewCalibration.status === "loaded"
              ? reviewCalibration.weight_review_blocked ? "추천 산식 변경 금지" : "조건 확인 가능"
              : "누적평가 없음"}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          포트폴리오 비중 결정은 실제 성과 관찰 기간이 지난 뒤 평가합니다. 이 카드의 목적은 왜 아직 금지인지와
          다음 성숙 시점을 보여주는 것입니다.
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
            <small>반박률 {formatCoveragePercent(reviewCalibration.contradiction_rate)}</small>
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
                반박률 {formatCoveragePercent(summary.contradiction_rate)}
              </span>
            </div>
          ))}
          {reviewCalibration.family_summaries.length === 0 ? (
            <p className="empty-state" style={{ margin: 0 }}>
              아직 누적평가 자료가 없습니다. 사후평가가 쌓이면 결정 유형별 신뢰도가 표시됩니다.
            </p>
          ) : null}
        </div>
      </article>

      <article
        className="bento-card span-4"
        style={{ borderColor: reviewCadence.should_run_now ? "var(--accent-red)" : "var(--border-light)" }}
      >
        <div className="section-heading">
          <div>
            <span className="metric-sub">사후평가 실행 시점</span>
            <h2>사후평가와 누적평가 일정</h2>
          </div>
          <span className={`risk-tag ${cadenceStatusClass(reviewCadence.cadence_status)}`}>
            {reviewCadence.status === "loaded" ? userFacingText(reviewCadence.cadence_status) : "실행 주기 없음"}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          최신 결정 이력, 사후평가와 누적평가의 연결 상태입니다. 실행 필요가 표시되어도 주문이나 추천 산식 변경은
          자동으로 허용되지 않습니다.
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
            <h2>성과 평가 실행 결과</h2>
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
          실행 주기 결과가 안전 작업으로 이어진 상태입니다. 실행 기록이 있어도 추천 산식 비중, 보유 비중과
          실거래 주문 전송은 자동으로 바뀌지 않습니다.
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
    </>
  );
}
