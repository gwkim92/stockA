import Link from "next/link";
import type { Route } from "next";

import { NewsTitleBlock } from "@/components/news-title-block";
import { koCode } from "@/lib/korean-labels";

import {
  formatScoreMetricValue,
  macroFlowRows,
  scoreComponentLabel,
  type ScoreComponent,
} from "./recommendation-score-component-model";
import { formatPanelPercent } from "./recommendation-panel-format";

type RecommendationMacroFlowPanelProps = {
  readonly symbol: string;
  readonly components: readonly ScoreComponent[];
};

function themeHref(themeKey: string | null | undefined) {
  return themeKey ? (`/themes/${encodeURIComponent(themeKey)}` as Route) : null;
}

export function RecommendationMacroFlowPanel({ symbol, components }: RecommendationMacroFlowPanelProps) {
  if (components.length === 0) {
    return null;
  }

  return (
    <section className="bento-card reveal delay-1" id="recommendation-macro-flow" aria-label="상위 흐름 전파 경로">
      <div style={{ marginBottom: "22px" }}>
        <span className="metric-sub">상위 흐름 전파 경로</span>
        <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>시장·테마 뉴스가 {symbol} 점수에 들어간 방식</h2>
        <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "820px" }}>
          종목을 직접 언급하지 않은 뉴스가 테마와 종목 노출도에 의해 이 추천과 연결된 경로다.
          전체 전파 근거 수와 아래 최근 사례 수는 다를 수 있다. 이 근거는 주문 결정이 아니라 점수 입력으로만 쓰인다.
        </p>
      </div>

      <div className="bento-list">
        {components.map((component) => {
          const rows = macroFlowRows(component);
          return (
            <div className="bento-list-item" key={component.component} style={{ alignItems: "flex-start", flexDirection: "column" }}>
              <div style={{ width: "100%", display: "flex", justifyContent: "space-between", gap: "16px", flexWrap: "wrap" }}>
                <div>
                  <span className="metric-sub">{scoreComponentLabel(component.component)}</span>
                  <strong>{formatPanelPercent(component.value)} · 현재 반영 비중 {formatPanelPercent(component.weight)}</strong>
                </div>
                <span style={{ color: "var(--text-secondary)" }}>
                  전체 전파 근거 {component.provenance?.evidence?.propagated_impact_count ?? rows.length}개 · 최근 표시 {rows.length}개
                </span>
              </div>

              <div className="relationship-list" aria-label={`${symbol} 상위 흐름 전파 근거`}>
                {rows.map((flow) => {
                  const href = themeHref(flow.theme_key);
                  return (
                    <div className="relationship-chip" key={`${component.component}-${flow.event_id}-${flow.theme_key}`}>
                      <span>{koCode(flow.theme_key)}</span>
                      <NewsTitleBlock
                        compact
                        title={flow.title}
                        koreanTitle={flow.korean_title}
                        koreanSummary={flow.korean_summary}
                        translationConfidence={flow.translation_confidence}
                        symbol={symbol}
                        themeKey={flow.theme_key}
                        impactDirection={flow.impact_direction}
                        impactScore={flow.impact_strength}
                      />
                      <small>
                        {koCode(flow.impact_direction)} · 강도 {formatScoreMetricValue(flow.impact_strength)} · 자료 신뢰도 {formatScoreMetricValue(flow.confidence)}
                      </small>
                      <small>
                        노출도 {formatScoreMetricValue(flow.exposure_weight)} · 발생 {flow.event_at}
                      </small>
                      {href ? <Link href={href}>테마 흐름 보기</Link> : null}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
