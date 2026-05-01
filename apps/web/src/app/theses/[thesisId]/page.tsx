import Link from "next/link";

import { getThesisDetail } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Thesis Detail" };

type ThesisPageProps = {
  params: Promise<{ thesisId: string }>;
};

export default async function ThesisPage({ params }: ThesisPageProps) {
  const { thesisId } = await params;
  const response = await getThesisDetail(thesisId);
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="detailHero reveal">
        <div>
          <p className="eyebrow">
            {data.symbol} / {data.status} / {data.thesis_version}
          </p>
          <h1>Thesis evidence ledger</h1>
          <p className="lede narrow">{data.summary}</p>
        </div>
        <div className="scoreSeal thesisSeal" aria-label="Latest thesis review">
          <span>review</span>
          <strong>{data.latest_review.action}</strong>
          <small>{data.latest_review.risk_level} risk</small>
        </div>
      </section>

      <section className="splitGrid reveal delay1">
        <article className="panel">
          <div className="sectionHeading">
            <p className="eyebrow">core claims</p>
            <h2>What must remain true</h2>
          </div>
          <ol className="claimList">
            {data.core_claims.map((claim) => (
              <li key={claim}>{claim}</li>
            ))}
          </ol>
        </article>

        <article className="panel">
          <div className="sectionHeading">
            <p className="eyebrow">invalidation</p>
            <h2>Break conditions</h2>
          </div>
          <div className="stackList">
            {data.invalidation_conditions.map((condition) => (
              <div className="compactRow" key={condition.condition}>
                <span>{condition.condition}</span>
                <strong>{condition.current_status}</strong>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="panel reveal delay2">
        <div className="sectionHeading">
          <p className="eyebrow">evidence</p>
          <h2>Traceable inputs</h2>
        </div>
        <div className="evidenceGrid">
          {data.evidence.map((evidence) => (
            <article key={evidence.evidence_id}>
              <span>{evidence.type}</span>
              <strong>{evidence.title}</strong>
              <small>{evidence.evidence_id}</small>
            </article>
          ))}
        </div>
        <Link className="button secondary detailButton" href={`/recommendations/${data.created_from_recommendation_id}`}>
          Back to source recommendation
        </Link>
      </section>
    </div>
  );
}
