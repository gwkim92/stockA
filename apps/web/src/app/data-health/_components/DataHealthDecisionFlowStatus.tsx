type DecisionFlowTone = "ready" | "watch" | "block";

export type DataHealthDecisionFlowCard = {
  readonly evidence: string;
  readonly href: string;
  readonly impact: string;
  readonly label: string;
  readonly statusLabel: string;
  readonly title: string;
  readonly tone: DecisionFlowTone;
};

type DataHealthDecisionFlowStatusProps = {
  readonly cards: readonly DataHealthDecisionFlowCard[];
};

function toneClassName(tone: DecisionFlowTone) {
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

export function DataHealthDecisionFlowStatus({ cards }: DataHealthDecisionFlowStatusProps) {
  return (
    <section className="feature-map-panel reveal delay-1" id="decision-flow-status" aria-labelledby="decision-flow-status-title">
      <div className="section-heading stacked-heading">
        <span>판단 흐름 상태</span>
        <h2 id="decision-flow-status-title">수집부터 성과 피드백까지 어느 판단 단계가 신뢰 가능한지 판정합니다</h2>
        <p>
          이 화면은 실행 로그가 아니라 투자 판단 흐름의 건강 상태를 먼저 보여줍니다. 세부 실행 기록은 아래 운영 상세에
          남깁니다.
        </p>
      </div>
      <div className="decision-brief-grid workspace-command-grid" aria-label="투자 판단 흐름 상태">
        {cards.map((card) => (
          <a className={`decision-card ${toneClassName(card.tone)}`} href={card.href} key={card.label}>
            <span>{card.label}</span>
            <strong>{card.title}</strong>
            <small>{card.statusLabel}</small>
            <p>{card.evidence}</p>
            <b>{card.impact}</b>
          </a>
        ))}
      </div>
    </section>
  );
}
