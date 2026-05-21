import Link from "next/link";
import type { Route } from "next";
import {
  getAiNewsClusters,
  getCockpitSnapshot,
  getEvents,
  getRecommendations,
  getTradingReadiness,
} from "@/lib/frontend-api";
import { koCode, koLabel, koReason } from "@/lib/korean-labels";

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

  const operatingSteps = [
    {
      index: "01",
      title: "수집이 정상인가",
      status: koCode(health.data.overall_status),
      detail: `${health.data.pipeline_runs.length}개 파이프라인, 실패 ${data.attention_summary.failed_pipeline_count}개`,
      href: "/data-health",
      cta: "수집 상태",
    },
    {
      index: "02",
      title: "뉴스와 AI가 무엇을 말하나",
      status: `${eventData.summary.event_count}개 이벤트`,
      detail: `AI 후보 ${eventData.summary.ai_extracted_count}개, 뉴스 묶음 ${clusterData.summary.cluster_count}개`,
      href: "/intelligence",
      cta: "뉴스 AI",
    },
    {
      index: "03",
      title: "어떤 종목이 영향 받았나",
      status: `${eventData.summary.themes_represented}개 테마`,
      detail: "종목 상세에서 가격, 뉴스 근거, 추천 연결을 같이 본다.",
      href: "/stocks",
      cta: "종목",
    },
    {
      index: "04",
      title: "추천과 보유가 막혔나",
      status: `${recommendationData.summary.reviewable_count}개 검토`,
      detail: `보유 커버리지 ${formatPercent(coverage.weight_coverage_ratio)}, 열린 티켓 ${ticketData.ticket_count}개`,
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

  const secondaryScreens = [
    {
      title: "뉴스 원장",
      copy: "개별 뉴스와 공시가 어떤 종목, 테마, AI 근거에 연결됐는지 본다.",
      href: "/events",
    },
    {
      title: "AI 후보 목록",
      copy: "Codex OAuth가 구조화한 개별 뉴스 후보와 신뢰도, 원천 문서를 확인한다.",
      href: "/ai-evidence",
    },
    {
      title: "사이클 보드",
      copy: "테마의 현재 국면과 이전 국면, 점수 구성요소를 비교한다.",
      href: "/cycles",
    },
    {
      title: "성과 분석",
      copy: "추천 이후 실제 성과와 벤치마크 대비 차이를 추적한다.",
      href: "/performance",
    },
  ];

  return (
    <div className="terminal-home">
      <section className="operator-hero reveal" aria-labelledby="dashboard-title">
        <div className="operator-hero-copy">
          <div className="bento-badge">오늘의 운용 순서</div>
          <h1 className="terminal-title operator-title" id="dashboard-title">
            <span>오늘은</span>
            <span>이 순서대로</span>
            <span className="title-muted">판단한다.</span>
          </h1>
          <p className="manifest-lede">
            이 프로젝트는 뉴스를 자동 수집하고, AI가 중요한 뉴스 후보를 구조화한 뒤, 종목과 테마에 연결해
            중장기 추천과 보유 검토의 근거로 남기는 투자 운영 시스템이다. 첫 화면에서는 결론보다
            “무엇을 먼저 확인해야 하는지”를 고정한다.
          </p>
          <div className="btn-row">
            <Link className="btn btn-primary" href="/data-health">
              01 수집 정상 여부
            </Link>
            <Link className="btn btn-secondary" href={"/intelligence" as Route}>
              02 뉴스 AI 해석
            </Link>
            <Link className="btn btn-secondary" href={"/recommendations" as Route}>
              03 추천 보유 검토
            </Link>
          </div>
        </div>

        <aside className="operator-brief" aria-label="현재 운영 결론">
          <span>지금 봐야 할 결론</span>
          <strong>
            {data.attention_summary.failed_pipeline_count > 0
              ? "먼저 수집 실패를 해결해야 한다."
              : data.attention_summary.open_ticket_count > 0
                ? "보완 큐부터 확인해야 한다."
                : "수집과 검토 큐가 안정 상태다."}
          </strong>
          <p>
            실패 파이프라인 {data.attention_summary.failed_pipeline_count}개, 열린 검토 티켓{" "}
            {data.attention_summary.open_ticket_count}개, 중요 사각지대{" "}
            {data.attention_summary.critical_blind_spot_count}개.
          </p>
          <dl>
            <div>
              <dt>데이터 제공자</dt>
              <dd>{koCode(providerBudget.provider)}</dd>
            </div>
            <div>
              <dt>호출 예산</dt>
              <dd>
                {providerBudget.remaining_request_count}/{providerBudget.daily_budget}
              </dd>
            </div>
            <div>
              <dt>자동화</dt>
              <dd>{koCode(data.run_status.scheduler)}</dd>
            </div>
          </dl>
        </aside>
      </section>

      <section className="operator-steps reveal delay-1" aria-label="오늘의 점검 순서">
        {operatingSteps.map((step) => (
          <Link className="operator-step-card" href={step.href as Route} key={step.index}>
            <span>{step.index}</span>
            <h2>{step.title}</h2>
            <strong className={step.tone ? `risk-tag ${step.tone}` : undefined}>{step.status}</strong>
            <p>{step.detail}</p>
            <small>{step.cta} 화면 열기</small>
          </Link>
        ))}
      </section>

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
          <small>AI/이벤트 근거 {recommendationData.summary.ai_or_event_evidence_count}개</small>
        </article>
        <article className="rail-cell">
          <span>거래 안전 차단</span>
          <strong>{trading.gate_summary.blocked_count}</strong>
          <small>{koCode(trading.execution_mode)} 모드</small>
        </article>
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
                      <td>{koReason(action.reason)}</td>
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
              <h2>{firstTicket ? `${firstTicket.symbol}: 투자 논리 공백` : "보완 티켓 없음"}</h2>
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
                    <dd>{koReason(firstTicket.reason)}</dd>
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
              <span>추천 입력</span>
              <h2>뉴스와 추천이 어디서 만나는가</h2>
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
              <Link href="/intelligence">뉴스 AI 흐름</Link>
              <Link href={firstRecommendationHref}>대표 추천 열기</Link>
            </div>
          </article>
        </aside>
      </section>

      <section className="flow-panel reveal delay-3" aria-labelledby="system-flow-title">
        <div className="section-heading flow-heading">
          <span>전체 시스템</span>
          <h2 id="system-flow-title">자동화는 데이터를 쌓고, 화면은 판단 순서를 고정한다</h2>
        </div>
        <div className="flow-steps operator-flow-steps">
          {[
            ["01", "수집", "뉴스, 가격, 공시, 거시 지표를 정해진 작업으로 저장한다."],
            ["02", "구조화", "AI와 규칙이 뉴스의 종목, 테마, 방향, 불확실성을 후보로 만든다."],
            ["03", "검증", "모르는 종목, 낮은 신뢰도, 원천 없는 해석은 추천 입력에서 막는다."],
            ["04", "추천", "장기 후보는 점수, 근거, 무효화 조건과 함께 검토 대상이 된다."],
            ["05", "거래 안전", "가상 거래와 실거래는 broker boundary, 한도, kill switch를 통과해야 한다."],
          ].map(([index, title, copy]) => (
            <article className="flow-step" key={index}>
              <span>{index}</span>
              <strong>{title}</strong>
              <p>{copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="route-index operator-secondary reveal delay-3" aria-label="상세 화면 바로가기">
        {secondaryScreens.map((screen, index) => (
          <Link className="route-card" href={screen.href as Route} key={screen.href}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{screen.title}</strong>
            <small>{screen.copy}</small>
          </Link>
        ))}
      </section>
    </div>
  );
}
