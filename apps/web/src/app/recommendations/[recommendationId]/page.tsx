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
    body: "금리, 물가, 유동성, 성장 같은 최상위 환경이 이 종목 검토에 어떤 배경으로 들어왔는지 본다.",
  },
  domain_cycle_score: {
    step: "2. 도메인",
    body: "기술, 에너지, 금융처럼 더 넓은 사업 영역의 사이클이 종목 후보를 밀어주는지 확인한다.",
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
    body: "상위 흐름과 종목 상태가 충돌하면 추천 점수에 감점 후보로 남긴다.",
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
    body: "DCF-lite, 상대 배수, 시나리오 범위를 근거로 비싸게 따라사는 후보인지 아닌지 확인한다.",
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
    body: "활성 thesis, 무효화 조건, 보유 검토 맥락이 추천 방향과 충돌하지 않는지 점검한다.",
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
        items.map((item) => <p key={item}>{koLabel(item)}</p>)
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
    advantaged: "우위 후보",
    in_line: "평균권",
    challenged: "열위 검토",
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
            ? model.summary
            : "추천서에서 매출, 마진, 현금흐름, 부채, 이익 품질을 확인하려면 SEC companyfacts와 재무 정규화가 먼저 필요하다. 이 값이 없으면 뉴스나 사이클만으로 중장기 판단을 확정하지 않는다."}
        </p>
        {sourceBlocker ? (
          <div className="status-rail compact-rail" aria-label="추천 재무 원천 차단 사유" style={{ marginTop: "18px" }}>
            <div className="rail-cell">
              <span>차단 사유</span>
              <strong>{sourceBlocker.label}</strong>
              <small>{sourceBlocker.blocker_code}</small>
            </div>
            <div className="rail-cell">
              <span>확인 위치</span>
              <strong>{sourceBlocker.source_pipeline}</strong>
              <small>{sourceBlocker.source_run_id || "정적 분류"}</small>
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
            {model.summary} 이 영역은 추천 총점을 바꾸지 않는 읽기 전용 근거이며, 재무 모델이 추천 논리를 보강하는지
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
        <span className="metric-sub">ETF·펀드 추천 검토</span>
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
            <p>보유 비중 {formatOptionalPercent(holding.target_weight)} · 신뢰도 {formatOptionalPercent(holding.confidence)}</p>
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
          <span>주문 경계</span>
          <strong>{koCode(analysis.order_boundary)}</strong>
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
            추천 총점에는 평가 전까지 직접 반영하지 않는다.
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
          <small>{peerComponent ? "현재 총점 미반영" : "추천 점수 항목 대기"}</small>
        </div>
        <div className="rail-cell">
          <span>지표 커버리지</span>
          <strong>{position.metric_coverage_count.toLocaleString("ko-KR")}</strong>
          <small>{position.source_run_id ?? "실행 번호 없음"}</small>
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
          계산 근거: {koLabel(position.rationale)}
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

  const badges = [koCode(provenance.source_type)];
  if (provenance.feature_code) {
    badges.push(koCode(provenance.feature_code));
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
      badges.push(koCode(provenance.evidence.cycle_stack_level));
    }
  }
  if (provenance.source_type === "fundamental_context") {
    badges.push(isZeroWeight(component.weight) ? "현재 총점 미반영" : "총점 반영");
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
      { label: "점수 항목", value: koCode(component.component) },
      { label: "근거 연결 번호", value: component.evidence_id },
    ];
  }

  return [
    { label: "점수 항목", value: koCode(component.component) },
    { label: "근거 연결 번호", value: component.evidence_id },
    { label: "입력 종류", value: koCode(provenance.source_type) },
    { label: "입력 설명", value: koLabel(provenance.label) },
    { label: "가격 지표", value: provenance.feature_code ? koCode(provenance.feature_code) : null },
    { label: "가격 지표 이름", value: provenance.feature_name ? koCode(provenance.feature_name) : null },
    { label: "기준일", value: provenance.as_of_date },
    { label: "수집·계산 실행 번호", value: provenance.source_run_id },
    { label: "종목군 계산 묶음", value: provenance.universe_batch_id },
    { label: "가격 계산 버전", value: provenance.evidence?.feature_set_version },
    { label: "종목군 순위", value: provenance.rank_position },
    { label: "종목군 전체 수", value: provenance.universe_member_count },
    { label: "관측치 수", value: provenance.observation_count ?? provenance.evidence?.observation_count },
    { label: "첫 가격일", value: provenance.evidence?.first_trade_date },
    { label: "최근 가격일", value: provenance.latest_trade_date ?? provenance.evidence?.latest_trade_date },
    { label: "사이클 계층", value: provenance.evidence?.cycle_stack_level ? koCode(provenance.evidence.cycle_stack_level) : null },
    { label: "선택 사이클 노드", value: provenance.evidence?.cycle_stack_node_code ? koCode(provenance.evidence.cycle_stack_node_code) : null },
    { label: "사이클 설명", value: provenance.evidence?.cycle_stack_explanation ? koLabel(provenance.evidence.cycle_stack_explanation) : null },
    { label: "적용 메모", value: provenance.evidence?.cycle_stack_note ? koLabel(provenance.evidence.cycle_stack_note) : null },
    { label: "기업 분석 항목", value: provenance.evidence?.fundamental_component_name ? koCode(provenance.evidence.fundamental_component_name) : null },
    { label: "기업 분석 설명", value: provenance.evidence?.fundamental_explanation ? koLabel(provenance.evidence.fundamental_explanation) : null },
    { label: "기업 분석 메모", value: provenance.evidence?.fundamental_note ? koLabel(provenance.evidence.fundamental_note) : null },
    { label: "전파 근거 수", value: provenance.evidence?.propagated_impact_count },
    { label: "선정 규칙", value: provenance.selection_rule },
    { label: "편입 사유", value: provenance.inclusion_reason },
  ];
}

function provenanceDetail(component: ScoreComponent) {
  const provenance = component.provenance;
  if (!provenance) {
    return "아직 이 점수의 입력 출처 요약이 붙지 않았다.";
  }
  if (provenance.source_type === "market_feature") {
    const featureName = provenance.feature_code ? koCode(provenance.feature_code) : koCode(provenance.feature_name ?? "market_feature");
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
    const status = isZeroWeight(component.weight) ? "현재 추천 총점에는 반영하지 않는 검증 항목" : "추천 총점에 반영되는 항목";
    return `${meta?.lens ?? "기업 분석"}: ${meta?.body ?? koLabel(provenance.label)} ${status}이다.`;
  }
  return koLabel(provenance.label);
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
    return "AI 근거 열기";
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

function recommendationQualityDecision(data: RecommendationDetailData) {
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
      summary: "정기 재무제표나 검증된 parser가 없어 이 추천은 기록으로만 보존한다. 뉴스·AI·가격 근거가 있어도 전문 투자 판단이나 페이퍼 검증 입력으로 넘기면 안 된다.",
    };
  }
  if (blockedCount > 0) {
    return {
      status: "검토 차단",
      tone: "risk-high",
      summary: "연결된 투자 논리, 점수 구성요소, 성과 측정 중 차단 조건이 있어 투자 검토로 넘기면 안 된다.",
    };
  }
  if (adverseRecommendation || weakScore) {
    return {
      status: "투자 보류",
      tone: "risk-high",
      summary: "현재 추천 조치나 점수가 중장기 신규 투자 후보로 보기 어렵다. 근거는 보존하되 채택하지 않는다.",
    };
  }
  if (warningCount > 0 || negativeAlpha || !outcomeMeasured) {
    return {
      status: "보강 후 검토",
      tone: "risk-medium",
      summary: "핵심 근거는 있으나 성과 측정, 근거 연결, 또는 최근 성과가 충분히 강하지 않아 AI 보강 검토가 먼저다.",
    };
  }
  return {
    status: "AI 검토 통과",
    tone: "risk-low",
    summary: "근거와 성과가 연결되어 있어 중장기 투자 후보로 자동 검토를 통과했다.",
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
        ? "AI 검토 통과"
        : koCode(data.evidence_review.quality_status),
      detail: `뉴스·AI 근거 ${aiEvidenceCount}개 · 가격/순위 출처 기록 ${marketProvenanceCount}개`,
    },
    {
      label: "성과 확인",
      value: outcomeMeasured ? koCode(data.outcome.label) : "성과 미측정",
      detail: outcomeMeasured
        ? `알파 ${formatPercent(data.outcome.alpha)} · 측정 종료 ${data.outcome.measurement_end_date}`
        : "성과 측정 기간이 끝나면 성과 기록을 생성해야 한다.",
    },
    {
      label: "주문 경계",
      value: "자동 주문 없음",
      detail: "이 판정은 추천 검토 결과이며 증권사 주문 흐름을 실행하지 않는다.",
    },
  ];
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
      label: "뉴스/AI 분석",
      value: traceStatusLabel(direct.status),
      detail:
        direct.status === "linked"
          ? `직접 종목 뉴스나 AI 근거가 추천 입력으로 연결됐다. 신뢰도 ${formatMetricValue(direct.confidence)}.`
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
      label: "보유검토 연결",
      value: traceStatusLabel(holding.status),
      detail:
        holding.status === "review_linked"
          ? `${koCode(holding.action)} · ${holding.reason ?? "보유검토 항목과 연결됨"}`
          : holding.status === "position_without_review"
            ? `포지션 ${formatMetricValue(holding.current_weight)}가 있으나 최신 보유검토 항목은 아직 연결되지 않았다.`
            : "현재 포트폴리오 보유 항목으로 확인되지 않았다.",
      href: holdingHref,
      hrefLabel: "보유 검토 보기",
      newsTitle: null,
    },
  ];
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
  const professionalResearchSteps: ResearchFlowStep[] = decisionWaterfall.steps.map((step, index) => ({
    id: step.step_key,
    label: String(index + 1).padStart(2, "0"),
    title: step.title,
    status: step.status,
    tone: researchFlowTone(step.tone),
    body: `${step.decision}. ${step.detail}`,
    facts: step.facts,
    href: step.href ? (step.href as Route) : undefined,
    hrefLabel: step.href_label ?? undefined,
  }));

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          추천 • {koCode(data.strategy_name)} • {koCode(data.horizon_type)} • {data.as_of_date}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>{data.symbol} 추천 검토서</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
              추천은 자동 매매 명령이 아니라 점수, 증거, 측정된 성과를 함께 검토하는 입력값이다.
              포트폴리오 조치 전 연결된 투자 논리와 성과를 함께 확인한다.
            </p>
          </div>
          
          <div style={{ 
            padding: "20px 32px", 
            background: "rgba(59, 130, 246, 0.1)", 
            border: "1px solid rgba(59, 130, 246, 0.2)",
            borderRadius: "var(--radius-md)",
            textAlign: "center"
          }}>
            <span className="metric-sub" style={{ color: "var(--accent-blue)" }}>종합 점수</span>
            <div style={{ fontSize: "2.5rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0" }}>
              {formatPercent(data.score)}
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--accent-blue)", fontWeight: 700 }}>
              {koCode(data.recommendation)}
            </div>
          </div>
        </div>
      </section>

      <section className="bento-card reveal delay-1" aria-label="중장기 추천 검토 판정">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap", marginBottom: "20px" }}>
          <div>
            <span className="metric-sub">중장기 검토 판정</span>
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

      <section className="bento-card reveal delay-1" aria-label="추천 사용 경계">
        <div className="section-heading">
          <div>
            <span className="metric-sub">추천 사용 경계</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>이 추천을 어디까지 써도 되는가</h2>
          </div>
          <span className={`risk-tag ${blockedDecisionStepCount > 0 ? "risk-high" : decisionWaterfall.paper_validation_input_allowed ? "risk-low" : "risk-medium"}`}>
            {blockedDecisionStepCount > 0 ? "입력 차단" : decisionWaterfall.paper_validation_input_allowed ? "검토 입력 가능" : "검토 대기"}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          {decisionWaterfall.summary} 이 판정은 추천 점수를 바꾸지 않고, 이 추천을 페이퍼 검증·보유 검토·주문 경계 중 어디까지
          넘길 수 있는지만 설명한다.
        </p>
        <div className="status-rail compact-rail" aria-label="추천 사용 경계 요약">
          <div className="rail-cell">
            <span>전문 흐름</span>
            <strong>{koCode(decisionWaterfall.status)}</strong>
            <small>{decisionWaterfall.as_of_date}</small>
          </div>
          <div className="rail-cell">
            <span>단계 상태</span>
            <strong>{readyDecisionStepCount}/{decisionWaterfall.steps.length}</strong>
            <small>주의 {watchDecisionStepCount} · 차단 {blockedDecisionStepCount}</small>
          </div>
          <div className="rail-cell">
            <span>페이퍼 검증 입력</span>
            <strong>{decisionWaterfall.paper_validation_input_allowed ? "허용" : "차단"}</strong>
            <small>원천 차단이면 입력 금지</small>
          </div>
          <div className="rail-cell rail-critical">
            <span>주문 경계</span>
            <strong>{koCode(decisionWaterfall.order_boundary)}</strong>
            <small>자동 주문 {decisionWaterfall.automatic_order_allowed || decisionWaterfall.broker_submit_allowed ? "허용" : "금지"}</small>
          </div>
        </div>
      </section>

      <ProfessionalResearchFlow
        eyebrow="전문 의사결정 흐름"
        title={`${data.symbol} 추천을 분석서처럼 읽는다`}
        summary={decisionWaterfall.summary}
        footer={`점수 정책: ${koCode(decisionWaterfall.score_policy)}. 주문 경계: ${koCode(decisionWaterfall.order_boundary)}.`}
        steps={professionalResearchSteps}
      />

      <section className="bento-card reveal delay-1" aria-label="추천 전문 분석 감사">
        <div className="section-heading">
          <div>
            <span className="metric-sub">추천 전문 분석 감사</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{professionalAudit.title}</h2>
          </div>
          <span className={`risk-tag ${professionalAuditTone(professionalAudit)}`}>
            {koCode(professionalAudit.status)}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0, maxWidth: "920px" }}>
          {professionalAudit.summary} {professionalAudit.next_action}
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
            <span>거래 경계</span>
            <strong>{koCode(professionalAudit.order_boundary)}</strong>
            <small>추천 산식 변경 {professionalAudit.automatic_weight_change_allowed ? "허용" : "금지"} · 주문 {professionalAudit.broker_submit_allowed ? "허용" : "금지"}</small>
          </div>
        </div>

        {professionalAudit.source_blocker.blocked ? (
          <div className="empty-state" style={{ marginTop: "18px" }}>
            <strong>{professionalAudit.source_blocker.blocker_label || "원천 차단"}</strong>
            <p style={{ margin: "8px 0 0", color: "var(--text-secondary)" }}>
              {professionalAudit.source_blocker.summary} {professionalAudit.source_blocker.next_action}
            </p>
          </div>
        ) : null}

        {professionalAudit.missing_layer_labels.length > 0 ? (
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "18px" }}>
            {professionalAudit.missing_layer_labels.map((label) => (
              <span className="risk-tag risk-medium" key={label}>{label}</span>
            ))}
          </div>
        ) : null}

        <div className="flow-steps" style={{ marginTop: "18px" }}>
          {professionalAudit.layer_checks.map((layer) => (
            <article className="flow-step" key={layer.key}>
              <span>{layer.label}</span>
              <strong className={`risk-tag ${professionalLayerTone(layer.status)}`}>
                {professionalLayerStatusLabel(layer.status)}
              </strong>
              <p>{layer.detail}</p>
              <small style={{ color: "var(--text-secondary)", fontWeight: 800 }}>
                원천: {koCode(layer.source)}
              </small>
              {layer.href ? <Link href={layer.href as Route}>관련 화면 열기</Link> : null}
            </article>
          ))}
        </div>
      </section>

      <FinancialStatementModelPanel model={financialStatementModel} symbol={data.symbol} />

      <FundInstrumentAnalysisPanel analysis={data.fund_instrument_analysis} />

      <ValuationTargetRangeCard
        valuation={valuationTargetRange}
        eyebrow="추천 가격 검토"
        title={`${data.symbol} 목표가 범위와 상승여지`}
      />

      {cycleStack.length > 0 ? (
        <section className="bento-card reveal delay-1" aria-label="계층형 사이클 추천 경로">
          <div style={{ marginBottom: "22px" }}>
            <span className="metric-sub">계층형 사이클 경로</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>왜 {data.symbol}을 지금 검토하는가</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "860px" }}>
              추천 점수를 한 덩어리로 보지 않고 거시 환경, 도메인, 테마, 종목 자체 상태, 충돌 감점을 분리해 보여준다.
              초기 가중치 0 항목은 결과를 흔들지 않기 위한 설명·검증용 항목이며, 품질 검증 후 점수 반영을 키운다.
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
                  <strong>{koCode(component.component)}</strong>
                  <p>{meta?.body ?? "계층형 사이클 근거를 설명하는 점수 항목이다."}</p>
                  <p style={{ marginTop: "8px", color: "var(--text-secondary)", fontSize: "0.78rem", fontWeight: 850 }}>
                    {nodeCode ? `기준 노드: ${koCode(nodeCode)}` : "기준 노드 미기록"}
                  </p>
                  <div style={{ marginTop: "14px", display: "grid", gap: "6px", color: "var(--text-secondary)", fontSize: "0.8rem", fontWeight: 800 }}>
                    <span>점수 {formatPercent(component.value)}</span>
                    <span>가중치 {formatPercent(component.weight)}</span>
                    <span>{isZeroWeight(component.weight) ? "현재 총점 영향 없음" : "총점에 반영됨"}</span>
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
              이 영역은 프로 애널리스트식 검토 축이다. 현재는 성과 표본이 부족하므로 추천 총점에는 반영하지 않고,
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
                  <strong>{meta?.title ?? koCode(component.component)}</strong>
                  <p>{meta?.body ?? provenanceDetail(component)}</p>
                  <div style={{ marginTop: "14px", display: "grid", gap: "6px", color: "var(--text-secondary)", fontSize: "0.8rem", fontWeight: 800 }}>
                    <span>검토 점수 {formatPercent(component.value)}</span>
                    <span>{isZeroWeight(component.weight) ? "추천 총점에는 아직 미반영" : `가중치 ${formatPercent(component.weight)}`}</span>
                    <span>{component.provenance?.label ?? "기업 분석 근거"}</span>
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

      <section className="bento-card reveal delay-1" aria-label="기업 리서치 연결">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "18px", flexWrap: "wrap", marginBottom: "22px" }}>
          <div>
            <span className="metric-sub">기업 리서치 연결</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>
              {equityResearch?.title || `${data.symbol} 기업 리서치가 아직 연결되지 않았다`}
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
              {equityResearch.korean_summary}
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
                <small>thesis 재검토 기준</small>
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
                    <span>{koCode(item.key)}</span>
                    <strong>{koLabel(item.value)}</strong>
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
            아직 이 종목의 기업 리서치 결과가 없다. `equity-research-reporting-daily`
            배치가 실행되면 사업 설명, 재무 변화, 촉매, 리스크, 무효화 조건이 이곳에 연결된다.
          </div>
        )}
      </section>

      <section className="bento-card reveal delay-1" aria-label="추천 근거 흐름 요약">
        <div style={{ marginBottom: "20px" }}>
          <span className="metric-sub">근거 흐름 요약</span>
          <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>무엇을 보고 이 추천을 검토해야 하나</h2>
          <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "820px" }}>
            뉴스와 AI 구조화 결과는 바로 주문으로 이어지지 않는다. 직접 종목 뉴스, 시장·테마 흐름, 보유검토 상태를
            분리한 뒤 AI 자동 검토가 추천 입력으로 쓸 수 있는지 판정한다.
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
        <section className="bento-card reveal delay-1" aria-label="상위 흐름 전파 경로">
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
                      <span className="metric-sub">{koCode(component.component)}</span>
                      <strong>{formatPercent(component.value)} · 가중치 {formatPercent(component.weight)}</strong>
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
                            {koCode(flow.impact_direction)} · 강도 {formatMetricValue(flow.impact_strength)} · 신뢰도 {formatMetricValue(flow.confidence)}
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

      <section className="bento-card reveal delay-1" aria-label="추천 근거 연결 점검">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap", marginBottom: "20px" }}>
          <div>
            <span className="metric-sub">근거 연결 점검</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{koCode(evidenceReview.quality_status)}</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "760px" }}>
              이 점검은 추천 점수를 새로 만들지 않는다. 추천이 투자 논리, 점수 항목, 뉴스·AI 근거, 성과 측정과
              충분히 연결됐는지 확인하는 읽기 전용 검토다.
            </p>
          </div>
          <div className="status-rail compact-rail" style={{ flex: "1 1 360px" }}>
            <div className="rail-cell">
              <span>통과</span>
              <strong>{reviewCount(evidenceReview.summary.pass_count)}</strong>
              <small>검토 기준 충족</small>
            </div>
            <div className="rail-cell">
              <span>주의</span>
              <strong>{reviewCount(evidenceReview.summary.warning_count)}</strong>
              <small>보강 필요</small>
            </div>
            <div className="rail-cell">
              <span>차단</span>
              <strong>{reviewCount(evidenceReview.summary.blocked_count)}</strong>
              <small>진행 금지</small>
            </div>
          </div>
        </div>

        <div className="bento-list">
          {evidenceReview.gates.map((gate) => (
            <div className="bento-list-item" key={gate.gate_key}>
              <div>
                <span className="metric-sub" style={{ color: gateStatusColor(gate.status) }}>{gateStatusLabel(gate.status)}</span>
                <strong>{koLabel(gate.label)}</strong>
                <span>{koLabel(gate.detail)}</span>
              </div>
              <span style={{ color: "var(--text-secondary)", maxWidth: "360px" }}>{koLabel(gate.next_step)}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">점수 근거</span>
            <h2 style={{ fontSize: "1.5rem" }}>{koCode(data.score_version)}</h2>
          </div>
          
          <div className="bento-list">
            {data.score_components.map((component) => {
              const href = evidenceHref(component.evidence_id, data.symbol);
              const badges = provenanceBadges(component);
              return (
                <div className="bento-list-item" key={component.component} style={{ alignItems: "flex-start", gap: "18px" }}>
                  <div style={{ flex: "1 1 360px", minWidth: 0 }}>
                    <strong style={{ display: "block", marginBottom: "6px" }}>{koCode(component.component)}</strong>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.55, margin: "0 0 10px" }}>
                      {provenanceDetail(component)}
                    </p>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "10px" }}>
                      {badges.map((badge) => (
                        <span key={`${component.component}-${badge}`} style={{
                          border: "1px solid var(--border-light)",
                          borderRadius: "999px",
                          color: "var(--text-secondary)",
                          fontSize: "0.72rem",
                          padding: "4px 8px"
                        }}>
                          {badge}
                        </span>
                      ))}
                    </div>
                    <div className="mini-link-stack">
                      {href ? (
                        <Link href={href}>
                          {evidenceLinkLabel(component.evidence_id)}
                        </Link>
                      ) : (
                        <span>연결된 상세 근거 없음</span>
                      )}
                    </div>
                    <AuditMetadata items={provenanceMetadata(component)} summary="계산 입력 상세 보기" />
                  </div>
                  <div style={{ flex: "0 0 110px", textAlign: "right" }}>
                    <strong style={{ fontSize: "1.1rem", color: "var(--text-primary)" }}>{formatPercent(component.value)}</strong>
                  </div>
                  <div style={{ flex: "0 0 120px", textAlign: "right" }}>
                    <span className="metric-sub">가중치 {formatPercent(component.weight)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
            <div>
              <span className="metric-sub">성과 측정</span>
              <h2 style={{ fontSize: "1.5rem" }}>
                {outcomeMeasured ? koCode(data.outcome.label) : "아직 성과 측정 전"}
              </h2>
            </div>
            <Link className="btn btn-primary" href={`/theses/${data.linked_thesis_id}`}>
              연결된 투자 논리 열기
            </Link>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">알파</span>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {outcomeMeasured ? formatPercent(data.outcome.alpha) : "측정 전"}
              </div>
            </div>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">절대수익률</span>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {outcomeMeasured ? formatPercent(data.outcome.absolute_return) : "측정 전"}
              </div>
            </div>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">벤치마크 수익률</span>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {outcomeMeasured ? formatPercent(data.outcome.benchmark_return) : "측정 전"}
              </div>
            </div>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">측정 종료일</span>
              <div style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "4px" }}>
                {outcomeMeasured ? data.outcome.measurement_end_date : "성과 측정 윈도우 대기"}
              </div>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}
