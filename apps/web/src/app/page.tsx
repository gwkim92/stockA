import Link from "next/link";
import type { Route } from "next";
import { DecisionReviewStrip } from "@/components/decision-review-strip";
import {
  getAiNewsClusters,
  getCockpitSnapshot,
  getEvents,
  getRecommendations,
  getTradingReadiness,
} from "@/lib/frontend-api";
import { koCode, koReason } from "@/lib/korean-labels";
import type { DailyCockpitData, DataHealthData } from "@/lib/types";

export const dynamic = "force-dynamic";

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function safeCount(value: unknown, fallback = 0) {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function riskClass(value: string) {
  if (value === "high") {
    return "risk-high";
  }
  if (value === "medium") {
    return "risk-medium";
  }
  return "risk-low";
}

function readinessTone(status: string) {
  if (status === "blocked") {
    return "risk-high";
  }
  if (status === "warning") {
    return "risk-medium";
  }
  return "risk-low";
}

function automationDisplayLabel(scheduler: DataHealthData["scheduler"], fallbackStatus: string) {
  const activation = scheduler.activation;
  const profileScheduler = scheduler.profile_scheduler;
  if (
    activation.approval_gate === "installed_on_ec2_systemd"
    || (profileScheduler && profileScheduler.active_timer_count > 0)
  ) {
    const active = profileScheduler?.active_timer_count ?? 0;
    const total = profileScheduler?.timer_count ?? active;
    return total > 0 ? `EC2 자동 반복 실행 중 (${active}/${total})` : "EC2 자동 반복 실행 중";
  }
  if (activation.activation_allowed && activation.scheduler_activation !== "not_installed") {
    return "자동 반복 실행 가능";
  }
  return koCode(fallbackStatus);
}

function fallbackOutcomeWaitMonitor(asOfDate: string): DataHealthData["outcome_maturity_wait_monitor"] {
  return {
    status: "unavailable",
    title: "성과 대기 정보가 아직 연결되지 않았다",
    summary: "추천 성과 측정일과 포트폴리오 사후 평가 성숙일이 아직 연결되지 않았다.",
    next_action: "데이터 상태 화면에서 성과 성숙 대기 정보가 연결됐는지 확인한다.",
    as_of_date: asOfDate,
    recommendation_next_due_date: "",
    recommendation_next_due_count: 0,
    recommendation_maturity_status: "unavailable",
    recommendation_action_status: "unavailable",
    recommendation_ready_for_backfill_count: 0,
    recommendation_overdue_count: 0,
    recommendation_price_gap_count: 0,
    portfolio_feedback_maturity_date: "",
    portfolio_feedback_status: "unavailable",
    portfolio_feedback_run_gap: 0,
    portfolio_mature_decision_gap: 0,
    earliest_action_date: "",
    wait_item_count: 0,
    wait_items: [],
    weight_review_blocked: true,
    weight_review_block_reason: "성과 성숙 대기 정보 미연결",
    manual_weight_review_allowed: false,
    recommendation_scoring_mutated: false,
    benchmark_definition_mutated: false,
    portfolio_position_mutated: false,
    automatic_weight_change_allowed: false,
    automatic_rebalance_allowed: false,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
  };
}

function shortReviewReason(value: string) {
  if (value.includes("single position review cap")) {
    return "단일 종목 비중이 검토 기준보다 높다.";
  }
  if (value.includes("missing_thesis")) {
    return "보유 또는 추천에 연결된 투자 논리가 비어 있다.";
  }
  if (value.includes("missing_outcome")) {
    return "성과 측정 기록이 아직 없다.";
  }
  if (value.includes("target weight equals current weight")) {
    return "현재 비중과 목표 비중이 같아 조치가 생략됐다.";
  }
  return koReason(value);
}

type TopAction = DailyCockpitData["top_actions"][number];

type TopActionGroup = {
  key: string;
  firstRank: number;
  symbols: string[];
  action: string;
  reason: string;
  suggestedRunner: string;
  riskLevel: TopAction["risk_level"];
  count: number;
};

function actionGroupKey(action: TopAction) {
  return [action.action, action.reason, action.suggested_runner, action.risk_level].join("\u0000");
}

function groupTopActions(actions: TopAction[]): TopActionGroup[] {
  const groups = new Map<string, TopActionGroup>();
  for (const action of actions) {
    const key = actionGroupKey(action);
    const existing = groups.get(key);
    if (existing) {
      existing.count += 1;
      existing.firstRank = Math.min(existing.firstRank, action.rank);
      if (!existing.symbols.includes(action.symbol)) {
        existing.symbols.push(action.symbol);
      }
      continue;
    }

    groups.set(key, {
      key,
      firstRank: action.rank,
      symbols: [action.symbol],
      action: action.action,
      reason: action.reason,
      suggestedRunner: action.suggested_runner,
      riskLevel: action.risk_level,
      count: 1,
    });
  }

  return Array.from(groups.values()).sort((left, right) => left.firstRank - right.firstRank);
}

function symbolGroupLabel(symbols: string[]) {
  const visibleSymbols = symbols.slice(0, 6).join(", ");
  const extraCount = symbols.length - 6;
  return extraCount > 0 ? `${visibleSymbols} 외 ${extraCount}개` : visibleSymbols;
}

export default async function HomePage() {
  const [snapshot, eventsResponse, newsClustersResponse, recommendationsResponse, tradingResponse] =
    await Promise.all([
      getCockpitSnapshot(),
      getEvents({ limit: 8 }),
      getAiNewsClusters({ limit: 3 }),
      getRecommendations(),
      getTradingReadiness(),
    ]);

  const { dashboard, tickets, health } = snapshot;
  const data = dashboard.data;
  const ticketData = tickets.data;
  const eventData = eventsResponse.data;
  const clusterData = newsClustersResponse.data;
  const recommendationData = recommendationsResponse.data;
  const trading = tradingResponse.data;
  const providerBudget = health.data.provider_budget;
  const coverage = data.latest_metrics;
  const firstRecommendation = recommendationData.recommendations[0];
  const rawRecommendationSummary = recommendationData.summary as typeof recommendationData.summary & Record<string, unknown>;
  const recommendationBoundary = {
    decision_review_ready_count: safeCount(
      rawRecommendationSummary.decision_review_ready_count,
      safeCount(rawRecommendationSummary.reviewable_count),
    ),
    paper_validation_pending_count: safeCount(rawRecommendationSummary.paper_validation_pending_count),
    decision_blocked_count: safeCount(
      rawRecommendationSummary.decision_blocked_count,
      safeCount(rawRecommendationSummary.blocked_count),
    ),
    order_blocked_count: safeCount(
      rawRecommendationSummary.order_blocked_count,
      safeCount(rawRecommendationSummary.blocked_count),
    ),
  };
  const ticketCount = safeCount(ticketData.ticket_count, ticketData.tickets.length);
  const tradingBlockedCount = safeCount(trading.gate_summary.blocked_count);
  const tradingWarningCount = safeCount(trading.gate_summary.warning_count);
  const brokerSubmittedCount = safeCount(trading.audit_summary.submitted_to_broker_count);
  const outcomeWaitMonitor =
    health.data.outcome_maturity_wait_monitor ?? fallbackOutcomeWaitMonitor(health.data.as_of_date || data.as_of_date);
  const recommendationOutcomeDate =
    outcomeWaitMonitor.recommendation_next_due_date || outcomeWaitMonitor.earliest_action_date || "미정";
  const portfolioFeedbackDate =
    outcomeWaitMonitor.portfolio_feedback_maturity_date || outcomeWaitMonitor.earliest_action_date || "미정";
  const weightReviewLabel = outcomeWaitMonitor.manual_weight_review_allowed
    ? "성과 표본 충족 시 산식 점검"
    : "추천 산식 검토 차단";
  const orderBoundaryLabel = outcomeWaitMonitor.broker_submit_allowed ? "증권사 주문 전송 가능" : "주문 제출 차단";
  const firstRecommendationHref = firstRecommendation
    ? (`/recommendations/${firstRecommendation.recommendation_id}` as Route)
    : ("/recommendations" as Route);
  const failedJobCount = data.attention_summary.failed_pipeline_count;
  const openTicketCount = data.attention_summary.open_ticket_count;
  const budgetLabel = `${providerBudget.remaining_request_count}/${providerBudget.daily_budget}`;
  const budgetDateLabel =
    providerBudget.status === "stale" ? `${providerBudget.budget_date} 기준` : `${providerBudget.budget_date} 오늘 기준`;
  const primaryFocus =
    failedJobCount > 0
      ? {
          title: "수집 문제를 먼저 해결한다.",
          body: `${failedJobCount}개 작업이 실패했거나 오래됐다. 추천·보유 판단보다 수집 상태 복구가 먼저다.`,
          href: "/data-health" as Route,
          cta: "수집 상태 열기",
        }
      : openTicketCount > 0
        ? {
            title: "보완 큐부터 확인한다.",
            body: `${openTicketCount}개 검토 항목이 열려 있다. 투자 논리 공백, 보유 충돌, 성과 미측정 항목을 먼저 처리한다.`,
            href: "/remediation" as Route,
            cta: "할 일 열기",
          }
        : tradingBlockedCount > 0
          ? {
              title: "거래 안전 조건을 확인한다.",
              body: `수집과 추천은 읽을 수 있지만 거래 안전 조건 ${tradingBlockedCount}개가 닫혀 있다.`,
              href: "/trading-readiness" as Route,
              cta: "거래 안전 열기",
            }
          : {
              title: "뉴스와 추천 변화를 점검한다.",
              body: "수집과 검토 큐가 안정 상태다. 오늘 새 뉴스가 어떤 종목과 추천에 연결됐는지 확인한다.",
              href: "/intelligence" as Route,
              cta: "뉴스 AI 열기",
            };
  const groupedTopActions = groupTopActions(data.top_actions);
  const repeatedActionCount = data.top_actions.length - groupedTopActions.length;
  const firstActionGroup = groupedTopActions[0] ?? null;

  const operatingSteps = [
    {
      index: "01",
      title: "수집이 정상인가",
      status: koCode(health.data.overall_status),
      detail: `${health.data.pipeline_runs.length}개 작업 중 실패 ${failedJobCount}개. 데이터가 불안정하면 여기서 멈춘다.`,
      href: "/data-health",
      cta: "수집 상태",
    },
    {
      index: "02",
      title: "시장 배경이 우호적인가",
      status: "지수·금리·달러",
      detail: "지수, 금리, 달러, 원자재, 변동성 압력을 시장 지도에서 먼저 본다.",
      href: "/market-map",
      cta: "시장 지도",
    },
    {
      index: "03",
      title: "뉴스 AI가 무엇을 말하나",
      status: `${eventData.summary.event_count}개 뉴스`,
      detail: `AI 후보 ${eventData.summary.ai_extracted_count}개, 뉴스 묶음 ${clusterData.summary.cluster_count}개`,
      href: "/intelligence",
      cta: "뉴스 AI",
    },
    {
      index: "04",
      title: "상위 흐름이 어디로 내려가나",
      status: `${eventData.summary.themes_represented}개 테마`,
      detail: "거시, 도메인, 테마, 종목 노출도를 흐름 지도에서 먼저 본다.",
      href: "/cycle-map",
      cta: "흐름 지도",
    },
    {
      index: "05",
      title: "추천 근거가 충분한가",
      status: `${recommendationBoundary.decision_review_ready_count}개 판단 후보`,
      detail: `가상 매매 검증 대기 ${recommendationBoundary.paper_validation_pending_count}개, 차단 ${recommendationBoundary.decision_blocked_count}개, 열린 검토 ${ticketCount}개`,
      href: "/recommendations",
      cta: "추천 근거",
    },
    {
      index: "06",
      title: "거래해도 안전한가",
      status: koCode(trading.readiness_status),
      detail: `차단 ${tradingBlockedCount}개, 경고 ${tradingWarningCount}개`,
      href: "/trading-readiness",
      cta: "거래 안전",
      tone: readinessTone(trading.readiness_status),
    },
  ];
  const decisionSteps = operatingSteps.map((step) => ({
    index: step.index,
    title: step.title,
    question: step.cta,
    status: step.status,
    body: step.detail,
    href: step.href as Route,
    cta: `${step.cta} 화면 열기`,
    tone:
      step.tone === "risk-high"
        ? "block" as const
        : step.tone === "risk-medium"
          ? "watch" as const
          : "ok" as const,
  }));

  const navigationGroups = [
    {
      label: "수집/분석 상태",
      title: "데이터가 믿을 만한가",
      copy: "캔들, 뉴스, AI 분석, 추천 갱신이 최근에 성공했는지 먼저 본다.",
      primaryHref: "/data-health",
      primaryCta: "수집 상태",
      links: [
        { href: "/market-map", label: "시장 지도" },
        { href: "/events", label: "수집 뉴스" },
        { href: "/events/classification", label: "1차 분류" },
        { href: "/ai-evidence/blocked", label: "차단 후보" },
      ],
    },
    {
      label: "뉴스/종목 관계",
      title: "뉴스가 어디에 영향을 주나",
      copy: "개별 뉴스, 뉴스 묶음, 종목 상세에서 직접 종목과 상위 흐름 전파를 확인한다.",
      primaryHref: "/intelligence",
      primaryCta: "뉴스 AI",
      links: [
        { href: "/ai-evidence", label: "AI 후보" },
        { href: "/ai-evidence/results", label: "구조화 결과" },
        { href: "/cycle-map", label: "흐름 지도" },
        { href: "/stocks", label: "종목" },
      ],
    },
    {
      label: "판단/거래 안전",
      title: "추천을 실행해도 되는가",
      copy: "추천 신호, 보유 투자 논리, 가상 검증, 거래 안전 조건을 분리해서 본다.",
      primaryHref: "/recommendations",
      primaryCta: "추천",
      links: [
        {
          href: firstRecommendation?.linked_thesis_id
            ? (`/theses/${firstRecommendation.linked_thesis_id}` as Route)
            : ("/portfolio/coverage" as Route),
          label: "보유 논리",
        },
        { href: "/paper-trading", label: "가상 거래" },
        { href: "/trading-readiness", label: "거래 안전" },
        { href: "/performance", label: "성과" },
      ],
    },
  ];

  return (
    <div className="terminal-home decision-page">
      <section className="decision-brief reveal" aria-labelledby="dashboard-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">오늘의 판단 지도 · {data.as_of_date}</span>
          <h1 className="decision-brief-title" id="dashboard-title">
            지금 할 일은 {primaryFocus.title}
          </h1>
          <p className="decision-brief-copy">
            {primaryFocus.body} 첫 화면에서는 수집 상태, 뉴스·AI 근거, 추천·보유 변화, 거래 안전 경계만 본다.
          </p>
          <div className="decision-brief-meta" aria-label="홈 핵심 상태">
            <span>실패 작업 {failedJobCount.toLocaleString("ko-KR")}개</span>
            <span>열린 검토 {openTicketCount.toLocaleString("ko-KR")}개</span>
            <span>호출 예산 {budgetLabel}</span>
            <span>{orderBoundaryLabel}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <Link className={failedJobCount > 0 ? "decision-card is-block" : "decision-card is-good"} href="/data-health">
            <span>수집 상태</span>
            <strong>{koCode(health.data.overall_status)}</strong>
            <small>자동화 {automationDisplayLabel(health.data.scheduler, data.run_status.scheduler)} · 예산 {budgetDateLabel}</small>
            <b>수집 확인</b>
          </Link>
          <Link className="decision-card is-good" href={"/intelligence" as Route}>
            <span>뉴스·AI</span>
            <strong>{eventData.summary.event_count.toLocaleString("ko-KR")}개 뉴스</strong>
            <small>AI 후보 {eventData.summary.ai_extracted_count.toLocaleString("ko-KR")}개 · 묶음 {clusterData.summary.cluster_count.toLocaleString("ko-KR")}개</small>
            <b>뉴스 근거</b>
          </Link>
          <Link className="decision-card is-watch" href={"/recommendations" as Route}>
            <span>추천·보유</span>
            <strong>{recommendationBoundary.decision_review_ready_count.toLocaleString("ko-KR")}개 후보</strong>
            <small>가상 매매 검증 대기 {recommendationBoundary.paper_validation_pending_count.toLocaleString("ko-KR")}개 · 열린 검토 {ticketCount.toLocaleString("ko-KR")}개</small>
            <b>추천 보기</b>
          </Link>
          <Link className={tradingBlockedCount > 0 ? "decision-card is-block" : "decision-card is-good"} href={"/trading-readiness" as Route}>
            <span>거래 안전</span>
            <strong>{koCode(trading.readiness_status)}</strong>
            <small>차단 {tradingBlockedCount.toLocaleString("ko-KR")}개 · 실제 주문 제출 {brokerSubmittedCount.toLocaleString("ko-KR")}건</small>
            <b>안전 경계</b>
          </Link>
        </div>
      </section>

      <DecisionReviewStrip
        activeIndex="01"
        description="이 순서가 현재 서비스의 기본 동선이다. 수집이 흔들리면 뒤 판단을 멈추고, 뉴스 근거와 흐름이 확인된 뒤 추천·가상 매매 검증으로 넘어간다."
        steps={decisionSteps}
      />

      <section
        className="feature-map-panel reveal delay-1"
        aria-labelledby="outcome-wait-title"
      >
        <div className="section-heading stacked-heading">
          <span>지금 결론</span>
          <h2 id="outcome-wait-title">{outcomeWaitMonitor.title}</h2>
        </div>
        <p className="manifest-lede compact-copy">
          {outcomeWaitMonitor.summary} 추천 산식은 성과 표본이 성숙하기 전까지 바꾸지 않는다.
          지금 할 일은 새 주문이 아니라 수집·뉴스 근거·가상 매매 결과가 다음 측정일까지 정상 누적되는지 확인하는 것이다.
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>추천 성과 측정</span>
            <strong>{recommendationOutcomeDate}</strong>
            <small>다음 측정 대상 {outcomeWaitMonitor.recommendation_next_due_count}개</small>
          </article>
          <article className="rail-cell">
            <span>포트폴리오 사후 평가</span>
            <strong>{portfolioFeedbackDate}</strong>
            <small>성숙 표본 부족 {outcomeWaitMonitor.portfolio_mature_decision_gap}개</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>추천 산식 검토</span>
            <strong>{weightReviewLabel}</strong>
            <small>{koReason(outcomeWaitMonitor.weight_review_block_reason)}</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>거래 경계</span>
            <strong>{orderBoundaryLabel}</strong>
            <small>{koCode(outcomeWaitMonitor.order_boundary)}</small>
          </article>
        </div>
        <div className="btn-row compact-btn-row">
          <Link className="btn btn-primary" href={"/data-health#outcome-maturity-wait-monitor" as Route}>
            대기 근거 자세히 보기
          </Link>
          <Link className="btn btn-secondary" href={"/recommendations" as Route}>
            추천 목록 보기
          </Link>
          <Link className="btn btn-secondary" href={"/portfolio/coverage" as Route}>
            포트폴리오 검토 보기
          </Link>
        </div>
      </section>

      <section className="status-rail reveal delay-1" aria-label="오늘의 핵심 숫자">
        <article className="rail-cell rail-critical">
          <span>운영 검토 항목</span>
          <strong>{data.attention_summary.open_ticket_count}</strong>
          <small>열린 검토 티켓</small>
        </article>
        <article className="rail-cell">
          <span>뉴스와 공시 이벤트</span>
          <strong>{eventData.summary.event_count}</strong>
          <small>AI 후보 {eventData.summary.ai_extracted_count}개</small>
        </article>
        <article className="rail-cell">
          <span>추천 판단 후보</span>
          <strong>{recommendationBoundary.decision_review_ready_count}</strong>
          <small>가상 매매 검증 대기 {recommendationBoundary.paper_validation_pending_count}개</small>
        </article>
        <article className="rail-cell rail-critical">
          <span>추천 사용 차단</span>
          <strong>{recommendationBoundary.decision_blocked_count}</strong>
          <small>주문 차단 {recommendationBoundary.order_blocked_count}개</small>
        </article>
        <article className="rail-cell">
          <span>거래 안전 차단</span>
          <strong>{tradingBlockedCount}</strong>
          <small>{koCode(trading.execution_mode)} 모드</small>
        </article>
      </section>

      <section className="where-grid reveal delay-2" aria-label="상세 화면 입구">
        {navigationGroups.map((group) => (
          <article className="where-card cockpit-route-card" key={group.label}>
            <span>{group.label}</span>
            <strong>{group.title}</strong>
            <p>{group.copy}</p>
            <div className="btn-row compact-btn-row">
              <Link className="btn btn-primary" href={group.primaryHref as Route}>
                {group.primaryCta}
              </Link>
              {group.links.map((link) => (
                <Link className="btn btn-secondary" href={link.href as Route} key={`${group.label}-${link.label}`}>
                  {link.label}
                </Link>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className="feature-map-panel reveal delay-2" aria-labelledby="feature-map-title">
        <div className="section-heading stacked-heading">
          <span>판단 기준</span>
          <h2 id="feature-map-title">첫 화면에서는 이 세 가지만 통과하면 된다</h2>
        </div>
        <div className="decision-brief-grid">
          <article className="decision-brief-card">
            <span>데이터</span>
            <strong>{koCode(health.data.overall_status)}</strong>
            <p>
              실패 작업 {failedJobCount}개. 데이터가 불안정하면 추천보다 수집 상태를 먼저 본다.
            </p>
          </article>
          <article className="decision-brief-card">
            <span>뉴스 근거</span>
            <strong>{eventData.summary.ai_extracted_count}개 AI 후보</strong>
            <p>
              뉴스 묶음 {clusterData.summary.cluster_count}개. 근거가 약하면 AI 상세와 원천 문서를 먼저 확인한다.
            </p>
          </article>
          <article className="decision-brief-card">
            <span>거래 안전</span>
            <strong>{koCode(trading.readiness_status)}</strong>
            <p>
              차단 조건 {tradingBlockedCount}개. 실제 주문 전송 {brokerSubmittedCount}건.
            </p>
          </article>
          <article className="decision-brief-card">
            <span>추천 사용 경계</span>
            <strong>{recommendationBoundary.decision_review_ready_count}개 판단 후보</strong>
            <p>
              가상 매매 검증 대기 {recommendationBoundary.paper_validation_pending_count}개, 근거·투자 논리 차단{" "}
              {recommendationBoundary.decision_blocked_count}개. 모든 추천은 주문 차단 상태다.
            </p>
          </article>
        </div>
      </section>

      <section className="operator-workbench reveal delay-2">
        <article className="ledger-panel queue-panel" aria-labelledby="priority-actions-title">
          <div className="section-heading">
            <span>우선순위</span>
            <h2 id="priority-actions-title">반복되는 보완 항목을 묶어서 본다</h2>
          </div>
          <p className="compact-copy">
            같은 사유가 여러 번 반복되면 표를 길게 읽지 말고 묶음 단위로 처리한다.
            {repeatedActionCount > 0
              ? ` 현재 ${data.top_actions.length}개 보완 기록은 ${groupedTopActions.length}개 묶음으로 압축됐다.`
              : " 현재 중복 보완 기록은 없다."}
          </p>
          <div className="bento-list">
            {groupedTopActions.length > 0 ? (
              groupedTopActions.map((group) => (
                <article className="bento-list-item" key={group.key}>
                  <div>
                    <span>
                      우선순위 {String(group.firstRank).padStart(2, "0")} · {group.count}건 반복 · {symbolGroupLabel(group.symbols)}
                    </span>
                    <strong>{koCode(group.action)}</strong>
                    <p className="flow-rationale">{shortReviewReason(group.reason)}</p>
                  </div>
                  <div style={{ flex: "0 1 260px" }}>
                    <span className={`risk-tag ${riskClass(group.riskLevel)}`}>{koCode(group.riskLevel)}</span>
                    <span>제안 실행: {koCode(group.suggestedRunner)}</span>
                    <Link href="/remediation">보완 큐에서 처리</Link>
                  </div>
                </article>
              ))
            ) : (
              <p className="empty-state">오늘 표시할 보완 조치가 없다.</p>
            )}
          </div>
        </article>

        <aside className="operator-side-stack">
          <article className="ledger-panel decision-panel">
            <div className="section-heading">
              <span>첫 보완 묶음</span>
              <h2>{firstActionGroup ? `${symbolGroupLabel(firstActionGroup.symbols)}: ${koCode(firstActionGroup.action)}` : "보완 티켓 없음"}</h2>
            </div>
            {firstActionGroup ? (
              <>
                <p className="decision-copy">
                  {shortReviewReason(firstActionGroup.reason)} 같은 항목이 {firstActionGroup.count}건 반복된다.
                  먼저 이 묶음의 기준을 정리한 뒤 개별 보유 검토로 내려간다.
                </p>
                <dl className="fact-list">
                  <div>
                    <dt>제안 실행</dt>
                    <dd>{koCode(firstActionGroup.suggestedRunner)}</dd>
                  </div>
                  <div>
                    <dt>대상</dt>
                    <dd>{symbolGroupLabel(firstActionGroup.symbols)}</dd>
                  </div>
                  <div>
                    <dt>위험도</dt>
                    <dd>
                      <span className={`risk-tag ${riskClass(firstActionGroup.riskLevel)}`}>
                        {koCode(firstActionGroup.riskLevel)}
                      </span>
                    </dd>
                  </div>
                </dl>
                <div className="mini-link-stack">
                  <Link href="/remediation">보완 큐 열기</Link>
                  <Link href="/portfolio/coverage">보유 검토 보기</Link>
                </div>
              </>
            ) : (
              <p className="decision-copy">현재 열린 보완 큐가 비어 있다.</p>
            )}
          </article>

          <article className="ledger-panel runtime-panel">
            <div className="section-heading">
              <span>뉴스가 추천에 붙은 증거</span>
              <h2>AI 근거가 실제 판단 입력으로 연결됐는가</h2>
            </div>
            <dl className="runtime-grid">
              <div>
                <dt>뉴스 묶음</dt>
                <dd>{clusterData.summary.cluster_count}개</dd>
              </div>
              <div>
                <dt>개별 AI 후보</dt>
                <dd>{eventData.summary.ai_extracted_count}개</dd>
              </div>
              <div>
                <dt>대표 추천</dt>
                <dd>{firstRecommendation ? firstRecommendation.symbol : "대기"}</dd>
              </div>
              <div>
                <dt>커버리지</dt>
                <dd>{formatPercent(coverage.weight_coverage_ratio)}</dd>
              </div>
            </dl>
            <div className="mini-link-stack">
              <Link href="/intelligence">뉴스 묶음 근거</Link>
              <Link href={firstRecommendationHref}>대표 추천 열기</Link>
            </div>
          </article>
        </aside>
      </section>

    </div>
  );
}
