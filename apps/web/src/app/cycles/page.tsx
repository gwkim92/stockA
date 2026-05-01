import { getCycleStates } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Cycles" };

function formatConfidence(value: number) {
  return `${Math.round(value * 100)}%`;
}

export default async function CyclesPage() {
  const response = await getCycleStates();
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="sectionHeading reveal">
        <p className="eyebrow">
          {data.strategy_name} / {data.horizon_type} / {data.universe_version}
        </p>
        <h1>Theme cycle board</h1>
        <p className="lede narrow">
          Cycle states are not buy signals. They are context for thesis quality, coverage gaps, and evidence review.
        </p>
      </section>

      <section className="cycleGrid reveal delay1">
        {data.cycle_states.map((cycle) => (
          <article className="panel cycleCard" key={cycle.theme_key}>
            <div>
              <p className="eyebrow">{cycle.theme_key}</p>
              <h2>{cycle.theme_name}</h2>
            </div>
            <div className="cycleState">
              <strong>{cycle.state}</strong>
              <span>from {cycle.previous_state}</span>
            </div>
            <dl className="factList">
              <div>
                <dt>Confidence</dt>
                <dd>{formatConfidence(cycle.confidence)}</dd>
              </div>
              <div>
                <dt>Instruments</dt>
                <dd>{cycle.instrument_count}</dd>
              </div>
              <div>
                <dt>Top symbols</dt>
                <dd>{cycle.top_symbols.join(", ")}</dd>
              </div>
            </dl>
          </article>
        ))}
      </section>
    </div>
  );
}
