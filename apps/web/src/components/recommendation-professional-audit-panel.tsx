import type { Route } from "next";
import Link from "next/link";
import { formatPercent } from "../lib/presentation";
import type { ProfessionalEvidenceAudit } from "../lib/types";
import {
  auditCopy,
  auditLayerDetailCopy,
  orderBoundaryLabel,
  professionalAuditStatusLabel,
  professionalAuditSummary,
  professionalLayerStatusLabel,
  professionalLayerTone,
  professionalProductLabel,
} from "./recommendation-professional-audit-model";
import styles from "./recommendation-professional-audit-panel.module.css";

type MetricProps = {
  readonly label: string;
  readonly value: string;
  readonly note: string;
  readonly tone?: "critical";
};

function Metric({ label, note, tone, value }: MetricProps) {
  return (
    <div className={tone === "critical" ? `${styles.metric} ${styles.criticalMetric}` : styles.metric}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

function BooleanBoundary({ allowed, label }: { readonly allowed: boolean; readonly label: string }) {
  return (
    <div className={allowed ? styles.policyReady : styles.policyBlocked}>
      <span>{label}</span>
      <strong>{allowed ? "허용" : "차단"}</strong>
    </div>
  );
}

function auditLayerHref(href: string | null | undefined, symbol: string) {
  if (!href) {
    return null;
  }
  return href.replaceAll("UNKNOWN", encodeURIComponent(symbol)) as Route;
}

export function RecommendationProfessionalAuditPanel({
  audit,
  symbol,
}: {
  readonly audit: ProfessionalEvidenceAudit;
  readonly symbol?: string;
}) {
  const summary = professionalAuditSummary(audit);
  const displaySymbol = audit.symbol === "UNKNOWN" && symbol ? symbol : audit.symbol;
  const cleanAuditCopy = (value: string) => auditCopy(value).replaceAll("UNKNOWN", displaySymbol);
  return (
    <section
      aria-labelledby="recommendation-professional-audit-title"
      className={`${styles.panel} ${styles[summary.tone]}`}
      id="recommendation-professional-audit"
    >
      <div className={styles.header}>
        <div>
          <span>전문 분석 감사</span>
          <h2 id="recommendation-professional-audit-title">{cleanAuditCopy(audit.title)}</h2>
          <p>
            {cleanAuditCopy(audit.summary)} {cleanAuditCopy(audit.next_action)}
          </p>
        </div>
        <strong className={styles.status}>{professionalAuditStatusLabel(audit.status)}</strong>
      </div>

      <div className={styles.metricGrid} aria-label="전문 분석 감사 요약">
        <Metric
          label="분석 대상"
          note={`${displaySymbol} · ${audit.as_of_date}`}
          value={professionalProductLabel(audit.product_type)}
        />
        <Metric
          label="근거 커버리지"
          note={`완료 ${audit.available_layer_count}/${audit.expected_layer_count}${audit.partial_layer_count > 0 ? ` · 일부 ${audit.partial_layer_count}` : ""}`}
          value={formatPercent(audit.coverage_ratio)}
        />
        <Metric
          label="차단·대기"
          note={`누락 ${audit.missing_layer_count}개`}
          tone={summary.blockedOrPendingCount > 0 ? "critical" : undefined}
          value={`${summary.blockedOrPendingCount}개`}
        />
        <Metric
          label="실거래 상태"
          note={`추천 산식 변경 ${audit.automatic_weight_change_allowed ? "허용" : "금지"} · 실거래 주문 ${audit.broker_submit_allowed ? "허용" : "금지"}`}
          tone="critical"
          value={orderBoundaryLabel(audit.order_boundary)}
        />
      </div>

      {summary.isSourceBlocked ? (
        <article className={styles.sourceBlocker} aria-label="전문 분석 원천 차단">
          <span>원천 차단</span>
          <strong>{audit.source_blocker.blocker_label || "검증 가능한 원천 부족"}</strong>
          <p>
            {cleanAuditCopy(audit.source_blocker.summary)} {cleanAuditCopy(audit.source_blocker.next_action)}
          </p>
        </article>
      ) : null}

      {audit.missing_layer_labels.length > 0 ? (
        <div className={styles.missingList} aria-label="부족한 전문 분석 레이어">
          {audit.missing_layer_labels.map((label) => (
            <span key={label}>{auditCopy(label)}</span>
          ))}
        </div>
      ) : null}

      <details className={styles.details}>
        <summary>
          <span>
            <small>세부 검증</small>
            <strong>전문 분석 레이어 자세히 보기</strong>
          </span>
          <b>
            <span className={styles.closedLabel}>펼치기</span>
            <span className={styles.openLabel}>접기</span>
          </b>
        </summary>
        <div className={styles.layerGrid}>
          {audit.layer_checks.map((layer) => {
            const tone = professionalLayerTone(layer.status);
            const href = auditLayerHref(layer.href, displaySymbol);
            return (
              <article className={`${styles.layerCard} ${styles[tone]}`} key={layer.key}>
                <div>
                  <span>{cleanAuditCopy(layer.label)}</span>
                  <strong>{professionalLayerStatusLabel(layer.status)}</strong>
                </div>
                <p>{cleanAuditCopy(auditLayerDetailCopy(layer.label, layer.detail))}</p>
                <small>원천: {cleanAuditCopy(layer.source)}</small>
                {href ? <Link href={href}>관련 화면 열기</Link> : null}
              </article>
            );
          })}
        </div>
      </details>

      <details className={styles.policyDetails}>
        <summary>
          <span>
            <small>정책 경계</small>
            <strong>추천 산식과 주문 경계 확인</strong>
          </span>
          <b>
            <span className={styles.closedLabel}>펼치기</span>
            <span className={styles.openLabel}>접기</span>
          </b>
        </summary>
        <div className={styles.policyGrid}>
          <BooleanBoundary allowed={audit.professional_decision_status !== "blocked"} label="전문 판단 입력" />
          <BooleanBoundary allowed={audit.paper_validation_input_allowed} label="가상 매매 검증 입력" />
          <BooleanBoundary allowed={audit.recommendation_scoring_mutated} label="추천 점수 변경" />
          <BooleanBoundary allowed={audit.automatic_order_allowed || audit.broker_submit_allowed} label="주문 실행" />
          <div className={styles.policyNote}>
            <span>추천 산식 정책</span>
            <p>{cleanAuditCopy(audit.score_policy)}</p>
          </div>
          <div className={styles.policyNote}>
            <span>근거 품질 상태</span>
            <p>
              {cleanAuditCopy(audit.evidence_quality_status)} · 차단 게이트 {audit.blocked_evidence_gate_count}개 · 주의 게이트{" "}
              {audit.warning_evidence_gate_count}개
            </p>
          </div>
        </div>
      </details>
    </section>
  );
}
