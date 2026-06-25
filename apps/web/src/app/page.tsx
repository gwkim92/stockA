import type { Route } from "next";
import Link from "next/link";

import { DecisionList } from "@/components/research/DecisionList";
import type { DecisionListItem } from "@/components/research/DecisionList";
import { DecisionSummary } from "@/components/research/DecisionSummary";
import { MetricStrip } from "@/components/research/MetricStrip";
import type { MetricItem } from "@/components/research/MetricStrip";
import { ResearchSection } from "@/components/research/ResearchSection";
import { StatusBadge } from "@/components/status/StatusBadge";
import {
  getAiNewsClusters,
  getCockpitSnapshot,
  getEvents,
  getRecommendations,
  getTradingReadiness,
} from "@/lib/frontend-api";
import { koCode, koReason } from "@/lib/korean-labels";
import { formatCount, formatPercent, investorCopy } from "@/lib/presentation";
import type { DisplayStatusKind } from "@/lib/presentation";

import styles from "./HomePage.module.css";

export const dynamic = "force-dynamic";

type DailyFocus = {
  readonly title: string;
  readonly description: string;
  readonly href: Route;
  readonly actionLabel: string;
  readonly status: DisplayStatusKind;
  readonly sideTitle: string;
  readonly sideDescription: string;
};

function safeCount(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function dailyFocus({
  failedJobCount,
  openTicketCount,
  newEvidenceCount,
}: {
  readonly failedJobCount: number;
  readonly openTicketCount: number;
  readonly newEvidenceCount: number;
}): DailyFocus {
  if (failedJobCount > 0) {
    return {
      title: "데이터 이상을 먼저 해소해야 한다",
      description: `${failedJobCount}개 수집·분석 작업에 이상이 있다. 시장과 추천은 볼 수 있지만 새 판단은 데이터가 안정된 뒤 확정한다.`,
      href: "/data-health",
      actionLabel: "데이터 이상 보기",
      status: "error",
      sideTitle: "새 판단 보류",
      sideDescription: "기존 분석은 유지하되, 문제가 생긴 데이터가 영향을 주는 범위를 먼저 파악한다.",
    };
  }
  if (openTicketCount > 0) {
    return {
      title: "보유 논리의 빈틈을 먼저 줄인다",
      description: `${openTicketCount}개 보완 항목이 남아 있다. 신규 후보보다 기존 보유와 추천의 논리·성과 공백이 우선이다.`,
      href: "/portfolio/coverage",
      actionLabel: "보유 위험 보기",
      status: "watch",
      sideTitle: "보유 위험 우선",
      sideDescription: "보유 비중, 투자 논리, 벤치마크 괴리와 성과 측정 상태를 함께 비교합니다.",
    };
  }
  return {
    title: "새 근거가 바꾼 종목부터 본다",
    description: `${newEvidenceCount}개 뉴스 근거가 현재 분석에 연결됐다. 시장 배경과 같은 방향인지 본 뒤 추천 후보로 내려간다.`,
    href: "/intelligence",
    actionLabel: "새 투자 근거 보기",
    status: "ready",
    sideTitle: "리서치 진행 가능",
    sideDescription: "새 뉴스 흐름, 관련 종목, 반대 근거를 먼저 읽고 추천과 보유 영향으로 이어간다.",
  };
}

export default async function HomePage() {
  const [snapshot, eventsResponse, clustersResponse, recommendationsResponse, tradingResponse] =
    await Promise.all([
      getCockpitSnapshot(),
      getEvents({ limit: 8 }),
      getAiNewsClusters({ limit: 4 }),
      getRecommendations(),
      getTradingReadiness(),
    ]);

  const dashboard = snapshot.dashboard.data;
  const health = snapshot.health.data;
  const tickets = snapshot.tickets.data;
  const events = eventsResponse.data;
  const clusters = clustersResponse.data;
  const recommendations = recommendationsResponse.data;
  const trading = tradingResponse.data;
  const failedJobCount = safeCount(dashboard.attention_summary.failed_pipeline_count);
  const openTicketCount = safeCount(dashboard.attention_summary.open_ticket_count);
  const newEvidenceCount = safeCount(events.summary.ai_extracted_count);
  const focus = dailyFocus({ failedJobCount, openTicketCount, newEvidenceCount });
  const firstRecommendation = recommendations.recommendations[0];
  const primaryRecommendationHref = firstRecommendation
    ? (`/recommendations/${encodeURIComponent(firstRecommendation.recommendation_id)}` as Route)
    : ("/recommendations" as Route);

  const metrics: readonly MetricItem[] = [
    {
      label: "새 투자 근거",
      value: formatCount(newEvidenceCount),
      context: `${formatCount(clusters.summary.cluster_count, "개")} 주요 뉴스 흐름`,
    },
    {
      label: "추천 판단 후보",
      value: formatCount(recommendations.summary.decision_review_ready_count, "개"),
      context: `${formatCount(recommendations.summary.decision_blocked_count, "개")} 판단 차단`,
    },
    {
      label: "보유 분석 커버리지",
      value: formatPercent(dashboard.latest_metrics.weight_coverage_ratio),
      context: `${formatCount(openTicketCount, "개")} 보완 항목`,
    },
    {
      label: "가상 검증",
      value: trading.readiness_status === "blocked" ? "안전 차단" : "검증 가능",
      context: "실거래 주문은 비활성",
    },
  ];

  const evidenceItems: readonly DecisionListItem[] = clusters.clusters.slice(0, 4).map((cluster) => ({
    key: cluster.evidence_id,
    label: cluster.theme_name || "시장 흐름",
    subject: cluster.symbols.filter((symbol) => symbol && symbol !== "UNCLASSIFIED").slice(0, 3).join(" · ") || "시장 전반",
    title: cluster.story_label || cluster.title,
    description: `${formatCount(cluster.event_count)} 뉴스가 묶였다. 신뢰도 ${formatPercent(cluster.confidence)}이며 원문과 반대 근거를 상세에서 함께 읽는다.`,
    status: cluster.confidence !== null && cluster.confidence >= 0.7 ? "ready" : "watch",
    href: `/ai-evidence/${encodeURIComponent(cluster.evidence_id)}` as Route,
    actionLabel: "근거 읽기",
  }));

  const recommendationItems: readonly DecisionListItem[] = recommendations.recommendations
    .slice(0, 5)
    .map((recommendation) => ({
      key: recommendation.recommendation_id,
      label: `${recommendation.rank_position}위 · ${investorCopy(koCode(recommendation.action))}`,
      subject: recommendation.symbol,
      title: recommendation.evidence_quality.title || `${recommendation.name} 투자 판단`,
      description: recommendation.evidence_quality.summary,
      status: recommendation.decision_boundary.paper_validation_input_allowed
        ? "ready"
        : recommendation.evidence_quality.source_blocker.blocked
          ? "source_limited"
          : "blocked",
      href: `/recommendations/${encodeURIComponent(recommendation.recommendation_id)}` as Route,
      actionLabel: "판단서 읽기",
    }));

  const riskItems: readonly DecisionListItem[] = dashboard.top_actions.slice(0, 5).map((action) => ({
    key: `${action.rank}-${action.symbol}-${action.action}`,
    label: `우선순위 ${action.rank}`,
    subject: action.symbol,
    title: investorCopy(koCode(action.action)),
    description: koReason(action.reason),
    status: action.risk_level === "high" ? "blocked" : "watch",
    href: "/remediation",
    actionLabel: "보완 항목 보기",
  }));

  return (
    <div className={styles.page}>
      <DecisionSummary
        eyebrow={`오늘의 투자 판단 · ${dashboard.as_of_date}`}
        title={focus.title}
        description={focus.description}
        primaryAction={{ href: focus.href, label: focus.actionLabel }}
        secondaryActions={[
          { href: "/market-map", label: "시장 지도" },
          { href: primaryRecommendationHref, label: "대표 추천" },
        ]}
        side={
          <>
            <StatusBadge kind={focus.status} />
            <strong>{focus.sideTitle}</strong>
            <p>{focus.sideDescription}</p>
          </>
        }
      />

      <MetricStrip items={metrics} label="오늘의 핵심 투자 지표" />

      <nav className={styles.decisionLine} aria-label="투자 판단 경로">
        {[
          ["/market-map", "시장", "자산군 압력"],
          ["/cycle-map", "사이클", "상위 흐름"],
          ["/intelligence", "뉴스", "새 근거"],
          ["/stocks", "종목", "기업 분석"],
          ["/recommendations", "추천", "판단 경계"],
          ["/portfolio/coverage", "포트폴리오", "보유 위험"],
        ].map(([href, label, context]) => (
          <Link href={href as Route} key={href}>
            <span>{label}</span>
            <small>{context}</small>
          </Link>
        ))}
      </nav>

      <ResearchSection
        eyebrow="새로운 시장 근거"
        title="오늘 새로 연결된 뉴스 흐름"
        description="원문이 같은 사건을 설명하는지, 방향이 일관되는지, 어떤 종목에 직접 또는 간접 영향을 주는지 순서대로 읽는다."
      >
        <DecisionList items={evidenceItems} emptyText="오늘 새로 구조화된 뉴스 흐름이 없다." />
      </ResearchSection>

      <ResearchSection
        eyebrow="추천 변화"
        title="현재 판단 단계에 있는 종목"
        description="점수 순위보다 근거 충족도, 원천 제한과 가상 매매 가능 여부가 중요합니다."
      >
        <DecisionList items={recommendationItems} emptyText="현재 표시할 추천 판단 후보가 없다." />
      </ResearchSection>

      <ResearchSection
        eyebrow="보유 위험"
        title="기존 판단에서 먼저 메울 공백"
        description={`${tickets.ticket_count.toLocaleString("ko-KR")}개 보완 기록 중 투자 논리와 보유 위험에 직접 연결된 항목을 우선 표시한다.`}
      >
        <DecisionList items={riskItems} emptyText="현재 우선 처리할 보유 위험이 없다." />
      </ResearchSection>

      <section className={styles.systemNotice} aria-label="시스템 신뢰 상태">
        <div>
          <span>시스템 신뢰 상태</span>
          <strong>{failedJobCount > 0 ? "일부 데이터 주의" : "최근 자동 작업 정상"}</strong>
          <p>
            투자 화면에는 판단에 영향을 주는 이상만 표시한다. 수집 주기, AI 인증, 실행 기록은 데이터 상태에서 분리해 관리한다.
          </p>
        </div>
        <Link href="/data-health">운영 상태 열기</Link>
      </section>
    </div>
  );
}
