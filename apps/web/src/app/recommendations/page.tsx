import type { Route } from "next";
import Link from "next/link";

import { DecisionSummary } from "@/components/research/DecisionSummary";
import { MetricStrip } from "@/components/research/MetricStrip";
import { ResearchSection } from "@/components/research/ResearchSection";
import { StatusBadge } from "@/components/status/StatusBadge";
import { getRecommendations } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import { formatPercent, investorCopy } from "@/lib/presentation";
import type { RecommendationListData } from "@/lib/types";

import styles from "./RecommendationsPage.module.css";

export const dynamic = "force-dynamic";
export const metadata = { title: "추천" };

type RecommendationRow = RecommendationListData["recommendations"][number];

function recommendationHref(recommendationId: string) {
  return `/recommendations/${encodeURIComponent(recommendationId)}` as Route;
}

function stockHref(symbol: string) {
  return `/stocks/${encodeURIComponent(symbol)}` as Route;
}

function recommendationStatus(row: RecommendationRow) {
  if (row.evidence_quality.status === "source_blocked" || row.evidence.quality_status === "blocked") {
    return { kind: "source_limited" as const, label: "원천 근거 부족" };
  }
  if (row.decision_boundary.status === "paper_validation_pending") {
    return { kind: "watch" as const, label: "가상 매매 대기" };
  }
  if (row.decision_boundary.status === "decision_review_ready") {
    return { kind: "ready" as const, label: "근거 연결됨" };
  }
  return { kind: "blocked" as const, label: "판단 보류" };
}

function recommendationEvidence(row: RecommendationRow) {
  const parts = [
    row.linked_thesis_id ? "투자 논리 연결" : "투자 논리 없음",
    `뉴스·공시 ${row.evidence.ai_or_event_component_count}개`,
    `상위 흐름 ${row.evidence.macro_flow_evidence_count}개`,
    `근거 충족 ${row.evidence_quality.available_layer_count}/${row.evidence_quality.expected_layer_count}`,
  ];
  return parts.join(" · ");
}

function recommendationRisk(row: RecommendationRow) {
  if (row.evidence_quality.missing_layer_labels.length > 0) {
    return `보강 필요: ${row.evidence_quality.missing_layer_labels
      .slice(0, 2)
      .map((label) => investorCopy(koCode(label)))
      .join(", ")}`;
  }
  if (row.outcome.label === "unmeasured") {
    return "성과 측정 기간 진행 중";
  }
  return `성과 ${koCode(row.outcome.label)} · 알파 ${formatPercent(row.outcome.alpha)}`;
}

export default async function RecommendationsPage() {
  const { data } = await getRecommendations();
  const lead = data.recommendations[0] ?? null;
  const sourceBlocked = data.summary.evidence_quality_source_blocked_count;
  const decisionReady = data.summary.decision_review_ready_count;

  return (
    <div className={styles.page}>
      <DecisionSummary
        eyebrow={`추천 · ${data.as_of_date || "기준일 미정"} · ${koCode(data.horizon_type)}`}
        title={lead ? `${lead.symbol}, 현재 최상위 중장기 후보` : "연결된 추천이 없습니다"}
        description="추천은 주문 지시가 아닙니다. 기대수익, 근거 충족도, 반대 신호와 가상 매매 상태를 함께 비교합니다."
        primaryAction={{
          href: lead ? recommendationHref(lead.recommendation_id) : ("/data-health" as Route),
          label: lead ? `${lead.symbol} 추천 분석` : "데이터 상태 확인",
        }}
        secondaryActions={[
          { href: "/stocks" as Route, label: "종목 비교" },
          { href: "/paper-trading" as Route, label: "가상 매매" },
        ]}
        side={
          <div className={styles.leadScore}>
            <span>최상위 점수</span>
            <strong>{lead ? formatPercent(lead.score) : "대기"}</strong>
            <small>{lead ? recommendationEvidence(lead) : "추천 산출 후 표시됩니다."}</small>
          </div>
        }
      />

      <MetricStrip
        label="추천 현황"
        items={[
          { label: "추천 후보", value: `${data.recommendation_count}개`, context: "현재 중장기 판단 대상" },
          { label: "근거 연결", value: `${decisionReady}개`, context: "핵심 판단 근거가 연결된 추천" },
          {
            label: "가상 매매 대기",
            value: `${data.summary.paper_validation_pending_count}개`,
            context: "실제 주문 전 성과·안전 검증",
          },
          {
            label: "원천 제한",
            value: `${sourceBlocked}개`,
            context: sourceBlocked > 0 ? "전문 판단 입력에서 제외" : "원천 차단 없음",
          },
        ]}
      />

      <ResearchSection
        eyebrow="추천 비교"
        title="중장기 후보와 판단 경계"
        description="점수보다 근거 충족도와 차단 사유를 먼저 비교합니다."
        id="recommendation-list"
      >
        {data.recommendations.length === 0 ? (
          <p className={styles.empty}>현재 검토할 추천이 없습니다.</p>
        ) : (
          <div className={styles.list}>
            {data.recommendations.map((row) => {
              const status = recommendationStatus(row);
              return (
                <article className={styles.row} key={row.recommendation_id}>
                  <div className={styles.identity}>
                    <span>#{row.rank_position}</span>
                    <Link href={stockHref(row.symbol)}>
                      <strong>{row.symbol}</strong>
                      <small>{row.name}</small>
                    </Link>
                  </div>
                  <div className={styles.score}>
                    <span>추천 점수</span>
                    <strong>{formatPercent(row.score)}</strong>
                    <small>목표 비중 {formatPercent(row.recommended_weight)}</small>
                  </div>
                  <div className={styles.evidence}>
                    <StatusBadge kind={status.kind} label={status.label} />
                    <strong>{recommendationEvidence(row)}</strong>
                    <p>{recommendationRisk(row)}</p>
                  </div>
                  <div className={styles.boundary}>
                    <span>현재 조치</span>
                    <strong>{koCode(row.action)}</strong>
                    <small>{investorCopy(koCode(row.decision_boundary.reason))}</small>
                  </div>
                  <Link className={styles.openAction} href={recommendationHref(row.recommendation_id)}>
                    분석 열기
                  </Link>
                </article>
              );
            })}
          </div>
        )}
      </ResearchSection>

      <aside className={styles.boundaryNote}>
        <div>
          <span>거래 경계</span>
          <strong>모든 추천은 읽기 전용입니다.</strong>
          <p>가상 매매와 위험 검증을 통과해도 증권사 주문 제출은 별도 승인 전까지 차단됩니다.</p>
        </div>
        <Link href="/trading-readiness">거래 안전 상태</Link>
      </aside>
    </div>
  );
}
