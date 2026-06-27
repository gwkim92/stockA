import { koCode } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";

import { userFacingRecommendationText } from "./recommendation-panel-format";
import styles from "./RecommendationEvidenceReviewPanel.module.css";

type EvidenceReview = RecommendationDetailData["evidence_review"];

type RecommendationEvidenceReviewPanelProps = {
  readonly evidenceReview: EvidenceReview;
};

function reviewCount(value: number | boolean | undefined) {
  if (typeof value === "boolean") {
    return value ? 1 : 0;
  }
  return value ?? 0;
}

function gateStatusLabel(status: string) {
  if (status === "pass" || status === "passed") {
    return "통과";
  }
  if (status === "warning") {
    return "주의";
  }
  if (status === "blocked") {
    return "차단";
  }
  return koCode(status);
}

function gateStatusClass(status: string) {
  if (status === "pass" || status === "passed") {
    return styles.statusPassed;
  }
  if (status === "warning") {
    return styles.statusWarning;
  }
  if (status === "blocked") {
    return styles.statusBlocked;
  }
  return "";
}

function gateToneClass(status: string) {
  if (status === "pass" || status === "passed") {
    return styles.gatePassed;
  }
  if (status === "warning") {
    return styles.gateWarning;
  }
  if (status === "blocked") {
    return styles.gateBlocked;
  }
  return "";
}

export function RecommendationEvidenceReviewPanel({ evidenceReview }: RecommendationEvidenceReviewPanelProps) {
  return (
    <section className={styles.panel} aria-label="추천 근거 연결 점검">
      <div className={styles.head}>
        <div>
          <span>근거 연결 점검</span>
          <h2>{koCode(evidenceReview.quality_status)}</h2>
          <p>투자 논리, 점수 항목, 뉴스 근거, 성과 측정의 연결 상태를 정리한다. 연결이 약하면 추천을 채택하지 않고 기록으로만 남긴다.</p>
        </div>
      </div>

      <div className={styles.summaryGrid} aria-label="근거 연결 점검 요약">
        <div className={styles.summaryCard}>
          <span>통과</span>
          <strong>{reviewCount(evidenceReview.summary.pass_count)}</strong>
          <small>기준 충족</small>
        </div>
        <div className={styles.summaryCard}>
          <span>주의</span>
          <strong>{reviewCount(evidenceReview.summary.warning_count)}</strong>
          <small>보강 필요</small>
        </div>
        <div className={styles.summaryCard}>
          <span>차단</span>
          <strong>{reviewCount(evidenceReview.summary.blocked_count)}</strong>
          <small>진행 금지</small>
        </div>
      </div>

      <div className={styles.gateGrid}>
        {evidenceReview.gates.map((gate) => (
          <article className={`${styles.gate} ${gateToneClass(gate.status)}`} key={gate.gate_key}>
            <div>
              <span className={gateStatusClass(gate.status)}>{gateStatusLabel(gate.status)}</span>
              <strong>{userFacingRecommendationText(gate.label)}</strong>
              <p>{userFacingRecommendationText(gate.detail)}</p>
            </div>
            <small>{userFacingRecommendationText(gate.next_step)}</small>
          </article>
        ))}
      </div>
    </section>
  );
}
