import type { DataHealthTone } from "@/components/operations/DataHealthOverview";

export type DataHealthDetailDecisionCard = {
  readonly body: string;
  readonly cta: string;
  readonly href: string;
  readonly label: string;
  readonly title: string;
  readonly tone: DataHealthTone;
};

type DataHealthDetailDecisionCardsSectionProps = {
  readonly cards: readonly DataHealthDetailDecisionCard[];
};

export function DataHealthDetailDecisionCardsSection({ cards }: DataHealthDetailDecisionCardsSectionProps) {
  return (
    <details className="operator-details-panel reveal delay-2">
      <summary>
        <span>세부 판단 카드</span>
        <strong>성과, 포트폴리오 검토, 전문 분석 세부 상태 {cards.length}개</strong>
      </summary>
      <div className="decision-brief-grid details-inner" aria-label="데이터 수집 세부 판단 요약">
        {cards.map((card) => (
          <a className="decision-brief-card data-decision-card" href={card.href} key={card.label}>
            <span>{card.label}</span>
            <strong className={`risk-tag ${card.tone}`}>{card.title}</strong>
            <p>{card.body}</p>
            <small>{card.cta}</small>
          </a>
        ))}
      </div>
    </details>
  );
}
