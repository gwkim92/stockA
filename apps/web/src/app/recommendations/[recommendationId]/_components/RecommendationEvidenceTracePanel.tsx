import type { ComponentProps } from "react";
import type { Route } from "next";
import Link from "next/link";

import { NewsTitleBlock } from "@/components/news-title-block";

export type RecommendationEvidenceTraceCard = {
  readonly label: string;
  readonly value: string;
  readonly detail: string;
  readonly newsTitle?: ComponentProps<typeof NewsTitleBlock> | null;
  readonly href?: Route | null;
  readonly hrefLabel?: string | null;
};

type RecommendationEvidenceTracePanelProps = {
  readonly cards: readonly RecommendationEvidenceTraceCard[];
};

export function RecommendationEvidenceTracePanel({ cards }: RecommendationEvidenceTracePanelProps) {
  return (
    <section className="bento-card reveal delay-1" id="recommendation-evidence-trace" aria-label="추천 근거 흐름 요약">
      <div style={{ marginBottom: "20px" }}>
        <span className="metric-sub">근거 흐름 요약</span>
        <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>무엇을 보고 이 추천을 확인해야 하나</h2>
        <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "820px" }}>
          뉴스 근거는 바로 주문으로 이어지지 않는다. 직접 종목 뉴스, 시장·테마 흐름, 보유 상태를
          분리해 추천 입력으로 사용할 수 있는지 결정합니다.
        </p>
      </div>

      <div className="flow-steps">
        {cards.map((card) => (
          <article className="flow-step" key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.detail}</p>
            {card.newsTitle ? <NewsTitleBlock compact {...card.newsTitle} /> : null}
            {card.href && card.hrefLabel ? <Link href={card.href}>{card.hrefLabel}</Link> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
