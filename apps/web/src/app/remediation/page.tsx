import { getRemediationTickets } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Remediation" };

export default async function RemediationPage() {
  const response = await getRemediationTickets();

  return (
    <div className="pageStack">
      <section className="sectionHeading reveal">
        <p className="eyebrow">{response.data.portfolio_name}</p>
        <h1>Persistent remediation backlog</h1>
        <p className="lede narrow">
          Tickets are read-only here. Status mutation stays deferred until actor identity, reason capture, and audit trail
          are implemented.
        </p>
      </section>

      <section className="panel reveal delay1">
        <div className="ticketTable" role="table" aria-label="Open remediation tickets">
          <div className="ticketRow heading" role="row">
            <span>Symbol</span>
            <span>Action</span>
            <span>Risk</span>
            <span>Required decision</span>
          </div>
          {response.data.tickets.map((ticket) => (
            <div className="ticketRow" role="row" key={ticket.ticket_id}>
              <strong>{ticket.symbol}</strong>
              <span>{ticket.action}</span>
              <span className={`riskPill ${ticket.risk_level}`}>{ticket.risk_level}</span>
              <span>{ticket.required_human_decision}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
