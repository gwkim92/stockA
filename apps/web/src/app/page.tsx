import Link from "next/link";
import type { Route } from "next";
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
    : "추천 산식 변경 잠금";
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
          title: "데이터 신뢰도가 먼저다",
          body: `${failedJobCount}개 수집·분석 작업이 정상 상태가 아니다. 추천·보유 판단보다 데이터 복구가 우선이다.`,
          href: "/data-health" as Route,
          cta: "수집 상태 열기",
        }
      : openTicketCount > 0
        ? {
            title: "판단 공백이 먼저다",
            body: `${openTicketCount}개 보완 항목이 남아 있다. 투자 논리 공백, 보유 충돌, 성과 미측정 항목이 추천 판단을 막고 있다.`,
            href: "/remediation" as Route,
            cta: "할 일 열기",
          }
        : tradingBlockedCount > 0
          ? {
              title: "거래 안전 조건이 닫혀 있다",
              body: `수집과 추천은 읽을 수 있지만 거래 안전 조건 ${tradingBlockedCount}개가 닫혀 있다.`,
              href: "/trading-readiness" as Route,
              cta: "거래 안전 열기",
            }
          : {
              title: "새 근거와 추천 변화가 초점이다",
              body: "수집과 보완 큐가 안정 상태다. 오늘 새 근거가 어떤 종목과 추천 판단을 바꾸는지 본다.",
              href: "/intelligence" as Route,
              cta: "뉴스 근거 열기",
            };
  const groupedTopActions = groupTopActions(data.top_actions);
  const repeatedActionCount = data.top_actions.length - groupedTopActions.length;
  const visibleTopActionGroups = groupedTopActions.slice(0, 5);
  const hiddenTopActionGroupCount = Math.max(groupedTopActions.length - visibleTopActionGroups.length, 0);
  const firstActionGroup = groupedTopActions[0] ?? null;

  const operatingSteps = [
    {
      index: "01",
      title: "데이터를 믿어도 되는가",
      status: koCode(health.data.overall_status),
      detail: `${health.data.pipeline_runs.length}개 수집·분석 작업 중 주의 ${failedJobCount}개. 데이터가 불안정하면 투자 판단을 보류한다.`,
      href: "/data-health",
      cta: "수집 상태",
    },
    {
      index: "02",
      title: "시장 배경이 우호적인가",
      status: "지수·금리·달러",
      detail: "지수, 금리, 달러, 원자재, 변동성 압력이 현재 포지션에 우호적인지 본다.",
      href: "/market-map",
      cta: "시장 지도",
    },
    {
      index: "03",
      title: "새 근거가 무엇을 바꾸나",
      status: `${eventData.summary.event_count}개 뉴스`,
      detail: `근거 후보 ${eventData.summary.ai_extracted_count}개, 주요 뉴스 흐름 ${clusterData.summary.cluster_count}개`,
      href: "/intelligence",
      cta: "뉴스 근거",
    },
    {
      index: "04",
      title: "사이클 배경이 맞나",
      status: `${eventData.summary.themes_represented}개 테마`,
      detail: "거시·섹터·테마 흐름이 종목 판단과 같은 방향인지 본다.",
      href: "/cycle-map",
      cta: "사이클 지도",
    },
    {
      index: "05",
      title: "추천 근거가 충분한가",
      status: `${recommendationBoundary.decision_review_ready_count}개 판단 후보`,
      detail: `가상 매매 확인 대기 ${recommendationBoundary.paper_validation_pending_count}개, 차단 ${recommendationBoundary.decision_blocked_count}개, 보완 항목 ${ticketCount}개`,
      href: "/recommendations",
      cta: "추천 근거",
    },
    {
      index: "06",
      title: "실행 가능 상태인가",
      status: trading.readiness_status === "blocked" ? "거래 차단" : koCode(trading.readiness_status),
      detail: `안전 조건 ${tradingBlockedCount}개 미충족, 경고 ${tradingWarningCount}개`,
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

  return (
    <div className="terminal-home analyst-home decision-page">
      <section className="analyst-hero reveal" aria-labelledby="dashboard-title">
        <div className="analyst-hero-copy">
          <span className="decision-brief-kicker">리서치 데스크 · {data.as_of_date}</span>
          <h1 className="analyst-title" id="dashboard-title">
            {primaryFocus.title}
          </h1>
          <p className="analyst-lede">
            {primaryFocus.body} 이 화면은 내부 처리 방식이 아니라 오늘의 결론, 결론을 흔드는 근거,
            보류해야 할 위험, 바로 열어야 할 화면만 남긴다.
          </p>
          <div className="analyst-action-row">
            <Link className="btn btn-primary" href={primaryFocus.href}>
              {primaryFocus.cta}
            </Link>
            <Link className="btn btn-secondary" href="/market-map">
              시장 지도
            </Link>
            <Link className="btn btn-secondary" href="/ai-evidence">
              뉴스 근거
            </Link>
            <Link className="btn btn-secondary" href="/recommendations">
              추천 검토
            </Link>
          </div>
        </div>
        <aside className="analyst-command-panel" aria-label="오늘의 투자 운영 결론">
          <span>오늘 결론</span>
          <strong>{outcomeWaitMonitor.title}</strong>
          <p>
              추천 산식과 실거래는 성과 표본이 성숙할 때까지 잠겨 있다. 지금 할 일은 새 주문이 아니라 보완 항목과 근거 품질 확인이다.
          </p>
          <dl className="analyst-fact-grid">
            <div>
              <dt>데이터 상태</dt>
              <dd>{koCode(health.data.overall_status)}</dd>
            </div>
            <div>
              <dt>뉴스 근거</dt>
              <dd>{eventData.summary.ai_extracted_count.toLocaleString("ko-KR")}개 후보</dd>
            </div>
            <div>
              <dt>추천 성과 측정</dt>
              <dd>{recommendationOutcomeDate}</dd>
            </div>
            <div>
              <dt>거래 경계</dt>
              <dd>{orderBoundaryLabel}</dd>
            </div>
          </dl>
        </aside>
      </section>

      <section className="analyst-reading-flow reveal delay-1" aria-labelledby="reading-flow-title">
        <div className="analyst-section-heading">
          <span>투자 체크포인트</span>
          <h2 id="reading-flow-title">오늘 판단을 바꾸는 항목만 본다</h2>
          <p>
            각 카드는 투자 판단을 바꿀 수 있는 질문이다. 정상이어도 매수 신호가 아니며,
            막힌 항목이 있으면 추천과 실행은 보류한다.
          </p>
        </div>
        <div className="analyst-flow-grid">
          {decisionSteps.map((step) => (
            <Link className={`analyst-flow-card tone-${step.tone ?? "ok"}`} href={step.href} key={step.index}>
              <span>{step.index}</span>
              <strong>{step.title}</strong>
              <em>{step.status}</em>
              <p>{step.body}</p>
              <small>{step.cta}</small>
            </Link>
          ))}
        </div>
      </section>

      <section className="analyst-packet-grid reveal delay-2" aria-label="핵심 분석 패킷">
        <Link className="analyst-packet-card packet-market" href="/market-map">
          <span>01 · 시장 배경</span>
          <strong>지수·금리·달러·원자재가 추천을 밀어주는가</strong>
          <p>위험 선호, 금리 부담, 달러 유동성, 원자재 충격이 보유·추천에 유리한 배경인지 본다.</p>
          <small>호출 예산 {budgetLabel} · {budgetDateLabel}</small>
        </Link>
        <Link className="analyst-packet-card packet-news" href="/intelligence">
          <span>02 · 뉴스 근거</span>
          <strong>{eventData.summary.event_count.toLocaleString("ko-KR")}개 뉴스 중 투자 판단에 영향을 줄 근거를 본다</strong>
          <p>원문, 한국어 요약, 종목·테마 영향, 차단 사유를 대조해 추천 근거로 쓸 수 있는지만 남긴다.</p>
          <small>근거 후보 {eventData.summary.ai_extracted_count.toLocaleString("ko-KR")}개 · 주요 흐름 {clusterData.summary.cluster_count.toLocaleString("ko-KR")}개</small>
        </Link>
        <Link className="analyst-packet-card packet-cycle" href="/cycle-map">
          <span>03 · 사이클 지도</span>
          <strong>거시·섹터·테마 흐름이 종목 판단과 맞는가</strong>
          <p>상위 흐름과 종목 노출도를 비교해 단일 뉴스가 아니라 지속되는 배경인지 판별한다.</p>
          <small>테마 {eventData.summary.themes_represented.toLocaleString("ko-KR")}개</small>
        </Link>
        <Link className="analyst-packet-card packet-recommendation" href="/recommendations">
          <span>04 · 추천·보유</span>
          <strong>추천 후보보다 먼저 근거 커버리지와 차단 사유를 본다</strong>
          <p>추천 점수, 투자 논리, 전문 분석 근거, 페이퍼 검증 상태를 분리해 과잉 확신을 막는다.</p>
          <small>검증 대기 {recommendationBoundary.paper_validation_pending_count.toLocaleString("ko-KR")}개 · 열린 검토 {ticketCount.toLocaleString("ko-KR")}개</small>
        </Link>
        <Link className="analyst-packet-card packet-safety" href="/trading-readiness">
          <span>05 · 거래 안전</span>
          <strong>{koCode(trading.readiness_status)} 상태에서 주문은 계속 통제한다</strong>
          <p>증권사 연결 경계, 긴급 중지, 주문 한도, 계좌 권한, 감사 기록을 분리해 실거래 오작동을 막는다.</p>
          <small>차단 {tradingBlockedCount.toLocaleString("ko-KR")}개 · 실제 주문 제출 {brokerSubmittedCount.toLocaleString("ko-KR")}건</small>
        </Link>
      </section>

      <section className="analyst-workbench reveal delay-2">
        <article className="ledger-panel queue-panel analyst-queue-panel" aria-labelledby="priority-actions-title">
          <div className="section-heading">
            <span>보완 큐</span>
            <h2 id="priority-actions-title">오늘 처리할 리서치 공백</h2>
          </div>
          <p className="compact-copy">
            추천을 읽기 전에 남은 공백부터 줄인다. 같은 사유가 반복되면 묶음 단위로 판단한다.
            {repeatedActionCount > 0
              ? ` 현재 ${data.top_actions.length}개 보완 기록은 ${groupedTopActions.length}개 묶음으로 압축됐다. 홈에는 먼저 볼 ${visibleTopActionGroups.length}개만 보여준다.`
              : " 현재 중복 보완 기록은 없다."}
          </p>
          <div className="bento-list">
            {visibleTopActionGroups.length > 0 ? (
              visibleTopActionGroups.map((group) => (
                <article className="bento-list-item" key={group.key}>
                  <div>
                    <span>
                      우선순위 {String(group.firstRank).padStart(2, "0")} · {group.count}건 반복 · {symbolGroupLabel(group.symbols)}
                    </span>
                    <strong>{koCode(group.action)}</strong>
                    <p className="flow-rationale">{shortReviewReason(group.reason)}</p>
                  </div>
                  <div className="bento-list-action">
                    <span className={`risk-tag ${riskClass(group.riskLevel)}`}>{koCode(group.riskLevel)}</span>
                    <span>제안 실행: {koCode(group.suggestedRunner)}</span>
                    <Link href="/remediation">보완 큐에서 처리</Link>
                  </div>
                </article>
              ))
            ) : (
              <p className="empty-state">오늘 표시할 보완 조치가 없다.</p>
            )}
            {hiddenTopActionGroupCount > 0 ? (
              <article className="bento-list-item bento-list-summary">
                <div>
                  <span>나머지 보완 묶음</span>
                  <strong>{hiddenTopActionGroupCount.toLocaleString("ko-KR")}개는 보완 큐 전체에서 확인</strong>
                  <p className="flow-rationale">
                    첫 화면은 가장 큰 보완 묶음만 남긴다. 전체 목록은 보완 큐에서 종목·사유별로 확인한다.
                  </p>
                </div>
                <div className="bento-list-action">
                  <Link href="/remediation">보완 큐 전체 보기</Link>
                </div>
              </article>
            ) : null}
          </div>
        </article>

        <aside className="operator-side-stack analyst-side-stack">
          <article className="ledger-panel decision-panel">
            <div className="section-heading">
              <span>첫 보완 묶음</span>
              <h2>{firstActionGroup ? `${symbolGroupLabel(firstActionGroup.symbols)}: ${koCode(firstActionGroup.action)}` : "보완 티켓 없음"}</h2>
            </div>
            {firstActionGroup ? (
              <>
                <p className="decision-copy">
                  {shortReviewReason(firstActionGroup.reason)} 같은 항목이 {firstActionGroup.count}건 반복된다.
                  이 묶음이 해소되기 전까지 관련 추천·보유 판단은 보류한다.
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
              <span>추천 근거</span>
              <h2>새 근거가 추천 판단을 바꾸는가</h2>
            </div>
            <dl className="runtime-grid">
              <div>
                <dt>뉴스 묶음</dt>
                <dd>{clusterData.summary.cluster_count}개</dd>
              </div>
              <div>
                <dt>개별 근거 후보</dt>
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
              <Link href="/intelligence">뉴스 근거 보기</Link>
              <Link href={firstRecommendationHref}>대표 추천 열기</Link>
            </div>
          </article>

          <article className="ledger-panel runtime-panel">
            <div className="section-heading">
              <span>성과 대기</span>
              <h2>{weightReviewLabel}</h2>
            </div>
            <p className="decision-copy">
              {outcomeWaitMonitor.summary} 추천 산식과 실거래는 성과 표본이 성숙할 때까지 계속 차단한다.
            </p>
            <dl className="runtime-grid">
              <div>
                <dt>추천 측정일</dt>
                <dd>{recommendationOutcomeDate}</dd>
              </div>
              <div>
                <dt>포트폴리오 평가</dt>
                <dd>{portfolioFeedbackDate}</dd>
              </div>
              <div>
                <dt>산식 검토</dt>
                <dd>{weightReviewLabel}</dd>
              </div>
              <div>
                <dt>주문 경계</dt>
                <dd>{koCode(outcomeWaitMonitor.order_boundary)}</dd>
              </div>
            </dl>
            <div className="mini-link-stack">
              <Link href={"/data-health#outcome-maturity-wait-monitor" as Route}>성과 대기 근거</Link>
              <Link href="/paper-trading">가상 매매 상태</Link>
            </div>
          </article>
        </aside>
      </section>

    </div>
  );
}
