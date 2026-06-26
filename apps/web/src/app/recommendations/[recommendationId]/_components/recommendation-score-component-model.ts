import { koCode } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";

import { userFacingRecommendationText } from "./recommendation-panel-format";

export type ScoreComponent = RecommendationDetailData["score_components"][number];

const SCORE_COMPONENT_LABELS: Record<string, string> = {
  macro_regime_score: "거시 환경",
  domain_cycle_score: "산업·도메인 사이클",
  theme_cycle_score: "테마 사이클",
  instrument_cycle_score: "종목 자체 사이클",
  cycle_conflict_penalty: "사이클 충돌 감점",
  macro_flow_score: "상위 흐름 전파",
  fundamental_quality_score: "재무 품질",
  valuation_margin_score: "밸류에이션 안전마진",
  peer_relative_score: "동종업계 비교",
  balance_sheet_risk_penalty: "재무 안정성 리스크",
  thesis_consistency_score: "투자 논리 일치도",
  broker_execution_readiness_score: "브로커 실행 가능성",
  broker_liquidity_warning: "브로커 유동성·주의사항",
  broker_price_basis_risk: "브로커 가격 기준 차이",
};

export const CYCLE_STACK_COMPONENT_ORDER = [
  "macro_regime_score",
  "domain_cycle_score",
  "theme_cycle_score",
  "instrument_cycle_score",
  "cycle_conflict_penalty",
] as const;

export const CYCLE_STACK_COMPONENT_META: Record<string, { readonly step: string; readonly body: string }> = {
  macro_regime_score: {
    step: "1. 거시",
    body: "금리, 물가, 유동성, 성장 같은 최상위 환경이 이 종목 분석의 배경으로 연결된다.",
  },
  domain_cycle_score: {
    step: "2. 도메인",
    body: "기술, 에너지, 금융처럼 더 넓은 사업 영역의 사이클이 종목 신호와 같은 방향인지 정리한다.",
  },
  theme_cycle_score: {
    step: "3. 테마",
    body: "AI 반도체, 양자컴퓨팅, 에너지 지정학 같은 구체 테마 흐름의 연결 여부를 분리한다.",
  },
  instrument_cycle_score: {
    step: "4. 종목",
    body: "종목 자체의 가격·사이클 상태가 상위 흐름과 충돌하는지 비교한다.",
  },
  cycle_conflict_penalty: {
    step: "5. 충돌",
    body: "상위 흐름과 종목 상태가 충돌하면 추천 점수에 감점 항목으로 남긴다.",
  },
};

export const FUNDAMENTAL_COMPONENT_META: Record<string, { readonly lens: string; readonly title: string; readonly body: string }> = {
  fundamental_quality_score: {
    lens: "재무 품질",
    title: "매출·마진·현금흐름이 투자 논리를 받치는가",
    body: "정규화 재무지표와 현금흐름 품질을 바탕으로 기업 자체 체력이 충분한지 보는 항목이다.",
  },
  valuation_margin_score: {
    lens: "밸류에이션",
    title: "현재 가격에 안전마진이 있는가",
    body: "간이 현금흐름 평가, 상대 배수, 시나리오 범위로 가격 부담을 분리한다.",
  },
  peer_relative_score: {
    lens: "피어 비교",
    title: "같은 그룹 안에서 상대적으로 우수한가",
    body: "같은 산업·테마 비교군에서 성장성, 수익성, 안정성 위치가 어느 정도인지 보는 항목이다.",
  },
  balance_sheet_risk_penalty: {
    lens: "재무 안정성",
    title: "부채와 재무 압력이 과하지 않은가",
    body: "레버리지와 재무 부담이 중장기 보유 리스크를 키우는지 분리한다.",
  },
  thesis_consistency_score: {
    lens: "투자 논리",
    title: "추천과 투자 논리가 서로 맞는가",
    body: "활성 투자 논리, 무효화 조건, 보유 상태 맥락이 추천 방향과 충돌하는지 정리한다.",
  },
};

export const BROKER_COMPONENT_META: Record<string, { readonly lens: string; readonly title: string; readonly body: string }> = {
  broker_execution_readiness_score: {
    lens: "실행 가능성",
    title: "토스증권 화면에서 체결·호가 근거가 보이는가",
    body: "관심 종목의 최신 체결가, 매수·매도 호가, 계좌 읽기 결과로 실행 현실을 구분한다.",
  },
  broker_liquidity_warning: {
    lens: "주의사항",
    title: "토스증권 기준 주의 종목이나 유동성 경고가 있는가",
    body: "브로커가 제공하는 주의 표시와 호가 데이터 부족 여부를 표시한다. 낮은 값은 주문 전 보강이 필요하다는 뜻이다.",
  },
  broker_price_basis_risk: {
    lens: "가격 기준",
    title: "분석 기준 가격과 토스증권 가격 차이를 설명할 수 있는가",
    body: "장중 미완성 일봉, 가격 기준 차이, 누락 여부를 분리한다. 차이는 곧 오류가 아니라 해석 항목이다.",
  },
};

const CYCLE_STACK_COMPONENT_SET = new Set<string>(CYCLE_STACK_COMPONENT_ORDER);
const FUNDAMENTAL_COMPONENT_SET = new Set<string>(Object.keys(FUNDAMENTAL_COMPONENT_META));
const BROKER_COMPONENT_SET = new Set<string>(Object.keys(BROKER_COMPONENT_META));

export function scoreComponentLabel(componentName: string) {
  return SCORE_COMPONENT_LABELS[componentName] ?? userFacingRecommendationText(componentName);
}

export function isZeroWeight(value: number) {
  return Math.abs(Number(value)) < 0.000001;
}

export function macroFlowRows(component: ScoreComponent) {
  if (component.provenance?.source_type !== "macro_flow_propagation") {
    return [];
  }
  return component.provenance.evidence?.recent_flows ?? [];
}

export function cycleStackNodeCode(component: ScoreComponent) {
  const explicitNode = component.provenance?.evidence?.cycle_stack_node_code;
  if (explicitNode) {
    return explicitNode;
  }
  const explanation = component.provenance?.evidence?.cycle_stack_explanation;
  const match = explanation?.match(/Selected recommendation node: ([A-Z0-9_]+)/);
  return match?.[1] ?? null;
}

function cycleStackLevel(component: ScoreComponent) {
  return component.provenance?.evidence?.cycle_stack_level ?? CYCLE_STACK_COMPONENT_META[component.component]?.step ?? "사이클";
}

function isCycleStackComponent(component: ScoreComponent) {
  return component.provenance?.source_type === "cycle_stack_context" || CYCLE_STACK_COMPONENT_SET.has(component.component);
}

function cycleStackOrder(componentName: string) {
  const index = CYCLE_STACK_COMPONENT_ORDER.findIndex((item) => item === componentName);
  return index === -1 ? CYCLE_STACK_COMPONENT_ORDER.length : index;
}

export function cycleStackComponents(components: readonly ScoreComponent[]) {
  return components
    .filter(isCycleStackComponent)
    .sort((left, right) => cycleStackOrder(left.component) - cycleStackOrder(right.component));
}

function isFundamentalComponent(component: ScoreComponent) {
  return component.provenance?.source_type === "fundamental_context" || FUNDAMENTAL_COMPONENT_SET.has(component.component);
}

function fundamentalOrder(componentName: string) {
  const index = Object.keys(FUNDAMENTAL_COMPONENT_META).findIndex((item) => item === componentName);
  return index === -1 ? Object.keys(FUNDAMENTAL_COMPONENT_META).length : index;
}

export function fundamentalComponents(components: readonly ScoreComponent[]) {
  return components
    .filter(isFundamentalComponent)
    .sort((left, right) => fundamentalOrder(left.component) - fundamentalOrder(right.component));
}

function isBrokerComponent(component: ScoreComponent) {
  return component.provenance?.source_type === "broker_reality_context" || BROKER_COMPONENT_SET.has(component.component);
}

function brokerOrder(componentName: string) {
  const index = Object.keys(BROKER_COMPONENT_META).findIndex((item) => item === componentName);
  return index === -1 ? Object.keys(BROKER_COMPONENT_META).length : index;
}

export function brokerComponents(components: readonly ScoreComponent[]) {
  return components
    .filter(isBrokerComponent)
    .sort((left, right) => brokerOrder(left.component) - brokerOrder(right.component));
}

export function formatScoreMetricValue(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "아직 계산되지 않음";
  }
  if (Math.abs(value) < 1) {
    return `${Math.round(value * 1000) / 10}%`;
  }
  return value.toLocaleString("ko-KR", { maximumFractionDigits: 4 });
}

export function provenanceDetail(component: ScoreComponent) {
  const provenance = component.provenance;
  if (!provenance) {
    return "아직 이 점수의 입력 출처 요약이 붙지 않았다.";
  }
  if (provenance.source_type === "cycle_stack_context") {
    const nodeCode = cycleStackNodeCode(component);
    const nodeText = nodeCode ? koCode(nodeCode) : "기준 노드 미기록";
    const meta = CYCLE_STACK_COMPONENT_META[component.component];
    return `${meta?.step ?? koCode(cycleStackLevel(component))}: 기준 노드 ${nodeText}. ${meta?.body ?? "계층형 사이클 점수의 출처를 설명한다."}`;
  }
  if (provenance.source_type === "fundamental_context") {
    const meta = FUNDAMENTAL_COMPONENT_META[component.component];
    const status = isZeroWeight(component.weight) ? "현재 최종 추천 점수에는 반영하지 않는 검증 항목" : "최종 추천 점수에 반영되는 항목";
    return `${meta?.lens ?? "기업 분석"}: ${meta?.body ?? userFacingRecommendationText(provenance.description ?? provenance.label)} ${status}.`;
  }
  if (provenance.source_type === "broker_reality_context") {
    const meta = BROKER_COMPONENT_META[component.component];
    const status = isZeroWeight(component.weight) ? "현재 최종 추천 점수에는 반영하지 않는 실행 확인 항목" : "최종 추천 점수에 반영되는 실행 확인 항목";
    return `${meta?.lens ?? "브로커 현실"}: ${meta?.body ?? userFacingRecommendationText(provenance.description ?? provenance.label)} ${status}.`;
  }
  return userFacingRecommendationText(provenance.description ?? provenance.label ?? provenance.source_type);
}
