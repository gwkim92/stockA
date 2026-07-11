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
import styles from "./RecommendationScoreComponentPanels.module.css";

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
        <section className="bento-card" id="recommendation-cycle-stack" aria-label="계층형 사이클 추천 경로">
          <div className={styles.head}>
            <span className="metric-sub">계층형 사이클 경로</span>
            <h2 className={styles.title}>왜 {symbol}이 지금 추천 신호로 올라왔는가</h2>
            <p className={`${styles.copy} ${styles.copyNarrow}`}>
              추천 점수를 한 덩어리로 보지 않고 거시 환경, 도메인, 테마, 종목 자체 상태, 충돌 감점을 분리해 보여준다.
              현재 반영 전 항목은 결과를 흔들지 않기 위한 설명·검증용 항목이며, 품질 검증 후 별도 승인으로만 반영한다.
            </p>
          </div>

          <div className={`${styles.grid} ${styles.cycleGrid}`}>
            {cycleStack.map((component) => {
              const meta = CYCLE_STACK_COMPONENT_META[component.component];
              const nodeCode = cycleStackNodeCode(component);
              return (
                <article
                  className={`detail-path-card ${
                    component.component === "cycle_conflict_penalty" ? styles.cyclePenaltyCard : styles.cycleCard
                  }`}
                  key={`cycle-stack-${component.component}`}
                >
                  <span>{meta?.step ?? koCode(component.component)}</span>
                  <strong>{scoreComponentLabel(component.component)}</strong>
                  <p>{meta?.body ?? "계층형 사이클 근거를 설명하는 점수 항목이다."}</p>
                  <p className={styles.node}>
                    {nodeCode ? `기준 노드: ${koCode(nodeCode)}` : "기준 노드 미기록"}
                  </p>
                  <div className={styles.facts}>
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
        <section className="bento-card" aria-label="재무와 밸류에이션 추천 근거">
          <div className={styles.head}>
            <span className="metric-sub">재무·밸류에이션 근거</span>
            <h2 className={styles.title}>뉴스가 아니라 <span className="keep-phrase">기업 자체</span>가 받쳐주는가</h2>
            <p className={styles.copy}>
              이 영역은 프로 애널리스트식 분석 축이다. 현재는 성과 표본이 부족하므로 최종 추천 점수에는 반영하지 않고,
              재무 품질과 가격 매력도가 추천 논리를 보강하거나 반박하는지 확인하는 근거로만 쓴다.
            </p>
          </div>

          <div className={styles.grid}>
            {fundamentalStack.map((component) => {
              const meta = FUNDAMENTAL_COMPONENT_META[component.component];
              return (
                <article
                  className={`detail-path-card ${styles.deepCard} ${styles.fundamentalCard}`}
                  key={`fundamental-${component.component}`}
                >
                  <span>{meta?.lens ?? "기업 분석"}</span>
                  <strong>{meta?.title ?? scoreComponentLabel(component.component)}</strong>
                  <p>{meta?.body ?? provenanceDetail(component)}</p>
                  <div className={styles.facts}>
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
        <section className="bento-card" aria-label="토스증권 브로커 현실 확인">
          <div className={styles.head}>
            <span className="metric-sub">토스증권 실행 현실</span>
            <h2 className={styles.title}>이 추천을 실제 계좌에서 확인할 수 있는가</h2>
            <p className={styles.copy}>
              토스증권 읽기 전용 데이터의 호가, 체결가, 주의 표시, 가격 기준 차이를 별도로 표시한다.
              이 항목은 현재 최종 추천 점수와 순위를 바꾸지 않고, 주문 전 현실 점검 근거로만 표시한다.
            </p>
          </div>

          <div className={styles.grid}>
            {brokerStack.map((component) => {
              const meta = BROKER_COMPONENT_META[component.component];
              return (
                <article
                  className={`detail-path-card ${styles.deepCard} ${styles.brokerCard}`}
                  key={`broker-${component.component}`}
                >
                  <span>{meta?.lens ?? "브로커 확인"}</span>
                  <strong>{meta?.title ?? scoreComponentLabel(component.component)}</strong>
                  <p>{meta?.body ?? provenanceDetail(component)}</p>
                  <div className={styles.facts}>
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
