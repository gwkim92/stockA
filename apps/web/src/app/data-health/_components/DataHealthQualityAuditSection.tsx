import type { qualityAuditSampleGroups } from "./dataHealthModel";
import {
  auditSampleHeadline,
  auditSampleMeta,
  auditSampleValue,
  operationCopy,
  qualityAuditExplanation,
  qualityAuditTitle,
  qualityAuditTone,
  qualityMetric,
} from "./dataHealthModel";
import type { CycleAiQualityAudit } from "./dataHealthTypes";

type DataHealthQualityAuditSectionProps = {
  readonly qualityAudit: CycleAiQualityAudit;
  readonly qualityAuditSamples: ReturnType<typeof qualityAuditSampleGroups>;
};

export function DataHealthQualityAuditSection({
  qualityAudit,
  qualityAuditSamples,
}: DataHealthQualityAuditSectionProps) {
  return (
    <section className="feature-map-panel reveal delay-1" id="quality-audit" aria-labelledby="quality-audit-title">
      <div className="section-heading stacked-heading">
        <span>품질 감사</span>
        <h2 id="quality-audit-title">수집·번역·AI·전파·추천 입력의 오염 여부</h2>
      </div>
      <p className="board-intro">{qualityAuditExplanation(qualityAudit)}</p>
      <div className="status-rail compact-rail">
        <article className="rail-cell">
          <span>감사 결과</span>
          <strong className={`risk-tag ${qualityAuditTone(qualityAudit)}`}>{qualityAuditTitle(qualityAudit)}</strong>
          <small>{qualityAudit.generated_at || "최근 결과 없음"}</small>
        </article>
        <article className="rail-cell">
          <span>감사 점수</span>
          <strong>{qualityAudit.audit_score}</strong>
          <small>{qualityAudit.lookback_days ? `${qualityAudit.lookback_days}일 기준` : "기간 미확인"}</small>
        </article>
        <article className="rail-cell rail-critical">
          <span>오염 의심</span>
          <strong>{qualityAudit.issue_count}</strong>
          <small>중복·오분류·근거 없음</small>
        </article>
        <article className="rail-cell">
          <span>한국어 번역</span>
          <strong>
            {qualityMetric(qualityAudit, "translated_document_count")}/
            {qualityMetric(qualityAudit, "rss_document_count")}
          </strong>
          <small>원천 뉴스</small>
        </article>
        <article className="rail-cell">
          <span>가상 매매 검증</span>
          <strong>{qualityMetric(qualityAudit, "paper_validation_passed_count")}</strong>
          <small>{qualityMetric(qualityAudit, "paper_validation_count")}회 중 통과</small>
        </article>
      </div>
      <div className="insight-grid">
        <article className="insight-card">
          <span>누락 실행 단계</span>
          <strong>{qualityAudit.readiness_gap_count}</strong>
          <p>
            {qualityAudit.readiness_gaps[0]
              ? `${qualityAudit.readiness_gaps[0].label} 때문에 감사 상태가 낮아졌다.`
              : "감사 기준에 필요한 수집·분석·전파·스냅샷 누락 수다."}
          </p>
        </article>
        <article className="insight-card">
          <span>중복 뉴스 묶음</span>
          <strong>{qualityMetric(qualityAudit, "duplicate_title_count")}</strong>
          <p>같은 제목이 반복 수집되어 같은 뉴스가 여러 근거처럼 보일 위험이다.</p>
        </article>
        <article className="insight-card">
          <span>근거 없는 종목 연결</span>
          <strong>{qualityMetric(qualityAudit, "ungrounded_direct_ticker_count")}</strong>
          <p>원문 제목이나 요약에서 확인되지 않는 직접 종목 영향이다.</p>
        </article>
        <article className="insight-card">
          <span>양자→에너지 오분류</span>
          <strong>{qualityMetric(qualityAudit, "quantum_energy_mislink_count")}</strong>
          <p>양자컴퓨팅 뉴스가 에너지 테마나 XOM/XLE로 잘못 묶인 사례다.</p>
        </article>
        <article className="insight-card">
          <span>교차 테마 불일치</span>
          <strong>{qualityMetric(qualityAudit, "cross_theme_mismatch_count")}</strong>
          <p>뉴스 내용과 연결된 사이클 흐름이 강하게 어긋나는 후보 수다.</p>
        </article>
        <article className="insight-card">
          <span>중복 흐름 근거</span>
          <strong>{qualityMetric(qualityAudit, "duplicate_flow_evidence_count")}</strong>
          <p>같은 뉴스가 여러 이벤트나 흐름으로 나뉘어 근거가 부풀려질 위험이다.</p>
        </article>
        <article className="insight-card">
          <span>약한 전파 근거</span>
          <strong>{qualityMetric(qualityAudit, "weak_propagation_evidence_count")}</strong>
          <p>상위 흐름에서 종목으로 내려가는 경로의 신뢰도·강도·경로 가중치가 낮다.</p>
        </article>
        <article className="insight-card">
          <span>정상 거시 흐름</span>
          <strong>{qualityMetric(qualityAudit, "normal_macro_flow_count")}</strong>
          <p>종목을 억지로 붙이지 않고 상위 흐름으로 남겨둔 뉴스다.</p>
        </article>
      </div>
      {qualityAudit.readiness_gaps.length > 0 ? (
        <div className="relationship-panel">
          <span>부족한 실행 단계</span>
          <div className="relationship-list">
            {qualityAudit.readiness_gaps.map((gap) => (
              <article className="relationship-chip" key={gap.gap_key}>
                <span>{gap.label}</span>
                <strong>
                  {gap.metric_key}: {String(gap.current_value ?? 0)}
                </strong>
                <small>다음 조치: {operationCopy(gap.next_action)}</small>
              </article>
            ))}
          </div>
        </div>
      ) : null}
      {qualityAuditSamples.length > 0 ? (
        <div className="relationship-panel">
          <span>감사 샘플</span>
          <div className="relationship-list">
            {qualityAuditSamples.map((group) => (
              <article className="relationship-chip" key={group.key}>
                <span>{group.label}</span>
                <strong>{group.description}</strong>
                {group.records.map((record, index) => (
                  <small key={`${group.key}-${auditSampleValue(record, "event_id") || "record"}-${index}`}>
                    {auditSampleHeadline(record)}
                    {auditSampleMeta(record) ? ` · ${auditSampleMeta(record)}` : ""}
                  </small>
                ))}
              </article>
            ))}
          </div>
        </div>
      ) : null}
      <div className="empty-state">
        <strong>다음 조치</strong>
        <p>{qualityAudit.next_actions[0] ? operationCopy(qualityAudit.next_actions[0]) : "현재 추가 조치 없음"}</p>
      </div>
    </section>
  );
}
