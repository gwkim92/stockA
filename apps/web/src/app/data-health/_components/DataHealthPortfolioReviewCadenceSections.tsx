import { koCode } from "@/lib/korean-labels";

import type { PortfolioReviewFeedbackActionRouter, PortfolioReviewFeedbackCadence } from "./dataHealthTypes";
import {
  actionRouterStatusClass,
  actionRouterTitle,
  cadenceStatusClass,
  operationCopy,
  orderBoundaryCopy,
  orderSubmitCopy,
  recordLabel,
} from "./dataHealthModel";

type DataHealthPortfolioReviewCadenceSectionsProps = {
  readonly portfolioReviewCadence: PortfolioReviewFeedbackCadence;
  readonly portfolioReviewActionRouter: PortfolioReviewFeedbackActionRouter;
};

export function DataHealthPortfolioReviewCadenceSections({
  portfolioReviewCadence,
  portfolioReviewActionRouter,
}: DataHealthPortfolioReviewCadenceSectionsProps) {
  return (
    <>
      <section
        className="feature-map-panel reveal delay-1"
        id="portfolio-review-cadence"
        aria-labelledby="portfolio-review-cadence-title"
      >
        <div className="section-heading stacked-heading">
          <span>포트폴리오 검토 실행시점</span>
          <h2 id="portfolio-review-cadence-title">사후평가와 누적평가를 언제 다시 돌릴지 판단한다.</h2>
        </div>
        <p className="board-intro">
	          검토 이력, 성과 측정 기간, 가격·가상 매매 검증 근거, 최신 사후평가, 최신 누적평가의 연결 상태를 보고
	          기다릴지, 사후평가를 실행할지, 누적평가를 실행할지 결정한다. 이 판단도 주문이나 추천 산식 변경이 아니다.
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
	            <span>실행 주기 상태</span>
            <strong className={`risk-tag ${cadenceStatusClass(portfolioReviewCadence.cadence_status)}`}>
              {koCode(portfolioReviewCadence.cadence_status)}
            </strong>
            <small>{recordLabel(portfolioReviewCadence.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>실행 여부</span>
            <strong>{portfolioReviewCadence.should_run_now ? "지금 실행" : "즉시 실행 아님"}</strong>
            <small>{portfolioReviewCadence.should_wait ? "대기 필요" : "대기 조건 없음"}</small>
          </article>
          <article className="rail-cell">
            <span>검토 이력 나이</span>
            <strong>{portfolioReviewCadence.evidence.history_age_days}일</strong>
            <small>최소 {portfolioReviewCadence.min_horizon_days}일 관찰</small>
          </article>
          <article className="rail-cell">
            <span>근거 연결률</span>
            <strong>
              {portfolioReviewCadence.evidence.recommendation_outcome_count}/
              {portfolioReviewCadence.evidence.recommendation_link_count}
            </strong>
	            <small>성과 연결 · 가격 {portfolioReviewCadence.evidence.price_evidence_count}개</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(portfolioReviewCadence.order_boundary)}</strong>
	            <small>{orderSubmitCopy(portfolioReviewCadence.broker_submit_allowed)}</small>
          </article>
        </div>
        <div className="insight-grid">
          <article className="insight-card">
            <span>다음 명령</span>
            <strong>{koCode(portfolioReviewCadence.action_type)}</strong>
	            <p>{operationCopy(portfolioReviewCadence.label)}</p>
	            <small>{operationCopy(portfolioReviewCadence.reason)}</small>
          </article>
          <article className="insight-card">
            <span>후속 명령</span>
            <strong>{portfolioReviewCadence.follow_up_command ? "있음" : "없음"}</strong>
            <p>{portfolioReviewCadence.follow_up_command || "현재 후속 명령은 없다."}</p>
          </article>
          <article className="insight-card">
	            <span>검토 이력 → 사후평가</span>
            <strong>
              {recordLabel(portfolioReviewCadence.history.eval_run_id)} → {recordLabel(portfolioReviewCadence.feedback.eval_run_id)}
            </strong>
            <p>
	              이력 {portfolioReviewCadence.history.decision_count}개 · 사후평가{" "}
              {portfolioReviewCadence.feedback.decision_count}개 · 상태{" "}
              {koCode(portfolioReviewCadence.feedback.feedback_status)}
            </p>
          </article>
          <article className="insight-card">
	            <span>사후평가 → 누적평가</span>
            <strong>
              {recordLabel(portfolioReviewCadence.feedback.eval_run_id)} → {recordLabel(portfolioReviewCadence.calibration.eval_run_id)}
            </strong>
            <p>
	              누적 사후평가 {portfolioReviewCadence.calibration.feedback_run_count}회 · 성숙 판단{" "}
              {portfolioReviewCadence.calibration.mature_decision_count}개
            </p>
          </article>
          <article className="insight-card">
	            <span>가상 매매 검증</span>
            <strong>{operationCopy(portfolioReviewCadence.evidence.paper_validation.status)}</strong>
            <p>
              검증일 {portfolioReviewCadence.evidence.paper_validation.validation_date || "없음"} · 충돌{" "}
              {portfolioReviewCadence.evidence.paper_validation.conflict_count}개
            </p>
          </article>
          <article className="insight-card">
	            <span>추천 산식 반영 비중</span>
            <strong>{portfolioReviewCadence.automatic_weight_change_allowed ? "변경 허용" : "변경 금지"}</strong>
	            <p>실행 주기 판단은 실행 순서만 정한다. 추천 점수와 포트폴리오 비중은 바꾸지 않는다.</p>
          </article>
        </div>
        <div className="empty-state">
          <strong>다음 조치</strong>
	          <p>{operationCopy(portfolioReviewCadence.next_action)}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="portfolio-review-action-router"
        aria-labelledby="portfolio-review-action-router-title"
      >
        <div className="section-heading stacked-heading">
	          <span>포트폴리오 검토 실행 분기</span>
          <h2 id="portfolio-review-action-router-title">대기할지, 사후평가를 돌릴지, 누적평가를 돌릴지 기록한다.</h2>
        </div>
        <p className="board-intro">
	          실행 주기는 “언제 실행해야 하는가”를 판단하고, 실행 분기는 그 판단을 안전한 후속 작업으로 바꾼다.
	          이 실행 분기가 동작해도 추천 산식 반영 비중, 보유 비중, 주문 전송은 자동으로 바뀌지 않는다.
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
	            <span>실행 분기 결과</span>
            <strong className={`risk-tag ${actionRouterStatusClass(portfolioReviewActionRouter.action_status)}`}>
              {actionRouterTitle(portfolioReviewActionRouter)}
            </strong>
            <small>{recordLabel(portfolioReviewActionRouter.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
	            <span>원천 실행 주기</span>
            <strong>{koCode(portfolioReviewActionRouter.cadence_status)}</strong>
            <small>{recordLabel(portfolioReviewActionRouter.source_cadence_eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>라우팅</span>
            <strong>{koCode(portfolioReviewActionRouter.route_action)}</strong>
            <small>요청 작업 {koCode(portfolioReviewActionRouter.source_action_type)}</small>
          </article>
          <article className="rail-cell">
            <span>실행한 작업</span>
            <strong>{portfolioReviewActionRouter.child_runner.executed ? "있음" : "없음"}</strong>
            <small>
              {portfolioReviewActionRouter.child_runner.executed
                ? `${operationCopy(portfolioReviewActionRouter.child_runner.report_name)} · ${recordLabel(portfolioReviewActionRouter.child_runner.eval_run_id)}`
	                : "성과 관찰 또는 안전 조건 때문에 후속 실행을 시작하지 않았다."}
            </small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(portfolioReviewActionRouter.order_boundary)}</strong>
	            <small>{orderSubmitCopy(portfolioReviewActionRouter.broker_submit_allowed)}</small>
          </article>
        </div>
        <div className="insight-grid">
          <article className="insight-card">
            <span>왜 이 결론인가</span>
            <strong>{koCode(portfolioReviewActionRouter.action_status)}</strong>
	            <p>{operationCopy(portfolioReviewActionRouter.reason || "저장된 설명 없음")}</p>
          </article>
          <article className="insight-card">
            <span>검토 이력 연결</span>
            <strong>{recordLabel(portfolioReviewActionRouter.history_eval_run_id)}</strong>
            <p>
	              사후평가 {recordLabel(portfolioReviewActionRouter.feedback_eval_run_id)} · 누적평가{" "}
              {recordLabel(portfolioReviewActionRouter.calibration_eval_run_id)}
            </p>
          </article>
          <article className="insight-card">
	            <span>후속 실행 상태</span>
            <strong>{koCode(portfolioReviewActionRouter.child_runner.status)}</strong>
            <p>
              실행 기록 {recordLabel(portfolioReviewActionRouter.child_runner.run_id)}
	              {portfolioReviewActionRouter.child_runner.feedback_status
	                ? ` · 사후평가 ${koCode(portfolioReviewActionRouter.child_runner.feedback_status)}`
	                : ""}
	              {portfolioReviewActionRouter.child_runner.calibration_status
	                ? ` · 누적평가 ${koCode(portfolioReviewActionRouter.child_runner.calibration_status)}`
	                : ""}
            </p>
          </article>
          <article className="insight-card">
            <span>안전 장치</span>
	            <strong>{portfolioReviewActionRouter.automatic_weight_change_allowed ? "추천 산식 변경 허용" : "추천 산식 변경 금지"}</strong>
            <p>
              리밸런싱 {portfolioReviewActionRouter.automatic_rebalance_allowed ? "허용" : "금지"} · 주문{" "}
              {portfolioReviewActionRouter.automatic_order_allowed ? "허용" : "금지"}
            </p>
          </article>
        </div>
	        <div className="empty-state">
	          <strong>다음 조치</strong>
	          <p>{operationCopy(portfolioReviewActionRouter.next_action)}</p>
	        </div>
	      </section>
    </>
  );
}
