import Link from "next/link";

import { getRecommendationDetail } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Recommendation Detail" };

type RecommendationPageProps = {
  params: Promise<{ recommendationId: string }>;
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

export default async function RecommendationPage({ params }: RecommendationPageProps) {
  const { recommendationId } = await params;
  const response = await getRecommendationDetail(recommendationId);
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="detailHero reveal">
        <div>
          <p className="eyebrow">
            {data.strategy_name} / {data.horizon_type} / {data.as_of_date}
          </p>
          <h1>{data.symbol} recommendation dossier</h1>
          <p className="lede narrow">
            The recommendation is presented as a scored thesis input, not an autonomous trade command. Outcome and evidence
            links remain visible before any portfolio action.
          </p>
        </div>
        <div className="scoreSeal" aria-label="Recommendation score">
          <span>score</span>
          <strong>{formatPercent(data.score)}</strong>
          <small>{data.recommendation}</small>
        </div>
      </section>

      <section className="splitGrid reveal delay1">
        <article className="panel">
          <div className="sectionHeading">
            <p className="eyebrow">score anatomy</p>
            <h2>{data.score_version}</h2>
          </div>
          <div className="componentStack">
            {data.score_components.map((component) => (
              <div className="componentRow" key={component.component}>
                <div>
                  <strong>{component.component}</strong>
                  <small>{component.evidence_id}</small>
                </div>
                <span>{formatPercent(component.value)}</span>
                <span>weight {formatPercent(component.weight)}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel actionPanel">
          <div className="sectionHeading">
            <p className="eyebrow">measured outcome</p>
            <h2>{data.outcome.label}</h2>
          </div>
          <dl className="factList">
            <div>
              <dt>Alpha</dt>
              <dd>{formatPercent(data.outcome.alpha)}</dd>
            </div>
            <div>
              <dt>Absolute return</dt>
              <dd>{formatPercent(data.outcome.absolute_return)}</dd>
            </div>
            <div>
              <dt>Benchmark return</dt>
              <dd>{formatPercent(data.outcome.benchmark_return)}</dd>
            </div>
            <div>
              <dt>Measurement end</dt>
              <dd>{data.outcome.measurement_end_date}</dd>
            </div>
          </dl>
          <Link className="button primary detailButton" href={`/theses/${data.linked_thesis_id}`}>
            Open linked thesis
          </Link>
        </article>
      </section>
    </div>
  );
}
