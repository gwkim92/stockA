import Link from "next/link";
import type { Route } from "next";
import { AuditMetadata, type AuditMetadataItem } from "@/components/audit-metadata";
import { ValuationTargetRangeCard } from "@/components/valuation-target-range-card";
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
    return "관련 뉴스·공시 보기";
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
    { label: "원문 검토 기록", value: thesisText(rationale.rawChangeNotes) },
    { label: "적용 조치 코드", value: rationale.action },
    ...rationale.signals.map((signal, index) => ({
      label: `검토 기준 ${index + 1}`,
      value: signal.code,
    })),
  ];
}

function reviewCount(value: number | boolean | undefined) {
  return typeof value === "number" ? value : value ? 1 : 0;
}

function thesisText(value: string | null | undefined) {
  return koLabel(value)
    .replace(/read only fallback/gi, "읽기 전용 대기")
    .replace(/lifecycle not available/gi, "투자 논리 생애주기 미연결")
    .replace(/not available/gi, "아직 없음")
    .replace(/fallback/gi, "대체 처리")
    .replace(/주문 경계/g, "실거래 상태")
    .replace(/증권사 연결 경계/g, "증권사 연결 상태")
    .replace(/좋은 thesis/g, "좋은 투자 논리")
    .replace(/thesis review/g, "투자 논리 검토")
    .replace(/thesis(?=[가-힣])/g, "투자 논리")
    .replace(/안전마진\s+근거/g, "근거")
    .replace(/안전마진\s+안전마진/g, "안전마진")
    .replace(/밸류에이션 스냅샷가/g, "밸류에이션 스냅샷이");
}

function compactThesisSummary(data: ThesisDetailData) {
  const summary = thesisText(data.summary).replace(/\s+/g, " ").trim();
  if (summary.length <= 220) {
    return `${summary} 이 투자 논리는 주문 지시가 아니라 매수 이유, 유지 조건, 무효화 조건을 검증하는 기준이다.`;
  }

  const theme = summary.match(/핵심 테마는\s*([^().,]+)(?:\s*\([^)]+\))?/u)?.[1]?.trim();
  const cycleState = summary.match(/사이클 상태는\s*([^,.]+)[,.]/u)?.[1]?.trim();
  const latestPriceRaw = summary.match(/최신 수정종가\s*([0-9]+(?:\.[0-9]+)?)/u)?.[1]?.trim();
  const latestPrice = latestPriceRaw
    ? Number(latestPriceRaw).toLocaleString("ko-KR", { maximumFractionDigits: 2 })
    : null;
  const facts = [
    theme ? `핵심 테마 ${koCode(theme)}` : null,
    cycleState ? `사이클 ${koCode(cycleState)}` : null,
    latestPrice ? `최근 가격 ${latestPrice}` : null,
  ].filter(Boolean);

  return `${data.symbol}의 중장기 투자 논리를 ${facts.length > 0 ? facts.join(", ") : "핵심 테마와 최근 검토 기준"}으로 점검한다. 원문 초안 전체를 먼저 읽기보다, 아래에서 매수 이유, 유지 조건, 무효화 조건, 연결 근거가 충분한지 확인한다.`;
}

function compactLatestReviewSummary(data: ThesisDetailData) {
  const rawSummary = data.latest_review.summary;
  if (!rawSummary) {
    return "아직 검토 요약이 없다.";
  }

  const summary = thesisText(rawSummary).replace(/\s+/g, " ").trim();
  const action = koCode(data.latest_review.action);
  const scoreRaw = summary.match(/(?:건강 점수|추천 점수)\s*([0-9]+(?:\.[0-9]+)?)/u)?.[1];
  const score = scoreRaw ? `${(Number(scoreRaw) * 100).toFixed(1)}%` : null;
  const cycleState = summary.match(/사이클은\s*([^.\s]+)\s*상태/u)?.[1]?.trim();
  const latestPriceRaw = summary.match(/최신 수정종가\s*([0-9]+(?:\.[0-9]+)?)/u)?.[1]?.trim();
  const latestPrice = latestPriceRaw
    ? Number(latestPriceRaw).toLocaleString("ko-KR", { maximumFractionDigits: 2 })
    : null;
  const nextReview = data.latest_review.next_review_date;
  const facts = [
    score ? `점수 ${score}` : null,
    cycleState ? `사이클 ${koCode(cycleState)}` : null,
    latestPrice ? `최근 가격 ${latestPrice}` : null,
    nextReview ? `다음 확인일 ${nextReview}` : null,
  ].filter(Boolean);

  return `${data.symbol} 최근 검토는 ${action} 판단이다. ${facts.length > 0 ? facts.join(", ") : "세부 입력은 아래 검토 기준"}을 기준으로 유지·보강 여부를 확인한다. 주문이나 가상 거래는 자동으로 만들지 않는다.`;
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

const LIFECYCLE_MISSING_LABELS: Record<string, string> = {
  catalysts: "촉매/성립 조건",
  core_claims: "핵심 주장",
  invalidation_conditions: "무효화 조건",
  next_review_date: "다음 재검토일",
  risks: "리스크",
  valuation_sensitivity: "밸류에이션 민감도",
};

function lifecycleReadinessLabel(status: string) {
  if (status === "complete") {
    return "생애주기 완비";
  }
  if (status === "needs_detail") {
    return "보강 필요";
  }
  if (status === "blocked") {
    return "채택 차단";
  }
  return koCode(status);
}

function lifecycleTone(status: string) {
  if (status === "complete") {
    return "risk-low";
  }
  if (status === "blocked") {
    return "risk-high";
  }
  return "risk-medium";
}

function lifecycleSourceLabel(source: string) {
  if (source === "equity_research_artifact") {
    return "AI 기업 리서치 연결";
  }
  if (source === "thesis_record") {
    return "투자 논리 원장만 사용";
  }
  return koCode(source);
}

function professionalGateTone(status: string) {
  if (status === "pass") {
    return "risk-low";
  }
  if (status === "blocked") {
    return "risk-high";
  }
  return "risk-medium";
}

function missingLifecycleItems(items: string[]) {
  if (items.length === 0) {
    return "누락 없음";
  }
  return items.map((item) => LIFECYCLE_MISSING_LABELS[item] ?? koCode(item)).join(", ");
}

function formatUnknownValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "미정";
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? value.toLocaleString("ko-KR") : "미정";
  }
  if (typeof value === "boolean") {
    return value ? "예" : "아니오";
  }
  return thesisText(String(value));
}

type ThesisLifecycle = ThesisDetailData["lifecycle"];

function valuationItems(valuation: ThesisLifecycle["valuation"]) {
  const rows = [
    { label: "기준 시나리오", value: valuation.base_case },
    { label: "상방 조건", value: valuation.upside_case },
    { label: "하방 조건", value: valuation.downside_case },
    { label: "안전마진 관점", value: valuation.margin_of_safety_view },
  ].filter((item) => item.value);

  if (rows.length > 0) {
    return rows;
  }

  return Object.entries(valuation.raw)
    .slice(0, 4)
    .map(([label, value]) => ({ label: koCode(label), value: formatUnknownValue(value) }));
}

function LifecycleList({ empty, items }: { empty: string; items: string[] }) {
  if (items.length === 0) {
    return <p style={{ color: "var(--text-secondary)", lineHeight: 1.65, margin: 0 }}>{empty}</p>;
  }

  return (
    <ul style={{ margin: 0, paddingLeft: "18px", color: "var(--text-primary)", lineHeight: 1.65 }}>
      {items.map((item) => (
        <li key={item}>{thesisText(item)}</li>
      ))}
    </ul>
  );
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
    status: "AI 검토 통과",
    tone: "risk-low",
    summary: "원천 근거, 성과 근거, 무효화 조건, 최근 검토가 연결되어 있어 AI 자동 검토가 중장기 보유 논리를 통과시켰다.",
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
      value: ["ai_review_passed", "ready_for_human_review"].includes(data.evidence_review.quality_status)
        ? "AI 검토 통과"
        : koCode(data.evidence_review.quality_status),
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
      label: "실거래 상태",
      value: "자동 주문 없음",
      detail: "이 판정은 투자 논리 품질 검토이며 증권사 주문 흐름을 실행하지 않는다.",
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
  const lifecycle = data.lifecycle;
  const professionalGates = data.professional_lifecycle_gates;
  const valuationTargetRange = data.valuation_target_range;
  const valuationRows = valuationItems(lifecycle.valuation);

  return (
    <div className="pageStack decision-page">
      <section className="decision-brief reveal" aria-labelledby="thesis-detail-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">
            투자 논리 · {data.symbol} · {koCode(data.status)} · {koCode(data.thesis_version)}
          </span>
          <h1 className="decision-brief-title" id="thesis-detail-title">
            {data.symbol} 투자 논리: 최근 검토 {koCode(data.latest_review.action)}
          </h1>
          <p className="decision-brief-copy">
            {compactThesisSummary(data)}
          </p>
          <div className="decision-brief-meta" aria-label="투자 논리 핵심 상태">
            <span>위험도 {koCode(data.latest_review.risk_level)}</span>
            <span>전문 게이트 {professionalGates.pass_count}/{professionalGates.gate_count} 통과</span>
            <span>차단 {professionalGates.blocked_count.toLocaleString("ko-KR")}개</span>
            <span>근거 {data.evidence.length.toLocaleString("ko-KR")}개</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <a className={professionalGates.blocked_count > 0 ? "decision-card is-block" : "decision-card is-good"} href="#thesis-professional-gates">
            <span>전문 검증</span>
            <strong>{professionalGates.status === "complete" ? "통과" : professionalGates.status === "blocked" ? "차단" : "재검토"}</strong>
            <small>주의 {professionalGates.warning_count.toLocaleString("ko-KR")}개 · 차단 {professionalGates.blocked_count.toLocaleString("ko-KR")}개</small>
            <b>게이트 보기</b>
          </a>
          <a className="decision-card is-watch" href="#thesis-lifecycle">
            <span>최근 검토</span>
            <strong>{koCode(data.latest_review.action)}</strong>
            <small>위험도 {koCode(data.latest_review.risk_level)} · 변화 사유를 아래에서 확인한다.</small>
            <b>검토 보기</b>
          </a>
          <a className={data.evidence.length > 0 ? "decision-card is-good" : "decision-card is-watch"} href="#thesis-evidence-ledger">
            <span>근거 원장</span>
            <strong>{data.evidence.length.toLocaleString("ko-KR")}개</strong>
            <small>뉴스·공시·성과 근거가 투자 논리를 받치는지 확인한다.</small>
            <b>근거 보기</b>
          </a>
          <a className="decision-card is-block" href="#thesis-professional-gates">
            <span>실거래 상태</span>
            <strong>자동 주문 없음</strong>
            <small>이 화면은 투자 논리 품질 검토이며 증권사 주문 흐름을 실행하지 않는다.</small>
            <b>경계 보기</b>
          </a>
        </div>
      </section>

      <section className="bento-card reveal delay-1" id="thesis-professional-gates" aria-label="전문 투자 논리 검증">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap", marginBottom: "20px" }}>
          <div>
            <span className="metric-sub">전문 투자 논리 검증</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>
              {professionalGates.status === "complete" ? "전문 검증 통과" : professionalGates.status === "blocked" ? "전문 검증 차단" : "재검토 필요"}
            </h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "860px" }}>
              {thesisText(professionalGates.summary)}
            </p>
          </div>
          <span className={`risk-tag ${professionalGates.blocked_count > 0 ? "risk-high" : professionalGates.warning_count > 0 ? "risk-medium" : "risk-low"}`}>
            읽기 전용·주문 금지
          </span>
        </div>

        <div className="status-rail compact-rail" style={{ marginBottom: "20px" }}>
          <div className="rail-cell">
            <span>통과</span>
            <strong>{professionalGates.pass_count}</strong>
            <small>{professionalGates.gate_count}개 검증 기준</small>
          </div>
          <div className="rail-cell">
            <span>주의</span>
            <strong>{professionalGates.warning_count}</strong>
            <small>보강/재검토</small>
          </div>
          <div className="rail-cell">
            <span>차단</span>
            <strong>{professionalGates.blocked_count}</strong>
            <small>진행 금지</small>
          </div>
          <div className="rail-cell">
            <span>최신 근거</span>
            <strong>{professionalGates.latest_evidence_at ? professionalGates.latest_evidence_at.slice(0, 10) : "미정"}</strong>
            <small>최근 검토 {professionalGates.latest_reviewed_at ? professionalGates.latest_reviewed_at.slice(0, 10) : "미정"}</small>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "14px" }}>
          {professionalGates.gates.map((gate) => (
            <article className="detail-path-card" key={gate.gate_key}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "flex-start", marginBottom: "10px" }}>
                <div>
                  <span>{thesisText(gate.title)}</span>
                  <strong style={{ display: "block", fontSize: "1rem", marginTop: "4px" }}>{thesisText(gate.decision)}</strong>
                </div>
                <span className={`risk-tag ${professionalGateTone(gate.status)}`}>
                  {gateStatusLabel(gate.status)}
                </span>
              </div>
              <p style={{ color: "var(--text-secondary)", lineHeight: 1.6, margin: "0 0 12px" }}>
                {thesisText(gate.detail)}
              </p>
              <dl className="research-flow-facts" style={{ marginBottom: "12px" }}>
                {gate.facts.map((fact) => (
                  <div key={`${gate.gate_key}-${fact.label}`}>
                    <dt>{thesisText(fact.label)}</dt>
                    <dd>{thesisText(fact.value)}</dd>
                  </div>
                ))}
              </dl>
              <p style={{ color: "var(--text-muted)", lineHeight: 1.55, margin: 0, fontSize: "0.86rem" }}>
                다음 조치: {thesisText(gate.next_step)}
              </p>
            </article>
          ))}
        </div>
      </section>

      <ValuationTargetRangeCard
        valuation={valuationTargetRange}
        eyebrow="투자 논리 가격 검토"
        title={`${data.symbol} 목표가 범위와 안전마진`}
      />

      <section className="bento-card reveal delay-1" id="thesis-lifecycle" aria-label="투자 논리 생애주기">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap", marginBottom: "20px" }}>
          <div>
            <span className="metric-sub">투자 논리 생애주기</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>
              {lifecycleReadinessLabel(lifecycle.readiness.status)}
            </h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "820px" }}>
              이 섹션은 종목을 볼 때 반드시 확인해야 하는 순서다. AI 리서치와 투자 논리 원장을 합쳐서 매수 논리, 성립 조건,
              이탈 조건, 밸류에이션 관점, 다음 재검토일을 분리한다.
            </p>
          </div>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
            <span className={`risk-tag ${lifecycleTone(lifecycle.readiness.status)}`}>
              {lifecycleSourceLabel(lifecycle.source)}
            </span>
            <span className="risk-tag risk-medium">자동 주문 없음</span>
          </div>
        </div>

        <div className="status-rail compact-rail" style={{ marginBottom: "20px" }}>
          <div className="rail-cell">
            <span>핵심 주장</span>
            <strong>{lifecycle.readiness.core_claim_count}</strong>
            <small>왜 사는가</small>
          </div>
          <div className="rail-cell">
            <span>성립 조건</span>
            <strong>{lifecycle.readiness.catalyst_count}</strong>
            <small>무엇이 맞아야 하나</small>
          </div>
          <div className="rail-cell">
            <span>리스크</span>
            <strong>{lifecycle.readiness.risk_count}</strong>
            <small>무엇을 조심하나</small>
          </div>
          <div className="rail-cell">
            <span>무효화</span>
            <strong>{lifecycle.readiness.invalidation_count}</strong>
            <small>무엇이 틀리면 나가나</small>
          </div>
        </div>

        <div className="bento-grid">
          <article className="bento-card span-2">
            <span className="metric-sub">왜 사는가</span>
            <h3 style={{ fontSize: "1.15rem", margin: "6px 0 12px" }}>{data.symbol} 장기 논리</h3>
            <p style={{ color: "var(--text-secondary)", lineHeight: 1.65, marginTop: 0 }}>
              {lifecycle.buy_case.summary ? thesisText(lifecycle.buy_case.summary) : compactThesisSummary(data)}
            </p>
            <LifecycleList empty="핵심 주장이 아직 분리되어 있지 않다." items={lifecycle.buy_case.core_claims} />
          </article>

          <article className="bento-card span-2">
            <span className="metric-sub">무엇이 맞아야 하는가</span>
            <h3 style={{ fontSize: "1.15rem", margin: "6px 0 12px" }}>촉매와 성립 조건</h3>
            <LifecycleList empty="AI 리서치나 투자 논리 원장에 촉매 조건이 없다." items={lifecycle.catalysts} />
          </article>

          <article className="bento-card span-2">
            <span className="metric-sub">무엇이 틀리면 나가는가</span>
            <h3 style={{ fontSize: "1.15rem", margin: "6px 0 12px" }}>리스크와 무효화 조건</h3>
            <LifecycleList empty="리스크 항목이 아직 없다." items={lifecycle.risks} />
            <div className="bento-list" style={{ marginTop: "14px" }}>
              {lifecycle.invalidation_conditions.map((condition) => (
                <div className="bento-list-item" key={condition.condition} style={{ alignItems: "center" }}>
                  <span style={{ color: "var(--text-primary)" }}>{thesisText(condition.condition)}</span>
                  <strong style={{ color: condition.current_status === "not_triggered" ? "var(--accent-green)" : "var(--accent-red)" }}>
                    {koCode(condition.current_status)}
                  </strong>
                </div>
              ))}
            </div>
          </article>

          <article className="bento-card span-2">
            <span className="metric-sub">밸류에이션 민감도</span>
            <h3 style={{ fontSize: "1.15rem", margin: "6px 0 12px" }}>가격 판단에 필요한 조건</h3>
            {valuationRows.length > 0 ? (
              <div className="bento-list">
                {valuationRows.map((item) => (
                  <div className="bento-list-item" key={item.label}>
                    <strong>{item.label}</strong>
                    <span>{formatUnknownValue(item.value)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "var(--text-secondary)", lineHeight: 1.65, margin: 0 }}>
                아직 밸류에이션 민감도 입력이 없다. 추천 점수에는 반영하지 않는다.
              </p>
            )}
          </article>

          <article className="bento-card span-4">
            <div style={{ display: "flex", justifyContent: "space-between", gap: "20px", flexWrap: "wrap" }}>
              <div>
                <span className="metric-sub">언제 다시 보는가</span>
                <h3 style={{ fontSize: "1.15rem", margin: "6px 0 8px" }}>
                  다음 재검토일 {lifecycle.review_cadence.next_review_date || "미정"}
                </h3>
                <p style={{ color: "var(--text-secondary)", lineHeight: 1.65, margin: 0 }}>
                  최근 조치 {koCode(lifecycle.review_cadence.latest_review_action)} · 위험도 {koCode(lifecycle.review_cadence.risk_level)}
                  {lifecycle.review_cadence.reviewed_at ? ` · 최근 검토 ${lifecycle.review_cadence.reviewed_at}` : ""}
                </p>
              </div>
              <div style={{ maxWidth: "420px", color: "var(--text-secondary)", lineHeight: 1.65 }}>
                보강 필요 항목: {missingLifecycleItems(lifecycle.readiness.missing_items)}
              </div>
            </div>
            <AuditMetadata
              items={[
                { label: "생애주기 원천", value: lifecycleSourceLabel(lifecycle.source) },
                { label: "기업 리서치 결과", value: lifecycle.equity_research_artifact_id || "없음" },
                { label: "누락 항목", value: missingLifecycleItems(lifecycle.readiness.missing_items) },
                { label: "밸류에이션 입력", value: lifecycle.readiness.has_valuation_view ? "확인됨" : "부족" },
              ]}
              summary="생애주기 판정 원천 보기"
            />
          </article>
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
          {compactLatestReviewSummary(data)}
        </p>
        {reviewRationale ? (
          <div className="review-rationale">
            {reviewRationale.signals.length > 0 ? (
              <div className="review-signal-list" aria-label="검토 기준">
                {reviewRationale.signals.map((signal) => (
                  <span className="review-signal-chip" key={signal.code}>
                    {signal.label}
                  </span>
                ))}
              </div>
            ) : (
              <p>{thesisText(data.latest_review.change_notes)}</p>
            )}
            <p>
              {reviewRationale.action ? `적용 조치: ${koCode(reviewRationale.action)}. ` : ""}
              {reviewRationale.safetyNote ? thesisText(reviewRationale.safetyNote) : "투자 논리 상태와 주문은 자동으로 변경하지 않는다."}
            </p>
            <AuditMetadata items={reviewRationaleMetadata(reviewRationale)} summary="검토 세부 기준 보기" />
          </div>
        ) : (
          <p style={{ color: "var(--text-secondary)", lineHeight: 1.65, margin: 0, fontSize: "0.92rem" }}>
            아직 검토 신호 기록이 없다.
          </p>
        )}
      </section>

      <section className="bento-card reveal delay-1" aria-label="투자 논리 근거 품질 점검">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap", marginBottom: "20px" }}>
          <div>
            <span className="metric-sub">근거 품질 점검</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{koCode(evidenceReview.quality_status)}</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "760px" }}>
              이 점검은 투자 논리를 주문으로 바꾸지 않는다. 원천 이벤트, 성과 근거, 무효화 조건, 최근 AI 자동 검토가
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
                <strong>{thesisText(gate.label)}</strong>
                <span>{thesisText(gate.detail)}</span>
              </div>
              <span style={{ color: "var(--text-secondary)", maxWidth: "360px" }}>{thesisText(gate.next_step)}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="bento-grid reveal delay-1" id="thesis-evidence-ledger">
        <article className="bento-card span-4">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
            <div>
              <span className="metric-sub">근거 자료</span>
              <h2 style={{ fontSize: "1.5rem" }}>투자 논리를 뒷받침한 원천 입력</h2>
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
                  <strong style={{ fontSize: "1.1rem" }}>{thesisText(evidence.title)}</strong>
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
                    <span className="metric-sub">연결된 근거 화면 없음</span>
                  )}
                  <AuditMetadata items={evidenceMetadata(evidence)} summary="근거 연결 정보 보기" />
                </div>
              );
            })}
          </div>
        </article>
      </section>
    </div>
  );
}
