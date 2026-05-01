import Link from "next/link";

import { getCockpitSnapshot } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

export default async function HomePage() {
  const { dashboard, tickets, health } = await getCockpitSnapshot();
  const data = dashboard.data;
  const firstTicket = tickets.data.tickets[0];

  return (
    <div className="pageStack">
      <section className="heroGrid reveal">
        <div className="heroCopy">
          <p className="eyebrow">as of {data.as_of_date} / fixture read model</p>
          <h1>Long-term portfolio review starts with the blind spot, not the recommendation.</h1>
          <p className="lede">
            This cockpit keeps cycle state, remediation backlog, scheduler readiness, and thesis coverage in the same
            operator view. AI narratives stay secondary until evidence and run provenance are visible.
          </p>
          <div className="buttonRow">
            <Link className="button primary" href="/remediation">
              Review open ticket
            </Link>
            <Link className="button secondary" href="/data-health">
              Inspect data health
            </Link>
          </div>
        </div>
        <aside className="statusLedger" aria-label="Daily run status">
          <div>
            <span>Daily automation</span>
            <strong>{data.run_status.daily_automation}</strong>
          </div>
          <div>
            <span>Scheduler</span>
            <strong>{data.run_status.scheduler}</strong>
          </div>
          <div>
            <span>Latest run</span>
            <strong>{data.run_status.latest_run_id}</strong>
          </div>
        </aside>
      </section>

      <section className="metricRail reveal delay1" aria-label="Attention summary">
        <article>
          <span>Open tickets</span>
          <strong>{data.attention_summary.open_ticket_count}</strong>
          <small>{tickets.data.status_filter} backlog</small>
        </article>
        <article className="riskHigh">
          <span>Critical blind spots</span>
          <strong>{data.attention_summary.critical_blind_spot_count}</strong>
          <small>requires human review</small>
        </article>
        <article>
          <span>Coverage ratio</span>
          <strong>{formatPercent(data.latest_metrics.weight_coverage_ratio)}</strong>
          <small>{formatPercent(data.latest_metrics.covered_weight)} covered weight</small>
        </article>
        <article>
          <span>Pipeline failures</span>
          <strong>{data.attention_summary.failed_pipeline_count}</strong>
          <small>{health.data.overall_status}</small>
        </article>
      </section>

      <section className="splitGrid reveal delay2">
        <article className="panel actionPanel">
          <div className="sectionHeading">
            <p className="eyebrow">top operator action</p>
            <h2>{firstTicket.symbol}: thesis coverage missing</h2>
          </div>
          <p className="bodyText">{firstTicket.required_human_decision}</p>
          <dl className="factList">
            <div>
              <dt>Suggested runner</dt>
              <dd>{firstTicket.suggested_runner}</dd>
            </div>
            <div>
              <dt>Reason</dt>
              <dd>{firstTicket.reason}</dd>
            </div>
            <div>
              <dt>Source run</dt>
              <dd>{firstTicket.source_run_id}</dd>
            </div>
          </dl>
        </article>

        <article className="panel">
          <div className="sectionHeading">
            <p className="eyebrow">next actions</p>
            <h2>Review queue</h2>
          </div>
          <div className="actionList">
            {data.top_actions.map((action) => (
              <div className="actionRow" key={`${action.rank}-${action.symbol}`}>
                <span className={`riskPill ${action.risk_level}`}>{action.risk_level}</span>
                <strong>{action.symbol}</strong>
                <span>{action.action}</span>
                <small>{action.reason}</small>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
