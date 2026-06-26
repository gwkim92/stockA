import { koCode } from "@/lib/korean-labels";

import type { ProfessionalAnalysisNextAction } from "./dataHealthTypes";
import { formatPercent, operationCopy, orderBoundaryCopy, professionalNextActionTone } from "./dataHealthModel";

type DataHealthProfessionalNextActionSectionProps = {
  readonly professionalNextAction: ProfessionalAnalysisNextAction;
};

export function DataHealthProfessionalNextActionSection({
  professionalNextAction,
}: DataHealthProfessionalNextActionSectionProps) {
  return (
      <section
        className="feature-map-panel reveal delay-1"
        id="professional-next-action"
        aria-labelledby="professional-next-action-title"
      >
        <div className="section-heading stacked-heading">
          <span>전문 분석 다음 행동</span>
          <h2 id="professional-next-action-title">재무·밸류에이션·원천 공백·성과 표본 중 지금 무엇을 봐야 하는지 정리한다.</h2>
        </div>
        <p className="board-intro">{operationCopy(professionalNextAction.summary)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>현재 판단</span>
            <strong className={`risk-tag ${professionalNextActionTone(professionalNextAction)}`}>
              {professionalNextAction.title}
            </strong>
            <small>{professionalNextAction.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell">
            <span>원천 공백</span>
            <strong>{professionalNextAction.source_gap_count}</strong>
            <small>원천 차단 {professionalNextAction.source_blocker_count}개</small>
          </article>
          <article className="rail-cell">
            <span>전문 판단 차단</span>
            <strong>{professionalNextAction.guarded_source_blocked_recommendation_count}</strong>
            <small>원천 없으면 합성 재무 금지</small>
          </article>
          <article className="rail-cell">
            <span>평균 연결률</span>
            <strong>{formatPercent(professionalNextAction.average_coverage_ratio)}</strong>
            <small>활성 후보 기준</small>
          </article>
          <article className="rail-cell">
            <span>성과 표본</span>
            <strong>{professionalNextAction.managed_wait ? "관리된 대기" : koCode(professionalNextAction.status)}</strong>
            <small>
              {professionalNextAction.estimated_maturity_date
                ? `${professionalNextAction.estimated_maturity_date} 이후 재평가`
                : "성숙일 미확인"}
            </small>
          </article>
          <article className="rail-cell rail-critical">
            <span>추천 산식/실거래 상태</span>
            <strong>{professionalNextAction.weight_review_blocked ? "추천 산식 변경 금지" : "성과 표본 충족"}</strong>
            <small>{orderBoundaryCopy(professionalNextAction.order_boundary)}</small>
          </article>
        </div>
        <div className="insight-grid">
          {professionalNextAction.readiness_items.map((item) => (
            <article className="insight-card" key={item.key}>
              <span>{operationCopy(item.label)}</span>
              <strong>{operationCopy(item.status)}</strong>
	              <p>{operationCopy(item.detail)}</p>
            </article>
          ))}
          {professionalNextAction.readiness_items.length === 0 ? (
            <article className="insight-card">
              <span>상태 없음</span>
              <strong>data-health payload 대기</strong>
	              <p>전문 분석 요약을 만들 원천 공백, 성과 사후평가, 추천 산식 검토 근거가 아직 없다.</p>
            </article>
          ) : null}
        </div>
        <div className="empty-state">
          <strong>다음 조치</strong>
	          <p>{operationCopy(professionalNextAction.next_action)}</p>
          {professionalNextAction.next_symbol ? (
            <p>
              우선 검토 후보{" "}
              {professionalNextAction.next_symbol_href ? (
                <a href={professionalNextAction.next_symbol_href}>{professionalNextAction.next_symbol}</a>
              ) : (
                professionalNextAction.next_symbol
              )}
	              {professionalNextAction.next_symbol_reason ? ` · ${operationCopy(professionalNextAction.next_symbol_reason)}` : ""}
            </p>
          ) : null}
        </div>
      </section>
  );
}
