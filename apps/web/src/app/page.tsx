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
import { koCode, koLabel, koReason } from "@/lib/korean-labels";
import type { DataHealthData } from "@/lib/types";

export const dynamic = "force-dynamic";

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
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
  const firstTicket = ticketData.tickets[0];
  const providerBudget = health.data.provider_budget;
  const coverage = data.latest_metrics;
  const firstRecommendation = recommendationData.recommendations[0];
  const firstRecommendationHref = firstRecommendation
    ? (`/recommendations/${firstRecommendation.recommendation_id}` as Route)
    : ("/recommendations" as Route);
  const failedJobCount = data.attention_summary.failed_pipeline_count;
  const openTicketCount = data.attention_summary.open_ticket_count;
  const criticalBlindSpotCount = data.attention_summary.critical_blind_spot_count;
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
        : trading.gate_summary.blocked_count > 0
          ? {
              title: "거래 안전 조건을 확인한다.",
              body: `수집과 추천은 읽을 수 있지만 거래 안전 조건 ${trading.gate_summary.blocked_count}개가 닫혀 있다.`,
              href: "/trading-readiness" as Route,
              cta: "거래 안전 열기",
            }
          : {
              title: "뉴스와 추천 변화를 점검한다.",
              body: "수집과 검토 큐가 안정 상태다. 오늘 새 뉴스가 어떤 종목과 추천에 연결됐는지 확인한다.",
              href: "/intelligence" as Route,
              cta: "뉴스 AI 열기",
            };

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
      title: "뉴스 AI가 무엇을 말하나",
      status: `${eventData.summary.event_count}개 뉴스`,
      detail: `AI 후보 ${eventData.summary.ai_extracted_count}개, 뉴스 묶음 ${clusterData.summary.cluster_count}개`,
      href: "/intelligence",
      cta: "뉴스 AI",
    },
    {
      index: "03",
      title: "상위 흐름이 어디로 내려가나",
      status: `${eventData.summary.themes_represented}개 테마`,
      detail: "거시, 도메인, 테마, 종목 노출도를 흐름 지도에서 먼저 본다.",
      href: "/cycle-map",
      cta: "흐름 지도",
    },
    {
      index: "04",
      title: "추천과 보유가 막혔나",
      status: `${recommendationData.summary.reviewable_count}개 검토`,
      detail: `보유 커버리지 ${formatPercent(coverage.weight_coverage_ratio)}, 열린 검토 ${ticketData.ticket_count}개`,
      href: "/recommendations",
      cta: "추천 보유",
    },
    {
      index: "05",
      title: "거래해도 안전한가",
      status: koCode(trading.readiness_status),
      detail: `차단 ${trading.gate_summary.blocked_count}개, 경고 ${trading.gate_summary.warning_count}개`,
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
    <div className="terminal-home">
      <section className="operator-hero reveal" aria-labelledby="dashboard-title">
        <div className="operator-hero-copy">
          <div className="bento-badge">오늘의 판단 지도</div>
          <h1 className="terminal-title operator-title" id="dashboard-title">
            <span>오늘 볼 것은</span>
            <span>수집, 근거,</span>
            <span className="title-muted">안전이다.</span>
          </h1>
          <p className="manifest-lede">
            이 첫 화면은 기능 목록이 아니라 판단 순서다. 수집이 정상인지 확인하고, 뉴스 AI가 어떤 종목과
            테마에 연결됐는지 본 뒤, 추천·보유·거래 안전 조건을 검토한다.
          </p>
          <div className="btn-row">
            <Link className="btn btn-primary" href="/data-health">
              01 수집 확인
            </Link>
            <Link className="btn btn-secondary" href={"/intelligence" as Route}>
              02 뉴스 근거
            </Link>
            <Link className="btn btn-secondary" href={"/recommendations" as Route}>
              03 추천 검토
            </Link>
          </div>
        </div>

        <aside className="operator-brief" aria-label="현재 운영 결론">
          <span>지금 할 일</span>
          <strong>{primaryFocus.title}</strong>
          <p>{primaryFocus.body}</p>
          <Link className="btn btn-primary operator-next-link" href={primaryFocus.href}>
            {primaryFocus.cta}
          </Link>
          <p>
            실패 작업 {failedJobCount}개, 열린 검토 {openTicketCount}개, 중요 사각지대 {criticalBlindSpotCount}개.
          </p>
          <dl>
            <div>
              <dt>데이터 제공자</dt>
              <dd>{koCode(providerBudget.provider)}</dd>
            </div>
            <div>
              <dt>호출 예산</dt>
              <dd>{budgetLabel} · {budgetDateLabel}</dd>
            </div>
            <div>
              <dt>자동화</dt>
              <dd>{automationDisplayLabel(health.data.scheduler, data.run_status.scheduler)}</dd>
            </div>
          </dl>
        </aside>
      </section>

      <DecisionReviewStrip
        activeIndex="01"
        description="이 순서가 현재 서비스의 기본 동선이다. 수집이 흔들리면 뒤 판단을 멈추고, 뉴스 근거와 흐름이 확인된 뒤 추천·페이퍼 검증으로 넘어간다."
        steps={decisionSteps}
      />

      <section className="status-rail reveal delay-1" aria-label="오늘의 핵심 숫자">
        <article className="rail-cell rail-critical">
          <span>사람이 확인할 항목</span>
          <strong>{data.attention_summary.open_ticket_count}</strong>
          <small>열린 검토 티켓</small>
        </article>
        <article className="rail-cell">
          <span>뉴스와 공시 이벤트</span>
          <strong>{eventData.summary.event_count}</strong>
          <small>AI 후보 {eventData.summary.ai_extracted_count}개</small>
        </article>
        <article className="rail-cell">
          <span>추천 검토 가능</span>
          <strong>{recommendationData.summary.reviewable_count}</strong>
          <small>뉴스·AI 근거 {recommendationData.summary.ai_or_event_evidence_count}개</small>
        </article>
        <article className="rail-cell">
          <span>거래 안전 차단</span>
          <strong>{trading.gate_summary.blocked_count}</strong>
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
              차단 조건 {trading.gate_summary.blocked_count}개. 실제 주문 전송 {trading.audit_summary.submitted_to_broker_count}건.
            </p>
          </article>
        </div>
      </section>

      <section className="operator-workbench reveal delay-2">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
            <span>우선순위</span>
            <h2>지금 사람이 처리해야 할 것</h2>
          </div>
          <div className="ledger-table-wrap">
            <table className="ledger-table">
              <thead>
                <tr>
                  <th scope="col">순위</th>
                  <th scope="col">심볼</th>
                  <th scope="col">위험</th>
                  <th scope="col">조치</th>
                  <th scope="col">사유</th>
                </tr>
              </thead>
              <tbody>
                {data.top_actions.length > 0 ? (
                  data.top_actions.map((action) => (
                    <tr key={`${action.rank}-${action.symbol}`}>
                      <td>{String(action.rank).padStart(2, "0")}</td>
                      <td>
                        <strong>{action.symbol}</strong>
                      </td>
                      <td>
                        <span className={`risk-tag ${riskClass(action.risk_level)}`}>
                          {koCode(action.risk_level)}
                        </span>
                      </td>
                      <td>{koCode(action.action)}</td>
                      <td>{shortReviewReason(action.reason)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5}>오늘 표시할 보완 조치가 없다.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </article>

        <aside className="operator-side-stack">
          <article className="ledger-panel decision-panel">
            <div className="section-heading">
              <span>첫 검토</span>
              <h2>{firstTicket ? `${firstTicket.symbol}: ${koCode(firstTicket.action)}` : "보완 티켓 없음"}</h2>
            </div>
            {firstTicket ? (
              <>
                <p className="decision-copy">{koLabel(firstTicket.required_human_decision)}</p>
                <dl className="fact-list">
                  <div>
                    <dt>제안 실행</dt>
                    <dd>{koCode(firstTicket.suggested_runner)}</dd>
                  </div>
                  <div>
                    <dt>사유</dt>
                    <dd>{shortReviewReason(firstTicket.reason)}</dd>
                  </div>
                  <div>
                    <dt>위험도</dt>
                    <dd>
                      <span className={`risk-tag ${riskClass(firstTicket.risk_level)}`}>
                        {koCode(firstTicket.risk_level)}
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
