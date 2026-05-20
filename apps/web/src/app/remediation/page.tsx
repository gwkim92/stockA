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

export default async function RemediationPage() {
  const response = await getRemediationTickets();
  const data = response.data;
  const highRiskCount = data.tickets.filter((ticket) => ticket.risk_level === "high").length;
  const runnerCount = new Set(data.tickets.map((ticket) => ticket.suggested_runner)).size;

  return (
    <div className="terminal-page">
      <section className="page-hero reveal" aria-labelledby="remediation-title">
        <div>
          <div className="bento-badge">Index 01 — Remediation Queue</div>
          <h1 className="page-title" id="remediation-title">
            열린 보완 티켓을 감사 가능한 결정으로 바꾼다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 읽기 전용 운영 원장이다. 상태 변경은 행위자 식별, 사유 기록, 감사 추적이
          준비될 때까지 보류한다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="보완 큐 요약">
        <article className="rail-cell">
          <span>01 포트폴리오</span>
          <strong>{koLabel(data.portfolio_name)}</strong>
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
          <span>04 실행 경로</span>
          <strong>{runnerCount}</strong>
          <small>제안 runner</small>
        </article>
      </section>

      <section className="split-ledger reveal delay-2">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
            <span>Index 01.A — Open Ledger</span>
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
              <span>Index 01.B — Status Counts</span>
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
              <span>Index 01.C — Decision Boundary</span>
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
