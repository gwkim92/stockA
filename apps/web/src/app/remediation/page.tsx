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
    <div className="terminal-page">
      <section className="page-hero reveal" aria-labelledby="remediation-title">
        <div>
          <div className="bento-badge">보완 큐</div>
          <h1 className="page-title" id="remediation-title">
            먼저 정리해야 할 판단 공백을 모은다.
          </h1>
        </div>
        <p className="page-lede">
          투자 논리 누락, 성과 측정 공백, 비중 검토처럼 자동으로 넘기면 안 되는 항목을 보여준다.
          실제 상태 변경은 감사 로그와 승인 경로가 준비된 뒤에만 다룬다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="보완 큐 요약">
        <article className="rail-cell">
          <span>01 포트폴리오</span>
          <strong className="rail-word-value">{koLabel(data.portfolio_name)}</strong>
          <small>{koCode(data.status_filter)} 필터</small>
        </article>
        <article className="rail-cell">
          <span>02 열린 티켓</span>
          <strong>{data.ticket_count}</strong>
          <small>검토 대기</small>
        </article>
        <article className="rail-cell rail-critical">
          <span>03 고위험</span>
          <strong>{highRiskCount}</strong>
          <small>우선 확인</small>
        </article>
        <article className="rail-cell">
          <span>04 비중 정책</span>
          <strong>{formatPercent(allocationPolicy.max_single_position_weight)}</strong>
          <small>단일 종목 상한</small>
        </article>
      </section>

      <section className="split-ledger reveal delay-2">
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
          <article className="ledger-panel">
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

          <article className="ledger-panel">
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

          <article className="ledger-panel">
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
