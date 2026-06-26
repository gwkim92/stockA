import { koCode } from "@/lib/korean-labels";

import {
  BROKER_COMPONENT_META,
  CYCLE_STACK_COMPONENT_META,
  FUNDAMENTAL_COMPONENT_META,
  cycleStackNodeCode,
  isZeroWeight,
  provenanceDetail,
  scoreComponentLabel,
  type ScoreComponent,
} from "./recommendation-score-component-model";
import { formatPanelPercent, userFacingRecommendationText } from "./recommendation-panel-format";

type RecommendationScoreComponentPanelsProps = {
  readonly symbol: string;
  readonly isCompany: boolean;
  readonly cycleStack: readonly ScoreComponent[];
  readonly fundamentalStack: readonly ScoreComponent[];
  readonly brokerStack: readonly ScoreComponent[];
};

function componentWeightLabel(component: ScoreComponent, zeroWeightLabel: string) {
  if (isZeroWeight(component.weight)) {
    return zeroWeightLabel;
  }
  return `현재 반영 비중 ${formatPanelPercent(component.weight)}`;
}

export function RecommendationScoreComponentPanels({
  symbol,
  isCompany,
  cycleStack,
  fundamentalStack,
  brokerStack,
}: RecommendationScoreComponentPanelsProps) {
  return (
    <>
      {cycleStack.length > 0 ? (
        <section className="bento-card reveal delay-1" id="recommendation-cycle-stack" aria-label="계층형 사이클 추천 경로">
          <div style={{ marginBottom: "22px" }}>
            <span className="metric-sub">계층형 사이클 경로</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>왜 {symbol}이 지금 추천 신호로 올라왔는가</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "860px" }}>
              추천 점수를 한 덩어리로 보지 않고 거시 환경, 도메인, 테마, 종목 자체 상태, 충돌 감점을 분리해 보여준다.
              현재 반영 전 항목은 결과를 흔들지 않기 위한 설명·검증용 항목이며, 품질 검증 후 별도 승인으로만 반영한다.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "12px" }}>
            {cycleStack.map((component) => {
              const meta = CYCLE_STACK_COMPONENT_META[component.component];
              const nodeCode = cycleStackNodeCode(component);
              return (
                <article
                  className="detail-path-card"
                  key={`cycle-stack-${component.component}`}
                  style={{
                    background:
                      component.component === "cycle_conflict_penalty"
                        ? "linear-gradient(180deg, rgba(255,255,255,0.86), rgba(168,59,52,0.08))"
                        : "linear-gradient(180deg, rgba(251,250,246,0.95), rgba(38,92,128,0.08))",
                  }}
                >
                  <span>{meta?.step ?? koCode(component.component)}</span>
                  <strong>{scoreComponentLabel(component.component)}</strong>
                  <p>{meta?.body ?? "계층형 사이클 근거를 설명하는 점수 항목이다."}</p>
                  <p style={{ marginTop: "8px", color: "var(--text-secondary)", fontSize: "0.78rem", fontWeight: 850 }}>
                    {nodeCode ? `기준 노드: ${koCode(nodeCode)}` : "기준 노드 미기록"}
                  </p>
                  <div style={{ marginTop: "14px", display: "grid", gap: "6px", color: "var(--text-secondary)", fontSize: "0.8rem", fontWeight: 800 }}>
                    <span>점수 {formatPanelPercent(component.value)}</span>
                    <span>현재 반영 비중 {formatPanelPercent(component.weight)}</span>
                    <span>{isZeroWeight(component.weight) ? "현재 최종 점수 영향 없음" : "최종 점수에 반영됨"}</span>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      ) : null}

      {isCompany && fundamentalStack.length > 0 ? (
        <section className="bento-card reveal delay-1" aria-label="재무와 밸류에이션 추천 근거">
          <div style={{ marginBottom: "22px" }}>
            <span className="metric-sub">재무·밸류에이션 근거</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>뉴스가 아니라 기업 자체가 받쳐주는가</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "900px" }}>
              이 영역은 프로 애널리스트식 분석 축이다. 현재는 성과 표본이 부족하므로 최종 추천 점수에는 반영하지 않고,
              재무 품질과 가격 매력도가 추천 논리를 보강하거나 반박하는지 확인하는 근거로만 쓴다.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: "14px" }}>
            {fundamentalStack.map((component) => {
              const meta = FUNDAMENTAL_COMPONENT_META[component.component];
              return (
                <article
                  className="detail-path-card"
                  key={`fundamental-${component.component}`}
                  style={{ background: "linear-gradient(180deg, rgba(251,250,246,0.96), rgba(96,70,35,0.08))", minHeight: "220px" }}
                >
                  <span>{meta?.lens ?? "기업 분석"}</span>
                  <strong>{meta?.title ?? scoreComponentLabel(component.component)}</strong>
                  <p>{meta?.body ?? provenanceDetail(component)}</p>
                  <div style={{ marginTop: "14px", display: "grid", gap: "6px", color: "var(--text-secondary)", fontSize: "0.8rem", fontWeight: 800 }}>
                    <span>분석 점수 {formatPanelPercent(component.value)}</span>
                    <span>{componentWeightLabel(component, "최종 추천 점수에는 아직 미반영")}</span>
                    <span>{component.provenance?.label ? userFacingRecommendationText(component.provenance.label) : "기업 분석 근거"}</span>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      ) : null}

      {brokerStack.length > 0 ? (
        <section className="bento-card reveal delay-1" aria-label="토스증권 브로커 현실 확인">
          <div style={{ marginBottom: "22px" }}>
            <span className="metric-sub">토스증권 실행 현실</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>이 추천을 실제 계좌에서 확인할 수 있는가</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "900px" }}>
              토스증권 읽기 전용 데이터의 호가, 체결가, 주의 표시, 가격 기준 차이를 별도로 표시합니다.
              이 항목은 현재 최종 추천 점수와 순위를 바꾸지 않고, 주문 전 현실 점검 근거로만 표시한다.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: "14px" }}>
            {brokerStack.map((component) => {
              const meta = BROKER_COMPONENT_META[component.component];
              return (
                <article
                  className="detail-path-card"
                  key={`broker-${component.component}`}
                  style={{ background: "linear-gradient(180deg, rgba(251,250,246,0.96), rgba(31,97,85,0.10))", minHeight: "220px" }}
                >
                  <span>{meta?.lens ?? "브로커 확인"}</span>
                  <strong>{meta?.title ?? scoreComponentLabel(component.component)}</strong>
                  <p>{meta?.body ?? provenanceDetail(component)}</p>
                  <div style={{ marginTop: "14px", display: "grid", gap: "6px", color: "var(--text-secondary)", fontSize: "0.8rem", fontWeight: 800 }}>
                    <span>확인 점수 {formatPanelPercent(component.value)}</span>
                    <span>{componentWeightLabel(component, "최종 추천 점수에는 미반영")}</span>
                    <span>{component.provenance?.label ? userFacingRecommendationText(component.provenance.label) : "토스증권 브로커 데이터"}</span>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      ) : null}
    </>
  );
}
