import Link from "next/link";
import type { Route } from "next";
import { AuditMetadata, type AuditMetadataItem } from "@/components/audit-metadata";
import { getThesisDetail } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { ThesisDetailData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "투자 논리 상세" };

type ThesisPageProps = {
  params: Promise<{ thesisId: string }>;
};

function evidenceHref(evidenceId: string, evidenceType: string, symbol: string) {
  if (evidenceType === "performance_outcome" || evidenceId.startsWith("performance-outcome-")) {
    return "/performance" as Route;
  }
  if (evidenceType === "source_document_event" || evidenceId.startsWith("event-") || evidenceId.startsWith("sec-event-")) {
    return `/events?symbol=${encodeURIComponent(symbol)}` as Route;
  }
  return null;
}

type ThesisEvidence = ThesisDetailData["evidence"][number];

function evidenceLinkLabel(evidence: ThesisEvidence) {
  if (evidence.type === "performance_outcome" || evidence.evidence_id.startsWith("performance-outcome-")) {
    return "성과 근거 보기";
  }
  if (
    evidence.type === "source_document_event"
    || evidence.evidence_id.startsWith("event-")
    || evidence.evidence_id.startsWith("sec-event-")
  ) {
    return "이벤트 원장 열기";
  }
  return "근거 화면 열기";
}

function evidenceMetadata(evidence: ThesisEvidence): AuditMetadataItem[] {
  return [
    { label: "근거 ID", value: evidence.evidence_id },
    { label: "근거 유형", value: evidence.type },
    { label: "근거 제목", value: evidence.title },
  ];
}

const REVIEW_RULE_LABELS: Record<string, string> = {
  cycle_correcting: "사이클이 조정 국면",
  cycle_score_unavailable: "사이클 점수 입력 없음",
  cycle_state_unavailable: "사이클 상태 입력 없음",
  cycle_structurally_broken: "사이클이 구조적으로 훼손",
  latest_adjusted_close_unavailable: "최신 수정종가 입력 없음",
  no_adverse_signal_keep: "청산 또는 축소 신호 없음",
  observation_window_return_unavailable: "관측 구간 수익률 입력 없음",
  recommendation_action_exclude: "추천 조치가 제외",
  recommendation_bucket_avoid: "추천 버킷이 회피 대상",
  return_1d_unavailable: "1일 수익률 입력 없음",
  "score_below_0.3500": "추천 점수가 최소 기준 0.3500 미만",
  watchlist_recommendation: "관찰 후보",
};

type ReviewSignal = {
  code: string;
  label: string;
};

type ReviewRationale = {
  action: string | null;
  rawChangeNotes: string;
  safetyNote: string | null;
  signals: ReviewSignal[];
};

function reviewRuleLabel(code: string, fallback: string) {
  const normalizedFallback = fallback.trim().replace(/^검토 근거:\s*/, "");
  return REVIEW_RULE_LABELS[code] ?? (normalizedFallback || koCode(code));
}

function parseReviewRationale(changeNotes: string | null | undefined): ReviewRationale | null {
  if (!changeNotes) {
    return null;
  }

  const signals: ReviewSignal[] = [];
  const labeledSignalPattern = /([^;().]+?)\s*\(([a-z0-9_.-]+)\)/g;
  for (const match of changeNotes.matchAll(labeledSignalPattern)) {
    signals.push({
      code: match[2],
      label: reviewRuleLabel(match[2], match[1]),
    });
  }

  if (signals.length === 0) {
    const legacySignals = changeNotes.match(/deterministic signals:\s*([^.]*)\./i)?.[1] ?? "";
    for (const code of legacySignals.split(",").map((item) => item.trim()).filter(Boolean)) {
      signals.push({ code, label: reviewRuleLabel(code, "") });
    }
  }

  const action = changeNotes.match(/(?:적용 조치:\s*|action=)([a-z_]+)/)?.[1] ?? null;
  const safetyNote =
    changeNotes.match(/(?:적용 조치:\s*[^.]+\.|action=[^;]+;)\s*(.*)$/)?.[1]?.trim()
    ?? null;

  return {
    action,
    rawChangeNotes: changeNotes,
    safetyNote,
    signals,
  };
}

function reviewRationaleMetadata(rationale: ReviewRationale): AuditMetadataItem[] {
  return [
    { label: "원문 change notes", value: rationale.rawChangeNotes },
    { label: "적용 조치 code", value: rationale.action },
    ...rationale.signals.map((signal, index) => ({
      label: `rule code ${index + 1}`,
      value: signal.code,
    })),
  ];
}

function reviewCount(value: number | boolean | undefined) {
  return typeof value === "number" ? value : value ? 1 : 0;
}

function gateStatusLabel(status: string) {
  if (status === "pass") {
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

function gateStatusColor(status: string) {
  if (status === "pass") {
    return "var(--accent-green)";
  }
  if (status === "warning") {
    return "var(--accent-yellow)";
  }
  if (status === "blocked") {
    return "var(--accent-red)";
  }
  return "var(--text-secondary)";
}

function thesisQualityDecision(data: ThesisDetailData) {
  const blockedCount = reviewCount(data.evidence_review.summary.blocked_count);
  const warningCount = reviewCount(data.evidence_review.summary.warning_count);
  const adverseReviewAction = ["reduce", "exit"].includes(data.latest_review.action);
  const highRiskReview = ["high", "critical"].includes(data.latest_review.risk_level);
  const triggeredInvalidations = data.invalidation_conditions.filter(
    (condition) => condition.current_status !== "not_triggered",
  ).length;

  if (blockedCount > 0 || triggeredInvalidations > 0) {
    return {
      status: "검토 차단",
      tone: "risk-high",
      summary: "무효화 조건이나 필수 근거 차단이 있어 장기 투자 논리로 채택하면 안 된다.",
    };
  }
  if (adverseReviewAction || highRiskReview) {
    return {
      status: "보유 축소 검토",
      tone: "risk-high",
      summary: "최근 검토가 축소 또는 청산 쪽으로 기울어져 있다. 근거는 보존하되 신규 채택보다 리스크 검토가 먼저다.",
    };
  }
  if (warningCount > 0) {
    return {
      status: "보강 후 검토",
      tone: "risk-medium",
      summary: "핵심 논리는 남아 있지만 성과 근거, 최신 검토, 또는 원천 이벤트 보강이 필요하다.",
    };
  }
  return {
    status: "사람 검토 가능",
    tone: "risk-low",
    summary: "원천 근거, 성과 근거, 무효화 조건, 최근 검토가 연결되어 있어 사람이 중장기 보유 논리를 검토할 수 있다.",
  };
}

function thesisQualityChecks(data: ThesisDetailData) {
  const sourceEventCount = reviewCount(data.evidence_review.summary.source_event_count);
  const performanceEvidenceCount = reviewCount(data.evidence_review.summary.performance_evidence_count);
  const invalidationCount = data.invalidation_conditions.length;
  const triggeredInvalidations = data.invalidation_conditions.filter(
    (condition) => condition.current_status !== "not_triggered",
  ).length;
  return [
    {
      label: "근거 품질",
      value: data.evidence_review.quality_status === "ready_for_human_review" ? "사람 검토 가능" : koCode(data.evidence_review.quality_status),
      detail: `원천 이벤트 ${sourceEventCount}개 · 성과 근거 ${performanceEvidenceCount}개`,
    },
    {
      label: "최근 검토",
      value: koCode(data.latest_review.action),
      detail: `위험도 ${koCode(data.latest_review.risk_level)} · 다음 검토일 ${data.latest_review.next_review_date || "미정"}`,
    },
    {
      label: "무효화 조건",
      value: triggeredInvalidations > 0 ? "발동 조건 있음" : "미발동",
      detail: `조건 ${invalidationCount}개 중 발동 ${triggeredInvalidations}개`,
    },
    {
      label: "주문 경계",
      value: "자동 주문 없음",
      detail: "이 판정은 투자 논리 품질 검토이며 broker/order flow를 실행하지 않는다.",
    },
  ];
}

export default async function ThesisPage({ params }: ThesisPageProps) {
  const { thesisId } = await params;
  const response = await getThesisDetail(thesisId);
  const data = response.data;
  const evidenceReview = data.evidence_review;
  const reviewRationale = parseReviewRationale(data.latest_review.change_notes);
  const qualityDecision = thesisQualityDecision(data);
  const qualityChecks = thesisQualityChecks(data);

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          투자 논리 • {data.symbol} • {koCode(data.status)} • {koCode(data.thesis_version)}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>투자 논리와 증거 원장</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
              {koLabel(data.summary)}
            </p>
          </div>
          
          <div style={{ 
            padding: "20px 32px", 
            background: "rgba(16, 185, 129, 0.1)", 
            border: "1px solid rgba(16, 185, 129, 0.2)",
            borderRadius: "var(--radius-md)",
            textAlign: "center"
          }}>
            <span className="metric-sub" style={{ color: "var(--accent-green)" }}>최근 검토</span>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0" }}>
              {koCode(data.latest_review.action)}
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--accent-green)", fontWeight: 500 }}>
              위험도 {koCode(data.latest_review.risk_level)}
            </div>
          </div>
        </div>
      </section>

      <section className="bento-card reveal delay-1" aria-label="중장기 투자 논리 품질 판정">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap", marginBottom: "20px" }}>
          <div>
            <span className="metric-sub">중장기 품질 판정</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{qualityDecision.status}</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "820px" }}>
              {qualityDecision.summary}
            </p>
          </div>
          <span className={`risk-tag ${qualityDecision.tone}`}>읽기 전용 평가</span>
        </div>
        <div className="flow-steps">
          {qualityChecks.map((check) => (
            <article className="flow-step" key={check.label}>
              <span>{check.label}</span>
              <strong>{check.value}</strong>
              <p>{check.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="bento-card reveal delay-1" aria-label="최근 투자 논리 검토 이유">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap", marginBottom: "18px" }}>
          <div>
            <span className="metric-sub">최근 검토 이유</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{koCode(data.latest_review.action)} 판단 근거</h2>
          </div>
          <div style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            다음 검토일 {data.latest_review.next_review_date || "미정"}
          </div>
        </div>
        <p style={{ color: "var(--text-primary)", lineHeight: 1.7, margin: "0 0 12px" }}>
          {koLabel(data.latest_review.summary || "아직 검토 요약이 없다.")}
        </p>
        {reviewRationale ? (
          <div className="review-rationale">
            {reviewRationale.signals.length > 0 ? (
              <div className="review-signal-list" aria-label="검토 rule signal">
                {reviewRationale.signals.map((signal) => (
                  <span className="review-signal-chip" key={signal.code}>
                    {signal.label}
                  </span>
                ))}
              </div>
            ) : (
              <p>{koLabel(data.latest_review.change_notes)}</p>
            )}
            <p>
              {reviewRationale.action ? `적용 조치: ${koCode(reviewRationale.action)}. ` : ""}
              {reviewRationale.safetyNote ? koLabel(reviewRationale.safetyNote) : "투자 논리 상태와 주문은 자동으로 변경하지 않는다."}
            </p>
            <AuditMetadata items={reviewRationaleMetadata(reviewRationale)} summary="검토 rule code 보기" />
          </div>
        ) : (
          <p style={{ color: "var(--text-secondary)", lineHeight: 1.65, margin: 0, fontSize: "0.92rem" }}>
            아직 검토 signal 기록이 없다.
          </p>
        )}
      </section>

      <section className="bento-card reveal delay-1" aria-label="투자 논리 근거 품질 점검">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap", marginBottom: "20px" }}>
          <div>
            <span className="metric-sub">근거 품질 점검</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{koCode(evidenceReview.quality_status)}</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "760px" }}>
              이 점검은 투자 논리를 자동으로 채택하지 않는다. 원천 이벤트, 성과 근거, 무효화 조건, 최근 사람 검토가
              붙어 있는지 확인하는 읽기 전용 품질 관리다.
            </p>
          </div>
          <div className="status-rail compact-rail" style={{ flex: "1 1 360px" }}>
            <div className="rail-cell">
              <span>통과</span>
              <strong>{reviewCount(evidenceReview.summary.pass_count)}</strong>
              <small>검토 기준 충족</small>
            </div>
            <div className="rail-cell">
              <span>주의</span>
              <strong>{reviewCount(evidenceReview.summary.warning_count)}</strong>
              <small>보강 필요</small>
            </div>
            <div className="rail-cell">
              <span>차단</span>
              <strong>{reviewCount(evidenceReview.summary.blocked_count)}</strong>
              <small>진행 금지</small>
            </div>
          </div>
        </div>

        <div className="bento-list">
          {evidenceReview.gates.map((gate) => (
            <div className="bento-list-item" key={gate.gate_key}>
              <div>
                <span className="metric-sub" style={{ color: gateStatusColor(gate.status) }}>{gateStatusLabel(gate.status)}</span>
                <strong>{koLabel(gate.label)}</strong>
                <span>{koLabel(gate.detail)}</span>
              </div>
              <span style={{ color: "var(--text-secondary)", maxWidth: "360px" }}>{koLabel(gate.next_step)}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">핵심 주장</span>
            <h2 style={{ fontSize: "1.5rem" }}>계속 참이어야 하는 조건</h2>
          </div>
          <ol style={{ 
            margin: 0, 
            paddingLeft: "20px", 
            color: "var(--text-secondary)", 
            display: "flex", 
            flexDirection: "column", 
            gap: "12px",
            lineHeight: 1.6
          }}>
            {data.core_claims.map((claim) => (
              <li key={claim} style={{ color: "var(--text-primary)" }}>{koLabel(claim)}</li>
            ))}
          </ol>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">무효화 조건</span>
            <h2 style={{ fontSize: "1.5rem" }}>발동되면 논리를 재검토할 조건</h2>
          </div>
          <div className="bento-list">
            {data.invalidation_conditions.map((condition) => (
              <div className="bento-list-item" key={condition.condition} style={{ alignItems: "center" }}>
                <span style={{ color: "var(--text-primary)" }}>{koLabel(condition.condition)}</span>
                <strong style={{ 
                  color: condition.current_status === "not_triggered" ? "var(--accent-green)" : "var(--accent-red)"
                }}>
                  {koCode(condition.current_status)}
                </strong>
              </div>
            ))}
          </div>
        </article>

        <article className="bento-card span-4">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
            <div>
              <span className="metric-sub">근거 자료</span>
              <h2 style={{ fontSize: "1.5rem" }}>원천까지 추적되는 입력</h2>
            </div>
            <Link className="btn btn-secondary" href={`/recommendations/${data.created_from_recommendation_id}`}>
              추천으로 돌아가기
            </Link>
          </div>
          
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "16px" }}>
            {data.evidence.map((evidence) => {
              const href = evidenceHref(evidence.evidence_id, evidence.type, data.symbol);
              return (
                <div key={evidence.evidence_id} style={{
                  padding: "20px",
                  background: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid var(--border-light)",
                  borderRadius: "var(--radius-sm)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px"
                }}>
                  <span className="metric-sub">{koCode(evidence.type)}</span>
                  <strong style={{ fontSize: "1.1rem" }}>{koLabel(evidence.title)}</strong>
                  {href ? (
                    <Link href={href} style={{
                      color: "var(--accent-blue)",
                      fontSize: "0.85rem",
                      textDecoration: "underline",
                      textUnderlineOffset: "4px",
                      marginTop: "8px",
                      width: "fit-content"
                    }}>
                      {evidenceLinkLabel(evidence)}
                    </Link>
                  ) : (
                    <span className="metric-sub">{evidenceLinkLabel(evidence)} 준비 중</span>
                  )}
                  <AuditMetadata items={evidenceMetadata(evidence)} summary="추적 ID 보기" />
                </div>
              );
            })}
          </div>
        </article>
      </section>
    </div>
  );
}
