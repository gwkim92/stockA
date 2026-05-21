import Link from "next/link";
import type { Route } from "next";
import { getCockpitSnapshot } from "@/lib/frontend-api";
import { koCode, koLabel, koReason } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";

function formatPercent(value: number) {
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

export default async function HomePage() {
  const { dashboard, tickets, health } = await getCockpitSnapshot();
  const data = dashboard.data;
  const ticketData = tickets.data;
  const firstTicket = ticketData.tickets[0];
  const providerBudget = health.data.provider_budget;
  const coverage = data.latest_metrics;

  return (
    <div className="terminal-home">
      <section className="manifest-grid reveal" aria-labelledby="dashboard-title">
        <div className="manifest-copy">
          <div className="bento-badge">운영 개요</div>
          <h1 className="terminal-title" id="dashboard-title">
            <span>데이터를</span>
            <span>모으고</span>
            <span>논리로</span>
            <span className="title-muted">검증한다.</span>
          </h1>
          <p className="manifest-lede">
            이 화면은 거시/공시/가격/포트폴리오 데이터를 모아 사이클, 추천, 투자 논리,
            보유 검토, 성과 측정으로 이어지는 현재 운영 상태를 보여준다. AI 해석은 결론이
            아니라 출처가 남는 보조 증거로만 다룬다.
          </p>
          <div className="btn-row">
            <Link className="btn btn-primary" href="/remediation">
              01 검토 큐 열기
            </Link>
            <Link className="btn btn-secondary" href="/data-health">
              02 데이터 상태 확인
            </Link>
            <Link className="btn btn-secondary" href={"/intelligence" as Route}>
              03 분석 지도 보기
            </Link>
          </div>
        </div>

        <figure className="signal-graph" aria-label="투자 운영 관계도">
          <div className="graph-kicker">
            <span>Fig. 01 — 운영 흐름</span>
            <strong>수집 / 증거 / 검토</strong>
          </div>
          <svg className="graph-svg" viewBox="0 0 640 440" role="img" aria-labelledby="graph-title">
            <title id="graph-title">데이터, 사이클, 투자 논리, 증거, 검토 큐의 연결 구조</title>
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="0.7" />
              </pattern>
            </defs>
            <rect className="graph-grid" x="44" y="34" width="552" height="338" fill="url(#grid)" />
            <path className="graph-edge" d="M132 284 C190 190 225 134 306 150" />
            <path className="graph-edge" d="M306 150 C380 140 435 188 500 116" />
            <path className="graph-edge" d="M306 150 C334 232 396 268 512 290" />
            <path className="graph-edge graph-edge-soft" d="M132 284 C234 326 352 350 512 290" />
            <path className="graph-edge graph-edge-soft" d="M204 78 C248 110 272 124 306 150" />
            <g className="graph-node">
              <rect x="92" y="244" width="80" height="80" />
              <text x="132" y="279">사이클</text>
              <text x="132" y="299">{formatPercent(coverage.weight_coverage_ratio)}</text>
            </g>
            <g className="graph-node graph-node-primary">
              <rect x="266" y="110" width="80" height="80" />
              <text x="306" y="145">논리</text>
              <text x="306" y="165">누락 {data.attention_summary.missing_thesis_count}</text>
            </g>
            <g className="graph-node">
              <rect x="460" y="76" width="80" height="80" />
              <text x="500" y="111">증거</text>
              <text x="500" y="131">출처</text>
            </g>
            <g className="graph-node graph-node-alert">
              <rect x="472" y="250" width="80" height="80" />
              <text x="512" y="285">검토</text>
              <text x="512" y="305">열림 {data.attention_summary.open_ticket_count}</text>
            </g>
            <g className="graph-node">
              <rect x="164" y="38" width="80" height="80" />
              <text x="204" y="73">데이터</text>
              <text x="204" y="93">{koCode(health.data.overall_status)}</text>
            </g>
            <line className="graph-axis" x1="596" x2="596" y1="34" y2="372" />
            <circle className="graph-axis-dot" cx="596" cy="34" r="6" />
            <circle className="graph-axis-dot" cx="596" cy="372" r="6" />
            <text className="graph-axis-label" x="606" y="42">확인됨</text>
            <text className="graph-axis-label" x="606" y="375">막힘</text>
          </svg>
          <figcaption className="graph-caption">
            커버리지 {formatPercent(coverage.covered_weight)} · 사각지대{" "}
            {data.attention_summary.critical_blind_spot_count} · 제공자{" "}
            {koCode(providerBudget.provider)}
          </figcaption>
        </figure>
      </section>

      <section className="status-rail reveal delay-1" aria-label="오늘의 운영 지표">
        <article className="rail-cell rail-critical">
          <span>01 중요 사각지대</span>
          <strong>{data.attention_summary.critical_blind_spot_count}</strong>
          <small>사람 검토 필요</small>
        </article>
        <article className="rail-cell">
          <span>02 커버리지</span>
          <strong>{formatPercent(coverage.weight_coverage_ratio)}</strong>
          <small>커버된 비중 {formatPercent(coverage.covered_weight)}</small>
        </article>
        <article className="rail-cell">
          <span>03 열린 검토 티켓</span>
          <strong>{data.attention_summary.open_ticket_count}</strong>
          <small>{koCode(ticketData.status_filter)} 검토 대기열</small>
        </article>
        <article className="rail-cell">
          <span>04 파이프라인 실패</span>
          <strong>{data.attention_summary.failed_pipeline_count}</strong>
          <small>{koCode(health.data.overall_status)}</small>
        </article>
      </section>

      <section className="flow-panel reveal delay-2" aria-labelledby="system-flow-title">
        <div className="section-heading flow-heading">
          <span>운영 흐름</span>
          <h2 id="system-flow-title">데이터가 투자 판단까지 가는 길</h2>
        </div>
        <div className="flow-steps">
          {[
            ["01", "수집", "가격, 뉴스, 공시, 거시 데이터를 정해진 주기로 가져와 원천을 남긴다."],
            ["02", "정리", "Postgres에 표준 형태로 저장하고, 어떤 작업이 언제 돌았는지 기록한다."],
            ["03", "분석", "뉴스 묶음, 개별 뉴스 AI 후보, 테마·사이클 상태를 근거로 만든다."],
            ["04", "추천", "장기 투자 후보와 점수 구성요소를 만들되, 주문으로 바로 연결하지 않는다."],
            ["05", "검토", "투자 논리, 보유 상태, 위험 사유를 사람이 확인할 수 있게 묶는다."],
            ["06", "성과", "추천 이후 실제 성과와 벤치마크 차이를 추적해 품질을 점검한다."],
          ].map(([index, title, copy]) => (
            <article className="flow-step" key={index}>
              <span>{index}</span>
              <strong>{title}</strong>
              <p>{copy}</p>
            </article>
          ))}
        </div>
        <p className="flow-note">
          현재 MVP는 로컬 Postgres, FastAPI 읽기 전용 백엔드, Next.js 관제 화면으로 동작한다. 페이퍼 거래와 실거래,
          쓰기 API, 자동 승인형 매매는 아직 범위 밖이다.
        </p>
      </section>

      <section className="ledger-grid reveal delay-2">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
          <span>우선순위</span>
            <h2>운영자가 먼저 볼 항목</h2>
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

        <article className="ledger-panel decision-panel">
          <div className="section-heading">
            <span>첫 검토 항목</span>
            <h2>{firstTicket ? `${firstTicket.symbol}: 투자 논리 커버리지 누락` : "보완 티켓 없음"}</h2>
          </div>
          {firstTicket ? (
            <>
              <p className="decision-copy">{koLabel(firstTicket.required_human_decision)}</p>
              <dl className="fact-list">
                <div>
                  <dt>제안 실행 경로</dt>
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
            </>
          ) : (
            <p className="decision-copy">현재 열린 보완 큐가 비어 있다.</p>
          )}
        </article>

        <article className="ledger-panel runtime-panel">
          <div className="section-heading">
            <span>실행 상태</span>
            <h2>자동화와 데이터 예산</h2>
          </div>
          <dl className="runtime-grid">
            <div>
              <dt>일일 자동화</dt>
              <dd>{koCode(data.run_status.daily_automation)}</dd>
            </div>
            <div>
              <dt>스케줄러</dt>
              <dd>{koCode(data.run_status.scheduler)}</dd>
            </div>
            <div>
              <dt>최근 실행</dt>
              <dd>{data.run_status.latest_run_id}</dd>
            </div>
            <div>
              <dt>호출 예산</dt>
              <dd>
                {providerBudget.remaining_request_count}/{providerBudget.daily_budget}
              </dd>
            </div>
          </dl>
        </article>
      </section>

      <section className="route-index reveal delay-3" aria-label="주요 화면 바로가기">
        <Link className="route-card" href={"/stocks" as Route}>
          <span>02</span>
          <strong>종목 확인실</strong>
          <small>수집 가격, 차트, 추천/보유 상태</small>
        </Link>
        <Link className="route-card" href={"/paper-trading" as Route}>
          <span>03</span>
          <strong>가상 거래 점검</strong>
          <small>실제 주문 전 추천/보유 충돌 확인</small>
        </Link>
        <Link className="route-card" href="/cycles">
          <span>05</span>
          <strong>사이클 보드</strong>
          <small>테마 상태와 이전 상태 비교</small>
        </Link>
        <Link className="route-card" href="/events">
          <span>06</span>
          <strong>이벤트 원장</strong>
          <small>AI 추출과 원천 문서 연결</small>
        </Link>
        <Link className="route-card" href="/portfolio/coverage">
          <span>10</span>
          <strong>보유 검토</strong>
          <small>포지션별 투자 논리/성과 공백</small>
        </Link>
        <Link className="route-card" href="/performance">
          <span>11</span>
          <strong>성과 분석</strong>
          <small>추천 성과와 벤치마크 대비</small>
        </Link>
      </section>
    </div>
  );
}
