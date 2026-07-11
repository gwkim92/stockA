import type { RecommendationQualityDecision } from "@/components/recommendation-product-overview";

import styles from "./RecommendationQualityBoundaryPanel.module.css";

type QualityCheck = {
  readonly label: string;
  readonly value: string;
  readonly detail: string;
};

type BoundarySummary = {
  readonly summary: string;
  readonly status: string;
  readonly asOfDate: string;
  readonly readyStepCount: number;
  readonly watchStepCount: number;
  readonly blockedStepCount: number;
  readonly totalStepCount: number;
  readonly paperValidationInputAllowed: boolean;
  readonly automaticOrderAllowed: boolean;
  readonly brokerSubmitAllowed: boolean;
  readonly orderBoundaryLabel: string;
};

type RecommendationQualityBoundaryPanelProps = {
  readonly qualityDecision: RecommendationQualityDecision;
  readonly qualityChecks: readonly QualityCheck[];
  readonly boundary: BoundarySummary;
};

function Metric({
  critical = false,
  label,
  note,
  value,
}: {
  readonly critical?: boolean;
  readonly label: string;
  readonly note: string;
  readonly value: string;
}) {
  return (
    <div className={critical ? `${styles.metric} ${styles.critical}` : styles.metric}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

export function RecommendationQualityBoundaryPanel({
  boundary,
  qualityChecks,
  qualityDecision,
}: RecommendationQualityBoundaryPanelProps) {
  return (
    <section className={styles.panel} aria-label="추천 품질과 사용 가능 범위">
      <div className={styles.head}>
        <div>
          <span>추천 품질과 사용 가능 범위</span>
          <h2>{qualityDecision.status}</h2>
          <p>{qualityDecision.summary}</p>
        </div>
        <strong className={styles.badge}>읽기 전용 평가</strong>
      </div>

      <div className={styles.metricGrid} aria-label="추천 사용 경계 요약">
        <Metric label="전문 흐름" note={boundary.asOfDate} value={boundary.status} />
        <Metric
          label="단계 상태"
          note={`주의 ${boundary.watchStepCount} · 차단 ${boundary.blockedStepCount}`}
          value={`${boundary.readyStepCount}/${boundary.totalStepCount}`}
        />
        <Metric
          critical={!boundary.paperValidationInputAllowed}
          label="가상 매매 입력"
          note="원천 차단이면 입력 금지"
          value={boundary.paperValidationInputAllowed ? "허용" : "차단"}
        />
        <Metric
          critical
          label="실거래 상태"
          note={`자동 주문 ${boundary.automaticOrderAllowed || boundary.brokerSubmitAllowed ? "허용" : "금지"}`}
          value={boundary.orderBoundaryLabel}
        />
      </div>

      <div className={styles.checkGrid} aria-label="중장기 품질 체크">
        {qualityChecks.map((check) => (
          <article className={styles.check} key={check.label}>
            <span>{check.label}</span>
            <strong>{check.value}</strong>
            <p>{check.detail}</p>
          </article>
        ))}
      </div>

      <p className={styles.boundaryNote}>
        {boundary.summary} 이 결과는 추천 점수를 바꾸지 않고, 이 추천을 가상 매매 검증·보유 상태·실거래 차단 중 어디까지
        넘길 수 있는지 설명한다.
      </p>
    </section>
  );
}
