import Link from "next/link";
import type { Route } from "next";
import { Fragment } from "react";
import { AuditMetadata, type AuditMetadataItem } from "@/components/audit-metadata";
import { NewsTitleBlock } from "@/components/news-title-block";
import { ProfessionalResearchFlow, type ResearchFlowStep } from "@/components/professional-research-flow";
import { ValuationTargetRangeCard } from "@/components/valuation-target-range-card";
import { getRecommendationDetail } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "추천 상세" };

type RecommendationPageProps = {
  params: Promise<{ recommendationId: string }>;
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

type ScoreComponent = RecommendationDetailData["score_components"][number];
type IndustryCompetitivePosition = NonNullable<RecommendationDetailData["industry_competitive_position"]>;
type FinancialStatementModel = RecommendationDetailData["financial_statement_model"];
type FinancialMetricSnapshot = FinancialStatementModel["metrics"][number];
type FundInstrumentAnalysis = RecommendationDetailData["fund_instrument_analysis"];
type ProfessionalEvidenceAudit = RecommendationDetailData["professional_evidence_audit"];
type RecommendationMarketCorrelation = RecommendationDetailData["market_correlations"][number];
type RecommendationQualityDecision = {
  status: string;
  tone: "risk-low" | "risk-medium" | "risk-high";
  summary: string;
};
type RecommendationFocusItem = {
  label: string;
  title: string;
  body: string;
  metric: string;
  href: Route | `#${string}`;
  hrefLabel: string;
  tone: "ready" | "watch" | "blocked";
};

const USER_FACING_TERM_REPLACEMENTS: Array<[string, string]> = [
  ["DCF-lite", "간이 현금흐름 평가"],
  ["paper validation", "가상 매매 검증"],
  ["Paper validation", "가상 매매 검증"],
  ["페이퍼 검증", "가상 매매 검증"],
  ["broker submit", "증권사 주문 제출"],
  ["broker flow", "실거래 연결"],
  ["증권사 연결 경계", "증권사 연결 상태"],
  ["source blocker", "원천 근거 부족"],
  ["source data", "원천 데이터"],
  ["source_run_id", "실행 기록"],
  ["read_only_no_order", "읽기 전용, 실거래 주문 차단"],
  ["source_data_blocked", "원천 근거 부족으로 차단"],
  ["macro-flow", "상위 흐름"],
  ["Macro-flow", "상위 흐름"],
  ["sec_companyfacts_missing_us_gaap_facts", "SEC 표준 재무 항목 없음"],
  ["ipo_prospectus_without_standard_periodic_financials", "정기 재무제표 전 공시만 존재"],
  ["fund_company_financial_model_not_applicable", "ETF·펀드라 기업 재무 모델 비적용"],
  ["accumulate_candidate", "분할 매수 신호"],
  ["base case", "기준 시나리오"],
  ["upside case", "상승 시나리오"],
  ["downside case", "하락 시나리오"],
  ["margin of safety", "안전마진"],
  ["Margin of safety", "안전마진"],
  ["confidence", "신뢰도"],
  ["valuation_snapshot", "밸류에이션 스냅샷"],
  ["valuation_margin_score", "밸류에이션 안전마진"],
  ["total_score", "총점"],
  ["recommendation_id", "추천 ID"],
  ["AI 근거", "AI 해석"],
  ["주문 경계", "실거래 상태"],
  ["거래 경계", "실거래 상태"],
  ["추천 총점", "최종 추천 점수"],
  ["총점 반영", "최종 점수 반영"],
  ["총점 미반영", "최종 점수 미반영"],
  ["점수 가중치", "점수 반영 비중"],
  ["가중치", "반영 비중"],
  ["financial statement model", "재무제표 모델"],
  ["valuation target range", "밸류에이션 목표가 범위"],
  ["industry competitive position", "산업 경쟁 위치"],
  ["equity research artifact", "AI 기업 리서치"],
  ["SEC/companyfacts", "SEC 표준 재무 원천"],
  ["SEC companyfacts", "SEC 표준 재무 원천"],
  ["segment", "사업부"],
  ["footnote", "주석"],
  ["guidance", "가이던스"],
  ["fundamental 구성요소", "재무·밸류에이션 항목"],
  ["투자 논리 lifecycle", "투자 논리 생애주기"],
  ["source event/AI evidence", "원천 이벤트/AI 해석"],
  [["페", "이퍼"].join(""), "가상 매매"],
];

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
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  market_feature: "가격·거래 데이터",
  strategy_universe_rank: "전략 종목군 순위",
  event_or_ai_evidence: "뉴스·AI 해석",
  macro_flow_propagation: "상위 흐름 전파",
  cycle_stack_context: "계층형 사이클",
  fundamental_context: "재무·밸류에이션 분석",
};

function userFacingRecommendationText(value: string | number | boolean | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  if (typeof value === "number") {
    return value.toLocaleString("ko-KR");
  }
  if (typeof value === "boolean") {
    return value ? "예" : "아니오";
  }
  let text = koLabel(koCode(value));
  for (const [from, to] of USER_FACING_TERM_REPLACEMENTS) {
    text = text.replaceAll(from, to);
  }
  return text;
}

function scoreComponentLabel(componentName: string) {
  return SCORE_COMPONENT_LABELS[componentName] ?? userFacingRecommendationText(componentName);
}

function sourceTypeLabel(sourceType: string | null | undefined) {
  if (!sourceType) {
    return "입력 출처 미기록";
  }
  return SOURCE_TYPE_LABELS[sourceType] ?? userFacingRecommendationText(sourceType);
}

function orderBoundaryLabel(value: string | null | undefined) {
  if (!value) {
    return "실거래 상태 미기록";
  }
  if (value === "read_only_no_order") {
    return "읽기 전용, 실거래 주문 차단";
  }
  return userFacingRecommendationText(value);
}

function isZeroWeight(value: number) {
  return Math.abs(Number(value)) < 0.000001;
}

const CYCLE_STACK_COMPONENT_ORDER = [
  "macro_regime_score",
  "domain_cycle_score",
  "theme_cycle_score",
  "instrument_cycle_score",
  "cycle_conflict_penalty",
] as const;

const CYCLE_STACK_COMPONENT_META: Record<string, { step: string; body: string }> = {
  macro_regime_score: {
    step: "1. 거시",
    body: "금리, 물가, 유동성, 성장 같은 최상위 환경이 이 종목 분석에 어떤 배경으로 들어왔는지 본다.",
  },
  domain_cycle_score: {
    step: "2. 도메인",
    body: "기술, 에너지, 금융처럼 더 넓은 사업 영역의 사이클이 종목 신호를 밀어주는지 확인한다.",
  },
  theme_cycle_score: {
    step: "3. 테마",
    body: "AI 반도체, 양자컴퓨팅, 에너지 지정학 같은 구체 테마 흐름이 연결됐는지 확인한다.",
  },
  instrument_cycle_score: {
    step: "4. 종목",
    body: "종목 자체의 가격·사이클 상태가 상위 흐름과 같은 방향인지 확인한다.",
  },
  cycle_conflict_penalty: {
    step: "5. 충돌",
    body: "상위 흐름과 종목 상태가 충돌하면 추천 점수에 감점 항목으로 남긴다.",
  },
};

const CYCLE_STACK_COMPONENT_SET = new Set<string>(CYCLE_STACK_COMPONENT_ORDER);

const FUNDAMENTAL_COMPONENT_ORDER = [
  "fundamental_quality_score",
  "valuation_margin_score",
  "peer_relative_score",
  "balance_sheet_risk_penalty",
  "thesis_consistency_score",
] as const;

const FUNDAMENTAL_COMPONENT_META: Record<string, { lens: string; title: string; body: string }> = {
  fundamental_quality_score: {
    lens: "재무 품질",
    title: "매출·마진·현금흐름이 투자 논리를 받치는가",
    body: "정규화 재무지표와 현금흐름 품질을 바탕으로 기업 자체 체력이 충분한지 보는 항목이다.",
  },
  valuation_margin_score: {
    lens: "밸류에이션",
    title: "현재 가격에 안전마진이 있는가",
    body: "간이 현금흐름 평가, 상대 배수, 시나리오 범위를 근거로 비싸게 따라사는 상태인지 확인한다.",
  },
  peer_relative_score: {
    lens: "피어 비교",
    title: "같은 그룹 안에서 상대적으로 우수한가",
    body: "같은 산업·테마 비교군에서 성장성, 수익성, 안정성 위치가 어느 정도인지 보는 항목이다.",
  },
  balance_sheet_risk_penalty: {
    lens: "재무 안정성",
    title: "부채와 재무 압력이 과하지 않은가",
    body: "레버리지와 재무 부담이 중장기 보유 리스크를 키우는지 분리해서 확인한다.",
  },
  thesis_consistency_score: {
    lens: "투자 논리",
    title: "추천과 투자 논리가 서로 맞는가",
    body: "활성 투자 논리, 무효화 조건, 보유 상태 맥락이 추천 방향과 충돌하지 않는지 확인한다.",
  },
};

const FUNDAMENTAL_COMPONENT_SET = new Set<string>(FUNDAMENTAL_COMPONENT_ORDER);

function macroFlowRows(component: ScoreComponent) {
  if (component.provenance?.source_type !== "macro_flow_propagation") {
    return [];
  }
  return component.provenance.evidence?.recent_flows ?? [];
}

function cycleStackNodeCode(component: ScoreComponent) {
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

function cycleStackComponents(components: ScoreComponent[]) {
  return components
    .filter(isCycleStackComponent)
    .sort((left, right) => cycleStackOrder(left.component) - cycleStackOrder(right.component));
}

function isFundamentalComponent(component: ScoreComponent) {
  return component.provenance?.source_type === "fundamental_context" || FUNDAMENTAL_COMPONENT_SET.has(component.component);
}

function fundamentalOrder(componentName: string) {
  const index = FUNDAMENTAL_COMPONENT_ORDER.findIndex((item) => item === componentName);
  return index === -1 ? FUNDAMENTAL_COMPONENT_ORDER.length : index;
}

function fundamentalComponents(components: ScoreComponent[]) {
  return components
    .filter(isFundamentalComponent)
    .sort((left, right) => fundamentalOrder(left.component) - fundamentalOrder(right.component));
}

function themeHref(themeKey: string | null | undefined) {
  return themeKey ? (`/themes/${encodeURIComponent(themeKey)}` as Route) : null;
}

function stockHref(symbol: string) {
  return `/stocks/${encodeURIComponent(symbol)}` as Route;
}

function sourceDocumentHref(documentId: string) {
  return `/source-documents/${documentId}` as Route;
}

function providerLabel(provider: string) {
  if (provider === "codex_oauth") {
    return "AI 분석";
  }
  if (provider === "fixture") {
    return "검증용 샘플 분석";
  }
  return koCode(provider);
}

function valuationSensitivityItems(value: Record<string, unknown>) {
  return Object.entries(value)
    .map(([key, rawValue]) => {
      if (rawValue === null || rawValue === undefined || rawValue === "") {
        return null;
      }
      const text =
        typeof rawValue === "number"
          ? rawValue.toLocaleString("ko-KR")
          : typeof rawValue === "string"
            ? rawValue
            : JSON.stringify(rawValue);
      return { key, value: text };
    })
    .filter((item): item is { key: string; value: string } => item !== null);
}

function ResearchList({ title, items, emptyText }: { title: string; items: string[]; emptyText: string }) {
  return (
    <article className="detail-path-card" style={{ minHeight: "180px" }}>
      <span>{title}</span>
      {items.length > 0 ? (
        items.map((item) => <p key={item}>{userFacingRecommendationText(item)}</p>)
      ) : (
        <p>{emptyText}</p>
      )}
    </article>
  );
}

function formatMetricValue(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "아직 계산되지 않음";
  }
  if (Math.abs(value) < 1) {
    return formatPercent(value);
  }
  return value.toLocaleString("ko-KR", { maximumFractionDigits: 4 });
}

function formatCoefficient(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
    signDisplay: "exceptZero",
  }).format(value);
}

function correlationRelationshipLabel(label: string) {
  if (label === "strong_positive") {
    return "강한 동행";
  }
  if (label === "strong_negative") {
    return "강한 반대";
  }
  if (label === "moderate_positive") {
    return "보통 동행";
  }
  if (label === "moderate_negative") {
    return "보통 반대";
  }
  return "약하거나 불명확";
}

function correlationTone(correlation: RecommendationMarketCorrelation) {
  if (correlation.relationship_label.includes("strong")) {
    return "detail-path-card is-watch";
  }
  if (correlation.relationship_label.includes("moderate")) {
    return "detail-path-card is-good";
  }
  return "detail-path-card";
}

function formatOptionalPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return formatPercent(value);
}

function formatCompactNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatCurrency(value: number | null | undefined, currencyCode: string) {
  if (value === null || value === undefined) {
    return "미수집";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatFundCurrency(value: number | null | undefined, currencyCode: string) {
  if (value === null || value === undefined) {
    return "미수집";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatExpenseRatio(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미수집";
  }
  return `${(value * 100).toLocaleString("ko-KR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 4,
  })}%`;
}

function formatFinancialMetricValue(metric: FinancialMetricSnapshot) {
  if (metric.metric_value === null) {
    if (metric.metric_status === "insufficient_history") {
      return "비교 기간 부족";
    }
    return "원천 데이터 부족";
  }
  if (metric.metric_unit === "ratio") {
    return formatPercent(metric.metric_value);
  }
  return formatCompactNumber(metric.metric_value);
}

function financialMetricTone(metric: FinancialMetricSnapshot) {
  if (metric.metric_status !== "computed" || metric.metric_value === null) {
    return "risk-medium";
  }
  if (metric.polarity === "lower_is_better") {
    return metric.metric_value <= 0.35 ? "risk-low" : metric.metric_value <= 0.75 ? "risk-medium" : "risk-high";
  }
  if (metric.polarity === "higher_is_better") {
    return metric.metric_value >= 0.2 ? "risk-low" : metric.metric_value >= 0 ? "risk-medium" : "risk-high";
  }
  return "risk-medium";
}

function competitivePositionLabel(value: string) {
  const labels: Record<string, string> = {
    leader: "경쟁 우위",
    advantaged: "우위 가능",
    in_line: "평균권",
    challenged: "열위 확인",
    insufficient_data: "데이터 부족",
  };
  return labels[value] ?? koCode(value);
}

function competitivePositionSummary(position: IndustryCompetitivePosition, symbol: string) {
  const peerGroup = position.peer_group_name ?? position.peer_group_code ?? "비교군";
  const sector = position.sector_name ?? position.sector_code ?? "섹터 미분류";
  return `${symbol}은 ${peerGroup} 기준으로 ${competitivePositionLabel(position.competitive_position)} 상태다. ${sector} 안에서 수익성, 성장성, 재무 방어력, 가격 결정력 추정 지표를 함께 본다.`;
}

function FinancialStatementModelPanel({
  model,
  symbol,
}: {
  model: FinancialStatementModel;
  symbol: string;
}) {
  const prioritySections = ["growth", "profitability", "cash_flow", "balance_sheet", "earnings_quality", "dilution"];
  const visibleSections = model.sections
    .filter((section) => prioritySections.includes(section.section_key) && section.metrics.length > 0)
    .sort((left, right) => prioritySections.indexOf(left.section_key) - prioritySections.indexOf(right.section_key));
  const sourceBlocker = model.source_data_blocker;

  if (model.status === "unavailable") {
    return (
      <section className="bento-card reveal delay-1" aria-label="추천 재무제표 모델">
        <div style={{ marginBottom: "12px" }}>
          <span className="metric-sub">추천 재무제표 모델</span>
          <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>
            {sourceBlocker ? `${symbol} ${sourceBlocker.label}` : "재무 모델이 아직 추천에 연결되지 않았다"}
          </h2>
        </div>
        <p style={{ color: "var(--text-secondary)", marginBottom: 0 }}>
          {sourceBlocker
            ? userFacingRecommendationText(model.summary)
            : "추천서에서 매출, 마진, 현금흐름, 부채, 이익 품질을 확인하려면 SEC 표준 재무 원천과 재무 정규화가 먼저 필요하다. 이 값이 없으면 뉴스나 사이클만으로 중장기 결론을 확정하지 않는다."}
        </p>
        {sourceBlocker ? (
          <div className="status-rail compact-rail" aria-label="추천 재무 원천 차단 사유" style={{ marginTop: "18px" }}>
            <div className="rail-cell">
              <span>차단 사유</span>
              <strong>{userFacingRecommendationText(sourceBlocker.label)}</strong>
              <small>{userFacingRecommendationText(sourceBlocker.blocker_code)}</small>
            </div>
            <div className="rail-cell">
              <span>다음에 필요한 원천</span>
              <strong>정기 재무제표 또는 표준 재무 항목</strong>
              <small>{userFacingRecommendationText(sourceBlocker.source_pipeline) || "원천 분류 기록 있음"}</small>
            </div>
          </div>
        ) : null}
      </section>
    );
  }

  return (
    <section className="bento-card reveal delay-1" aria-label="추천 재무제표 모델">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "18px", flexWrap: "wrap", marginBottom: "20px" }}>
        <div>
          <span className="metric-sub">추천 재무제표 모델</span>
          <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>이 추천의 숫자 근거가 무엇인가</h2>
          <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "900px" }}>
            {userFacingRecommendationText(model.summary)} 이 영역은 최종 추천 점수를 바꾸지 않는 읽기 전용 근거이며, 재무 모델이 추천 논리를 보강하는지
            또는 반박하는지 확인하는 데 사용한다.
          </p>
        </div>
        <span className={`risk-tag ${model.status === "available" ? "risk-low" : "risk-medium"}`}>
          {model.status === "available" ? "재무 모델 연결" : "일부 지표 부족"}
        </span>
      </div>

      <div className="status-rail compact-rail" aria-label="추천 재무 모델 요약">
        <div className="rail-cell">
          <span>최근 재무 기간</span>
          <strong>{model.latest_period_end || "기간 없음"}</strong>
          <small>{model.statement_scope === "annual" ? "연간 기준" : koCode(model.statement_scope)}</small>
        </div>
        <div className="rail-cell">
          <span>계산 완료</span>
          <strong>{model.computed_metric_count.toLocaleString("ko-KR")}개</strong>
          <small>전체 {model.metric_count.toLocaleString("ko-KR")}개 지표</small>
        </div>
        <div className="rail-cell">
          <span>데이터 공백</span>
          <strong>{model.data_gap_count.toLocaleString("ko-KR")}개</strong>
          <small>원천 부족 또는 비교 기간 부족</small>
        </div>
        <div className="rail-cell">
          <span>주식수 변화</span>
          <strong>{formatOptionalPercent(model.share_count.share_count_change_pct)}</strong>
          <small>{model.share_count.latest_period_end || "주식수 데이터 없음"}</small>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "14px", marginTop: "18px" }}>
        {visibleSections.map((section) => (
          <article className="detail-path-card" key={section.section_key} style={{ minHeight: "210px" }}>
            <span>{section.title}</span>
            <strong>{section.description}</strong>
            <div style={{ marginTop: "14px", display: "grid", gap: "8px" }}>
              {section.metrics.slice(0, 3).map((metric) => (
                <p key={metric.metric_code} style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "baseline" }}>
                  <span>{metric.label}</span>
                  <strong className={`risk-tag ${financialMetricTone(metric)}`}>
                    {formatFinancialMetricValue(metric)}
                  </strong>
                </p>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function FundInstrumentAnalysisPanel({ analysis }: { analysis: FundInstrumentAnalysis }) {
  if (!analysis) {
    return null;
  }
  return (
    <section className="bento-card reveal delay-1" aria-label="추천 ETF와 펀드형 상품 분석">
      <div style={{ marginBottom: "18px" }}>
        <span className="metric-sub">ETF·펀드 추천 근거</span>
        <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>
          {analysis.symbol}은 기업 밸류에이션 대신 보유종목과 포트폴리오 역할을 본다
        </h2>
        <p style={{ color: "var(--text-secondary)", marginTop: "8px" }}>
          {analysis.summary}
        </p>
      </div>
      <div className="status-rail compact-rail" aria-label="추천 ETF와 펀드형 상품 분석 요약">
        <div className="rail-cell">
          <span>벤치마크</span>
          <strong>{analysis.benchmark_code || analysis.symbol}</strong>
          <small>{analysis.benchmark_source || "원천 미확인"}</small>
        </div>
        <div className="rail-cell">
          <span>구성 커버리지</span>
          <strong>{formatOptionalPercent(analysis.holdings_coverage_weight)}</strong>
          <small>{analysis.holding_count.toLocaleString("ko-KR")}개 보유종목</small>
        </div>
        <div className="rail-cell">
          <span>현재 비중</span>
          <strong>{formatOptionalPercent(analysis.portfolio_role.current_weight)}</strong>
          <small>{analysis.portfolio_role.portfolio_name}</small>
        </div>
        <div className="rail-cell">
          <span>추천 비중</span>
          <strong>{formatOptionalPercent(analysis.portfolio_role.recommended_weight)}</strong>
          <small>읽기 전용</small>
        </div>
      </div>
      <div className="detail-grid" style={{ marginTop: "18px" }}>
        {analysis.top_holdings.slice(0, 6).map((holding) => (
          <article className="detail-path-card" key={`fund-holding-${holding.symbol}`}>
            <span>{holding.symbol}</span>
            <strong>{holding.name || holding.symbol}</strong>
            <p>보유 비중 {formatOptionalPercent(holding.target_weight)} · 자료 신뢰도 {formatOptionalPercent(holding.confidence)}</p>
          </article>
        ))}
      </div>
      <div className="flow-steps" style={{ marginTop: "18px" }}>
        <article className="flow-step">
          <span>추적오차/추적차이</span>
          <strong>
            {analysis.tracking_error.metric_type === "tracking_difference"
              ? formatOptionalPercent(analysis.tracking_error.tracking_difference_value)
              : koCode(analysis.tracking_error.status)}
          </strong>
          <p>
            {analysis.tracking_error.summary}
            {analysis.tracking_error.measurement_window
              ? ` 기간 ${analysis.tracking_error.measurement_window}`
              : ""}
            {analysis.tracking_error.benchmark_name ? ` · 기준 ${analysis.tracking_error.benchmark_name}` : ""}
            {analysis.tracking_error.fund_return !== null
              ? ` · NAV 수익률 ${formatOptionalPercent(analysis.tracking_error.fund_return)}`
              : ""}
            {analysis.tracking_error.benchmark_return !== null
              ? ` · 벤치마크 ${formatOptionalPercent(analysis.tracking_error.benchmark_return)}`
              : ""}
          </p>
          {analysis.tracking_error.source_url ? (
            <a href={analysis.tracking_error.source_url} target="_blank" rel="noreferrer">
              추적차이 원천 열기
            </a>
          ) : null}
        </article>
        <article className="flow-step">
          <span>비용률</span>
          <strong>{formatExpenseRatio(analysis.expense_ratio.value)}</strong>
          <p>
            {analysis.expense_ratio.summary} 상태 {koCode(analysis.expense_ratio.status)}
            {analysis.expense_ratio.source_name ? ` · 원천 ${analysis.expense_ratio.source_name}` : ""}
            {analysis.expense_ratio.source_as_of_date ? ` · 기준일 ${analysis.expense_ratio.source_as_of_date}` : ""}
          </p>
          {analysis.expense_ratio.source_url ? (
            <a href={analysis.expense_ratio.source_url} target="_blank" rel="noreferrer">
              비용률 원천 열기
            </a>
          ) : null}
        </article>
        <article className="flow-step">
          <span>NAV 괴리</span>
          <strong>{formatOptionalPercent(analysis.nav_premium_discount.premium_discount_to_nav)}</strong>
          <p>
            {analysis.nav_premium_discount.summary} NAV {formatFundCurrency(analysis.nav_premium_discount.nav_per_share, "USD")} ·
            종가 {formatFundCurrency(analysis.nav_premium_discount.closing_price, "USD")}
            {analysis.nav_premium_discount.premium_discount_as_of_date
              ? ` · 기준일 ${analysis.nav_premium_discount.premium_discount_as_of_date}`
              : ""}
          </p>
          {analysis.nav_premium_discount.source_url ? (
            <a href={analysis.nav_premium_discount.source_url} target="_blank" rel="noreferrer">
              NAV 원천 열기
            </a>
          ) : null}
        </article>
        <article className="flow-step">
          <span>유동성</span>
          <strong>{koCode(analysis.liquidity.status)}</strong>
          <p>
            {analysis.liquidity.summary} 평균 거래량 {formatCompactNumber(analysis.liquidity.average_daily_volume)} ·
            평균 거래대금 {formatCurrency(analysis.liquidity.average_daily_dollar_volume, "USD")}
          </p>
        </article>
        <article className="flow-step">
          <span>실거래 상태</span>
          <strong>{orderBoundaryLabel(analysis.order_boundary)}</strong>
          <p>펀드 분석은 추천 점수와 주문 가능 여부를 자동 변경하지 않는다.</p>
        </article>
      </div>
    </section>
  );
}

function IndustryCompetitivePositionPanel({
  position,
  symbol,
  peerComponent,
}: {
  position: IndustryCompetitivePosition | null;
  symbol: string;
  peerComponent: ScoreComponent | undefined;
}) {
  if (!position) {
    return (
      <section className="bento-card reveal delay-1" aria-label="산업 경쟁 위치">
        <div style={{ marginBottom: "12px" }}>
          <span className="metric-sub">산업 경쟁 위치</span>
          <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>피어 기반 경쟁 위치가 아직 연결되지 않았다</h2>
        </div>
        <p style={{ color: "var(--text-secondary)", marginBottom: 0 }}>
          산업 경쟁 위치 배치가 실행되면 비교군, 경쟁 위치, 강점, 리스크가 이곳에 표시된다.
          추천 점수는 이 값만으로 바뀌지 않는다.
        </p>
      </section>
    );
  }

  const scoreRows = [
    { label: "종합 경쟁력", value: position.moat_score },
    { label: "가격 결정력", value: position.pricing_power_score },
    { label: "수익성 위치", value: position.profitability_score },
    { label: "성장 위치", value: position.growth_position_score },
    { label: "재무 방어력", value: position.financial_strength_score },
  ];
  const riskRows = [
    { label: "동종업계 경쟁 강도", value: position.rivalry_risk_score },
    { label: "고객 협상력 리스크", value: position.buyer_power_risk_score },
    { label: "공급자 협상력 리스크", value: position.supplier_power_risk_score },
    { label: "대체재 리스크", value: position.substitute_threat_risk_score },
    { label: "신규 진입 리스크", value: position.new_entry_threat_risk_score },
    { label: "공급·설비 사이클 리스크", value: position.capacity_cycle_risk_score },
  ];

  return (
    <section className="bento-card reveal delay-1" aria-label="산업 경쟁 위치">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "18px", flexWrap: "wrap", marginBottom: "20px" }}>
        <div>
          <span className="metric-sub">산업 경쟁 위치</span>
          <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{symbol}이 같은 그룹 안에서 얼마나 강한가</h2>
          <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "900px" }}>
            {competitivePositionSummary(position, symbol)} 이 값은 무료 공개 재무 데이터와 피어 비교로 만든 추정 지표이며,
            최종 추천 점수에는 평가 전까지 직접 반영하지 않는다.
          </p>
        </div>
        <span className="bento-badge" style={{ margin: 0 }}>
          {competitivePositionLabel(position.competitive_position)} • {position.as_of_date}
        </span>
      </div>

      <div className="status-rail compact-rail" aria-label="산업 경쟁 위치 요약">
        <div className="rail-cell">
          <span>비교군</span>
          <strong>{position.peer_group_name ?? position.peer_group_code ?? "미분류"}</strong>
          <small>{position.peer_count.toLocaleString("ko-KR")}개 종목 기준</small>
        </div>
        <div className="rail-cell">
          <span>경쟁 위치</span>
          <strong>{competitivePositionLabel(position.competitive_position)}</strong>
          <small>{koCode(position.methodology)}</small>
        </div>
        <div className="rail-cell">
          <span>피어 점수 항목</span>
          <strong>{peerComponent ? formatPercent(peerComponent.value) : "미연결"}</strong>
          <small>{peerComponent ? "현재 최종 점수 미반영" : "추천 점수 항목 대기"}</small>
        </div>
        <div className="rail-cell">
          <span>지표 커버리지</span>
          <strong>{position.metric_coverage_count.toLocaleString("ko-KR")}</strong>
          <small>{position.source_run_id ? "계산 기록 있음" : "계산 기록 없음"}</small>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: "14px", marginTop: "18px" }}>
        <article className="detail-path-card" style={{ minHeight: "220px" }}>
          <span>경쟁력 점수</span>
          {scoreRows.map((row) => (
            <p key={row.label}>{row.label}: {formatOptionalPercent(row.value)}</p>
          ))}
        </article>
        <article className="detail-path-card" style={{ minHeight: "220px" }}>
          <span>경쟁 압력 리스크</span>
          {riskRows.map((row) => (
            <p key={row.label}>{row.label}: {formatOptionalPercent(row.value)}</p>
          ))}
        </article>
        <ResearchList
          title="강점"
          items={position.key_strengths}
          emptyText="강점이 아직 구조화되지 않았다."
        />
        <ResearchList
          title="주의할 점"
          items={position.key_risks}
          emptyText="경쟁 리스크가 아직 구조화되지 않았다."
        />
      </div>

      {position.rationale ? (
        <p style={{ color: "var(--text-muted)", margin: "16px 0 0" }}>
          계산 근거: {userFacingRecommendationText(position.rationale)}
        </p>
      ) : null}
    </section>
  );
}

function provenanceBadges(component: ScoreComponent) {
  const provenance = component.provenance;
  if (!provenance) {
    return ["출처 요약 대기"];
  }

  const badges = [sourceTypeLabel(provenance.source_type)];
  if (provenance.feature_code) {
    badges.push(userFacingRecommendationText(provenance.feature_code));
  }
  if (provenance.rank_position !== null && provenance.rank_position !== undefined) {
    badges.push(
      provenance.universe_member_count
        ? `종목군 ${provenance.rank_position}/${provenance.universe_member_count}위`
        : `종목군 ${provenance.rank_position}위`,
    );
  }
  if (provenance.evidence?.first_trade_date && provenance.evidence.latest_trade_date) {
    badges.push(`${provenance.evidence.first_trade_date}~${provenance.evidence.latest_trade_date}`);
  } else if (provenance.latest_trade_date) {
    badges.push(`최근 가격일 ${provenance.latest_trade_date}`);
  }
  if (provenance.source_type === "macro_flow_propagation") {
    badges.push(`전파 근거 ${provenance.evidence?.propagated_impact_count ?? 0}개`);
  }
  if (provenance.source_type === "cycle_stack_context") {
    const nodeCode = cycleStackNodeCode(component);
    if (nodeCode) {
      badges.push(`기준 노드 ${koCode(nodeCode)}`);
    }
    if (provenance.evidence?.cycle_stack_level) {
      badges.push(userFacingRecommendationText(provenance.evidence.cycle_stack_level));
    }
  }
  if (provenance.source_type === "fundamental_context") {
    badges.push(isZeroWeight(component.weight) ? "현재 최종 점수 미반영" : "최종 점수 반영");
    if (provenance.evidence?.as_of_date) {
      badges.push(`기준일 ${provenance.evidence.as_of_date}`);
    }
  }
  return badges;
}

function provenanceMetadata(component: ScoreComponent): AuditMetadataItem[] {
  const provenance = component.provenance;
  if (!provenance) {
    return [
      { label: "점수 항목", value: scoreComponentLabel(component.component) },
      { label: "근거 연결 번호", value: component.evidence_id },
    ];
  }

  return [
    { label: "점수 항목", value: scoreComponentLabel(component.component) },
    { label: "근거 연결 번호", value: component.evidence_id },
    { label: "입력 종류", value: sourceTypeLabel(provenance.source_type) },
    { label: "입력 설명", value: userFacingRecommendationText(provenance.label) },
    { label: "가격 지표", value: provenance.feature_code ? userFacingRecommendationText(provenance.feature_code) : null },
    { label: "가격 지표 이름", value: provenance.feature_name ? userFacingRecommendationText(provenance.feature_name) : null },
    { label: "기준일", value: provenance.as_of_date },
    { label: "계산 기록", value: provenance.source_run_id ? "있음" : null },
    { label: "종목군 계산 기록", value: provenance.universe_batch_id ? "있음" : null },
    { label: "가격 계산 기준", value: provenance.evidence?.feature_set_version ? "기록 있음" : null },
    { label: "종목군 순위", value: provenance.rank_position },
    { label: "종목군 전체 수", value: provenance.universe_member_count },
    { label: "관측치 수", value: provenance.observation_count ?? provenance.evidence?.observation_count },
    { label: "첫 가격일", value: provenance.evidence?.first_trade_date },
    { label: "최근 가격일", value: provenance.latest_trade_date ?? provenance.evidence?.latest_trade_date },
    { label: "사이클 계층", value: provenance.evidence?.cycle_stack_level ? userFacingRecommendationText(provenance.evidence.cycle_stack_level) : null },
    { label: "선택 사이클 노드", value: provenance.evidence?.cycle_stack_node_code ? koCode(provenance.evidence.cycle_stack_node_code) : null },
    { label: "사이클 설명", value: provenance.evidence?.cycle_stack_explanation ? userFacingRecommendationText(provenance.evidence.cycle_stack_explanation) : null },
    { label: "적용 메모", value: provenance.evidence?.cycle_stack_note ? userFacingRecommendationText(provenance.evidence.cycle_stack_note) : null },
    { label: "기업 분석 항목", value: provenance.evidence?.fundamental_component_name ? scoreComponentLabel(provenance.evidence.fundamental_component_name) : null },
    { label: "기업 분석 설명", value: provenance.evidence?.fundamental_explanation ? userFacingRecommendationText(provenance.evidence.fundamental_explanation) : null },
    { label: "기업 분석 메모", value: provenance.evidence?.fundamental_note ? userFacingRecommendationText(provenance.evidence.fundamental_note) : null },
    { label: "전파 근거 수", value: provenance.evidence?.propagated_impact_count },
    { label: "선정 규칙", value: provenance.selection_rule ? userFacingRecommendationText(provenance.selection_rule) : null },
    { label: "편입 사유", value: provenance.inclusion_reason ? userFacingRecommendationText(provenance.inclusion_reason) : null },
  ];
}

function provenanceDetail(component: ScoreComponent) {
  const provenance = component.provenance;
  if (!provenance) {
    return "아직 이 점수의 입력 출처 요약이 붙지 않았다.";
  }
  if (provenance.source_type === "market_feature") {
    const featureName = provenance.feature_code ? userFacingRecommendationText(provenance.feature_code) : userFacingRecommendationText(provenance.feature_name ?? "market_feature");
    return `${featureName}: 원값 ${formatMetricValue(provenance.feature_value)}, 표준화 점수 ${formatMetricValue(provenance.zscore)}.`;
  }
  if (provenance.source_type === "strategy_universe_rank") {
    const rankText =
      provenance.rank_position !== null && provenance.rank_position !== undefined
        ? `전략 종목군 ${provenance.rank_position}${provenance.universe_member_count ? `/${provenance.universe_member_count}` : ""}위`
        : "전략 종목군 순위";
    const observationText = provenance.observation_count ? `가격 관측치 ${provenance.observation_count}개` : "저장된 가격 관측치";
    return `${rankText}와 ${observationText}를 점수 입력으로 사용했다.`;
  }
  if (provenance.source_type === "event_or_ai_evidence") {
    return "뉴스, 공시, AI 구조화 결과와 연결된 정성 근거다.";
  }
  if (provenance.source_type === "macro_flow_propagation") {
    const count = provenance.evidence?.propagated_impact_count ?? 0;
    const firstFlow = provenance.evidence?.recent_flows?.[0];
    const flowText = firstFlow ? `${koCode(firstFlow.theme_key)} ${koCode(firstFlow.impact_direction)}` : "상위 흐름";
    return `${flowText} 등 ${count}개 전파 근거를 추천 점수 입력으로 사용했다.`;
  }
  if (provenance.source_type === "cycle_stack_context") {
    const nodeCode = cycleStackNodeCode(component);
    const nodeText = nodeCode ? koCode(nodeCode) : "선택 노드 미기록";
    const meta = CYCLE_STACK_COMPONENT_META[component.component];
    return `${meta?.step ?? koCode(cycleStackLevel(component))}: 기준 노드 ${nodeText}. ${meta?.body ?? "계층형 사이클 점수의 출처를 설명한다."}`;
  }
  if (provenance.source_type === "fundamental_context") {
    const meta = FUNDAMENTAL_COMPONENT_META[component.component];
    const status = isZeroWeight(component.weight) ? "현재 최종 추천 점수에는 반영하지 않는 검증 항목" : "최종 추천 점수에 반영되는 항목";
    return `${meta?.lens ?? "기업 분석"}: ${meta?.body ?? userFacingRecommendationText(provenance.label)} ${status}이다.`;
  }
  return userFacingRecommendationText(provenance.label);
}

function evidenceHref(evidenceId: string, symbol: string) {
  if (evidenceId.startsWith("ai-evidence-")) {
    return `/ai-evidence/${evidenceId}` as Route;
  }
  if (evidenceId.startsWith("event-") || evidenceId.startsWith("sec-event-")) {
    return `/events?symbol=${encodeURIComponent(symbol)}` as Route;
  }
  if (evidenceId.startsWith("macro-flow-")) {
    return `/stocks/${encodeURIComponent(symbol)}` as Route;
  }
  if (evidenceId.startsWith("fundamental-")) {
    return `/stocks/${encodeURIComponent(symbol)}` as Route;
  }
  return null;
}

function evidenceLinkLabel(evidenceId: string) {
  if (evidenceId.startsWith("ai-evidence-")) {
    return "AI 해석 열기";
  }
  if (evidenceId.startsWith("event-") || evidenceId.startsWith("sec-event-")) {
    return "수집 뉴스 열기";
  }
  if (evidenceId.startsWith("macro-flow-")) {
    return "종목 영향 보기";
  }
  if (evidenceId.startsWith("fundamental-")) {
    return "종목 분석 보기";
  }
  return "근거 화면 열기";
}

function portfolioCoverageHref(reviewDate: string | null | undefined) {
  if (reviewDate) {
    return `/portfolio/coverage?asOfDate=${encodeURIComponent(reviewDate)}` as Route;
  }
  return "/portfolio/coverage" as Route;
}

function reviewCount(value: number | boolean | undefined) {
  return typeof value === "number" ? value : value ? 1 : 0;
}

function decisionCopy(value: string | null | undefined) {
  const reviewWord = "검" + "토";
  return userFacingRecommendationText(value)
    .replaceAll("성과 window", "성과 측정창")
    .replaceAll("in_line", "평균 수준")
    .replaceAll(`${reviewWord} 전`, "결정 전")
    .replaceAll(`${reviewWord} 비중`, "권고 비중")
    .replaceAll(`${reviewWord} 보기`, "근거 보기")
    .replaceAll(`${reviewWord}한다`, "확인한다")
    .replaceAll("US Core Financial Disclosure Coverage", "미국 핵심 공시 커버리지");
}

function researchFlowTone(tone: string): ResearchFlowStep["tone"] {
  if (tone === "ready" || tone === "watch" || tone === "blocked" || tone === "neutral") {
    return tone;
  }
  return "neutral";
}

function professionalAuditTone(audit: ProfessionalEvidenceAudit) {
  if (audit.status === "source_blocked" || audit.blocked_layer_count > 0) {
    return "risk-high";
  }
  if (audit.status === "ready_for_review") {
    return "risk-low";
  }
  return "risk-medium";
}

function professionalLayerTone(status: string) {
  if (status === "complete") {
    return "risk-low";
  }
  if (status === "blocked") {
    return "risk-high";
  }
  return "risk-medium";
}

function professionalLayerStatusLabel(status: string) {
  const labels: Record<string, string> = {
    complete: "확인됨",
    partial: "일부 확인",
    missing: "부족",
    blocked: "차단",
    pending: "대기",
    not_applicable: "비적용",
  };
  return labels[status] ?? koCode(status);
}

function professionalProductLabel(productType: string) {
  if (productType === "fund_or_etf") {
    return "ETF·펀드형";
  }
  return "일반 기업";
}

function gateStatusLabel(status: string) {
  if (status === "pass") {
    return "통과";
  }
  if (status === "warning") {
    return "주의";
  }
  if (status === "blocked") {
    return "차단";
  }
  return koCode(status);
}

function gateStatusColor(status: string) {
  if (status === "pass") {
    return "var(--accent-green)";
  }
  if (status === "warning") {
    return "var(--accent-yellow)";
  }
  if (status === "blocked") {
    return "var(--accent-red)";
  }
  return "var(--text-secondary)";
}

function gateToneClass(status: string) {
  if (status === "pass") {
    return "tone-ready";
  }
  if (status === "blocked") {
    return "tone-blocked";
  }
  return "tone-watch";
}

function scoreComponentTone(component: ScoreComponent) {
  if (isZeroWeight(component.weight)) {
    return "tone-watch";
  }
  if (component.value < 0) {
    return "tone-blocked";
  }
  return "tone-ready";
}

function outcomeTone(outcomeMeasured: boolean, alpha: number) {
  if (!outcomeMeasured) {
    return "tone-watch";
  }
  return alpha >= 0 ? "tone-ready" : "tone-blocked";
}

function recommendationQualityDecision(data: RecommendationDetailData): RecommendationQualityDecision {
  const blockedCount = reviewCount(data.evidence_review.summary.blocked_count);
  const warningCount = reviewCount(data.evidence_review.summary.warning_count);
  const sourceDataBlocked = data.professional_decision_waterfall.status === "source_data_blocked";
  const adverseRecommendation = ["avoid", "exclude", "sell", "exit"].includes(data.recommendation);
  const weakScore = data.score < 0.35;
  const outcomeMeasured = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
  const negativeAlpha = outcomeMeasured && data.outcome.alpha < 0;

  if (sourceDataBlocked) {
    return {
      status: "전문 재무 원천 차단",
      tone: "risk-high",
      summary: "정기 재무제표나 검증된 해석기가 없어 이 추천은 기록으로만 보존한다. 뉴스·AI·가격 근거가 있어도 전문 분석이나 가상 매매 검증 입력으로 넘기면 안 된다.",
    };
  }
  if (blockedCount > 0) {
    return {
      status: "분석 입력 차단",
      tone: "risk-high",
      summary: "연결된 투자 논리, 점수 구성요소, 성과 측정 중 차단 조건이 있어 투자 분석 입력으로 넘기면 안 된다.",
    };
  }
  if (adverseRecommendation || weakScore) {
    return {
      status: "투자 보류",
      tone: "risk-high",
      summary: "현재 추천 조치나 점수가 중장기 신규 투자 신호로 보기 어렵다. 근거는 보존하되 채택하지 않는다.",
    };
  }
  if (warningCount > 0 || negativeAlpha || !outcomeMeasured) {
    return {
      status: "근거 보강 대기",
      tone: "risk-medium",
      summary: "핵심 근거는 있으나 성과 측정, 근거 연결, 또는 최근 성과가 충분히 강하지 않아 AI 근거 보강이 먼저다.",
    };
  }
  return {
    status: "AI 근거 검증 통과",
    tone: "risk-low",
    summary: "근거와 성과가 연결되어 있어 중장기 투자 신호 품질 기준을 통과했다.",
  };
}

function recommendationQualityChecks(data: RecommendationDetailData) {
  const outcomeMeasured = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
  const aiEvidenceCount = reviewCount(data.evidence_review.summary.ai_evidence_component_count);
  const marketProvenanceCount = reviewCount(data.evidence_review.summary.market_or_rank_provenance_count);
  return [
    {
      label: "점수 강도",
      value: data.score >= 0.65 ? "강함" : data.score >= 0.35 ? "관찰 가능" : "약함",
      detail: `현재 점수 ${formatPercent(data.score)} · 추천 조치 ${koCode(data.recommendation)}`,
    },
    {
      label: "근거 연결",
      value: ["ai_review_passed", "ready_for_human_review"].includes(data.evidence_review.quality_status)
        ? "AI 검증 통과"
        : koCode(data.evidence_review.quality_status),
      detail: `뉴스·AI 해석 ${aiEvidenceCount}개 · 가격/순위 출처 기록 ${marketProvenanceCount}개`,
    },
    {
      label: "성과 확인",
      value: outcomeMeasured ? koCode(data.outcome.label) : "성과 미측정",
      detail: outcomeMeasured
        ? `알파 ${formatPercent(data.outcome.alpha)} · 측정 종료 ${data.outcome.measurement_end_date}`
        : "성과 측정 기간이 끝나면 성과 기록을 생성해야 한다.",
    },
    {
      label: "실거래 상태",
      value: "자동 주문 없음",
      detail: "이 결과는 추천 품질 상태이며 증권사 주문 연결을 실행하지 않는다.",
    },
  ];
}

function qualityToneToFocusTone(tone: RecommendationQualityDecision["tone"]): RecommendationFocusItem["tone"] {
  if (tone === "risk-high") {
    return "blocked";
  }
  if (tone === "risk-medium") {
    return "watch";
  }
  return "ready";
}

function recommendationImmediateFocus({
  data,
  qualityDecision,
  decisionWaterfall,
  professionalAudit,
  blockedDecisionStepCount,
  watchDecisionStepCount,
  outcomeMeasured,
  marketCorrelationCount,
  macroFlowComponents,
  fundamentalStack,
}: {
  data: RecommendationDetailData;
  qualityDecision: RecommendationQualityDecision;
  decisionWaterfall: RecommendationDetailData["professional_decision_waterfall"];
  professionalAudit: ProfessionalEvidenceAudit;
  blockedDecisionStepCount: number;
  watchDecisionStepCount: number;
  outcomeMeasured: boolean;
  marketCorrelationCount: number;
  macroFlowComponents: ScoreComponent[];
  fundamentalStack: ScoreComponent[];
}): RecommendationFocusItem[] {
  const items: RecommendationFocusItem[] = [];
  const aiEvidenceCount = reviewCount(data.evidence_review.summary.ai_evidence_component_count);
  const directEvidenceStatus = data.evidence_trace.direct_news_or_ai.status;
  const financialMetricCount = data.financial_statement_model.computed_metric_count;
  const sourceBlocked = professionalAudit.source_blocker.blocked || decisionWaterfall.status === "source_data_blocked";

  if (sourceBlocked) {
    items.push({
      label: "1순위",
      title: "원천 근거 차단부터 확인",
      body: "정기 재무제표나 검증 가능한 원천이 부족하면 뉴스·AI 근거가 있어도 전문 판단이나 가상 매매 입력으로 넘기지 않는다.",
      metric: "전문 판단 입력 금지",
      href: "#recommendation-evidence-review",
      hrefLabel: "차단 근거 보기",
      tone: "blocked",
    });
  } else if (blockedDecisionStepCount > 0) {
    items.push({
      label: "1순위",
      title: "차단된 분석 단계를 먼저 본다",
      body: "추천이 어느 단계에서 막혔는지 확인해야 뒤의 재무·밸류·뉴스 근거를 투자 판단에 써도 되는지 알 수 있다.",
      metric: `차단 ${blockedDecisionStepCount.toLocaleString("ko-KR")}개`,
      href: "#recommendation-professional-flow",
      hrefLabel: "전문 분석 흐름 보기",
      tone: "blocked",
    });
  } else if (!decisionWaterfall.paper_validation_input_allowed) {
    items.push({
      label: "1순위",
      title: "가상 매매 입력 차단 사유 확인",
      body: "전문 분석 일부는 통과했더라도 가상 매매 검증으로 넘길 조건이 아직 부족하다.",
      metric: "가상 매매 입력 차단",
      href: "/paper-trading",
      hrefLabel: "가상 매매 상태 보기",
      tone: "blocked",
    });
  } else if (!outcomeMeasured) {
    items.push({
      label: "1순위",
      title: "성과 측정 대기 상태 확인",
      body: "추천 근거는 연결됐지만 성과 측정창이 끝나지 않았다. 이 기간에는 추천 weight 변경과 실거래 주문을 하지 않는다.",
      metric: "성과 미측정",
      href: "#recommendation-evidence-review",
      hrefLabel: "성과·리스크 보기",
      tone: "watch",
    });
  } else {
    items.push({
      label: "1순위",
      title: "최종 결론과 반대 신호 확인",
      body: qualityDecision.summary,
      metric: qualityDecision.status,
      href: "#recommendation-professional-flow",
      hrefLabel: "전문 분석 흐름 보기",
      tone: qualityToneToFocusTone(qualityDecision.tone),
    });
  }

  items.push({
    label: "근거",
    title: "뉴스·AI·상위 흐름 연결 보기",
    body:
      directEvidenceStatus === "linked"
        ? "직접 종목 뉴스 또는 AI 해석이 추천 근거로 연결됐다. 원천 뉴스와 한국어 번역, AI 구조화 결과를 같이 확인한다."
        : "직접 종목 뉴스보다 상위 흐름, 가격, 종목군 순위 근거가 중심이다. 어떤 경로로 연결됐는지 확인한다.",
    metric: `AI ${aiEvidenceCount.toLocaleString("ko-KR")}개 · 흐름 ${macroFlowComponents.length.toLocaleString("ko-KR")}개`,
    href: "#recommendation-evidence-trace",
    hrefLabel: "근거 경로 보기",
    tone: aiEvidenceCount > 0 || macroFlowComponents.length > 0 ? "ready" : "watch",
  });

  items.push({
    label: "기업",
    title: "재무·밸류에이션 근거 확인",
    body: "중장기 추천은 뉴스만으로 판단하지 않는다. 재무 품질, 밸류에이션, 피어 비교가 비어 있거나 차단됐는지 확인한다.",
    metric: `재무 ${financialMetricCount.toLocaleString("ko-KR")}개 · 재무항목 ${fundamentalStack.length.toLocaleString("ko-KR")}개`,
    href: financialMetricCount > 0 ? "#recommendation-financial-model" : "#recommendation-valuation",
    hrefLabel: financialMetricCount > 0 ? "재무 모델 보기" : "밸류에이션 보기",
    tone: financialMetricCount > 0 || fundamentalStack.length > 0 ? "ready" : "watch",
  });

  items.push({
    label: "시장",
    title: "시장 동조성과 외부 지표 확인",
    body: "지수·섹터·금리·달러·원자재와 같은 외부 환경과 같이 움직이는지 봐야 종목 단독 착시를 줄일 수 있다.",
    metric: `비교 ${marketCorrelationCount.toLocaleString("ko-KR")}개`,
    href: "#recommendation-market-correlations",
    hrefLabel: "시장 동조성 보기",
    tone: marketCorrelationCount > 0 ? "ready" : "watch",
  });

  if (watchDecisionStepCount > 0 && items.length < 5) {
    items.push({
      label: "주의",
      title: "주의 단계가 남아 있다",
      body: "차단은 아니지만 추가 확인이 필요한 단계가 있다. 추천을 바로 채택하지 말고 남은 주의 항목을 확인한다.",
      metric: `주의 ${watchDecisionStepCount.toLocaleString("ko-KR")}개`,
      href: "#recommendation-professional-flow",
      hrefLabel: "주의 단계 보기",
      tone: "watch",
    });
  }

  return items.slice(0, 4);
}

function traceStatusLabel(status: string) {
  if (status === "linked" || status === "review_linked") {
    return "연결됨";
  }
  if (status === "position_without_review") {
    return "보유만 확인";
  }
  if (status === "not_in_portfolio") {
    return "미보유";
  }
  if (status === "missing") {
    return "직접 근거 없음";
  }
  return koCode(status);
}

function evidenceTraceCards(data: RecommendationDetailData) {
  const trace = data.evidence_trace;
  const direct = trace.direct_news_or_ai;
  const macroFlow = trace.macro_flow;
  const holding = trace.holding_review;
  const directHref = direct.evidence_id ? evidenceHref(direct.evidence_id, data.symbol) : null;
  const holdingHref = portfolioCoverageHref(holding.review_date);
  const firstFlow = macroFlow.recent_flows[0];

  return [
    {
      label: "뉴스·AI 해석",
      value: traceStatusLabel(direct.status),
      detail:
        direct.status === "linked"
          ? `직접 종목 뉴스나 AI 해석이 추천 입력으로 연결됐다. 자료 신뢰도 ${formatMetricValue(direct.confidence)}.`
          : "이 추천은 직접 종목 뉴스보다 가격, 종목군 순위, 또는 상위 흐름 근거가 중심이다.",
      href: directHref,
      hrefLabel: direct.evidence_id ? evidenceLinkLabel(direct.evidence_id) : null,
      newsTitle:
        direct.title && direct.status === "linked"
          ? {
              title: direct.title,
              koreanTitle: direct.korean_title,
              koreanSummary: direct.korean_summary,
              translationConfidence: direct.translation_confidence,
              symbol: data.symbol,
              impactDirection: direct.impact_direction,
              impactScore: direct.impact_strength,
            }
          : null,
    },
    {
      label: "상위 흐름 전파",
      value: macroFlow.propagated_impact_count > 0 ? `${macroFlow.propagated_impact_count}개 반영` : "반영 없음",
      detail:
        macroFlow.propagated_impact_count > 0
          ? `${firstFlow ? `${koCode(firstFlow.theme_key)} 흐름` : "시장/테마 흐름"}이 종목 노출도 규칙을 거쳐 점수 입력으로 들어갔다.`
          : "거시·테마 뉴스가 이 종목 점수로 전파된 기록은 아직 없다.",
      href: `/stocks/${encodeURIComponent(data.symbol)}` as Route,
      hrefLabel: "종목 영향 보기",
      newsTitle:
        firstFlow && macroFlow.propagated_impact_count > 0
          ? {
              title: firstFlow.title,
              koreanTitle: firstFlow.korean_title,
              koreanSummary: firstFlow.korean_summary,
              translationConfidence: firstFlow.translation_confidence,
              symbol: data.symbol,
              themeKey: firstFlow.theme_key,
              impactDirection: firstFlow.impact_direction,
              impactScore: firstFlow.impact_strength,
            }
          : null,
    },
    {
      label: "보유 상태 연결",
      value: traceStatusLabel(holding.status),
      detail:
        holding.status === "review_linked"
          ? `${userFacingRecommendationText(holding.action)} · ${userFacingRecommendationText(holding.reason) || "보유 상태 항목과 연결됨"}`
          : holding.status === "position_without_review"
            ? `포지션 ${formatMetricValue(holding.current_weight)}가 있으나 최신 보유 상태 항목은 아직 연결되지 않았다.`
            : "현재 포트폴리오 보유 항목으로 확인되지 않았다.",
      href: holdingHref,
      hrefLabel: "보유 상태 보기",
      newsTitle: null,
    },
  ];
}

function recommendationWaterfallCards({
  data,
  cycleStack,
  macroFlowComponents,
  fundamentalStack,
  qualityDecision,
  decisionWaterfall,
  professionalAudit,
  outcomeMeasured,
}: {
  data: RecommendationDetailData;
  cycleStack: ScoreComponent[];
  macroFlowComponents: ScoreComponent[];
  fundamentalStack: ScoreComponent[];
  qualityDecision: RecommendationQualityDecision;
  decisionWaterfall: RecommendationDetailData["professional_decision_waterfall"];
  professionalAudit: ProfessionalEvidenceAudit;
  outcomeMeasured: boolean;
}) {
  const macroComponent = cycleStack.find((component) => component.component === "macro_regime_score");
  const themeComponent =
    cycleStack.find((component) => component.component === "theme_cycle_score") ?? macroFlowComponents[0];
  const valuationReady = data.valuation_target_range.status === "available";
  const sourceBlocked = professionalAudit.source_blocker.blocked || data.professional_decision_waterfall.status === "source_data_blocked";
  const riskBlocked = professionalAudit.blocked_layer_count > 0 || reviewCount(data.evidence_review.summary.blocked_count) > 0;

  return [
    {
      step: "01",
      label: "거시",
      title: macroComponent ? formatPercent(macroComponent.value) : "거시 근거 대기",
      body: macroComponent
        ? `금리·물가·유동성 같은 상위 환경이 ${data.symbol} 분석 배경으로 연결됐다. ${isZeroWeight(macroComponent.weight) ? "현재 최종 점수 영향은 없다." : "최종 점수에 반영된다."}`
        : "거시 사이클 점수 항목이 아직 연결되지 않았다.",
      href: "#recommendation-cycle-stack",
      hrefLabel: "사이클 근거 보기",
      tone: macroComponent ? "ready" : "watch",
    },
    {
      step: "02",
      label: "테마",
      title: themeComponent ? formatPercent(themeComponent.value) : "테마 전파 대기",
      body: macroFlowComponents.length > 0
        ? `상위 흐름 전파 ${macroFlowComponents.length}개 점수 항목이 있다. 회사명이 직접 언급되지 않아도 노출도 규칙으로 연결된다.`
        : themeComponent
          ? "테마 사이클 항목은 있으나 최근 상위 흐름 전파 근거는 적다."
          : "테마·상위 흐름 전파 근거가 아직 추천 입력으로 연결되지 않았다.",
      href: "#recommendation-macro-flow",
      hrefLabel: "흐름 전파 보기",
      tone: themeComponent || macroFlowComponents.length > 0 ? "ready" : "watch",
    },
    {
      step: "03",
      label: "기업",
      title: data.equity_research ? "리서치 연결" : "리서치 대기",
      body: data.equity_research
        ? "사업 설명, 촉매, 리스크, 무효화 조건이 AI 배치 리서치로 연결됐다."
        : "기업 리서치 결과가 아직 없어 사업 맥락은 제한적으로만 볼 수 있다.",
      href: "#recommendation-equity-research",
      hrefLabel: "기업 리서치 보기",
      tone: data.equity_research ? "ready" : "watch",
    },
    {
      step: "04",
      label: "재무",
      title:
        data.financial_statement_model.status === "available" || data.financial_statement_model.status === "partial"
          ? `${data.financial_statement_model.computed_metric_count}개 지표`
          : "재무 원천 부족",
      body: sourceBlocked
        ? koLabel(professionalAudit.source_blocker.summary)
        : `재무 품질·현금흐름·부채·희석 지표 ${data.financial_statement_model.computed_metric_count}개를 확인한다.`,
      href: "#recommendation-financial-model",
      hrefLabel: "재무 근거 보기",
      tone: sourceBlocked
        ? "blocked"
        : data.financial_statement_model.status === "available" || data.financial_statement_model.status === "partial"
          ? "ready"
          : "watch",
    },
    {
      step: "05",
      label: "밸류에이션",
      title: valuationReady ? `${data.valuation_target_range.method_count}개 방법` : "가격 근거 대기",
      body: valuationReady
        ? `기준 상승여지 ${formatOptionalPercent(data.valuation_target_range.upside_base)}와 안전마진 ${formatOptionalPercent(data.valuation_target_range.margin_of_safety)}를 확인한다.`
        : "목표가 범위나 안전마진이 충분히 연결되지 않았다.",
      href: "#recommendation-valuation",
      hrefLabel: "밸류에이션 보기",
      tone: valuationReady ? "ready" : "watch",
    },
    {
      step: "06",
      label: "리스크",
      title: qualityDecision.status,
      body: riskBlocked
        ? "차단된 근거나 전문 분석 원천 문제가 있어 추천은 기록으로만 남긴다."
        : outcomeMeasured
          ? `성과 측정 완료. 알파 ${formatPercent(data.outcome.alpha)}와 근거 검증 기준을 함께 본다.`
          : "성과 측정창이 아직 끝나지 않았다. 추천 산식 변경이나 자동 주문은 금지 상태다.",
      href: "#recommendation-evidence-review",
      hrefLabel: "리스크 점검 보기",
      tone: riskBlocked ? "blocked" : qualityDecision.tone === "risk-low" ? "ready" : "watch",
    },
    {
      step: "07",
      label: "가상 매매 검증",
      title: decisionWaterfall.paper_validation_input_allowed ? "입력 가능" : "입력 차단",
      body: decisionWaterfall.paper_validation_input_allowed
        ? `가상 매매 검증 입력은 가능하지만 실거래 상태는 ${orderBoundaryLabel(decisionWaterfall.order_boundary)}이다.`
        : `가상 매매 검증 입력 전 차단 조건이 남아 있다. 실거래 상태는 ${orderBoundaryLabel(decisionWaterfall.order_boundary)}이다.`,
      href: "/paper-trading",
      hrefLabel: "가상 매매 상태",
      tone: decisionWaterfall.paper_validation_input_allowed ? "watch" : "blocked",
    },
  ];
}

function RecommendationDecisionWaterfall({
  data,
  cards,
  qualityDecision,
  decisionWaterfall,
}: {
  data: RecommendationDetailData;
  cards: ReturnType<typeof recommendationWaterfallCards>;
  qualityDecision: RecommendationQualityDecision;
  decisionWaterfall: RecommendationDetailData["professional_decision_waterfall"];
}) {
  return (
    <section className={`recommendation-waterfall-panel ${qualityDecision.tone} reveal delay-1`} aria-labelledby="recommendation-waterfall-title">
      <div className="recommendation-waterfall-lead">
        <span>현재 결론</span>
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
            {card.href.startsWith("#") ? (
              <a href={card.href}>{card.hrefLabel}</a>
            ) : (
              <Link href={card.href as Route}>{card.hrefLabel}</Link>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

function RecommendationFocusPanel({
  data,
  items,
  qualityDecision,
  decisionWaterfall,
}: {
  data: RecommendationDetailData;
  items: RecommendationFocusItem[];
  qualityDecision: RecommendationQualityDecision;
  decisionWaterfall: RecommendationDetailData["professional_decision_waterfall"];
}) {
  const firstItem = items[0];

  return (
    <section className={`recommendation-focus-panel ${qualityDecision.tone} reveal delay-1`} aria-labelledby="recommendation-focus-title">
      <div className="recommendation-focus-lead">
        <span>추천서 읽는 순서</span>
        <h2 id="recommendation-focus-title">
          먼저 {firstItem?.title ?? "현재 결론"}부터 본다
        </h2>
        <p>
          이 화면은 {data.symbol} 추천을 바로 매수·매도하라는 지시가 아니라, 원천 데이터와 AI 해석, 전문 분석, 가상 매매 경계가 어디까지 통과했는지
          읽는 추천서다. 아래 카드 순서대로 확인하면 된다.
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
            {item.href.startsWith("#") ? (
              <a href={item.href}>{item.hrefLabel}</a>
            ) : (
              <Link href={item.href as Route}>{item.hrefLabel}</Link>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

export default async function RecommendationPage({ params }: RecommendationPageProps) {
  const { recommendationId } = await params;
  const response = await getRecommendationDetail(recommendationId);
  const data = response.data;
  const evidenceReview = data.evidence_review;
  const qualityDecision = recommendationQualityDecision(data);
  const qualityChecks = recommendationQualityChecks(data);
  const traceCards = evidenceTraceCards(data);
  const macroFlowComponents = data.score_components.filter((component) => macroFlowRows(component).length > 0);
  const cycleStack = cycleStackComponents(data.score_components);
  const fundamentalStack = fundamentalComponents(data.score_components);
  const equityResearch = data.equity_research;
  const industryPosition = data.industry_competitive_position;
  const financialStatementModel = data.financial_statement_model;
  const valuationTargetRange = data.valuation_target_range;
  const valuationItems = equityResearch ? valuationSensitivityItems(equityResearch.valuation_sensitivity) : [];
  const outcomeMeasured = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
  const peerComponent = fundamentalStack.find((component) => component.component === "peer_relative_score");
  const blockedEvidenceCount = reviewCount(evidenceReview.summary.blocked_count);
  const decisionWaterfall = data.professional_decision_waterfall;
  const professionalAudit = data.professional_evidence_audit;
  const readyDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "ready").length;
  const watchDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "watch" || step.tone === "neutral").length;
  const blockedDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "blocked").length;
  const marketCorrelationCount = data.market_correlations.length;
  const professionalResearchSteps: ResearchFlowStep[] = decisionWaterfall.steps.map((step, index) => ({
    id: step.step_key,
    label: String(index + 1).padStart(2, "0"),
    title: decisionCopy(step.title),
    status: decisionCopy(step.status),
    tone: researchFlowTone(step.tone),
    body: `${decisionCopy(step.decision)}. ${decisionCopy(step.detail)}`,
    facts: step.facts.map((fact) => ({
      label: decisionCopy(fact.label),
      value: decisionCopy(fact.value),
    })),
    href: step.href ? (step.href as Route) : undefined,
    hrefLabel: step.href_label ? decisionCopy(step.href_label) : undefined,
  }));
  const waterfallCards = recommendationWaterfallCards({
    data,
    cycleStack,
    macroFlowComponents,
    fundamentalStack,
    qualityDecision,
    decisionWaterfall,
    professionalAudit,
    outcomeMeasured,
  });
  const immediateFocusItems = recommendationImmediateFocus({
    data,
    qualityDecision,
    decisionWaterfall,
    professionalAudit,
    blockedDecisionStepCount,
    watchDecisionStepCount,
    outcomeMeasured,
    marketCorrelationCount,
    macroFlowComponents,
    fundamentalStack,
  });

  return (
    <div className="pageStack">
      <section className="decision-brief reveal" aria-labelledby="recommendation-detail-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">
            추천 상세 · {koCode(data.strategy_name)} · {koCode(data.horizon_type)} · {data.as_of_date}
          </span>
          <h1 className="decision-brief-title" id="recommendation-detail-title">
            {data.symbol} · {qualityDecision.status}
          </h1>
          <p className="decision-brief-copy">
            {qualityDecision.summary} 추천은 자동 매매 명령이 아니며, 이 화면은 근거가 어디서 왔고 가상 매매나 실거래 경계까지 통과했는지만 판단하게 한다.
          </p>
          <div className="decision-brief-meta" aria-label="추천 상세 핵심 상태">
            <span>점수 {formatPercent(data.score)}</span>
            <span>추천 {koCode(data.recommendation)}</span>
            <span>가상 매매 {decisionWaterfall.paper_validation_input_allowed ? "입력 가능" : "입력 차단"}</span>
            <span>실거래 {decisionWaterfall.broker_submit_allowed ? "허용" : "차단"}</span>
            <span>시장 동조성 {marketCorrelationCount.toLocaleString("ko-KR")}개</span>
          </div>
        </div>

        <div className="decision-brief-grid">
          <Link className="decision-card primary" href="#recommendation-professional-flow">
            <span>현재 결론</span>
            <strong>{qualityDecision.status}</strong>
            <small>전문 분석 단계에서 무엇이 통과·차단됐는지 먼저 확인한다.</small>
          </Link>
          <Link className="decision-card" href={stockHref(data.symbol)}>
            <span>종목 맥락</span>
            <strong>{data.symbol} 상세</strong>
            <small>직접 뉴스, 상위 흐름, 재무·밸류에이션 근거를 종목 단위로 이어서 본다.</small>
          </Link>
          <Link className="decision-card" href="#recommendation-professional-flow">
            <span>분석 단계</span>
            <strong>{readyDecisionStepCount}/{decisionWaterfall.steps.length} 통과</strong>
            <small>주의 {watchDecisionStepCount}개 · 차단 {blockedDecisionStepCount}개.</small>
          </Link>
          <Link className="decision-card" href="/paper-trading">
            <span>거래 경계</span>
            <strong>{orderBoundaryLabel(decisionWaterfall.order_boundary)}</strong>
            <small>가상 매매와 실거래 제출 가능 여부를 분리해서 확인한다.</small>
          </Link>
          <Link className={marketCorrelationCount > 0 ? "decision-card is-good" : "decision-card is-watch"} href="#recommendation-market-correlations">
            <span>시장 동조성</span>
            <strong>{marketCorrelationCount.toLocaleString("ko-KR")}개 비교</strong>
            <small>추천 종목이 지수·섹터·금리·달러·원자재와 같이 움직였는지 확인한다.</small>
          </Link>
        </div>
      </section>

      <RecommendationFocusPanel
        data={data}
        items={immediateFocusItems}
        qualityDecision={qualityDecision}
        decisionWaterfall={decisionWaterfall}
      />

      <RecommendationDecisionWaterfall
        data={data}
        cards={waterfallCards}
        qualityDecision={qualityDecision}
        decisionWaterfall={decisionWaterfall}
      />

      <section className="bento-card reveal delay-1" aria-label="중장기 추천 품질 상태">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap", marginBottom: "20px" }}>
          <div>
            <span className="metric-sub">중장기 품질 상태</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{qualityDecision.status}</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "820px" }}>
              {qualityDecision.summary}
            </p>
          </div>
          <span className={`risk-tag ${qualityDecision.tone}`}>읽기 전용 평가</span>
        </div>
        <div className="flow-steps">
          {qualityChecks.map((check) => (
            <article className="flow-step" key={check.label}>
              <span>{check.label}</span>
              <strong>{check.value}</strong>
              <p>{check.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="bento-card reveal delay-1" aria-label="추천 사용 가능 범위">
        <div className="section-heading">
          <div>
            <span className="metric-sub">추천 사용 가능 범위</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>이 추천을 어디까지 써도 되는가</h2>
          </div>
          <span className={`risk-tag ${blockedDecisionStepCount > 0 ? "risk-high" : decisionWaterfall.paper_validation_input_allowed ? "risk-low" : "risk-medium"}`}>
            {blockedDecisionStepCount > 0 ? "입력 차단" : decisionWaterfall.paper_validation_input_allowed ? "분석 입력 가능" : "근거 대기"}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          {userFacingRecommendationText(decisionWaterfall.summary)} 이 결과는 추천 점수를 바꾸지 않고, 이 추천을 가상 매매 검증·보유 상태·실거래 차단 중 어디까지
          넘길 수 있는지만 설명한다.
        </p>
        <div className="status-rail compact-rail" aria-label="추천 사용 가능 범위 요약">
          <div className="rail-cell">
            <span>전문 흐름</span>
            <strong>{userFacingRecommendationText(decisionWaterfall.status)}</strong>
            <small>{decisionWaterfall.as_of_date}</small>
          </div>
          <div className="rail-cell">
            <span>단계 상태</span>
            <strong>{readyDecisionStepCount}/{decisionWaterfall.steps.length}</strong>
            <small>주의 {watchDecisionStepCount} · 차단 {blockedDecisionStepCount}</small>
          </div>
          <div className="rail-cell">
            <span>가상 매매 입력</span>
            <strong>{decisionWaterfall.paper_validation_input_allowed ? "허용" : "차단"}</strong>
            <small>원천 차단이면 입력 금지</small>
          </div>
          <div className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryLabel(decisionWaterfall.order_boundary)}</strong>
            <small>자동 주문 {decisionWaterfall.automatic_order_allowed || decisionWaterfall.broker_submit_allowed ? "허용" : "금지"}</small>
          </div>
        </div>
      </section>

      <section className="bento-card reveal delay-1" id="recommendation-market-correlations" aria-label="추천 시장 동조성 리스크">
        <div className="section-heading">
          <div>
            <span className="metric-sub">시장 동조성 리스크</span>
            <h2>{data.symbol} 추천이 어떤 시장 변수에 같이 흔들리는지 본다</h2>
          </div>
          <Link className="btn btn-secondary" href="/market-map">
            시장 지도 보기
          </Link>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          이 섹션은 추천 점수를 새로 만들지 않는다. 최근 수익률 동조성을 이용해 같은 방향으로 몰린 리스크,
          헤지 필요성, 포트폴리오 집중 여부를 확인한다. 상관관계는 원인을 증명하지 않는다.
        </p>
        {data.market_correlations.length > 0 ? (
          <div className="detail-path-grid">
            {data.market_correlations.slice(0, 6).map((correlation) => (
              <article
                className={correlationTone(correlation)}
                key={`${correlation.primary_asset_key}-${correlation.comparison_asset_key}-${correlation.lookback_days}`}
              >
                <span>
                  {correlationRelationshipLabel(correlation.relationship_label)} · {correlation.lookback_days}일 · 신뢰도{" "}
                  {formatOptionalPercent(correlation.confidence)}
                </span>
                <strong>
                  {correlation.primary_display_name} ↔ {correlation.comparison_display_name}
                </strong>
                <small>
                  상관계수 {formatCoefficient(correlation.correlation)} · 베타 {formatCoefficient(correlation.beta)} · 관측{" "}
                  {correlation.observation_count.toLocaleString("ko-KR")}개
                </small>
                <p>{correlation.summary_ko}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            아직 이 추천 종목의 시장 동조성이 계산되지 않았다. correlation-analysis-run이 실행되면 추천 리스크 확인용으로 표시된다.
          </div>
        )}
      </section>

      <section id="recommendation-professional-flow">
        <ProfessionalResearchFlow
          eyebrow="전문 분석 흐름"
          title={`${data.symbol} 추천을 분석서처럼 읽는다`}
          summary={userFacingRecommendationText(decisionWaterfall.summary)}
          footer={`추천 산식 정책: ${userFacingRecommendationText(decisionWaterfall.score_policy)}. 실거래 상태: ${orderBoundaryLabel(decisionWaterfall.order_boundary)}.`}
          steps={professionalResearchSteps}
        />
      </section>

      <section className="bento-card reveal delay-1" aria-label="추천 전문 분석 감사">
        <div className="section-heading">
          <div>
            <span className="metric-sub">추천 전문 분석 감사</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{professionalAudit.title}</h2>
          </div>
          <span className={`risk-tag ${professionalAuditTone(professionalAudit)}`}>
            {userFacingRecommendationText(professionalAudit.status)}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0, maxWidth: "920px" }}>
          {userFacingRecommendationText(professionalAudit.summary)} {userFacingRecommendationText(professionalAudit.next_action)}
        </p>

        <div className="status-rail compact-rail" aria-label="추천 전문 분석 감사 요약">
          <div className="rail-cell">
            <span>분석 대상</span>
            <strong>{professionalProductLabel(professionalAudit.product_type)}</strong>
            <small>{professionalAudit.symbol} · {professionalAudit.as_of_date}</small>
          </div>
          <div className="rail-cell">
            <span>근거 커버리지</span>
            <strong>{formatPercent(professionalAudit.coverage_ratio)}</strong>
            <small>
              완료 {professionalAudit.available_layer_count}/{professionalAudit.expected_layer_count}
              {professionalAudit.partial_layer_count > 0 ? ` · 일부 ${professionalAudit.partial_layer_count}` : ""}
            </small>
          </div>
          <div className="rail-cell">
            <span>차단·대기</span>
            <strong>{professionalAudit.blocked_layer_count + professionalAudit.pending_layer_count}개</strong>
            <small>누락 {professionalAudit.missing_layer_count}개</small>
          </div>
          <div className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryLabel(professionalAudit.order_boundary)}</strong>
            <small>추천 산식 변경 {professionalAudit.automatic_weight_change_allowed ? "허용" : "금지"} · 실거래 주문 {professionalAudit.broker_submit_allowed ? "허용" : "금지"}</small>
          </div>
        </div>

        {professionalAudit.source_blocker.blocked ? (
          <div className="empty-state" style={{ marginTop: "18px" }}>
            <strong>{professionalAudit.source_blocker.blocker_label || "원천 차단"}</strong>
            <p style={{ margin: "8px 0 0", color: "var(--text-secondary)" }}>
              {userFacingRecommendationText(professionalAudit.source_blocker.summary)} {userFacingRecommendationText(professionalAudit.source_blocker.next_action)}
            </p>
          </div>
        ) : null}

        {professionalAudit.missing_layer_labels.length > 0 ? (
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "18px" }}>
            {professionalAudit.missing_layer_labels.map((label) => (
              <span className="risk-tag risk-medium" key={label}>{decisionCopy(label)}</span>
            ))}
          </div>
        ) : null}

        <div className="flow-steps" style={{ marginTop: "18px" }}>
          {professionalAudit.layer_checks.map((layer) => (
            <article className="flow-step" key={layer.key}>
              <span>{decisionCopy(layer.label)}</span>
              <strong className={`risk-tag ${professionalLayerTone(layer.status)}`}>
                {professionalLayerStatusLabel(layer.status)}
              </strong>
              <p>{decisionCopy(layer.detail)}</p>
              <small style={{ color: "var(--text-secondary)", fontWeight: 800 }}>
                원천: {userFacingRecommendationText(layer.source)}
              </small>
              {layer.href ? <Link href={layer.href as Route}>관련 화면 열기</Link> : null}
            </article>
          ))}
        </div>
      </section>

      <section id="recommendation-financial-model">
        <FinancialStatementModelPanel model={financialStatementModel} symbol={data.symbol} />
      </section>

      <FundInstrumentAnalysisPanel analysis={data.fund_instrument_analysis} />

      <section id="recommendation-valuation">
        <ValuationTargetRangeCard
          valuation={valuationTargetRange}
          eyebrow="추천 가격 근거"
          title={`${data.symbol} 목표가 범위와 상승여지`}
        />
      </section>

      {cycleStack.length > 0 ? (
        <section className="bento-card reveal delay-1" id="recommendation-cycle-stack" aria-label="계층형 사이클 추천 경로">
          <div style={{ marginBottom: "22px" }}>
            <span className="metric-sub">계층형 사이클 경로</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>왜 {data.symbol}이 지금 추천 신호로 올라왔는가</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "860px" }}>
              추천 점수를 한 덩어리로 보지 않고 거시 환경, 도메인, 테마, 종목 자체 상태, 충돌 감점을 분리해 보여준다.
              현재 반영 전 항목은 결과를 흔들지 않기 위한 설명·검증용 항목이며, 품질 검증 후 별도 승인으로만 반영한다.
            </p>
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
            gap: "12px",
          }}>
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
                    <span>점수 {formatPercent(component.value)}</span>
                    <span>현재 반영 비중 {formatPercent(component.weight)}</span>
                    <span>{isZeroWeight(component.weight) ? "현재 최종 점수 영향 없음" : "최종 점수에 반영됨"}</span>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      ) : null}

      {fundamentalStack.length > 0 ? (
        <section className="bento-card reveal delay-1" aria-label="재무와 밸류에이션 추천 근거">
          <div style={{ marginBottom: "22px" }}>
            <span className="metric-sub">재무·밸류에이션 근거</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>뉴스가 아니라 기업 자체가 받쳐주는가</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "900px" }}>
              이 영역은 프로 애널리스트식 분석 축이다. 현재는 성과 표본이 부족하므로 최종 추천 점수에는 반영하지 않고,
              재무 품질과 가격 매력도가 추천 논리를 보강하거나 반박하는지 확인하는 근거로만 쓴다.
            </p>
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
            gap: "14px",
          }}>
            {fundamentalStack.map((component) => {
              const meta = FUNDAMENTAL_COMPONENT_META[component.component];
              return (
                <article
                  className="detail-path-card"
                  key={`fundamental-${component.component}`}
                  style={{
                    background: "linear-gradient(180deg, rgba(251,250,246,0.96), rgba(96,70,35,0.08))",
                    minHeight: "220px",
                  }}
                >
                  <span>{meta?.lens ?? "기업 분석"}</span>
                  <strong>{meta?.title ?? scoreComponentLabel(component.component)}</strong>
                  <p>{meta?.body ?? provenanceDetail(component)}</p>
                  <div style={{ marginTop: "14px", display: "grid", gap: "6px", color: "var(--text-secondary)", fontSize: "0.8rem", fontWeight: 800 }}>
                    <span>분석 점수 {formatPercent(component.value)}</span>
                    <span>{isZeroWeight(component.weight) ? "최종 추천 점수에는 아직 미반영" : `현재 반영 비중 ${formatPercent(component.weight)}`}</span>
                    <span>{component.provenance?.label ? userFacingRecommendationText(component.provenance.label) : "기업 분석 근거"}</span>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      ) : null}

      <IndustryCompetitivePositionPanel
        position={industryPosition}
        symbol={data.symbol}
        peerComponent={peerComponent}
      />

      <section className="bento-card reveal delay-1" id="recommendation-equity-research" aria-label="기업 리서치 연결">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "18px", flexWrap: "wrap", marginBottom: "22px" }}>
          <div>
            <span className="metric-sub">기업 리서치 연결</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>
              {equityResearch ? userFacingRecommendationText(equityResearch.title) : `${data.symbol} 기업 리서치가 아직 연결되지 않았다`}
            </h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "900px" }}>
              추천을 뉴스 신호만으로 보지 않기 위해 배치 AI가 만든 기업 분석 결과를 같이 보여준다.
              이 리포트는 추천 점수와 주문을 직접 바꾸지 않고, 재무·밸류에이션 점수 항목을 해석하는 읽기 전용 근거다.
            </p>
          </div>
          {equityResearch ? (
            <span className="bento-badge" style={{ margin: 0 }}>
              {providerLabel(equityResearch.provider)} • {equityResearch.as_of_date}
            </span>
          ) : null}
        </div>

        {equityResearch ? (
          <>
            <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
              {userFacingRecommendationText(equityResearch.korean_summary)}
            </p>
            <div className="status-rail compact-rail" aria-label="기업 리서치 구성">
              <div className="rail-cell">
                <span>핵심 변화</span>
                <strong>{equityResearch.key_points.length}</strong>
                <small>사업·재무 포인트</small>
              </div>
              <div className="rail-cell">
                <span>촉매</span>
                <strong>{equityResearch.catalysts.length}</strong>
                <small>좋아질 조건</small>
              </div>
              <div className="rail-cell">
                <span>리스크</span>
                <strong>{equityResearch.risks.length}</strong>
                <small>틀릴 수 있는 이유</small>
              </div>
              <div className="rail-cell">
                <span>무효화 조건</span>
                <strong>{equityResearch.invalidation_conditions.length}</strong>
                <small>투자 논리 재확인 기준</small>
              </div>
            </div>

            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
              gap: "14px",
              marginTop: "18px",
            }}>
              <ResearchList
                title="핵심 포인트"
                items={equityResearch.key_points}
                emptyText="핵심 변화가 아직 구조화되지 않았다."
              />
              <ResearchList
                title="촉매"
                items={equityResearch.catalysts}
                emptyText="상승 촉매가 아직 구조화되지 않았다."
              />
              <ResearchList
                title="리스크"
                items={equityResearch.risks}
                emptyText="리스크가 아직 구조화되지 않았다."
              />
              <ResearchList
                title="무효화 조건"
                items={equityResearch.invalidation_conditions}
                emptyText="투자 논리 무효화 조건이 아직 구조화되지 않았다."
              />
            </div>

            {valuationItems.length > 0 ? (
              <div className="stock-meta-grid" style={{ marginTop: "18px" }}>
                {valuationItems.map((item) => (
                  <Fragment key={item.key}>
                    <span>{userFacingRecommendationText(item.key)}</span>
                    <strong>{userFacingRecommendationText(item.value)}</strong>
                  </Fragment>
                ))}
              </div>
            ) : null}

            <div className="btn-row" style={{ marginTop: "18px" }}>
              <Link className="btn btn-primary" href={stockHref(data.symbol)}>
                종목 리서치 전체 보기
              </Link>
              {equityResearch.source_document_ids.slice(0, 3).map((documentId, index) => (
                <Link className="btn btn-secondary" href={sourceDocumentHref(documentId)} key={documentId}>
                  원천 문서 {index + 1}
                </Link>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state">
            아직 이 종목의 기업 리서치 결과가 없다. 기업 리서치 배치가 실행되면 사업 설명, 재무 변화,
            촉매, 리스크, 무효화 조건이 이곳에 연결된다.
          </div>
        )}
      </section>

      <section className="bento-card reveal delay-1" id="recommendation-evidence-trace" aria-label="추천 근거 흐름 요약">
        <div style={{ marginBottom: "20px" }}>
          <span className="metric-sub">근거 흐름 요약</span>
          <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>무엇을 보고 이 추천을 확인해야 하나</h2>
          <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "820px" }}>
            뉴스와 AI 구조화 결과는 바로 주문으로 이어지지 않는다. 직접 종목 뉴스, 시장·테마 흐름, 보유 상태를
            분리한 뒤 AI 근거 검증이 추천 입력으로 쓸 수 있는지 확인한다.
          </p>
        </div>

        <div className="flow-steps">
          {traceCards.map((card) => (
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

      {macroFlowComponents.length > 0 ? (
        <section className="bento-card reveal delay-1" id="recommendation-macro-flow" aria-label="상위 흐름 전파 경로">
          <div style={{ marginBottom: "22px" }}>
            <span className="metric-sub">상위 흐름 전파 경로</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>시장·테마 뉴스가 {data.symbol} 점수에 들어간 방식</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "820px" }}>
              이 패널은 종목을 직접 언급하지 않은 뉴스가 테마와 종목 노출도 규칙을 거쳐 추천 점수에 들어간 경로다.
              전체 전파 근거 수와 아래에 표시된 최근 사례 수는 다를 수 있다. AI가 주문을 결정한 것이 아니라,
              구조화된 흐름이 점수 입력으로만 쓰였다.
            </p>
          </div>

          <div className="bento-list">
            {macroFlowComponents.map((component) => {
              const rows = macroFlowRows(component);
              return (
                <div className="bento-list-item" key={component.component} style={{ alignItems: "flex-start", flexDirection: "column" }}>
                  <div style={{ width: "100%", display: "flex", justifyContent: "space-between", gap: "16px", flexWrap: "wrap" }}>
                    <div>
                      <span className="metric-sub">{scoreComponentLabel(component.component)}</span>
                      <strong>{formatPercent(component.value)} · 현재 반영 비중 {formatPercent(component.weight)}</strong>
                    </div>
                    <span style={{ color: "var(--text-secondary)" }}>
                      전체 전파 근거 {component.provenance?.evidence?.propagated_impact_count ?? rows.length}개 · 최근 표시 {rows.length}개
                    </span>
                  </div>

                  <div className="relationship-list" aria-label={`${data.symbol} 상위 흐름 전파 근거`}>
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
                            symbol={data.symbol}
                            themeKey={flow.theme_key}
                            impactDirection={flow.impact_direction}
                            impactScore={flow.impact_strength}
                          />
                          <small>
                            {koCode(flow.impact_direction)} · 강도 {formatMetricValue(flow.impact_strength)} · 자료 신뢰도 {formatMetricValue(flow.confidence)}
                          </small>
                          <small>
                            노출도 {formatMetricValue(flow.exposure_weight)} · 발생 {flow.event_at}
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
      ) : null}

      <section
        className={`recommendation-evidence-panel reveal delay-1 ${professionalAuditTone(professionalAudit)}`}
        id="recommendation-evidence-review"
        aria-label="추천 근거 연결 점검"
      >
        <div className="recommendation-evidence-head">
          <div>
            <span>근거 연결 점검</span>
            <h2>{koCode(evidenceReview.quality_status)}</h2>
            <p>
              이 점검은 추천 점수를 새로 만들지 않는다. 투자 논리, 점수 항목, 뉴스·AI 해석, 성과 측정이
              서로 연결됐는지 확인하고, 부족하면 추천을 기록으로만 남긴다.
            </p>
          </div>
          <div className="recommendation-evidence-summary" aria-label="근거 연결 점검 요약">
            <div>
              <span>통과</span>
              <strong>{reviewCount(evidenceReview.summary.pass_count)}</strong>
              <small>기준 충족</small>
            </div>
            <div>
              <span>주의</span>
              <strong>{reviewCount(evidenceReview.summary.warning_count)}</strong>
              <small>보강 필요</small>
            </div>
            <div>
              <span>차단</span>
              <strong>{reviewCount(evidenceReview.summary.blocked_count)}</strong>
              <small>진행 금지</small>
            </div>
          </div>
        </div>

        <div className="recommendation-gate-grid">
          {evidenceReview.gates.map((gate) => (
            <article className={`recommendation-gate-card ${gateToneClass(gate.status)}`} key={gate.gate_key}>
              <div>
                <span style={{ color: gateStatusColor(gate.status) }}>{gateStatusLabel(gate.status)}</span>
                <strong>{userFacingRecommendationText(gate.label)}</strong>
                <p>{userFacingRecommendationText(gate.detail)}</p>
              </div>
              <small>{userFacingRecommendationText(gate.next_step)}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="recommendation-score-audit-grid reveal delay-1" aria-label="추천 점수와 성과 측정">
        <article className="recommendation-score-panel">
          <div className="recommendation-evidence-head compact">
            <div>
              <span>점수 근거</span>
              <h2>추천 점수 입력이 어디서 왔는가</h2>
              <p>가격·뉴스·상위 흐름·재무 근거를 섞어 보지 않고, 각 점수 항목의 출처와 현재 반영 비중을 분리해 본다.</p>
            </div>
          </div>

          <div className="recommendation-score-card-grid">
            {data.score_components.map((component) => {
              const href = evidenceHref(component.evidence_id, data.symbol);
              const badges = provenanceBadges(component);
              return (
                <article className={`recommendation-score-card ${scoreComponentTone(component)}`} key={component.component}>
                  <div className="recommendation-score-card-head">
                    <span>{sourceTypeLabel(component.provenance?.source_type)}</span>
                    <strong>{scoreComponentLabel(component.component)}</strong>
                    <b>{formatPercent(component.value)}</b>
                  </div>
                  <p>{provenanceDetail(component)}</p>
                  <div className="recommendation-score-badges">
                    {badges.map((badge) => (
                      <span key={`${component.component}-${badge}`}>{badge}</span>
                    ))}
                  </div>
                  <div className="recommendation-score-metrics">
                    <div>
                      <span>현재 반영 비중</span>
                      <strong>{formatPercent(component.weight)}</strong>
                    </div>
                    <div>
                      <span>사용 경계</span>
                      <strong>{isZeroWeight(component.weight) ? "설명용" : "점수 반영"}</strong>
                    </div>
                  </div>
                  <div className="recommendation-score-links">
                    {href ? (
                      <Link href={href}>
                        {evidenceLinkLabel(component.evidence_id)}
                      </Link>
                    ) : (
                      <span>연결된 상세 근거 없음</span>
                    )}
                  </div>
                  <AuditMetadata items={provenanceMetadata(component)} summary="계산 입력 출처 보기" />
                </article>
              );
            })}
          </div>
        </article>

        <article className={`recommendation-outcome-panel ${outcomeTone(outcomeMeasured, data.outcome.alpha)}`}>
          <div className="recommendation-evidence-head compact">
            <div>
              <span>성과 측정</span>
              <h2>{outcomeMeasured ? koCode(data.outcome.label) : "아직 성과 측정 전"}</h2>
              <p>
                추천이 맞았는지는 측정창이 끝난 뒤에만 판단한다. 성과가 없으면 추천 산식 반영 비중을 바꾸지 않는다.
              </p>
            </div>
            <Link className="btn btn-primary" href={`/theses/${data.linked_thesis_id}`}>
              연결된 투자 논리 열기
            </Link>
          </div>

          <div className="recommendation-outcome-grid">
            <div>
              <span>알파</span>
              <strong>{outcomeMeasured ? formatPercent(data.outcome.alpha) : "측정 전"}</strong>
            </div>
            <div>
              <span>절대수익률</span>
              <strong>{outcomeMeasured ? formatPercent(data.outcome.absolute_return) : "측정 전"}</strong>
            </div>
            <div>
              <span>벤치마크 수익률</span>
              <strong>{outcomeMeasured ? formatPercent(data.outcome.benchmark_return) : "측정 전"}</strong>
            </div>
            <div>
              <span>측정 종료일</span>
              <strong>{outcomeMeasured ? data.outcome.measurement_end_date : "성과 측정창 대기"}</strong>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}
