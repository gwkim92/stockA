import { getDataHealth } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Data Health" };

export default async function DataHealthPage() {
  const response = await getDataHealth();
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="sectionHeading reveal">
        <p className="eyebrow">runtime gates / {data.as_of_date}</p>
        <h1>Data health before conviction</h1>
        <p className="lede narrow">
          The UI treats scheduler readiness, pipeline provenance, and stale datasets as first-class investment risk.
        </p>
      </section>

      <section className="splitGrid reveal delay1">
        <article className="panel">
          <div className="sectionHeading">
            <p className="eyebrow">pipeline runs</p>
            <h2>{data.overall_status}</h2>
          </div>
          <div className="stackList">
            {data.pipeline_runs.map((run) => (
              <div className="compactRow" key={run.latest_run_id}>
                <span>{run.pipeline_name}</span>
                <strong>{run.latest_status}</strong>
                <small>{run.finished_at}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="sectionHeading">
            <p className="eyebrow">open gates</p>
            <h2>{data.open_gates.length} gates remain</h2>
          </div>
          <div className="gateCloud">
            {data.open_gates.map((gate) => (
              <span key={gate}>{gate}</span>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
