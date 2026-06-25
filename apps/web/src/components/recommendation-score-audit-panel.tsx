import type { Route } from "next";
import Link from "next/link";
import { AuditMetadata } from "./audit-metadata";
import { koCode } from "../lib/korean-labels";
import { formatPercent } from "../lib/presentation";
import {
  componentBadges,
  componentDetail,
  componentMetadata,
  componentTone,
  evidenceHref,
  evidenceLinkLabel,
  isZeroWeight,
  outcomeTone,
  scoreAuditSummary,
  scoreComponentLabel,
  sourceTypeLabel,
  type RecommendationScoreAuditData,
} from "./recommendation-score-audit-model";
import styles from "./recommendation-score-audit-panel.module.css";

type MetricProps = {
  readonly label: string;
  readonly value: string;
  readonly note: string;
};

function Metric({ label, note, value }: MetricProps) {
  return (
    <div className={styles.metric}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

export function RecommendationScoreAuditPanel({ data }: { readonly data: RecommendationScoreAuditData }) {
  const summary = scoreAuditSummary(data);
  return (
    <section className={styles.panel} id="recommendation-score-audit" aria-labelledby="recommendation-score-audit-title">
      <div className={styles.header}>
        <div>
          <span>점수·성과 감사</span>
          <h2 id="recommendation-score-audit-title">점수는 먼저 요약하고, 세부 근거는 필요할 때만 펼쳐본다</h2>
          <p>추천 점수, 실제 반영 항목, 판단 보조 항목, 성과 측정 상태를 분리한다. 긴 계산 근거는 접어서 판단 흐름을 방해하지 않는다.</p>
        </div>
        <span className={styles.badge}>{outcomeTone(data)}</span>
      </div>

      <div className={styles.summaryGrid} aria-label="추천 점수와 성과 요약">
        <Metric label="추천 점수" value={formatPercent(data.score)} note={`${data.symbol} 현재 추천 강도`} />
        <Metric label="점수 항목" value={`${summary.totalComponents}개`} note="가격·뉴스·사이클·재무 입력" />
        <Metric label="실제 반영" value={`${summary.activeComponents}개`} note={`판단 보조 ${summary.explanatoryComponents}개`} />
        <Metric label="성과 측정" value={summary.measured ? koCode(data.outcome.label) : "측정 전"} note={summary.measured ? data.outcome.measurement_end_date : "성과 측정창 대기"} />
      </div>

      <details className={styles.details}>
        <summary>
          <span className={styles.detailSummary}>
            <span>상세 계산 입력</span>
            <strong>점수 항목 자세히 보기</strong>
            <small>각 항목의 값, 최종 점수 반영 여부, 연결 근거, 계산 출처를 확인한다.</small>
          </span>
          <span className={styles.toggle}>
            <span className={styles.toggleClosed}>펼치기</span>
            <span className={styles.toggleOpen}>접기</span>
          </span>
        </summary>
        <div className={styles.scoreGrid}>
          {data.score_components.map((component) => {
            const href = evidenceHref(component.evidence_id, data.symbol);
            return (
              <article className={`recommendation-score-card ${componentTone(component)}`} key={component.component}>
                <div className="recommendation-score-card-head">
                  <span>{sourceTypeLabel(component.provenance?.source_type)}</span>
                  <strong>{scoreComponentLabel(component.component)}</strong>
                  <b>{formatPercent(component.value)}</b>
                </div>
                <p>{componentDetail(component)}</p>
                <div className="recommendation-score-badges">
                  {componentBadges(component).map((badge) => (
                    <span key={`${component.component}-${badge}`}>{badge}</span>
                  ))}
                </div>
                <div className="recommendation-score-metrics">
                  <div>
                    <span>현재 반영 비중</span>
                    <strong>{formatPercent(component.weight)}</strong>
                  </div>
                  <div>
                    <span>판단 반영 여부</span>
                    <strong>{isZeroWeight(component.weight) ? "참고 전용" : "점수 반영"}</strong>
                  </div>
                </div>
                <div className="recommendation-score-links">
                  {href ? <Link href={href as Route}>{evidenceLinkLabel(component.evidence_id)}</Link> : <span>연결된 상세 근거 없음</span>}
                </div>
                <AuditMetadata items={componentMetadata(component)} summary="근거 출처 자세히 보기" />
              </article>
            );
          })}
        </div>
      </details>

      <article className={styles.outcome} aria-label="추천 성과 측정">
        <div className={styles.outcomeHeader}>
          <div>
            <span>성과 측정</span>
            <h3>{summary.measured ? koCode(data.outcome.label) : "아직 성과 측정 전"}</h3>
            <p>추천이 맞았는지는 측정창이 끝난 뒤에만 판단한다. 성과가 없으면 추천 산식 반영 비중을 바꾸지 않는다.</p>
          </div>
          {data.linked_thesis_id ? <Link href={`/theses/${data.linked_thesis_id}` as Route}>연결된 투자 논리 열기</Link> : null}
        </div>
        <div className={styles.outcomeGrid}>
          <div>
            <span>알파</span>
            <strong>{summary.measured ? formatPercent(data.outcome.alpha) : "측정 전"}</strong>
          </div>
          <div>
            <span>절대수익률</span>
            <strong>{summary.measured ? formatPercent(data.outcome.absolute_return) : "측정 전"}</strong>
          </div>
          <div>
            <span>벤치마크 수익률</span>
            <strong>{summary.measured ? formatPercent(data.outcome.benchmark_return) : "측정 전"}</strong>
          </div>
          <div>
            <span>측정 종료일</span>
            <strong>{summary.measured ? data.outcome.measurement_end_date : "성과 측정창 대기"}</strong>
          </div>
        </div>
      </article>
    </section>
  );
}
