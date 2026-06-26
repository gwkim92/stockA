import type { ProfessionalRecommendationCoverageAudit } from "./dataHealthTypes";
import {
  formatPercent,
  operationCopy,
  orderBoundaryCopy,
  professionalRecommendationAuditItemTone,
  professionalRecommendationAuditTone,
} from "./dataHealthModel";

type DataHealthProfessionalRecommendationAuditSectionProps = {
  readonly professionalRecommendationAudit: ProfessionalRecommendationCoverageAudit;
};

export function DataHealthProfessionalRecommendationAuditSection({
  professionalRecommendationAudit,
}: DataHealthProfessionalRecommendationAuditSectionProps) {
  return (
      <section
        className="feature-map-panel reveal delay-1"
        id="professional-recommendation-coverage-audit"
        aria-labelledby="professional-recommendation-coverage-audit-title"
      >
        <div className="section-heading stacked-heading">
          <span>추천별 전문 감사</span>
          <h2 id="professional-recommendation-coverage-audit-title">
            활성 추천마다 전문 분석 근거가 실제로 연결됐는지 표시합니다.
          </h2>
        </div>
        <p className="board-intro">{operationCopy(professionalRecommendationAudit.summary)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>감사 판정</span>
            <strong className={`risk-tag ${professionalRecommendationAuditTone(professionalRecommendationAudit)}`}>
              {professionalRecommendationAudit.title}
            </strong>
            <small>{professionalRecommendationAudit.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell">
	            <span>활성 추천</span>
            <strong>{professionalRecommendationAudit.recommendation_count}</strong>
	            <small>검토 대상</small>
          </article>
          <article className="rail-cell">
            <span>전문 근거 충족</span>
            <strong>{professionalRecommendationAudit.ready_for_review_count}</strong>
            <small>전문 근거와 가상 매매 검증 통과</small>
          </article>
          <article className="rail-cell">
            <span>근거 부족</span>
            <strong>{professionalRecommendationAudit.coverage_gap_count}</strong>
            <small>재무·피어·밸류에이션·산업·리서치</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>원천 차단</span>
            <strong>{professionalRecommendationAudit.source_blocked_count}</strong>
            <small>합성 재무 금지</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
	            <strong>{professionalRecommendationAudit.broker_submit_allowed ? "제출 가능" : "제출 금지"}</strong>
            <small>{orderBoundaryCopy(professionalRecommendationAudit.order_boundary)}</small>
          </article>
        </div>

        {professionalRecommendationAudit.items.length > 0 ? (
          <div className="feature-map-grid collection-map-grid">
            {professionalRecommendationAudit.items.map((item) => (
              <article className="feature-map-card collection-map-card" key={item.recommendation_id}>
                <span>
                  #{item.rank} · {item.product_type === "fund_or_etf" ? "ETF·펀드형" : "개별 기업"}
                </span>
                <strong>
                  <a href={item.detail_href}>{item.symbol}</a> · {operationCopy(item.audit_status)}
                </strong>
                <small>{item.instrument_name || "종목명 미확인"}</small>
                <small>
                  추천 점수 {formatPercent(item.recommendation_score)} · 목표 비중 {formatPercent(item.recommended_weight)}
                </small>
                <small>
	                  연결률 {formatPercent(item.coverage_ratio)} · 근거 {item.available_layer_count}/{item.expected_layer_count}
                </small>
                <small className={`risk-tag ${professionalRecommendationAuditItemTone(item.audit_status)}`}>
                  {operationCopy(item.professional_decision_status)}
                </small>
                <div className="tag-ledger">
                  {item.layer_checks.map((check) => (
                    <span className={`risk-tag ${check.status === "complete" || check.status === "passed" ? "risk-low" : check.status === "not_applicable" ? "risk-medium" : "risk-high"}`} key={check.key}>
                      {operationCopy(check.label)}: {operationCopy(check.status)}
                    </span>
                  ))}
                </div>
                {item.missing_layer_labels.length > 0 ? (
                  <p>부족 근거: {item.missing_layer_labels.join(" · ")}</p>
                ) : (
                  <p>표시할 부족 근거가 없다.</p>
                )}
                <dl className="fact-list compact-facts">
                  <div>
	                    <dt>투자 논리</dt>
                    <dd>{item.has_active_thesis ? "연결됨" : "없음"}</dd>
                  </div>
                  <div>
                    <dt>가상 매매 검증</dt>
                    <dd>{operationCopy(item.paper_validation_status)}</dd>
                  </div>
                  <div>
                    <dt>주문</dt>
                    <dd>{item.broker_submit_allowed ? "제출 가능" : "제출 금지"}</dd>
                  </div>
                </dl>
	                {item.remediation_action ? <p>{operationCopy(item.remediation_action)}</p> : null}
                <a href={item.stock_href}>종목 상세 보기</a>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">추천별 전문 분석 감사 대상이 없다.</div>
        )}

        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(professionalRecommendationAudit.next_action)}</p>
        </div>
      </section>
  );
}
