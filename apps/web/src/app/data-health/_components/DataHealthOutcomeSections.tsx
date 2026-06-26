import { koCode } from "@/lib/korean-labels";

import type {
  OutcomeMaturityWaitMonitor,
  RecommendationOutcomeCalibration,
  RecommendationOutcomeDueActionRouter,
  RecommendationOutcomeMaturity,
  RecommendationWeightReviewReadiness,
} from "./dataHealthTypes";
import {
  actionRouterStatusClass,
  formatPercent,
  operationCopy,
  orderBoundaryCopy,
  orderSubmitCopy,
  outcomeCalibrationExplanation,
  outcomeCalibrationTitle,
  outcomeCalibrationTone,
  outcomeDueActionRouterTitle,
  outcomeMaturityExplanation,
  outcomeMaturityTitle,
  outcomeMaturityTone,
  outcomeWaitMonitorTone,
  recordLabel,
} from "./dataHealthModel";

type DataHealthOutcomeSectionsProps = {
  readonly outcomeWaitMonitor: OutcomeMaturityWaitMonitor;
  readonly outcomeCalibration: RecommendationOutcomeCalibration;
  readonly outcomeMaturity: RecommendationOutcomeMaturity;
  readonly outcomeDueActionRouter: RecommendationOutcomeDueActionRouter;
  readonly weightReviewReadiness: RecommendationWeightReviewReadiness;
};

export function DataHealthOutcomeSections({
  outcomeWaitMonitor,
  outcomeCalibration,
  outcomeMaturity,
  outcomeDueActionRouter,
  weightReviewReadiness,
}: DataHealthOutcomeSectionsProps) {
  return (
    <>
	      <section
	        className="feature-map-panel reveal delay-1"
	        id="outcome-maturity-wait-monitor"
        aria-labelledby="outcome-maturity-wait-monitor-title"
      >
        <div className="section-heading stacked-heading">
          <span>성과 성숙 대기 모니터</span>
          <h2 id="outcome-maturity-wait-monitor-title">
	            추천 성과와 포트폴리오 사후평가가 성숙하기 전에는 추천 산식 반영 비중을 바꾸지 않는다.
          </h2>
        </div>
        <p className="board-intro">
          {operationCopy(outcomeWaitMonitor.summary)} {operationCopy(outcomeWaitMonitor.next_action)}
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>현재 결론</span>
            <strong className={`risk-tag ${outcomeWaitMonitorTone(outcomeWaitMonitor)}`}>
              {outcomeWaitMonitor.title}
            </strong>
            <small>{outcomeWaitMonitor.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell">
	            <span>추천 성과</span>
            <strong>{outcomeWaitMonitor.recommendation_next_due_date || "대기일 없음"}</strong>
            <small>
              다음 창 {outcomeWaitMonitor.recommendation_next_due_count}개 · 상태{" "}
              {koCode(outcomeWaitMonitor.recommendation_maturity_status)}
            </small>
          </article>
          <article className="rail-cell">
	            <span>포트폴리오 사후평가</span>
            <strong>{outcomeWaitMonitor.portfolio_feedback_maturity_date || "성숙일 없음"}</strong>
            <small>
              성숙 판단 부족 {outcomeWaitMonitor.portfolio_mature_decision_gap}개 · 실행 부족{" "}
              {outcomeWaitMonitor.portfolio_feedback_run_gap}회
            </small>
          </article>
          <article className="rail-cell rail-critical">
            <span>추천 산식 검토</span>
            <strong>{outcomeWaitMonitor.weight_review_blocked ? "변경 차단" : "성과 표본 충족"}</strong>
            <small>실거래 상태 {orderBoundaryCopy(outcomeWaitMonitor.order_boundary)}</small>
          </article>
        </div>
        <div className="insight-grid">
          {outcomeWaitMonitor.wait_items.map((item) => (
            <article className="insight-card" key={item.scope}>
              <span>{item.label}</span>
              <strong>{item.wait_until || "날짜 미정"}</strong>
              <p>{operationCopy(item.reason)}</p>
              <small>
                {koCode(item.status)} · {koCode(item.action_status)} · 대상 {item.count}개
              </small>
            </article>
          ))}
          <article className="insight-card">
            <span>추천 산식 차단 이유</span>
            <strong>{outcomeWaitMonitor.manual_weight_review_allowed ? "성과 표본 충족" : "성과 표본 대기"}</strong>
            <p>{operationCopy(outcomeWaitMonitor.weight_review_block_reason)}</p>
          </article>
          <article className="insight-card">
            <span>안전 경계</span>
            <strong>{outcomeWaitMonitor.automatic_weight_change_allowed ? "자동 변경 허용" : "자동 변경 금지"}</strong>
            <p>
              추천 점수 변경 {outcomeWaitMonitor.recommendation_scoring_mutated ? "감지" : "없음"} ·
              {orderSubmitCopy(outcomeWaitMonitor.broker_submit_allowed)}
            </p>
          </article>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="outcome-calibration"
        aria-labelledby="outcome-calibration-title"
      >
        <div className="section-heading stacked-heading">
          <span>추천 성과검증</span>
          <h2 id="outcome-calibration-title">추천 산식 반영 비중을 바꾸기 전 성과 표본과 부진 사례</h2>
        </div>
        <p className="board-intro">{outcomeCalibrationExplanation(outcomeCalibration)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>판정</span>
            <strong className={`risk-tag ${outcomeCalibrationTone(outcomeCalibration)}`}>
              {outcomeCalibrationTitle(outcomeCalibration)}
            </strong>
            <small>{recordLabel(outcomeCalibration.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>성과 표본</span>
            <strong>
              {outcomeCalibration.outcome_count}/{outcomeCalibration.recommendation_horizon_count}
            </strong>
            <small>추천×기간 기준</small>
          </article>
          <article className="rail-cell">
            <span>표본 연결률</span>
            <strong>{formatPercent(outcomeCalibration.outcome_coverage_rate)}</strong>
            <small>{outcomeCalibration.horizon_days.join(" · ") || "기간 미확인"}일</small>
          </article>
          <article className="rail-cell">
            <span>추가 산출 후보</span>
            <strong>{outcomeCalibration.ready_for_backfill_count}</strong>
            <small>가격 이력으로 계산 가능</small>
          </article>
          <article className="rail-cell">
            <span>컴포넌트 진단</span>
            <strong>{outcomeCalibration.component_diagnostic_count}</strong>
            <small>zero-weight 전문 지표</small>
          </article>
        </div>
        <div className="insight-grid">
          <article className="insight-card">
            <span>성과 측정창</span>
            <strong className={`risk-tag ${outcomeMaturityTone(outcomeMaturity)}`}>
              {outcomeMaturityTitle(outcomeMaturity)}
            </strong>
            <p>{outcomeMaturityExplanation(outcomeMaturity)}</p>
          </article>
          <article className="insight-card">
            <span>다음 측정일</span>
            <strong>{outcomeMaturity.next_due_date || "대기 없음"}</strong>
            <p>
              다음에 열릴 추천×기간 {outcomeMaturity.next_due_count}개 · 아직 대기{" "}
              {outcomeMaturity.not_due_count}개 · 산출 가능 {outcomeMaturity.ready_for_backfill_count}개
            </p>
          </article>
          <article className="insight-card">
            <span>지연/가격 보강</span>
            <strong>{outcomeMaturity.overdue_count + outcomeMaturity.price_gap_count}</strong>
            <p>
              지연 {outcomeMaturity.overdue_count}개, 가격 이력 부족 {outcomeMaturity.price_gap_count}개다. 이 값이
	              있으면 추천 산식 검토보다 성과 보강이 먼저다.
            </p>
          </article>
          <article className="insight-card">
            <span>실행 액션</span>
            <strong>{koCode(outcomeMaturity.cadence_action.status)}</strong>
            <p>{operationCopy(outcomeMaturity.cadence_action.reason)}</p>
            <small>{operationCopy(outcomeMaturity.cadence_action.label)}</small>
          </article>
          <article className="insight-card">
            <span>성과 실행 라우터</span>
            <strong className={`risk-tag ${actionRouterStatusClass(outcomeDueActionRouter.action_status)}`}>
              {outcomeDueActionRouterTitle(outcomeDueActionRouter)}
            </strong>
            <p>{operationCopy(outcomeDueActionRouter.reason || "저장된 실행 분기 판단이 없다.")}</p>
            <small>{recordLabel(outcomeDueActionRouter.eval_run_id)}</small>
          </article>
          <article className="insight-card">
            <span>후속 실행</span>
            <strong>{outcomeDueActionRouter.child_runner.executed ? "실행됨" : "실행 안 함"}</strong>
            <p>
              {outcomeDueActionRouter.child_runner.executed
                ? `${operationCopy(outcomeDueActionRouter.child_runner.report_name)} · ${recordLabel(outcomeDueActionRouter.child_runner.eval_run_id)}`
                : "측정일 대기, 가격 이력 차단, 또는 안전 조건 때문에 누적평가 실행을 시작하지 않았다."}
            </p>
          </article>
          <article className="insight-card">
            <span>추천 산식 반영 비중</span>
            <strong>{outcomeCalibration.recommendation_scoring_mutated ? "변경 감지" : "변경 없음"}</strong>
            <p>성과 검증은 추천 산식 변경이 아니다. 반영 비중 조정은 별도 승인된 시험 작업 전까지 막는다.</p>
          </article>
          <article className="insight-card">
            <span>가격 이력 부족</span>
            <strong>
              {outcomeCalibration.missing_entry_price_count + outcomeCalibration.missing_exit_price_count}
            </strong>
            <p>entry 또는 exit 가격이 없어 성과 산출이 막힌 추천×기간 수다.</p>
          </article>
          <article className="insight-card">
            <span>품질 평가</span>
            <strong>{koCode(outcomeCalibration.quality_status)}</strong>
            <p>전문 분석 연결률과 성과 표본이 추천 산식 검토 기준을 충족하는지 본다.</p>
          </article>
          <article className="insight-card">
            <span>추천 산식 변경 조건</span>
            <strong>{weightReviewReadiness.manual_weight_review_allowed ? "성과 표본 충족" : "변경 차단"}</strong>
            <p>
              {weightReviewReadiness.blocker_message
                ? operationCopy(weightReviewReadiness.blocker_message)
                : operationCopy(weightReviewReadiness.next_action)}
            </p>
          </article>
          <article className="insight-card">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(outcomeCalibration.order_boundary)}</strong>
            <p>성과검증은 주문 생성이나 실거래 제출을 허용하지 않는다.</p>
          </article>
        </div>
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(outcomeDueActionRouter.next_action || outcomeMaturity.cadence_action.label)}</p>
        </div>
      </section>
    </>
  );
}
