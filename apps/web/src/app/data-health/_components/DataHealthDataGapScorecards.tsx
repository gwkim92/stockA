type DataGapTone = "ready" | "watch" | "block";

export type DataHealthDataGapCard = {
  readonly currentPolicy: string;
  readonly impact: string;
  readonly label: string;
  readonly nextAction: string;
  readonly priority: string;
  readonly title: string;
  readonly tone: DataGapTone;
};

type DataHealthDataGapScorecardsProps = {
  readonly cards: readonly DataHealthDataGapCard[];
};

function toneClassName(tone: DataGapTone) {
  switch (tone) {
    case "ready":
      return "is-good";
    case "block":
      return "is-block";
    case "watch":
      return "is-watch";
    default: {
      const exhaustive: never = tone;
      return exhaustive;
    }
  }
}

export function DataHealthDataGapScorecards({ cards }: DataHealthDataGapScorecardsProps) {
  return (
    <section className="feature-map-panel reveal delay-1" id="data-gap-scorecards" aria-labelledby="data-gap-scorecards-title">
      <div className="section-heading stacked-heading">
        <span>데이터 공백 점수판</span>
        <h2 id="data-gap-scorecards-title">없는 데이터를 추정하지 않고 판단 한계로 남깁니다</h2>
        <p>
          추가 데이터 후보는 무료 가능성, 품질 제한, 추천 영향, 현재 차단 정책으로 나눕니다. 부족한 데이터는 바로 점수에
          넣지 않고 원천 한계나 반영 비중 0인 근거로 남깁니다.
        </p>
      </div>
      <div className="decision-brief-grid workspace-command-grid" aria-label="데이터 공백별 사용 정책">
        {cards.map((card) => (
          <article className={`decision-card ${toneClassName(card.tone)}`} key={card.label}>
            <span>{card.label}</span>
            <strong>{card.title}</strong>
            <small>{card.priority}</small>
            <p>{card.currentPolicy}</p>
            <small>{card.impact}</small>
            <b>{card.nextAction}</b>
          </article>
        ))}
      </div>
    </section>
  );
}
