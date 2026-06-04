import { getRemediationTickets } from "@/lib/frontend-api";
import { koCode, koLabel, koReason } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "보완 큐" };

function riskClass(value: string) {
  if (value === "high") {
    return "risk-high";
  }
  if (value === "medium") {
    return "risk-medium";
  }
  return "risk-low";
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미설정";
  }
  return `${(value * 100).toFixed(1)}%`;
}

export default async function RemediationPage() {
  const response = await getRemediationTickets();
  const data = response.data;
  const allocationPolicy = data.allocation_policy;
  const highRiskCount = data.tickets.filter((ticket) => ticket.risk_level === "high").length;

  return (
    <div className="terminal-page decision-page">
      <section className="decision-brief reveal" aria-labelledby="remediation-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">보완 큐 · {koLabel(data.portfolio_name)} · {koCode(data.status_filter)}</span>
          <h1 className="decision-brief-title" id="remediation-title">
            먼저 정리해야 할 판단 공백 {data.ticket_count.toLocaleString("ko-KR")}개
          </h1>
          <p className="decision-brief-copy">
            투자 논리 누락, 성과 측정 공백, 비중 검토처럼 자동으로 넘기면 안 되는 항목을 모은다. 실제 상태 변경은 감사 로그와 승인 경로가 준비된 뒤에만 다룬다.
          </p>
          <div className="decision-brief-meta" aria-label="보완 큐 핵심 상태">
            <span>열린 티켓 {data.ticket_count.toLocaleString("ko-KR")}개</span>
            <span>고위험 {highRiskCount.toLocaleString("ko-KR")}개</span>
            <span>단일 종목 상한 {formatPercent(allocationPolicy.max_single_position_weight)}</span>
            <span>리밸런싱 기준 {formatPercent(allocationPolicy.min_rebalance_target_weight)}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <a className={highRiskCount > 0 ? "decision-card is-block" : "decision-card is-good"} href="#remediation-open-items">
            <span>열린 항목</span>
            <strong>{data.ticket_count.toLocaleString("ko-KR")}개</strong>
            <small>고위험 {highRiskCount.toLocaleString("ko-KR")}개. 자동 조치하지 말고 필요한 결정만 확인한다.</small>
            <b>티켓 보기</b>
          </a>
          <a className="decision-card is-watch" href="#remediation-policy">
            <span>비중 정책</span>
            <strong>{formatPercent(allocationPolicy.max_single_position_weight)}</strong>
            <small>추천 비중과 보유 비중 조정은 별도 정책과 승인 경로가 필요하다.</small>
            <b>정책 보기</b>
          </a>
          <a className="decision-card" href="#remediation-status-counts">
            <span>상태 분포</span>
            <strong>{Object.keys(data.status_counts).length.toLocaleString("ko-KR")}개 상태</strong>
            <small>큐가 어디에 몰려 있는지 확인한다.</small>
            <b>분포 보기</b>
          </a>
          <a className="decision-card is-block" href="#remediation-boundary">
            <span>자동 조치</span>
            <strong>금지</strong>
            <small>티켓은 추천이나 주문이 아니라 보완 입력이다.</small>
            <b>경계 보기</b>
          </a>
        </div>
      </section>

      <section className="split-ledger reveal delay-2" id="remediation-open-items">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
            <span>열린 항목</span>
            <h2>심볼별 필수 결정</h2>
          </div>
          <div className="ledger-table-wrap">
            <table className="ledger-table remediation-table">
              <thead>
                <tr>
                  <th scope="col">티켓</th>
                  <th scope="col">심볼</th>
                  <th scope="col">조치</th>
                  <th scope="col">위험</th>
                  <th scope="col">필수 결정</th>
                  <th scope="col">업데이트</th>
                </tr>
              </thead>
              <tbody>
                {data.tickets.map((ticket, index) => (
                  <tr key={ticket.ticket_id}>
                    <td>{String(index + 1).padStart(2, "0")}</td>
                    <td>
                      <strong>{ticket.symbol}</strong>
                      <small>{ticket.instrument_id}</small>
                    </td>
                    <td>{koCode(ticket.action)}</td>
                    <td>
                      <span className={`risk-tag ${riskClass(ticket.risk_level)}`}>
                        {koCode(ticket.risk_level)}
                      </span>
                    </td>
                    <td>{koLabel(ticket.required_human_decision)}</td>
                    <td>{ticket.updated_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <aside className="side-ledger">
          <article className="ledger-panel" id="remediation-policy">
            <div className="section-heading stacked-heading">
              <span>비중 정책</span>
              <h2>현재 적용 기준</h2>
            </div>
            <p className="decision-copy">
              추천 비중은 신호 크기이고, 보유 비중 축소 여부는 이 정책 기준으로 별도 판단한다.
            </p>
            <dl className="fact-list">
              <div>
                <dt>정책</dt>
                <dd>{koCode(allocationPolicy.policy_name)}</dd>
              </div>
              <div>
                <dt>적용 범위</dt>
                <dd>{koCode(allocationPolicy.policy_scope)}</dd>
              </div>
              <div>
                <dt>단일 종목 상한</dt>
                <dd>{formatPercent(allocationPolicy.max_single_position_weight)}</dd>
              </div>
              <div>
                <dt>리밸런싱 목표 해석</dt>
                <dd>{formatPercent(allocationPolicy.min_rebalance_target_weight)} 이상만 목표 비중으로 해석</dd>
              </div>
            </dl>
          </article>

          <article className="ledger-panel" id="remediation-status-counts">
            <div className="section-heading stacked-heading">
              <span>상태 분포</span>
              <h2>큐 분포</h2>
            </div>
            <dl className="fact-list">
              {Object.entries(data.status_counts).map(([status, count]) => (
                <div key={status}>
                  <dt>{koCode(status)}</dt>
                  <dd>{count}</dd>
                </div>
              ))}
            </dl>
          </article>

          <article className="ledger-panel" id="remediation-boundary">
            <div className="section-heading stacked-heading">
              <span>결정 경계</span>
              <h2>자동 조치 금지</h2>
            </div>
            <p className="decision-copy">
              티켓은 추천이 아니라 운영 입력이다. 실제 보유 판단은 당시 입력 데이터, 점수, thesis,
              무효화 조건을 함께 저장한 뒤 별도 승인 경로에서만 다룬다.
            </p>
            <dl className="fact-list">
              {data.tickets.slice(0, 2).map((ticket) => (
                <div key={`${ticket.ticket_id}-runner`}>
                  <dt>{ticket.symbol}</dt>
                  <dd>{koReason(ticket.reason)}</dd>
                </div>
              ))}
            </dl>
          </article>
        </aside>
      </section>
    </div>
  );
}
