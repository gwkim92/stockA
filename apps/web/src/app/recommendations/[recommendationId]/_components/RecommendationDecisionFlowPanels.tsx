import type { Route } from "next";
import Link from "next/link";

import type { RecommendationQualityDecision } from "@/components/recommendation-product-overview";
import { koCode } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";

type DecisionFlowTone = "ready" | "watch" | "blocked";

export type RecommendationWaterfallCard = {
  readonly step: string;
  readonly label: string;
  readonly title: string;
  readonly body: string;
  readonly href: Route | `#${string}`;
  readonly hrefLabel: string;
  readonly tone: DecisionFlowTone;
};

export type RecommendationFocusItem = {
  readonly label: string;
  readonly title: string;
  readonly body: string;
  readonly metric: string;
  readonly href: Route | `#${string}`;
  readonly hrefLabel: string;
  readonly tone: DecisionFlowTone;
};

type RecommendationDecisionWaterfallProps = {
  readonly data: RecommendationDetailData;
  readonly cards: readonly RecommendationWaterfallCard[];
  readonly qualityDecision: RecommendationQualityDecision;
  readonly decisionWaterfall: RecommendationDetailData["professional_decision_waterfall"];
};

type RecommendationFocusPanelProps = {
  readonly data: RecommendationDetailData;
  readonly items: readonly RecommendationFocusItem[];
  readonly qualityDecision: RecommendationQualityDecision;
  readonly decisionWaterfall: RecommendationDetailData["professional_decision_waterfall"];
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function stockHref(symbol: string) {
  return `/stocks/${encodeURIComponent(symbol)}` as Route;
}

function routeLink(href: Route | `#${string}`, label: string) {
  if (href.startsWith("#")) {
    return <a href={href}>{label}</a>;
  }
  return <Link href={href as Route}>{label}</Link>;
}

export function RecommendationDecisionWaterfall({
  data,
  cards,
  qualityDecision,
  decisionWaterfall,
}: RecommendationDecisionWaterfallProps) {
  return (
    <section className={`recommendation-waterfall-panel ${qualityDecision.tone} reveal delay-1`} aria-labelledby="recommendation-waterfall-title">
      <div className="recommendation-waterfall-lead">
        <span>판단 흐름</span>
        <h2 id="recommendation-waterfall-title">
          {data.symbol} · {qualityDecision.status}
        </h2>
        <p>{qualityDecision.summary}</p>
        <div className="recommendation-waterfall-metrics" aria-label="추천 핵심 지표">
          <div>
            <span>추천</span>
            <strong>{koCode(data.recommendation)}</strong>
          </div>
          <div>
            <span>점수</span>
            <strong>{formatPercent(data.score)}</strong>
          </div>
          <div>
            <span>가상 매매 검증</span>
            <strong>{decisionWaterfall.paper_validation_input_allowed ? "입력 가능" : "입력 차단"}</strong>
          </div>
          <div>
            <span>실거래 주문</span>
            <strong>{decisionWaterfall.broker_submit_allowed ? "허용" : "차단"}</strong>
          </div>
        </div>
        <div className="recommendation-waterfall-actions">
          <Link className="btn btn-primary" href={stockHref(data.symbol)}>
            종목 상세 보기
          </Link>
          <Link className="btn btn-secondary" href={`/theses/${data.linked_thesis_id}` as Route}>
            투자 논리 보기
          </Link>
          <Link className="btn btn-secondary" href="/paper-trading">
            가상 매매 상태
          </Link>
        </div>
      </div>

      <div className="recommendation-waterfall-track">
        {cards.map((card) => (
          <article className={`recommendation-waterfall-card tone-${card.tone}`} key={card.label}>
            <span>{card.step} · {card.label}</span>
            <strong>{card.title}</strong>
            <p>{card.body}</p>
            {routeLink(card.href, card.hrefLabel)}
          </article>
        ))}
      </div>
    </section>
  );
}

export function RecommendationFocusPanel({
  data,
  items,
  qualityDecision,
  decisionWaterfall,
}: RecommendationFocusPanelProps) {
  const firstItem = items[0];
  const focusTitle = firstItem ? `지금 확인할 항목: ${firstItem.title}` : "현재 결론";

  return (
    <section className={`recommendation-focus-panel ${qualityDecision.tone} reveal delay-1`} aria-labelledby="recommendation-focus-title">
      <div className="recommendation-focus-lead">
        <span>추천 판단 순서</span>
        <h2 id="recommendation-focus-title">{focusTitle}</h2>
        <p>
          {data.symbol} 추천의 채택·보류·기록 판단을 원천 근거, 전문 분석, 가상 매매 경계 순서로 정리했다.
        </p>
        <div className="recommendation-focus-metrics" aria-label="추천서 핵심 상태">
          <div>
            <span>추천</span>
            <strong>{koCode(data.recommendation)}</strong>
          </div>
          <div>
            <span>점수</span>
            <strong>{formatPercent(data.score)}</strong>
          </div>
          <div>
            <span>전문 결론</span>
            <strong>{qualityDecision.status}</strong>
          </div>
          <div>
            <span>실거래</span>
            <strong>{decisionWaterfall.broker_submit_allowed ? "허용" : "차단"}</strong>
          </div>
        </div>
      </div>

      <div className="recommendation-focus-list">
        {items.map((item) => (
          <article className={`recommendation-focus-card tone-${item.tone}`} key={`${item.label}-${item.title}`}>
            <span>{item.label}</span>
            <strong>{item.title}</strong>
            <b>{item.metric}</b>
            <p>{item.body}</p>
            {routeLink(item.href, item.hrefLabel)}
          </article>
        ))}
      </div>
    </section>
  );
}
