import { koCode, koReason } from "@/lib/korean-labels";

import type { PortfolioReviewDecisionFeedback, PortfolioReviewDecisionHistory } from "./dataHealthTypes";
import {
  decisionSeverityClass,
  feedbackStatusClass,
  formatPercent,
  operationCopy,
  orderBoundaryCopy,
  orderSubmitCopy,
  recordLabel,
} from "./dataHealthModel";

type DataHealthPortfolioReviewHistorySectionsProps = {
  readonly portfolioReviewHistory: PortfolioReviewDecisionHistory;
  readonly portfolioReviewFeedback: PortfolioReviewDecisionFeedback;
};

export function DataHealthPortfolioReviewHistorySections({
  portfolioReviewHistory,
  portfolioReviewFeedback,
}: DataHealthPortfolioReviewHistorySectionsProps) {
  return (
    <>
      <section
        className="feature-map-panel reveal delay-1"
        id="portfolio-review-history"
        aria-labelledby="portfolio-review-history-title"
      >
        <div className="section-heading stacked-heading">
          <span>포트폴리오 검토 결정 이력</span>
          <h2 id="portfolio-review-history-title">화면에서 본 판단이 나중에도 추적되는가</h2>
        </div>
        <p className="board-intro">
          {portfolioReviewHistory.attention_required
            ? "벤치마크 괴리와 포지션 크기 검토는 주문 지시가 아니다. 이 섹션은 그 판단 후보가 언제 어떤 근거로 저장됐는지 보여주는 감사 이력이다."
            : operationCopy(portfolioReviewHistory.managed_review_reason)}
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>상태</span>
            <strong className={`risk-tag ${portfolioReviewHistory.attention_required ? "risk-medium" : "risk-low"}`}>
              {portfolioReviewHistory.attention_required ? koCode(portfolioReviewHistory.decision_status) : "관리 중"}
            </strong>
            <small>{recordLabel(portfolioReviewHistory.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>기준일</span>
            <strong>{portfolioReviewHistory.as_of_date || "미저장"}</strong>
            <small>{portfolioReviewHistory.created_at || "생성 시각 없음"}</small>
          </article>
          <article className="rail-cell">
            <span>저장된 결정</span>
            <strong>{portfolioReviewHistory.decision_count}</strong>
            <small>보강 필요 {portfolioReviewHistory.review_required_count}개</small>
          </article>
          <article className="rail-cell">
            <span>벤치마크 / 포지션</span>
            <strong>
              {portfolioReviewHistory.benchmark_decision_count} / {portfolioReviewHistory.position_sizing_decision_count}
            </strong>
	            <small>판단군 분리 저장</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(portfolioReviewHistory.guardrails.order_boundary)}</strong>
	            <small>{orderSubmitCopy(portfolioReviewHistory.guardrails.broker_submit_allowed)}</small>
          </article>
        </div>
        {portfolioReviewHistory.latest_decisions.length > 0 ? (
          <div className="ledger-table-wrap">
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">순위</th>
                  <th scope="col">종목</th>
                  <th scope="col">결정</th>
	                  <th scope="col">판단군</th>
                  <th scope="col">근거</th>
                </tr>
              </thead>
              <tbody>
                {portfolioReviewHistory.latest_decisions.slice(0, 8).map((decision) => (
                  <tr key={`${decision.decision_family}-${decision.priority}-${decision.symbol}`}>
                    <td>{decision.priority.toString().padStart(2, "0")}</td>
                    <td>
                      <strong>{decision.symbol}</strong>
                      <small>{decision.related_recommendation_id || "추천 연결 없음"}</small>
                    </td>
                    <td>
                      <span className={`risk-tag ${decisionSeverityClass(decision.severity)}`}>
                        {decision.decision_label || koCode(decision.decision_type)}
                      </span>
                      <small>{operationCopy(koReason(decision.next_review_action))}</small>
                    </td>
                    <td>{operationCopy(decision.decision_family)}</td>
                    <td>
	                      <small>{operationCopy(koReason(decision.rationale || "저장된 설명 없음"))}</small>
	                      <small>{orderBoundaryCopy(decision.order_boundary)} · {orderSubmitCopy(decision.broker_submit_allowed)}</small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            아직 저장된 포트폴리오 검토 결정 이력이 없다. 최신 후보를 이력화하려면 검토 이력 저장 작업을 실행해야 한다.
          </div>
        )}
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(portfolioReviewHistory.next_action)}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="portfolio-review-feedback"
        aria-labelledby="portfolio-review-feedback-title"
      >
        <div className="section-heading stacked-heading">
          <span>포트폴리오 검토 사후평가</span>
          <h2 id="portfolio-review-feedback-title">저장한 판단이 나중의 성과와 맞았는지 본다.</h2>
        </div>
        <p className="board-intro">
	          이 섹션은 검토 결정을 추천 산식 반영 비중으로 바로 바꾸지 않는다. 저장된 축소 검토, 증액 금지, 유지 검토가
	          이후 추천 성과, 투자 논리 성과, 가상 매매 검증, 가격 변화와 맞았는지만 읽기 전용으로 평가한다.
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>평가 상태</span>
            <strong className={`risk-tag ${feedbackStatusClass(portfolioReviewFeedback.feedback_status)}`}>
              {koCode(portfolioReviewFeedback.feedback_status)}
            </strong>
            <small>{recordLabel(portfolioReviewFeedback.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>검증 / 반박</span>
            <strong>
              {portfolioReviewFeedback.validated_count} / {portfolioReviewFeedback.contradicted_count}
            </strong>
            <small>전체 {portfolioReviewFeedback.decision_count}개 결정</small>
          </article>
          <article className="rail-cell">
            <span>아직 이른 항목</span>
            <strong>{portfolioReviewFeedback.too_early_count}</strong>
            <small>{portfolioReviewFeedback.min_horizon_days}일 최소 관찰</small>
          </article>
          <article className="rail-cell">
            <span>근거 부족</span>
            <strong>{portfolioReviewFeedback.needs_more_data_count}</strong>
	            <small>성과/가상 매매/가격 보강 필요</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(portfolioReviewFeedback.guardrails.order_boundary)}</strong>
	            <small>{orderSubmitCopy(portfolioReviewFeedback.guardrails.broker_submit_allowed)}</small>
          </article>
        </div>
        {portfolioReviewFeedback.latest_items.length > 0 ? (
          <div className="ledger-table-wrap">
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">종목</th>
                  <th scope="col">원래 결정</th>
                  <th scope="col">사후평가</th>
                  <th scope="col">후속 근거</th>
                  <th scope="col">해석</th>
                </tr>
              </thead>
              <tbody>
                {portfolioReviewFeedback.latest_items.slice(0, 8).map((item) => (
                  <tr key={`${item.decision_index}-${item.symbol}-${item.feedback_status}`}>
                    <td>
                      <strong>{item.symbol}</strong>
                      <small>{item.source_decision.related_recommendation_id || "추천 연결 없음"}</small>
                    </td>
                    <td>
                      <span className={`risk-tag ${decisionSeverityClass(item.source_decision.severity)}`}>
                        {item.decision_label || koCode(item.decision_type)}
                      </span>
	                      <small>{operationCopy(koReason(item.source_decision.rationale || "원래 판단 설명 없음"))}</small>
                    </td>
                    <td>
                      <span className={`risk-tag ${feedbackStatusClass(item.feedback_status)}`}>
                        {koCode(item.feedback_status)}
                      </span>
	                      <small>{item.evidence.recommendation_outcome.outcome_label || "성과 미측정"}</small>
                    </td>
                    <td>
                      <small>
	                        초과수익 {formatPercent(item.evidence.recommendation_outcome.alpha_pct)} · 가격{" "}
                        {formatPercent(item.evidence.price_evidence.price_return_pct)}
                      </small>
                      <small>
	                        가상 매매 {operationCopy(item.evidence.paper_validation.status)} · 투자 논리 {operationCopy(item.evidence.thesis.status || "없음")}
                      </small>
                    </td>
                    <td>
	                      <small>{operationCopy(koReason(item.feedback_reason))}</small>
	                      <small>{orderBoundaryCopy(item.order_boundary)} · {orderSubmitCopy(item.broker_submit_allowed)}</small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
	            아직 검토 결정 사후평가가 없다. 먼저 검토 결정 이력을 저장하고, 이후 성과 측정 기간이 끝나면 사후평가를 실행한다.
          </div>
        )}
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(portfolioReviewFeedback.next_action)}</p>
        </div>
      </section>
    </>
  );
}
