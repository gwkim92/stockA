import { koCode } from "@/lib/korean-labels";

import type { PortfolioReviewFeedbackCalibration } from "./dataHealthTypes";
import {
  feedbackStatusClass,
  formatPercent,
  operationCopy,
  orderBoundaryCopy,
  orderSubmitCopy,
  recordLabel,
} from "./dataHealthModel";

type DataHealthPortfolioReviewCalibrationSectionProps = {
  readonly portfolioReviewCalibration: PortfolioReviewFeedbackCalibration;
};

export function DataHealthPortfolioReviewCalibrationSection({
  portfolioReviewCalibration,
}: DataHealthPortfolioReviewCalibrationSectionProps) {
  return (
      <section
        className="feature-map-panel reveal delay-1"
        id="portfolio-review-calibration"
        aria-labelledby="portfolio-review-calibration-title"
      >
        <div className="section-heading stacked-heading">
          <span>포트폴리오 검토 신뢰도 누적평가</span>
	          <h2 id="portfolio-review-calibration-title">성과 표본이 성숙하기 전에는 추천 산식 반영 비중을 바꾸지 않는다.</h2>
        </div>
        <p className="board-intro">
	          검토 결정은 최소 관찰 기간을 지난 뒤 실제 성과와 대조해야 한다. 이 섹션은 지금 추천 산식 변경이 왜
          막혀 있는지, 어떤 표본이 부족한지, 언제 다시 사후평가를 실행해야 하는지를 보여주는 읽기 전용 안전장치다.
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
	            <span>추천 산식 검토 상태</span>
            <strong className={`risk-tag ${portfolioReviewCalibration.managed_wait ? "risk-low" : portfolioReviewCalibration.weight_review_blocked ? "risk-medium" : "risk-low"}`}>
              {portfolioReviewCalibration.managed_wait
                ? "관리된 대기"
                : portfolioReviewCalibration.weight_review_blocked
                  ? "변경 금지"
                  : "성과 표본 충족"}
            </strong>
            <small>{operationCopy(portfolioReviewCalibration.maturity_status)} · {recordLabel(portfolioReviewCalibration.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
	            <span>사후평가 실행</span>
            <strong>
              {portfolioReviewCalibration.feedback_run_count}/{portfolioReviewCalibration.min_feedback_runs}
            </strong>
	            <small>부족 {portfolioReviewCalibration.feedback_run_gap}회 · {portfolioReviewCalibration.lookback_days || "기간 미확인"}일 관찰</small>
          </article>
          <article className="rail-cell">
            <span>성숙한 판단</span>
            <strong>
              {portfolioReviewCalibration.mature_decision_count}/{portfolioReviewCalibration.min_mature_decisions}
            </strong>
            <small>부족 {portfolioReviewCalibration.mature_decision_gap}개 · 전체 판단 {portfolioReviewCalibration.decision_count}개</small>
          </article>
          <article className="rail-cell">
            <span>예상 성숙일</span>
            <strong>{portfolioReviewCalibration.estimated_maturity_date || "계산 불가"}</strong>
            <small>
              {portfolioReviewCalibration.days_until_maturity === null
                ? "다음 실행 조건 미확인"
                : portfolioReviewCalibration.days_until_maturity > 0
                  ? `${portfolioReviewCalibration.days_until_maturity}일 대기`
                  : "다시 평가 가능일 도달"}
            </small>
          </article>
          <article className="rail-cell">
            <span>검증 / 반박률</span>
            <strong>
              {portfolioReviewCalibration.validated_count} / {formatPercent(portfolioReviewCalibration.contradiction_rate)}
            </strong>
            <small>허용 반박률 {formatPercent(portfolioReviewCalibration.max_contradiction_rate)}</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(portfolioReviewCalibration.guardrails.order_boundary)}</strong>
	            <small>{orderSubmitCopy(portfolioReviewCalibration.guardrails.broker_submit_allowed)}</small>
          </article>
        </div>
        <div className="empty-state">
	          <strong>{portfolioReviewCalibration.managed_wait ? "왜 열린 문제로 보지 않는가" : "왜 막혀 있나"}</strong>
          <p>
            {portfolioReviewCalibration.managed_wait
	              ? operationCopy(portfolioReviewCalibration.managed_gate_reason)
	              : operationCopy(portfolioReviewCalibration.weight_review_block_reason)}
          </p>
        </div>
        <div className="insight-grid">
          {portfolioReviewCalibration.family_summaries.slice(0, 3).map((summary) => (
            <article className="insight-card" key={`family-${summary.decision_family}`}>
	              <span>판단군</span>
              <strong>{koCode(summary.decision_family || "unknown")}</strong>
              <p>
                전체 {summary.decision_count}개 · 성숙 {summary.mature_decision_count}개 · 반박{" "}
                {summary.contradicted_count}개 · 아직 이른 판단 {summary.too_early_count}개
              </p>
            </article>
          ))}
          {portfolioReviewCalibration.symbol_summaries.slice(0, 3).map((summary) => (
            <article className="insight-card" key={`symbol-${summary.symbol}`}>
	              <span>종목별 사후평가</span>
              <strong>{summary.symbol || "미분류"}</strong>
              <p>
                성숙 {summary.mature_decision_count}개 · 검증 {summary.validated_count}개 · 반박률{" "}
                {formatPercent(summary.contradiction_rate)}
              </p>
            </article>
          ))}
          {portfolioReviewCalibration.family_summaries.length === 0
            && portfolioReviewCalibration.symbol_summaries.length === 0 ? (
              <article className="insight-card">
                <span>누적 자료 없음</span>
	                <strong>사후평가를 더 쌓아야 함</strong>
	                <p>검토 이력과 사후평가가 여러 번 쌓여야 별도 추천 산식 검토로 넘어갈 수 있다.</p>
              </article>
            ) : null}
        </div>
        {portfolioReviewCalibration.latest_feedback_runs.length > 0 ? (
          <div className="ledger-table-wrap">
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">평가 기록</th>
                  <th scope="col">기준일</th>
                  <th scope="col">상태</th>
                  <th scope="col">검증/반박</th>
                  <th scope="col">아직 이른 판단</th>
                </tr>
              </thead>
              <tbody>
                {portfolioReviewCalibration.latest_feedback_runs.map((run) => (
                  <tr key={`${run.eval_run_id}-${run.as_of_date}`}>
                    <td>{recordLabel(run.eval_run_id)}</td>
                    <td>{run.as_of_date || "기준일 없음"}</td>
                    <td>
                      <span className={`risk-tag ${feedbackStatusClass(run.feedback_status)}`}>
                        {koCode(run.feedback_status)}
                      </span>
                    </td>
                    <td>{run.validated_count} / {run.contradicted_count}</td>
                    <td>{run.too_early_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        <div className="empty-state">
          <strong>다음 조치</strong>
	          <p>{operationCopy(portfolioReviewCalibration.next_calibration_action || portfolioReviewCalibration.next_action)}</p>
        </div>
      </section>
  );
}
