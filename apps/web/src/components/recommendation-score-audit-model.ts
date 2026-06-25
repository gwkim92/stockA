import type { AuditMetadataItem } from "./audit-metadata";
import { koCode } from "../lib/korean-labels";
import { formatPercent, recommendationCopy } from "../lib/presentation";
import type { RecommendationDetailData } from "../lib/types";

export type ScoreComponent = RecommendationDetailData["score_components"][number];

export type RecommendationScoreAuditData = Pick<
  RecommendationDetailData,
  "linked_thesis_id" | "outcome" | "score" | "score_components" | "symbol"
>;

const SCORE_COMPONENT_LABELS: Readonly<Record<string, string>> = {
  balance_sheet_risk_penalty: "재무 안정성 리스크",
  broker_execution_readiness_score: "브로커 실행 가능성",
  broker_liquidity_warning: "브로커 유동성·주의사항",
  broker_price_basis_risk: "브로커 가격 기준 차이",
  cycle_conflict_penalty: "사이클 충돌 감점",
  domain_cycle_score: "산업·도메인 사이클",
  fundamental_quality_score: "재무 품질",
  instrument_cycle_score: "종목 자체 사이클",
  macro_flow_score: "상위 흐름 전파",
  macro_regime_score: "거시 환경",
  peer_relative_score: "동종업계 비교",
  theme_cycle_score: "테마 사이클",
  thesis_consistency_score: "투자 논리 일치도",
  valuation_margin_score: "밸류에이션 안전마진",
};

const SOURCE_TYPE_LABELS: Readonly<Record<string, string>> = {
  broker_reality_context: "토스증권 브로커 현실",
  cycle_stack_context: "계층형 사이클",
  event_or_ai_evidence: "뉴스·투자 근거",
  fundamental_context: "재무·밸류에이션 분석",
  macro_flow_propagation: "상위 흐름 전파",
  market_feature: "가격·거래 데이터",
  strategy_universe_rank: "전략 종목군 순위",
};

export function investorText(value: string | number | boolean | null | undefined): string {
  return recommendationCopy(value);
}

export function scoreComponentLabel(componentName: string): string {
  return SCORE_COMPONENT_LABELS[componentName] ?? investorText(componentName);
}

export function sourceTypeLabel(sourceType: string | null | undefined): string {
  if (!sourceType) {
    return "근거 출처 미기록";
  }
  return SOURCE_TYPE_LABELS[sourceType] ?? investorText(sourceType);
}

export function isZeroWeight(value: number): boolean {
  return Math.abs(Number(value)) < 0.000001;
}

export function formatMetricValue(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  if (Math.abs(value) < 1) {
    return formatPercent(value);
  }
  return value.toLocaleString("ko-KR", { maximumFractionDigits: 4 });
}

export function componentTone(component: ScoreComponent): string {
  if (isZeroWeight(component.weight)) {
    return "tone-watch";
  }
  if (component.value < 0) {
    return "tone-blocked";
  }
  return "tone-ready";
}

export function outcomeMeasured(data: RecommendationScoreAuditData): boolean {
  return data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
}

export function outcomeTone(data: RecommendationScoreAuditData): string {
  if (!outcomeMeasured(data)) {
    return "성과 측정 대기";
  }
  return data.outcome.alpha >= 0 ? "성과 우위" : "성과 열위";
}

export function scoreAuditSummary(data: RecommendationScoreAuditData) {
  const activeComponents = data.score_components.filter((component) => !isZeroWeight(component.weight)).length;
  const explanatoryComponents = data.score_components.length - activeComponents;
  return {
    activeComponents,
    explanatoryComponents,
    measured: outcomeMeasured(data),
    totalComponents: data.score_components.length,
  };
}

export function evidenceHref(evidenceId: string, symbol: string): string | null {
  if (evidenceId.startsWith("ai-evidence-")) {
    return `/ai-evidence/${evidenceId}`;
  }
  if (evidenceId.startsWith("event-") || evidenceId.startsWith("sec-event-")) {
    return `/events?symbol=${encodeURIComponent(symbol)}`;
  }
  if (evidenceId.startsWith("macro-flow-") || evidenceId.startsWith("fundamental-") || evidenceId.startsWith("broker-reality-")) {
    return `/stocks/${encodeURIComponent(symbol)}`;
  }
  return null;
}

export function evidenceLinkLabel(evidenceId: string): string {
  if (evidenceId.startsWith("ai-evidence-")) {
    return "투자 근거 열기";
  }
  if (evidenceId.startsWith("event-") || evidenceId.startsWith("sec-event-")) {
    return "수집 뉴스 열기";
  }
  if (evidenceId.startsWith("broker-reality-")) {
    return "토스증권 데이터 보기";
  }
  return "근거 화면 열기";
}

export function componentDetail(component: ScoreComponent): string {
  const provenance = component.provenance;
  if (!provenance) {
    return "아직 이 점수의 입력 출처 요약이 붙지 않았다.";
  }
  if (provenance.source_type === "market_feature") {
    const featureName = provenance.feature_code ? investorText(provenance.feature_code) : investorText(provenance.feature_name ?? "가격 지표");
    return `${featureName}: 원값 ${formatMetricValue(provenance.feature_value)}, 표준화 점수 ${formatMetricValue(provenance.zscore)}.`;
  }
  if (provenance.source_type === "strategy_universe_rank") {
    const rank = provenance.rank_position ? `전략 종목군 ${provenance.rank_position}위` : "전략 종목군 순위";
    const observations = provenance.observation_count ? `가격 관측치 ${provenance.observation_count}개` : "저장된 가격 관측치";
    return `${rank}와 ${observations}를 점수 입력으로 사용했다.`;
  }
  if (provenance.source_type === "macro_flow_propagation") {
    const count = provenance.evidence?.propagated_impact_count ?? 0;
    return `시장·테마 흐름 ${count}개가 종목 노출도를 통해 연결된 근거다.`;
  }
  return investorText(provenance.label);
}

export function componentBadges(component: ScoreComponent): readonly string[] {
  const provenance = component.provenance;
  if (!provenance) {
    return ["출처 요약 대기"];
  }
  return [
    sourceTypeLabel(provenance.source_type),
    isZeroWeight(component.weight) ? "참고 전용" : "점수 반영",
    provenance.latest_trade_date ? `최근 가격일 ${provenance.latest_trade_date}` : null,
  ].filter((badge): badge is string => badge !== null);
}

export function componentMetadata(component: ScoreComponent): AuditMetadataItem[] {
  const provenance = component.provenance;
  const evidence = provenance?.evidence;
  return [
    { label: "점수 항목", value: scoreComponentLabel(component.component) },
    { label: "근거 연결 번호", value: component.evidence_id },
    { label: "근거 종류", value: sourceTypeLabel(provenance?.source_type) },
    { label: "근거 설명", value: investorText(provenance?.label) },
    { label: "가격 지표", value: provenance?.feature_code ? investorText(provenance.feature_code) : null },
    { label: "가격 지표 이름", value: provenance?.feature_name ? investorText(provenance.feature_name) : null },
    { label: "원값", value: provenance ? formatMetricValue(provenance.feature_value) : null },
    { label: "표준화 점수", value: provenance ? formatMetricValue(provenance.zscore) : null },
    { label: "기준일", value: provenance?.as_of_date },
    { label: "계산 기록", value: provenance?.source_run_id ? "있음" : null },
    { label: "종목군 계산 기록", value: provenance?.universe_batch_id ? "있음" : null },
    { label: "가격 계산 기준", value: evidence?.feature_set_version ? "기록 있음" : null },
    { label: "종목군 순위", value: provenance?.rank_position },
    { label: "종목군 전체 수", value: provenance?.universe_member_count },
    { label: "선정 점수", value: provenance ? formatMetricValue(provenance.selection_score) : null },
    { label: "관측치 수", value: provenance?.observation_count ?? provenance?.evidence?.observation_count },
    { label: "첫 가격일", value: evidence?.first_trade_date },
    { label: "최근 가격일", value: provenance?.latest_trade_date ?? provenance?.evidence?.latest_trade_date },
    { label: "사이클 계층", value: evidence?.cycle_stack_level ? investorText(evidence.cycle_stack_level) : null },
    { label: "선택 사이클 노드", value: evidence?.cycle_stack_node_code ? koCode(evidence.cycle_stack_node_code) : null },
    { label: "사이클 설명", value: evidence?.cycle_stack_explanation ? investorText(evidence.cycle_stack_explanation) : null },
    { label: "적용 메모", value: evidence?.cycle_stack_note ? investorText(evidence.cycle_stack_note) : null },
    { label: "기업 분석 항목", value: evidence?.fundamental_component_name ? scoreComponentLabel(evidence.fundamental_component_name) : null },
    { label: "기업 분석 설명", value: evidence?.fundamental_explanation ? investorText(evidence.fundamental_explanation) : null },
    { label: "기업 분석 메모", value: evidence?.fundamental_note ? investorText(evidence.fundamental_note) : null },
    { label: "브로커 확인 항목", value: evidence?.broker_component_name ? scoreComponentLabel(evidence.broker_component_name) : null },
    { label: "브로커 확인 점수", value: formatMetricValue(evidence?.broker_component_score) },
    { label: "브로커 확인 비중", value: evidence?.broker_component_weight === null || evidence?.broker_component_weight === undefined ? null : formatPercent(evidence.broker_component_weight) },
    { label: "브로커 확인 설명", value: evidence?.broker_explanation ? investorText(evidence.broker_explanation) : null },
    { label: "브로커 확인 메모", value: evidence?.broker_note ? investorText(evidence.broker_note) : null },
    { label: "전파 근거 수", value: evidence?.propagated_impact_count },
    { label: "선정 규칙", value: provenance?.selection_rule ? investorText(provenance.selection_rule) : null },
    { label: "편입 사유", value: provenance?.inclusion_reason ? investorText(provenance.inclusion_reason) : null },
  ];
}
