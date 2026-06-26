import type { ProfessionalAnalysisQuality } from "./dataHealthTypes";
import { formatPercent, operationCopy, orderBoundaryCopy, professionalQualityTone } from "./dataHealthModel";

type DataHealthProfessionalQualitySectionProps = {
  readonly professionalQuality: ProfessionalAnalysisQuality;
};

export function DataHealthProfessionalQualitySection({
  professionalQuality,
}: DataHealthProfessionalQualitySectionProps) {
  return (
      <section
        className="feature-map-panel reveal delay-1"
        id="professional-analysis-quality"
        aria-labelledby="professional-analysis-quality-title"
      >
        <div className="section-heading stacked-heading">
          <span>전문 분석 품질</span>
          <h2 id="professional-analysis-quality-title">
            재무·피어·밸류에이션·산업·AI 리서치 근거가 추천 판단에 붙었는지 본다.
          </h2>
        </div>
        <p className="board-intro">{operationCopy(professionalQuality.summary)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>품질 판정</span>
            <strong className={`risk-tag ${professionalQualityTone(professionalQuality)}`}>
              {professionalQuality.title}
            </strong>
            <small>{professionalQuality.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell">
            <span>활성 후보</span>
            <strong>{professionalQuality.active_candidate_count}</strong>
            <small>전문 분석 품질 점검 대상</small>
          </article>
          <article className="rail-cell">
            <span>근거 연결 완료</span>
            <strong>{professionalQuality.complete_candidate_count}</strong>
            <small>필수 근거 충족 후보</small>
          </article>
          <article className="rail-cell">
            <span>평균 연결률</span>
            <strong>{formatPercent(professionalQuality.average_coverage_ratio)}</strong>
            <small>재무·피어·밸류에이션·산업·리서치</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>원천 차단</span>
            <strong>{professionalQuality.source_blocked_count}</strong>
            <small>합성 재무 금지</small>
          </article>
          <article className="rail-cell rail-critical">
	            <span>추천 산식/실거래 상태</span>
	            <strong>{professionalQuality.automatic_weight_change_allowed ? "추천 산식 변경 허용" : "추천 산식 변경 금지"}</strong>
            <small>{orderBoundaryCopy(professionalQuality.order_boundary)}</small>
          </article>
        </div>
        <div className="insight-grid">
          {professionalQuality.layer_checks.map((layer) => (
            <article className="insight-card" key={layer.layer_key}>
              <span>{operationCopy(layer.label)}</span>
              <strong>{operationCopy(layer.status)}</strong>
              <p>
                {layer.available_count}/{layer.expected_count}개 후보 연결 · 근거 연결률 {formatPercent(layer.coverage_ratio)}
              </p>
            </article>
          ))}
        </div>
        <div className="flow-steps data-health-summary-grid">
          {professionalQuality.quality_checks.map((check) => (
            <article className="flow-step" key={check.key}>
              <span>{operationCopy(check.label)}</span>
              <strong>{operationCopy(check.status)}</strong>
	              <p>{operationCopy(check.detail)}</p>
            </article>
          ))}
        </div>
        <div className="empty-state">
          <strong>다음 조치</strong>
	          <p>{operationCopy(professionalQuality.next_action)}</p>
        </div>
      </section>
  );
}
