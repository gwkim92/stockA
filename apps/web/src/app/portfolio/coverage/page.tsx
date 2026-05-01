import { getPortfolioCoverage } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Portfolio Coverage" };

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

export default async function PortfolioCoveragePage() {
  const response = await getPortfolioCoverage();
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="detailHero reveal">
        <div>
          <p className="eyebrow">
            {data.portfolio_name} / {data.strategy_name} / {data.as_of_date}
          </p>
          <h1>Portfolio coverage gate</h1>
          <p className="lede narrow">
            Attribution is blocked until every meaningful position has a thesis and measurable outcome path. Cash is shown
            explicitly instead of disappearing into portfolio math.
          </p>
        </div>
        <div className="scoreSeal coverageSeal" aria-label="Weight coverage ratio">
          <span>weight coverage</span>
          <strong>{formatPercent(data.summary.weight_coverage_ratio)}</strong>
          <small>{data.attribution_readiness.is_ready ? "ready" : "blocked"}</small>
        </div>
      </section>

      <section className="metricRail reveal delay1" aria-label="Portfolio coverage summary">
        <article>
          <span>Positions</span>
          <strong>{data.summary.position_count}</strong>
          <small>{data.summary.covered_position_count} covered</small>
        </article>
        <article className="riskHigh">
          <span>Missing thesis</span>
          <strong>{data.summary.missing_thesis_count}</strong>
          <small>{formatPercent(data.summary.missing_thesis_weight)} weight</small>
        </article>
        <article>
          <span>Cash</span>
          <strong>{formatPercent(data.summary.cash_weight)}</strong>
          <small>explicit allocation</small>
        </article>
        <article>
          <span>Outcomes missing</span>
          <strong>{data.summary.missing_outcome_count}</strong>
          <small>measurement end {data.coverage_measurement_end_date}</small>
        </article>
      </section>

      <section className="panel reveal delay2">
        <div className="sectionHeading">
          <p className="eyebrow">position coverage</p>
          <h2>Review map</h2>
        </div>
        <div className="ticketTable coverageTable" role="table" aria-label="Portfolio coverage positions">
          <div className="ticketRow heading coverageRow" role="row">
            <span>Symbol</span>
            <span>Weight</span>
            <span>Coverage</span>
            <span>Outcome</span>
            <span>Action</span>
          </div>
          {data.positions.map((position) => (
            <div className="ticketRow coverageRow" role="row" key={position.instrument_id}>
              <strong>{position.symbol}</strong>
              <span>{formatPercent(position.weight)}</span>
              <span>{position.coverage_status}</span>
              <span>{position.outcome_status}</span>
              <span>{position.action}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
