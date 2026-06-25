import Link from "next/link";
import type { Route } from "next";
import { Fragment } from "react";

import { CandlestickChart } from "@/components/candlestick-chart";
import { NewsTitleBlock } from "@/components/news-title-block";
import { ProfessionalResearchFlow, type ResearchFlowStep } from "@/components/professional-research-flow";
import { ValuationTargetRangeCard } from "@/components/valuation-target-range-card";
import { getAiEvidenceNeighborhood, getStockDetail } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import { stockCopy } from "@/lib/presentation";
import type { AiEvidenceNeighborhoodData, StockDetailData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "종목 상세" };

type StockDetailPageProps = {
  params: Promise<{ symbol: string }>;
};

type IndustryCompetitivePosition = NonNullable<StockDetailData["industry_competitive_position"]>;
type FinancialStatementModel = StockDetailData["financial_statement_model"];
type FinancialMetricSnapshot = FinancialStatementModel["metrics"][number];
type FundInstrumentAnalysis = StockDetailData["fund_instrument_analysis"];
type ProfessionalSourceGuardrail = StockDetailData["professional_source_guardrail"];
type StockMarketCorrelation = StockDetailData["market_correlations"][number];
type StockProfessionalLayerStatus = "complete" | "partial" | "pending" | "blocked" | "missing" | "not_applicable";

type StockProfessionalLayer = {
  key: string;
  label: string;
  status: StockProfessionalLayerStatus;
  detail: string;
  source: string;
  href?: string;
  hrefLabel?: string;
};

function formatCurrency(value: number | null, currencyCode: string) {
  if (value === null) {
    return "가격 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 2,
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

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "없음";
  }
  return value.toLocaleString("ko-KR");
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
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

function correlationTone(correlation: StockMarketCorrelation) {
  if (correlation.relationship_label.includes("strong")) {
    return "detail-path-card is-watch";
  }
  if (correlation.relationship_label.includes("moderate")) {
    return "detail-path-card is-good";
  }
  return "detail-path-card";
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

function formatStoryBasis(basis: string[]) {
  const labels: Record<string, string> = {
    same_title_signature: "제목 핵심 단어",
    same_source_document: "원천 문서 연결",
    same_theme: "테마 연결",
  };
  if (basis.length === 0) {
    return "단일 이벤트";
  }
  return basis.map((item) => labels[item] ?? koCode(item)).join(" · ");
}

function formatDate(value: string) {
  return value ? value.slice(0, 10) : "날짜 없음";
}

function evidenceChunkPreview(value: string | null | undefined) {
  if (!value) {
    return "문서 미리보기 없음";
  }
  const titleMatch = value.match(/Title:\s*(.*?)(?:\s+Summary:|\s+Published\/Event At:|$)/);
  if (titleMatch?.[1]) {
    const text = titleMatch[1].toLowerCase();
    if (/(fed|warsh|rate|rates|treasury|bond|yield|inflation)/.test(text)) {
      return "한국어 요약: 금리·연준 관련 원천 근거";
    }
    if (/(oil|iran|hormuz|crude|energy|gas|xom|drilling)/.test(text)) {
      return "한국어 요약: 에너지·지정학 관련 원천 근거";
    }
    if (/(quantum|qubit|rigetti|d-wave|ionq|qbts|qubt|ibm)/.test(text)) {
      return "한국어 요약: 양자컴퓨팅·정책 수혜 관련 원천 근거";
    }
    if (/(nvidia|semiconductor|chip|qualcomm|skyworks|qorvo|tower semiconductor|tsem)/.test(text)) {
      return "한국어 요약: AI 반도체 사이클 관련 원천 근거";
    }
    return "한국어 요약: 시장 뉴스 흐름 관련 원천 근거";
  }
  return koLabel(value.split(" Retrieval context:")[0] ?? value);
}

function recommendationHref(recommendationId: string) {
  return `/recommendations/${recommendationId}` as Route;
}

function thesisHref(thesisId: string) {
  return `/theses/${thesisId}` as Route;
}

function evidenceHref(evidenceId: string | null) {
  return evidenceId ? (`/ai-evidence/${evidenceId}` as Route) : null;
}

function sourceDocumentHref(documentId: string | null) {
  return documentId ? (`/source-documents/${documentId}` as Route) : null;
}

function providerLabel(provider: string) {
  if (provider === "codex_oauth") {
    return "심화 근거 분석";
  }
  if (provider === "fixture") {
    return "검증용 샘플 분석";
  }
  return koCode(provider);
}

function userFacingStockText(value: string | null | undefined) {
  return stockCopy(value);
}

function valuationSensitivityLabel(key: string) {
  const labels: Record<string, string> = {
    "base case": "기준 시나리오",
    base_case: "기준 시나리오",
    confidence: "신뢰도",
    "upside case": "상승 시나리오",
    upside_case: "상승 시나리오",
    downside_case: "하락 시나리오",
  };
  return labels[key] ?? labels[key.toLowerCase()] ?? userFacingStockText(koCode(key));
}

function stockDecisionOutcome(
  data: StockDetailData,
  guardrail: ProfessionalSourceGuardrail,
  hasPriceData: boolean,
) {
  if (guardrail.blocked) {
    return {
      tone: "blocked",
      label: "입력 차단",
      title: `${data.symbol} 상태: 투자 판단 입력 제외`,
      body: userFacingStockText(guardrail.summary),
    };
  }
  if (data.recommendation && data.position) {
    return {
      tone: "ready",
      label: "추천·보유 연결",
      title: `${data.symbol} 상태: 추천과 보유 모두 연결`,
      body: "추천 이유, 현재 보유 비중, 투자 논리, 가상 매매 검증 상태가 서로 맞는지 본다.",
    };
  }
  if (data.recommendation) {
    return {
      tone: "ready",
      label: "추천 근거 있음",
      title: `${data.symbol} 상태: 추천 근거 있음`,
      body: "추천 상세에서 점수 구성, 기업 분석, 뉴스·사이클 근거, 실거래 차단 상태를 함께 본다.",
    };
  }
  if (data.position) {
    return {
      tone: "watch",
      label: "보유 상태",
      title: `${data.symbol} 상태: 보유 중, 최신 추천 없음`,
      body: "보유 이유와 최근 뉴스·상위 흐름이 유지 조건을 깨지 않는지 먼저 본다.",
    };
  }
  if (!hasPriceData) {
    return {
      tone: "watch",
      label: "가격 보강 필요",
      title: `${data.symbol} 상태: 가격 데이터 부족`,
      body: "뉴스·상위 흐름은 볼 수 있지만 가격 차트와 수익률 판단은 아직 보류한다.",
    };
  }
  return {
    tone: "neutral",
    label: "관찰 종목",
    title: `${data.symbol} 상태: 관찰 단계`,
    body: "가격 데이터는 있으나 추천·보유 연결은 아직 없다. 뉴스와 사이클 근거가 쌓이는지 본다.",
  };
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
  const peerGroup = userFacingStockText(position.peer_group_name ?? position.peer_group_code ?? "비교군");
  const sector = userFacingStockText(position.sector_name ?? position.sector_code ?? "섹터 미분류");
  return `${symbol}은 ${peerGroup} 기준으로 ${competitivePositionLabel(position.competitive_position)} 상태다. ${sector} 안에서 수익성, 성장성, 재무 방어력, 가격 결정력 추정 지표를 함께 본다.`;
}

function FinancialStatementModelPanel({
  model,
  symbol,
}: {
  model: FinancialStatementModel;
  symbol: string;
}) {
  const visibleSections = model.sections.filter((section) => section.metrics.length > 0 || section.status !== "missing");
  const sourceBlocker = model.source_data_blocker;

  if (model.status === "unavailable") {
    return (
      <section className="bento-card span-4 reveal delay-3" id="stock-financial-model" aria-label="재무제표 모델">
        <div className="section-heading stacked-heading">
          <span className="metric-sub">재무제표 모델</span>
          <h2>{sourceBlocker ? `${symbol} ${sourceBlocker.label}` : `${symbol} 재무 모델이 아직 준비되지 않았다`}</h2>
        </div>
        <p style={{ color: "var(--text-secondary)", marginBottom: 0 }}>
          {sourceBlocker
            ? userFacingStockText(model.summary)
          : "SEC 공시 재무 데이터 수집과 재무 정규화가 완료되면 매출 성장, 마진, 현금흐름, 부채, 이익 품질을 이곳에서 본다. 이 데이터가 없으면 뉴스나 사이클만으로 장기 투자 판단을 확정하지 않는다."}
        </p>
        {sourceBlocker ? (
          <div className="status-rail compact-rail" aria-label="재무 원천 차단 사유" style={{ marginTop: "18px" }}>
            <div className="rail-cell">
              <span>부족한 근거</span>
              <strong>{userFacingStockText(sourceBlocker.label)}</strong>
              <small>{userFacingStockText(koCode(sourceBlocker.blocker_code))}</small>
            </div>
            <div className="rail-cell">
              <span>확인 기준</span>
              <strong>{userFacingStockText(sourceBlocker.source_pipeline)}</strong>
              <small>{sourceBlocker.source_run_id ? "수집 실행 기록 있음" : "정적 분류"}</small>
            </div>
          </div>
        ) : null}
      </section>
    );
  }

  return (
    <section className="bento-card span-4 reveal delay-3" id="stock-financial-model" aria-label="재무제표 모델">
      <div className="section-heading">
        <div>
          <span className="metric-sub">재무제표 모델</span>
          <h2>{symbol}의 숫자가 투자 논리를 버티는가</h2>
        </div>
        <span className={`risk-tag ${model.status === "available" ? "risk-low" : "risk-medium"}`}>
          {model.status === "available" ? "재무 모델 연결" : "일부 지표 부족"}
        </span>
      </div>
      <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
        {userFacingStockText(model.summary)} 이 섹션은 기존 정규화 재무 지표를 읽는 화면이며, 추천 점수와 주문 가능 여부를 바꾸지 않는다.
      </p>

      <div className="status-rail compact-rail" aria-label="재무 모델 요약">
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
          <strong>{formatPercent(model.share_count.share_count_change_pct)}</strong>
          <small>{model.share_count.latest_period_end || "주식수 데이터 없음"}</small>
        </div>
      </div>

      <div className="bento-grid" style={{ marginTop: "18px" }}>
        {visibleSections.map((section) => (
          <article className="bento-card" key={section.section_key}>
            <span className="metric-sub">{section.title}</span>
            <h3 style={{ margin: "6px 0 8px" }}>{section.description}</h3>
            <div className="stock-meta-grid">
              {section.metrics.length > 0 ? (
                section.metrics.map((metric) => (
                  <Fragment key={metric.metric_code}>
                    <span>
                      {metric.label}
                      <small style={{ display: "block", color: "var(--text-muted)" }}>{metric.period_end || "기간 없음"}</small>
                    </span>
                    <strong className={`risk-tag ${financialMetricTone(metric)}`}>
                      {formatFinancialMetricValue(metric)}
                    </strong>
                  </Fragment>
                ))
              ) : (
                <>
                  <span>상태</span>
                  <strong>지표 없음</strong>
                </>
              )}
            </div>
          </article>
        ))}
      </div>

      <p style={{ color: "var(--text-muted)", margin: "18px 0 0" }}>
        재무 지표는 저장된 공시 데이터로 계산한다. 이 영역은 읽기 전용 분석이며 주문 제출과 연결하지 않는다.
      </p>
    </section>
  );
}

function FundInstrumentAnalysisPanel({ analysis }: { analysis: FundInstrumentAnalysis }) {
  if (!analysis) {
    return null;
  }
  return (
    <section className="bento-card span-4 reveal delay-2" id="stock-fund-analysis" aria-label="ETF와 펀드형 상품 분석">
      <div className="section-heading">
        <div>
          <span className="metric-sub">ETF·펀드 분석</span>
          <h2>{analysis.symbol}은 기업 재무제표가 아니라 보유종목과 노출도로 본다</h2>
        </div>
        <span className="bento-badge" style={{ margin: 0 }}>{koCode(analysis.status)}</span>
      </div>
      <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
        {analysis.summary}
      </p>
      <div className="status-rail compact-rail" aria-label="ETF와 펀드형 상품 분석 요약">
        <div className="rail-cell">
          <span>벤치마크</span>
          <strong>{analysis.benchmark_code || analysis.symbol}</strong>
          <small>{analysis.benchmark_source || "원천 미확인"}</small>
        </div>
        <div className="rail-cell">
          <span>보유종목 커버리지</span>
          <strong>{formatPercent(analysis.holdings_coverage_weight)}</strong>
          <small>{analysis.holding_count.toLocaleString("ko-KR")}개 구성종목</small>
        </div>
        <div className="rail-cell">
          <span>현재 포트폴리오 비중</span>
          <strong>{formatPercent(analysis.portfolio_role.current_weight)}</strong>
          <small>{analysis.portfolio_role.portfolio_name}</small>
        </div>
        <div className="rail-cell">
          <span>추천 목표 비중</span>
          <strong>{formatPercent(analysis.portfolio_role.recommended_weight)}</strong>
          <small>주문 자동 생성 없음</small>
        </div>
      </div>
      <div className="relationship-panel" aria-label="상위 보유종목">
        <span>상위 보유종목</span>
        <div className="relationship-list">
          {analysis.top_holdings.slice(0, 6).map((holding) => (
            <div className="relationship-chip" key={holding.symbol}>
              <span>{holding.symbol}</span>
              <strong>{holding.name || holding.symbol}</strong>
              <small>
                목표 비중 {formatPercent(holding.target_weight)} · 신뢰도 {formatPercent(holding.confidence)}
              </small>
            </div>
          ))}
          {analysis.top_holdings.length === 0 ? (
            <p className="relationship-empty">보유종목 원천이 아직 연결되지 않았다.</p>
          ) : null}
        </div>
      </div>
      <div className="flow-steps">
        <article className="flow-step">
          <span>추적오차/추적차이</span>
          <strong>
            {analysis.tracking_error.metric_type === "tracking_difference"
              ? formatPercent(analysis.tracking_error.tracking_difference_value)
              : koCode(analysis.tracking_error.status)}
          </strong>
          <p>
            {analysis.tracking_error.summary}
            {analysis.tracking_error.measurement_window
              ? ` 기간 ${analysis.tracking_error.measurement_window}`
              : ""}
            {analysis.tracking_error.benchmark_name ? ` · 기준 ${analysis.tracking_error.benchmark_name}` : ""}
            {analysis.tracking_error.fund_return !== null
              ? ` · NAV 수익률 ${formatPercent(analysis.tracking_error.fund_return)}`
              : ""}
            {analysis.tracking_error.benchmark_return !== null
              ? ` · 벤치마크 ${formatPercent(analysis.tracking_error.benchmark_return)}`
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
          <strong>{formatPercent(analysis.nav_premium_discount.premium_discount_to_nav)}</strong>
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
          <strong>{koCode(analysis.order_boundary)}</strong>
          <p>이 분석은 추천 점수와 주문 가능 여부를 자동 변경하지 않는다.</p>
        </article>
      </div>
    </section>
  );
}

function IndustryCompetitivePositionPanel({
  position,
  symbol,
}: {
  position: IndustryCompetitivePosition | null;
  symbol: string;
}) {
  if (!position) {
    return (
      <section className="bento-card span-4 reveal delay-3" id="stock-industry-position" aria-label="산업 경쟁 위치">
        <div className="section-heading stacked-heading">
          <span className="metric-sub">산업 경쟁 위치</span>
          <h2>동종업계 비교가 아직 이 종목에 연결되지 않았다</h2>
        </div>
        <p style={{ color: "var(--text-secondary)", marginBottom: 0 }}>
          산업 경쟁 위치 배치가 실행되면 피어 그룹, 경쟁 위치, 가격 결정력, 재무 방어력, 경쟁 압력 추정 지표가
          이곳에 표시된다. 추천 점수는 이 값만으로 바뀌지 않는다.
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
    <section className="bento-card span-4 reveal delay-3" id="stock-industry-position" aria-label="산업 경쟁 위치">
      <div className="section-heading">
        <div>
          <span className="metric-sub">산업 경쟁 위치</span>
          <h2>{symbol}이 같은 그룹 안에서 얼마나 강한가</h2>
        </div>
        <span className="bento-badge" style={{ margin: 0 }}>
          {competitivePositionLabel(position.competitive_position)} • {position.as_of_date}
        </span>
      </div>
      <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
        {competitivePositionSummary(position, symbol)} 이 값은 유료 시장점유율 데이터가 아니라 저장된 재무 지표와
        동종업계 비교로 만든 추정 지표이며, 최종 추천 판단은 별도 화면에서 본다.
      </p>

      <div className="status-rail compact-rail" aria-label="산업 경쟁 위치 요약">
        <div className="rail-cell">
          <span>경쟁 위치</span>
          <strong>{competitivePositionLabel(position.competitive_position)}</strong>
          <small>{koCode(position.methodology)}</small>
        </div>
        <div className="rail-cell">
          <span>비교군</span>
          <strong>{userFacingStockText(position.peer_group_name ?? position.peer_group_code ?? "미분류")}</strong>
          <small>{position.peer_count.toLocaleString("ko-KR")}개 종목 기준</small>
        </div>
        <div className="rail-cell">
          <span>섹터</span>
          <strong>{userFacingStockText(position.sector_name ?? position.sector_code ?? "미분류")}</strong>
          <small>산업/테마 분류 기준</small>
        </div>
        <div className="rail-cell">
          <span>지표 커버리지</span>
          <strong>{position.metric_coverage_count.toLocaleString("ko-KR")}</strong>
          <small>{position.source_run_id ? "계산 실행 기록 있음" : "실행 기록 없음"}</small>
        </div>
      </div>

      <div className="bento-grid" style={{ marginTop: "18px" }}>
        <article className="bento-card">
          <span className="metric-sub">경쟁력 점수</span>
          <div className="stock-meta-grid" style={{ marginTop: "12px" }}>
            {scoreRows.map((row) => (
              <Fragment key={row.label}>
                <span>{row.label}</span>
                <strong>{formatPercent(row.value)}</strong>
              </Fragment>
            ))}
          </div>
        </article>
        <article className="bento-card">
          <span className="metric-sub">경쟁 압력 리스크</span>
          <div className="stock-meta-grid" style={{ marginTop: "12px" }}>
            {riskRows.map((row) => (
              <Fragment key={row.label}>
                <span>{row.label}</span>
                <strong>{formatPercent(row.value)}</strong>
              </Fragment>
            ))}
          </div>
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
        <p style={{ color: "var(--text-muted)", marginBottom: 0 }}>
          계산 근거: {koLabel(position.rationale)}
        </p>
      ) : null}
    </section>
  );
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
    <article className="bento-card">
      <span className="metric-sub">{title}</span>
      <div className="bento-list compact-list">
        {items.length > 0 ? (
          items.map((item) => (
            <div className="bento-list-item" key={item}>{userFacingStockText(item)}</div>
          ))
        ) : (
          <div className="empty-state">{emptyText}</div>
        )}
      </div>
    </article>
  );
}

function cleanFlowText(
  value: string | null | undefined,
  options: {
    themeKey: string;
    symbol: string;
    impactDirection: string;
  },
) {
  const { themeKey, symbol, impactDirection } = options;
  if (!value) {
    return `${koCode(themeKey)} 흐름이 ${koCode(symbol)}에 ${koCode(impactDirection)} 방향으로 전파됐다. 노출도와 신뢰도는 위 수치를 기준으로 본다.`;
  }
  if (/flow propagated to/i.test(value) || /directly exposed/i.test(value)) {
    return `${koCode(themeKey)} 흐름이 ${koCode(symbol)}에 ${koCode(impactDirection)} 방향으로 전파됐다. 자세한 근거는 상세 버튼에서 본다.`;
  }
  const interpretation = value.match(/해석:\s*(.*?)(?:\s*근거:|;\s*노출 근거:|$)/)?.[1]?.trim();
  const evidence = value.match(/근거:\s*(.*?)(?:;\s*노출 근거:|$)/)?.[1]?.trim();
  const exposure = value.match(/노출 근거:\s*(.*)$/)?.[1]?.trim();
  const parts = [
    interpretation ? `해석: ${koLabel(interpretation)}` : null,
    evidence ? `근거: ${koLabel(evidence)}` : null,
    exposure
      ? `노출: ${
          /directly exposed/i.test(exposure)
            ? "이 종목은 해당 테마의 자금 지원·상용화 뉴스에 직접 노출된다."
            : koLabel(exposure)
        }`
      : null,
  ].filter(Boolean);
  if (parts.length > 0) {
    return parts.join(" ");
  }
  return koLabel(value);
}

function stockGuardrails() {
  return [
    "읽기 전용 상태다. 추천 점수, 포지션, 주문을 변경하지 않는다.",
    "민감한 접속 정보와 API 키는 화면에 노출하지 않는다.",
    "새 분석을 만들지 않고 저장된 근거만 보여준다.",
  ];
}

function professionalGuardrailTone(guardrail: ProfessionalSourceGuardrail) {
  if (guardrail.blocked) {
    return "risk-high";
  }
  if (!guardrail.paper_validation_input_allowed || !guardrail.professional_decision_use_allowed) {
    return "risk-medium";
  }
  return "risk-low";
}

function professionalGuardrailTitle(guardrail: ProfessionalSourceGuardrail) {
  if (guardrail.blocked) {
    return "투자 판단 입력 차단";
  }
  if (guardrail.status === "fund_or_etf_company_model_not_applicable") {
    return "ETF·펀드 경계 적용";
  }
  return "투자 판단 입력 가능";
}

function stockProfessionalLayerStatusLabel(status: StockProfessionalLayerStatus) {
  const labels: Record<StockProfessionalLayerStatus, string> = {
    complete: "완료",
    partial: "일부",
    pending: "대기",
    blocked: "차단",
    missing: "누락",
    not_applicable: "비적용",
  };
  return labels[status];
}

function stockProfessionalLayerTone(status: StockProfessionalLayerStatus) {
  if (status === "complete" || status === "not_applicable") {
    return "risk-low";
  }
  if (status === "blocked") {
    return "risk-high";
  }
  return "risk-medium";
}

function stockProfessionalAuditStatus({
  blockedCount,
  missingCount,
  pendingCount,
}: {
  blockedCount: number;
  missingCount: number;
  pendingCount: number;
}) {
  if (blockedCount > 0) {
    return {
      tone: "risk-high",
      title: "전문 판단 입력 차단",
      summary: "차단된 원천 근거가 있어 종목 분석을 투자 판단이나 가상 매매 입력으로 넘기면 안 된다.",
    };
  }
  if (missingCount > 0) {
    return {
      tone: "risk-medium",
      title: "근거 보강 필요",
      summary: "중장기 판단에 필요한 전문 근거가 일부 빠져 있다. 추천이나 보유 판단 전에 빠진 레이어가 먼저다.",
    };
  }
  if (pendingCount > 0) {
    return {
      tone: "risk-medium",
      title: "성과 검증 대기",
      summary: "핵심 근거는 연결됐지만 성과 측정창이나 가상 매매 검증 상태가 아직 끝나지 않았다.",
    };
  }
  return {
    tone: "risk-low",
    title: "전문 근거 연결",
    summary: "전문 분석 레이어가 연결됐다. 읽기 전용 상태이며 산식 변경과 실거래 주문은 하지 않는다.",
  };
}

function buildStockProfessionalLayers({
  data,
  neighborhood,
  linkedThesisId,
  hasPriceData,
}: {
  data: StockDetailData;
  neighborhood: AiEvidenceNeighborhoodData;
  linkedThesisId: string | null;
  hasPriceData: boolean;
}): StockProfessionalLayer[] {
  const guardrail = data.professional_source_guardrail;
  const isFundLike = guardrail.status === "fund_or_etf_company_model_not_applicable" || data.fund_instrument_analysis !== null;
  const valuationItems = data.equity_research ? valuationSensitivityItems(data.equity_research.valuation_sensitivity) : [];
  const newsCount = data.recent_events.length + data.macro_flow_impacts.length;
  const aiEvidenceCount = neighborhood.summary.ai_artifact_count;

  return [
    {
      key: "business_research",
      label: "사업 리서치",
      status: data.equity_research ? "complete" : "missing",
      detail: data.equity_research
        ? `기업 리서치가 ${data.equity_research.as_of_date} 기준으로 저장됐다. 사업 설명, 촉매, 리스크, 무효화 조건을 아래에서 본다.`
        : "사업 설명, 촉매, 리스크, 무효화 조건을 요약한 기업 리서치가 아직 없다.",
      source: "research.equity_research_artifact",
      href: "#stock-equity-research",
      hrefLabel: "기업 리서치",
    },
    {
      key: "financial_model",
      label: "재무제표 모델",
      status: isFundLike
        ? "not_applicable"
        : guardrail.blocked
          ? "blocked"
          : data.financial_statement_model.status === "available"
            ? "complete"
            : data.financial_statement_model.status === "partial" || data.financial_statement_model.computed_metric_count > 0
              ? "partial"
              : "missing",
      detail: isFundLike
        ? "ETF·펀드형 상품은 개별 기업 재무제표 모델 대신 보유종목, 비용률, NAV, 추적 차이를 본다."
        : guardrail.blocked
          ? userFacingStockText(guardrail.summary)
          : data.financial_statement_model.computed_metric_count > 0
            ? `정규화 재무 지표 ${data.financial_statement_model.computed_metric_count}개가 계산됐다. 데이터 공백은 ${data.financial_statement_model.data_gap_count}개다.`
            : "매출, 마진, 현금흐름, 부채, 희석 같은 정규화 재무 지표가 아직 충분하지 않다.",
      source: "market.financial_metric_normalized",
      href: "#stock-financial-model",
      hrefLabel: "재무 근거",
    },
    {
      key: "fund_source",
      label: "ETF·펀드 근거",
      status: isFundLike ? (data.fund_instrument_analysis ? "complete" : "missing") : "not_applicable",
      detail: data.fund_instrument_analysis
        ? `보유종목 ${data.fund_instrument_analysis.holding_count}개, 커버리지 ${formatPercent(data.fund_instrument_analysis.holdings_coverage_weight)}가 연결됐다.`
        : isFundLike
          ? "펀드형 상품으로 분류됐지만 보유종목, 비용률, NAV, 추적차이 원천이 아직 충분하지 않다."
          : "일반 기업 종목이므로 ETF·펀드 근거 레이어는 적용하지 않는다.",
      source: "fund_instrument_analysis",
      href: "#stock-fund-analysis",
      hrefLabel: "ETF·펀드 근거",
    },
    {
      key: "peer_industry",
      label: "피어·산업 위치",
      status: isFundLike ? "not_applicable" : data.industry_competitive_position ? "complete" : "missing",
      detail: isFundLike
        ? "ETF·펀드형 상품은 기업 peer 대신 보유종목 구성과 벤치마크 노출을 본다."
        : data.industry_competitive_position
          ? `${data.industry_competitive_position.peer_group_name ?? data.industry_competitive_position.peer_group_code ?? "비교군"} 기준 ${competitivePositionLabel(data.industry_competitive_position.competitive_position)} 상태다.`
          : "같은 산업·테마 비교군 안의 상대 위치가 아직 연결되지 않았다.",
      source: "research.industry_competitive_position",
      href: "#stock-industry-position",
      hrefLabel: "산업 위치",
    },
    {
      key: "valuation",
      label: "밸류에이션",
      status: isFundLike
        ? "not_applicable"
        : data.valuation_target_range.status === "available"
          ? "complete"
          : valuationItems.length > 0
            ? "partial"
            : "missing",
      detail: isFundLike
        ? "ETF·펀드형 상품은 DCF 목표가 대신 NAV 괴리, 비용률, 추적 차이, 유동성을 본다."
        : data.valuation_target_range.status === "available"
          ? `목표가 범위 ${data.valuation_target_range.method_count}개 방법과 기준 상승여지 ${formatPercent(data.valuation_target_range.upside_base)}가 연결됐다.`
          : valuationItems.length > 0
            ? "기업 리서치의 밸류에이션 민감도는 있으나 목표가 범위 snapshot은 아직 부족하다."
            : "DCF-lite, 상대 배수, 시나리오 범위, SOTP 목표가가 아직 충분히 연결되지 않았다.",
      source: "market.valuation_snapshot",
      href: "#stock-valuation",
      hrefLabel: "가격 근거",
    },
    {
      key: "news_cycle",
      label: "뉴스·사이클",
      status: newsCount > 0 || aiEvidenceCount > 0 ? "complete" : "missing",
      detail:
        newsCount > 0 || aiEvidenceCount > 0
          ? `직접 뉴스 ${data.recent_events.length}개, 상위 흐름 ${data.macro_flow_impacts.length}개, 심화 근거 ${aiEvidenceCount}개가 연결됐다.`
          : "이 종목에 연결된 직접 뉴스, 상위 흐름 전파, 투자 근거가 아직 없다.",
      source: "event_and_ai_evidence",
      href: "#stock-flow-impacts",
      hrefLabel: "뉴스·흐름",
    },
    {
      key: "thesis",
      label: "투자 논리",
      status: linkedThesisId ? "complete" : "blocked",
      detail: linkedThesisId
        ? "매수 이유, 유지 조건, 무효화 조건을 추적할 투자 논리가 연결됐다."
        : "투자 논리가 없으면 중장기 추천이나 보유 판단에 쓰면 안 된다.",
      source: "signal.investment_thesis",
      href: linkedThesisId ? thesisHref(linkedThesisId) : undefined,
      hrefLabel: linkedThesisId ? "투자 논리" : undefined,
    },
    {
      key: "recommendation",
      label: "추천 영향",
      status: data.recommendation ? "complete" : "missing",
      detail: data.recommendation
        ? `최신 추천 ${koCode(data.recommendation.action)}, 점수 ${formatPercent(data.recommendation.score)}가 연결됐다.`
        : "아직 이 종목을 대상으로 한 최신 추천 신호가 없다.",
      source: "signal.recommendation",
      href: data.recommendation ? recommendationHref(data.recommendation.recommendation_id) : undefined,
      hrefLabel: data.recommendation ? "추천 상세" : undefined,
    },
    {
      key: "paper_boundary",
      label: "가상 매매·실거래",
      status: guardrail.blocked ? "blocked" : data.recommendation ? "pending" : "missing",
      detail: guardrail.blocked
        ? "원천 근거가 차단되어 가상 매매 검증 입력도 차단한다. 실거래 주문은 계속 닫혀 있다."
        : data.recommendation
          ? "추천이 있어도 성과 측정창과 가상 매매 검증을 거치기 전에는 weight 변경과 실거래 주문으로 넘기지 않는다."
          : "추천 신호가 없으므로 가상 매매 검증 입력 대상도 아직 아니다.",
      source: "paper_validation_and_order_boundary",
      href: "/paper-trading" as Route,
      hrefLabel: "가상 매매",
    },
    {
      key: "price_history",
      label: "가격 데이터",
      status: hasPriceData ? "complete" : "missing",
      detail: hasPriceData
        ? `가격 캔들 ${data.summary.bar_count}개가 수집됐다. 가격은 판단 보조 근거이며 주문을 만들지 않는다.`
        : "가격 캔들이 부족해 가격 흐름과 수익률 판단은 아직 제한된다.",
      source: "market.daily_price_bar",
      href: "#stock-price-data",
      hrefLabel: "가격 차트",
    },
  ];
}

function StockProfessionalEvidenceAuditPanel({
  data,
  neighborhood,
  linkedThesisId,
  hasPriceData,
}: {
  data: StockDetailData;
  neighborhood: AiEvidenceNeighborhoodData;
  linkedThesisId: string | null;
  hasPriceData: boolean;
}) {
  const layers = buildStockProfessionalLayers({ data, neighborhood, linkedThesisId, hasPriceData });
  const applicableLayers = layers.filter((layer) => layer.status !== "not_applicable");
  const completeCount = applicableLayers.filter((layer) => layer.status === "complete").length;
  const partialCount = applicableLayers.filter((layer) => layer.status === "partial").length;
  const pendingCount = applicableLayers.filter((layer) => layer.status === "pending").length;
  const blockedCount = applicableLayers.filter((layer) => layer.status === "blocked").length;
  const missingLayers = applicableLayers.filter((layer) => layer.status === "missing");
  const coverageRatio =
    applicableLayers.length > 0 ? (completeCount + partialCount * 0.5) / applicableLayers.length : 1;
  const auditStatus = stockProfessionalAuditStatus({
    blockedCount,
    missingCount: missingLayers.length,
    pendingCount,
  });

  return (
    <section className="bento-card span-4 reveal delay-1" aria-label="종목 전문 근거 감사">
      <div className="section-heading">
        <div>
          <span className="metric-sub">전문 근거 감사</span>
          <h2>{data.symbol}을 중장기 판단에 써도 되는가</h2>
        </div>
        <span className={`risk-tag ${auditStatus.tone}`}>{auditStatus.title}</span>
      </div>
      <p style={{ color: "var(--text-secondary)", marginTop: 0, maxWidth: "920px" }}>
        {auditStatus.summary} 이 감사는 저장된 근거가 실제로 남아 있는지 보는 읽기 전용 점검이며 추천 점수, 포지션, 주문을 바꾸지 않는다.
      </p>
      <div className="status-rail compact-rail decision-boundary-rail" aria-label="종목 전문 근거 감사 요약">
        <div className="rail-cell">
          <span>근거 커버리지</span>
          <strong>{formatPercent(coverageRatio)}</strong>
          <small>완료 {completeCount}/{applicableLayers.length} · 일부 {partialCount}</small>
        </div>
        <div className="rail-cell">
          <span>차단·대기</span>
          <strong>{(blockedCount + pendingCount).toLocaleString("ko-KR")}개</strong>
          <small>차단 {blockedCount} · 대기 {pendingCount}</small>
        </div>
        <div className="rail-cell">
          <span>빠진 근거</span>
          <strong>{missingLayers.length.toLocaleString("ko-KR")}개</strong>
          <small>
            {missingLayers.length > 0
              ? missingLayers.slice(0, 2).map((layer) => layer.label).join(", ")
              : "핵심 누락 없음"}
          </small>
        </div>
        <div className="rail-cell rail-critical">
          <span>실거래 상태</span>
          <strong className="rail-status-value">{koCode(data.professional_source_guardrail.order_boundary)}</strong>
          <small>증권사 주문 {data.professional_source_guardrail.broker_submit_allowed ? "허용" : "차단"}</small>
        </div>
      </div>

      <div className="flow-steps" style={{ marginTop: "18px" }}>
        {layers.map((layer) => (
          <article className="flow-step" key={layer.key}>
            <span>{layer.label}</span>
            <strong className={`risk-tag ${stockProfessionalLayerTone(layer.status)}`}>
              {stockProfessionalLayerStatusLabel(layer.status)}
            </strong>
            <p>{layer.detail}</p>
            <div className="flow-step-foot">
              <small>원천: {userFacingStockText(layer.source)}</small>
              {layer.href && layer.hrefLabel ? (
                layer.href.startsWith("#") ? (
                  <a href={layer.href}>{layer.hrefLabel} 보기</a>
                ) : (
                  <Link href={layer.href as Route}>{layer.hrefLabel} 보기</Link>
                )
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ProfessionalSourceGuardrailPanel({
  guardrail,
  symbol,
}: {
  guardrail: ProfessionalSourceGuardrail;
  symbol: string;
}) {
  const brokerSubmitLabel = guardrail.broker_submit_allowed ? "실거래 가능" : "읽기 전용";
  const brokerSubmitDetail = guardrail.broker_submit_allowed ? "증권사 주문 전송 허용" : "증권사 주문 전송 금지";

  return (
    <section className="bento-card span-4 reveal delay-2" aria-label="투자 판단 사용 가능 여부">
      <div className="section-heading">
        <div>
          <span className="metric-sub">투자 판단 사용 여부</span>
          <h2>{symbol} 분석을 투자 판단 입력으로 써도 되는가</h2>
        </div>
        <span className={`risk-tag ${professionalGuardrailTone(guardrail)}`}>
          {professionalGuardrailTitle(guardrail)}
        </span>
      </div>
      <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
        {userFacingStockText(guardrail.summary)} 추천 점수나 보유 비중을 바꾸지 않고, 투자 판단·가상 매매 검증·실거래 가능 여부를
        분리해서 보여준다.
      </p>
      <div className="status-rail compact-rail decision-boundary-rail" aria-label="투자 판단 사용 가능 여부 요약">
        <div className="rail-cell">
          <span>투자 판단 입력</span>
          <strong>{guardrail.professional_decision_use_allowed ? "가능" : "차단"}</strong>
          <small>{userFacingStockText(koCode(guardrail.status))}</small>
        </div>
        <div className="rail-cell">
          <span>가상 매매 검증</span>
          <strong>{guardrail.paper_validation_input_allowed ? "가능" : "차단"}</strong>
          <small>성과 확인 전 입력 여부</small>
        </div>
        <div className="rail-cell">
          <span>부족한 근거</span>
          <strong>{guardrail.blocker_label || "없음"}</strong>
          <small>{guardrail.blocker_code ? userFacingStockText(koCode(guardrail.blocker_code)) : "추가 보강 필요 없음"}</small>
        </div>
        <div className="rail-cell rail-critical">
          <span>실거래 상태</span>
          <strong className="rail-status-value">{brokerSubmitLabel}</strong>
          <small>{brokerSubmitDetail} · {koCode(guardrail.order_boundary)}</small>
        </div>
      </div>
      <div className="empty-state" style={{ marginTop: "18px" }}>
        <strong>다음 확인</strong>
        <p>{userFacingStockText(guardrail.next_action)}</p>
        <div className="btn-row">
          <Link className="btn btn-secondary" href="/data-health">
            원천 상태 보기
          </Link>
          <Link className="btn btn-secondary" href="/paper-trading">
            가상 매매 상태 보기
          </Link>
        </div>
      </div>
    </section>
  );
}

function EvidenceNeighborhoodPanel({ neighborhood }: { neighborhood: AiEvidenceNeighborhoodData }) {
  const firstTheme = neighborhood.themes[0];
  const firstArtifact = neighborhood.ai_artifacts[0];
  const firstThesis = neighborhood.theses[0];
  const firstRecommendation = neighborhood.recommendations[0];
  const storyGroups = neighborhood.story_groups ?? [];
  const ragContext = neighborhood.internal_rag_context;
  const ragInventory = ragContext.context_inventory;
  const ragPassedGateCount = ragContext.quality_gates.filter((gate) => gate.status === "passed").length;
  const investmentLinkCount = neighborhood.summary.thesis_count + neighborhood.summary.recommendation_count;
  const firstEvidenceHref = firstArtifact ? evidenceHref(firstArtifact.evidence_id) : null;
  const readinessLabel = ragContext.status === "ready" ? "판단 근거 준비됨" : "근거 보강 필요";
  const readinessCopy =
    ragContext.status === "ready"
      ? "뉴스, 번역, 원문 근거, 기존 추천·투자 논리가 함께 조회된다. 저장된 근거만 보여준다."
      : "연결된 자료가 부족합니다. 원문과 번역 상태가 확보되기 전에는 추천이나 보유 판단에 사용하지 않습니다.";

  return (
    <section className="stock-evidence-panel reveal delay-4" aria-label="이 종목이 뉴스와 엮인 이유">
      <div className="stock-evidence-head">
        <div>
          <span className="metric-sub">뉴스·투자 근거 연결</span>
          <h2>{neighborhood.symbol}에 영향을 줄 수 있는 뉴스가 어디서 왔고, 어떻게 연결됐는지 본다</h2>
          <p>
            수집 뉴스, 한국어 요약, 종목·테마 영향, 원문 근거, 추천·투자 논리 연결을 한 흐름으로 정리했다.
            저장된 분석만 읽고 새 추천이나 주문은 만들지 않는다.
          </p>
        </div>
        <aside>
          <span>현재 상태</span>
          <strong>{readinessLabel}</strong>
          <small>
            검사 {ragPassedGateCount}/{ragContext.quality_gates.length}개 통과 · 투자 연결 {investmentLinkCount.toLocaleString("ko-KR")}개
          </small>
        </aside>
      </div>

      <div className="stock-evidence-summary" aria-label="뉴스와 종목 연결 요약">
        <div>
          <span>수집 이벤트</span>
          <strong>{neighborhood.summary.event_count.toLocaleString("ko-KR")}개</strong>
          <small>뉴스·공시가 이 종목에 연결된 수</small>
        </div>
        <div>
          <span>뉴스 묶음</span>
          <strong>{(neighborhood.summary.story_group_count ?? storyGroups.length).toLocaleString("ko-KR")}개</strong>
          <small>같은 이슈로 묶인 후보</small>
        </div>
        <div>
          <span>심화 근거</span>
          <strong>{neighborhood.summary.ai_artifact_count.toLocaleString("ko-KR")}개</strong>
          <small>저장된 투자 근거</small>
        </div>
        <div>
          <span>원문 근거</span>
          <strong>{neighborhood.summary.evidence_chunk_count.toLocaleString("ko-KR")}개</strong>
          <small>뉴스·공시 본문 연결</small>
        </div>
      </div>

      <div className="stock-evidence-readiness" aria-label={`${neighborhood.symbol} 근거 준비 상태`}>
        <div className="stock-evidence-readiness-copy">
          <span>추천 입력 전 확인</span>
          <strong>{readinessLabel}</strong>
          <p>{readinessCopy}</p>
        </div>
        <div className="stock-evidence-gate-grid">
          {ragContext.quality_gates.map((gate) => (
            <article className="stock-evidence-gate-card" data-status={gate.status} key={gate.gate}>
              <span>{gate.status === "passed" ? "통과" : gate.status === "watch" ? "관찰" : "보강 필요"}</span>
              <strong>{userFacingStockText(koCode(gate.gate))}</strong>
              <p>{userFacingStockText(gate.message_ko)}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="stock-evidence-chain" aria-label={`${neighborhood.symbol} 뉴스 근거 관계 흐름`}>
        <article className="stock-evidence-chain-card">
          <span>1. 수집된 사건</span>
          <strong>이벤트 {neighborhood.summary.event_count.toLocaleString("ko-KR")}개</strong>
          <p>
            {neighborhood.events[0]
              ? koLabel(neighborhood.events[0].title)
              : "아직 이 종목에 연결된 이벤트가 없다."}
          </p>
          <Link href={`/events?symbol=${encodeURIComponent(neighborhood.symbol)}` as Route}>수집 뉴스 보기</Link>
        </article>
        <article className="stock-evidence-chain-card">
          <span>2. 테마·노출</span>
          <strong>{firstTheme ? koCode(firstTheme.theme_key) : "테마 없음"}</strong>
          <p>
            {firstTheme
              ? `멤버십 ${koCode(firstTheme.membership_type)} · 신뢰도 ${formatPercent(firstTheme.confidence)}`
              : "테마 연결이 쌓이면 이 위치에 표시된다."}
          </p>
        </article>
        <article className="stock-evidence-chain-card">
          <span>3. 투자 영향</span>
          <strong>{firstArtifact ? koCode(firstArtifact.evidence_type) : "심화 근거 없음"}</strong>
          <p>
            {firstArtifact
              ? `${providerLabel(firstArtifact.provider)} · 신뢰도 ${formatPercent(firstArtifact.confidence)}`
              : "아직 저장된 투자 근거가 없다."}
          </p>
          {firstEvidenceHref ? <Link href={firstEvidenceHref}>근거 상세 열기</Link> : <small>근거 대기</small>}
        </article>
        <article className="stock-evidence-chain-card final">
          <span>4. 투자 판단 연결</span>
          <strong>{firstRecommendation ? koCode(firstRecommendation.action) : firstThesis ? "투자 논리만 있음" : "판단 대기"}</strong>
          <p>
            {firstRecommendation
              ? `점수 ${formatPercent(firstRecommendation.total_score)} · 목표 비중 ${formatPercent(firstRecommendation.recommended_weight)}`
              : firstThesis
                ? `${userFacingStockText(firstThesis.title)} · 확신 ${formatPercent(firstThesis.conviction_score)}`
                : "추천이나 보유 판단으로 연결되기 전 단계다."}
          </p>
          <div className="mini-link-stack">
            {firstRecommendation ? <Link href={recommendationHref(firstRecommendation.recommendation_id)}>추천 상세</Link> : null}
            {firstThesis ? <Link href={thesisHref(firstThesis.thesis_id)}>투자 논리</Link> : null}
          </div>
        </article>
      </div>

      <section className="stock-evidence-section" aria-label={`${neighborhood.symbol} 뉴스 이야기 묶음`}>
        <div className="stock-evidence-section-head">
          <div>
            <span>뉴스 묶음 이유</span>
            <h3>같은 이슈로 묶인 뉴스와 그 근거</h3>
          </div>
          <p>제목만 보지 않고, 테마·종목·원문 근거·묶음 신뢰도를 함께 본다.</p>
        </div>
        <div className="stock-story-card-grid">
          {storyGroups.slice(0, 4).map((group) => {
            const firstSource = sourceDocumentHref(group.source_document_ids[0] ?? null);
            return (
              <article className="stock-story-card" key={group.story_id}>
                <div className="stock-story-card-top">
                  <span>{formatStoryBasis(group.basis)}</span>
                  <strong>묶음 신뢰도 {formatPercent(group.confidence)}</strong>
                </div>
                <NewsTitleBlock
                  compact
                  title={group.title}
                  koreanTitle={group.korean_title}
                  koreanSummary={group.korean_summary}
                  translationConfidence={group.translation_confidence}
                  themeKey={group.theme_keys[0]}
                />
                <div className="stock-story-metrics">
                  <span>이벤트 {group.event_count.toLocaleString("ko-KR")}개</span>
                  <span>원천 {group.source_document_count.toLocaleString("ko-KR")}개</span>
                  <span>원문 근거 {group.linked_chunk_count.toLocaleString("ko-KR")}개</span>
                </div>
                <div className="stock-story-reasons">
                  {group.relation_reasons.slice(0, 3).map((reason) => (
                    <p key={`${group.story_id}-${reason}`}>묶인 이유: {koLabel(reason)}</p>
                  ))}
                </div>
                {group.events.slice(0, 2).map((event) => (
                  <div className="stock-story-event" key={`${group.story_id}-${event.event_id}`}>
                    <small>대표 이벤트 · {formatDate(event.event_at)} · {koCode(event.impact_direction)}</small>
                    <NewsTitleBlock
                      compact
                      title={event.title}
                      koreanTitle={event.korean_title}
                      koreanSummary={event.korean_summary}
                      translationConfidence={event.translation_confidence}
                      themeKey={event.theme_key}
                      impactDirection={event.impact_direction}
                      impactScore={event.impact_score}
                    />
                  </div>
                ))}
                <div className="mini-link-stack">
                  {firstSource ? <Link href={firstSource}>원천 문서</Link> : null}
                  <Link href={`/events?symbol=${encodeURIComponent(neighborhood.symbol)}` as Route}>수집 뉴스</Link>
                </div>
              </article>
            );
          })}
          {storyGroups.length === 0 ? (
            <p className="stock-evidence-empty">아직 같은 이야기로 묶을 수 있는 뉴스 근거가 없다.</p>
          ) : null}
        </div>
      </section>

      <section className="stock-evidence-section" aria-label={`${neighborhood.symbol} 저장된 원문 근거`}>
        <div className="stock-evidence-section-head">
          <div>
            <span>원천 대조</span>
            <h3>투자 근거가 참조한 원문</h3>
          </div>
          <p>본문 추출 여부와 출처를 먼저 보여준다. 영어 원문은 필요할 때만 연다.</p>
        </div>
        <div className="stock-source-card-grid">
          {neighborhood.evidence_chunks.slice(0, 4).map((chunk) => {
            const document = sourceDocumentHref(chunk.source_document_id);
            const sourceKind =
              chunk.source_text_kind === "raw_html_text"
                ? "원문 본문 추출"
                : chunk.used_metadata_fallback
                  ? "본문 부족, 문서 정보 대체"
                  : "추출 상태 미확인";
            return (
              <article className="stock-source-card" key={chunk.chunk_id}>
                <span>{chunk.used_metadata_fallback ? "요약 정보 기반" : "원문 본문 기반"}</span>
                <strong>{evidenceChunkPreview(chunk.text_preview)}</strong>
                <p>{chunk.source_url_host || "출처 없음"} · {sourceKind} · 근거 저장 상태 {koCode(chunk.embedding_status)}</p>
                {document ? <Link href={document}>원천 문서 열기</Link> : null}
              </article>
            );
          })}
          {neighborhood.evidence_chunks.length === 0 ? (
            <p className="stock-evidence-empty">아직 이 종목에 연결된 원문 근거가 없다.</p>
          ) : null}
        </div>
      </section>

      <div className="stock-guardrail-list" aria-label="종목 근거 화면 사용 경계">
        {stockGuardrails().map((guardrail) => (
          <article key={guardrail}>
            <span>사용 경계</span>
            <p>{koLabel(guardrail)}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export default async function StockDetailPage({ params }: StockDetailPageProps) {
  const { symbol } = await params;
  const [response, neighborhoodResponse] = await Promise.all([
    getStockDetail(symbol),
    getAiEvidenceNeighborhood(symbol),
  ]);
  const data = response.data;
  const neighborhood = neighborhoodResponse.data;
  const hasPriceData = data.summary.bar_count > 0 && data.latest_price.close !== null;
  const equityResearch = data.equity_research;
  const industryPosition = data.industry_competitive_position;
  const financialStatementModel = data.financial_statement_model;
  const valuationTargetRange = data.valuation_target_range;
  const sourceGuardrail = data.professional_source_guardrail;
  const sourceBlocked = sourceGuardrail.blocked;
  const hasTargetRange = valuationTargetRange.status === "available";
  const valuationItems = equityResearch ? valuationSensitivityItems(equityResearch.valuation_sensitivity) : [];
  const hasEvidenceOnlyData =
    !hasPriceData && (data.macro_flow_impacts.length > 0 || data.recent_events.length > 0);
  const linkedThesisId = data.recommendation?.linked_thesis_id ?? neighborhood.theses[0]?.thesis_id ?? null;
  const marketCorrelationCount = data.market_correlations.length;
  const professionalResearchSteps: ResearchFlowStep[] = [
    {
      id: "business",
      label: "01",
      title: "사업 개요",
      status: equityResearch ? "리서치 생성" : "리서치 대기",
      tone: equityResearch ? "ready" : "watch",
      body: equityResearch?.korean_summary
        ? userFacingStockText(equityResearch.korean_summary)
        : "이 종목의 사업 설명 결과가 아직 없다. 현재 화면에서는 가격, 뉴스, 상위 흐름까지만 신뢰할 수 있다.",
      facts: [
        { label: "종목", value: `${data.symbol} · ${data.name}` },
        { label: "시장", value: `${data.market_code} · ${data.currency_code}` },
      ],
    },
    {
      id: "financial-quality",
      label: "02",
      title: "재무 품질",
      status: sourceBlocked
        ? "투자 판단 차단"
        : financialStatementModel.status === "available" || financialStatementModel.status === "partial"
          ? `${financialStatementModel.computed_metric_count}개 지표`
          : "재무 모델 대기",
      tone: sourceBlocked
        ? "blocked"
        : financialStatementModel.status === "available" || financialStatementModel.status === "partial"
          ? "ready"
          : "watch",
      body: sourceBlocked
        ? userFacingStockText(sourceGuardrail.summary)
        : financialStatementModel.status === "available" || financialStatementModel.status === "partial" || financialStatementModel.source_data_blocker
          ? userFacingStockText(financialStatementModel.summary)
          : "매출, 마진, 현금흐름, 부채, 이익 품질을 확인할 정규화 재무 모델이 아직 충분하지 않다.",
      facts: [
        { label: "최근 기간", value: financialStatementModel.latest_period_end || "없음" },
        { label: "계산 지표", value: `${financialStatementModel.computed_metric_count}개` },
        { label: "데이터 공백", value: `${financialStatementModel.data_gap_count}개` },
        { label: "근거 상태", value: sourceBlocked ? sourceGuardrail.blocker_label : "차단 없음" },
      ],
    },
    {
      id: "peer-position",
      label: "03",
      title: "피어·경쟁 위치",
      status: industryPosition ? competitivePositionLabel(industryPosition.competitive_position) : "비교군 표시 대기",
      tone: industryPosition ? "ready" : "watch",
      body: industryPosition
        ? competitivePositionSummary(industryPosition, data.symbol)
        : "동일 산업·테마 비교군 안에서 수익성, 성장성, 재무 안정성, 가격 결정력 추정 지표를 보여주는 데이터가 아직 없다.",
      facts: industryPosition
        ? [
            { label: "비교군", value: industryPosition.peer_group_name ?? industryPosition.peer_group_code ?? "미분류" },
            { label: "종합 경쟁력", value: formatPercent(industryPosition.moat_score) },
            { label: "경쟁 강도", value: formatPercent(industryPosition.rivalry_risk_score) },
          ]
        : undefined,
      href: data.recommendation ? recommendationHref(data.recommendation.recommendation_id) : undefined,
      hrefLabel: data.recommendation ? "추천 상세에서 같이 보기" : undefined,
    },
    {
      id: "valuation",
      label: "04",
      title: "밸류에이션",
      status: hasTargetRange ? `${valuationTargetRange.method_count}개 목표가 산출` : (valuationItems.length ? `${valuationItems.length}개 민감도` : "산출 대기"),
      tone: hasTargetRange || valuationItems.length ? "ready" : "watch",
      body: hasTargetRange
        ? "현재가 대비 목표가 하단·기준·상단과 안전마진을 비교한다. 이 값은 추천 점수를 바로 바꾸지 않고 가격 근거로만 쓴다."
        : valuationItems.length
          ? "현금흐름, 상대 배수, 시나리오 범위가 추천 점수를 바로 바꾸지는 않지만, 비싸게 사는지 여부를 확인하는 핵심 입력이다."
        : "아직 목표가 범위, 안전마진, 시나리오 민감도가 충분히 저장되지 않았다.",
      facts:
        hasTargetRange
          ? [
              { label: "기준 목표가", value: formatCurrency(valuationTargetRange.target_base, valuationTargetRange.currency_code) },
              { label: "기준 상승여지", value: formatPercent(valuationTargetRange.upside_base) },
              { label: "산출 방법", value: `${valuationTargetRange.method_count}개` },
            ]
          : valuationItems.length > 0
          ? valuationItems.slice(0, 3).map((item) => ({
              label: valuationSensitivityLabel(item.key),
              value: userFacingStockText(item.value),
            }))
          : [{ label: "상태", value: "밸류에이션 결과 대기" }],
    },
    {
      id: "news-cycle",
      label: "05",
      title: "뉴스·사이클 영향",
      status: `${data.recent_events.length + data.macro_flow_impacts.length}개 뉴스·흐름 · ${marketCorrelationCount}개 동조성`,
      tone: data.recent_events.length + data.macro_flow_impacts.length + marketCorrelationCount > 0 ? "ready" : "neutral",
      body:
        data.recent_events.length + data.macro_flow_impacts.length + marketCorrelationCount > 0
          ? "직접 종목 뉴스, 거시·테마 흐름 전파, 시장 지표와의 동조성을 분리해서 본다. 동조성은 원인 단정이 아니라 리스크 점검 입력이다."
          : "아직 이 종목에 연결된 직접 뉴스, 상위 흐름 전파, 시장 동조성 근거가 없다.",
      facts: [
        { label: "직접 뉴스", value: `${data.recent_events.length}개` },
        { label: "상위 흐름", value: `${data.macro_flow_impacts.length}개` },
        { label: "시장 동조성", value: `${marketCorrelationCount}개` },
      ],
      href: "/intelligence" as Route,
      hrefLabel: "뉴스 근거 흐름 보기",
    },
    {
      id: "thesis",
      label: "06",
      title: "투자 논리 생애주기",
      status: linkedThesisId ? "투자 논리 연결" : "투자 논리 없음",
      tone: linkedThesisId ? "ready" : "blocked",
      body: linkedThesisId
        ? "왜 사는지, 무엇이 맞아야 하는지, 무엇이 틀리면 나가는지를 투자 논리 화면에서 본다."
        : "중장기 투자 시스템에서는 투자 논리 없이 추천이나 보유 판단을 신뢰하면 안 된다.",
      href: linkedThesisId ? thesisHref(linkedThesisId) : undefined,
      hrefLabel: linkedThesisId ? "투자 논리 열기" : undefined,
    },
    {
      id: "paper-validation",
      label: "07",
      title: "가상 매매·실거래 상태",
      status: sourceBlocked ? "가상 검증 입력 차단" : data.position ? "보유 상태 있음" : data.recommendation ? "추천 근거 있음" : "거래 입력 전",
      tone: sourceBlocked ? "blocked" : "neutral",
      body: sourceBlocked
        ? `${userFacingStockText(sourceGuardrail.next_action)} 실제 증권사 주문 전송은 계속 닫혀 있다.`
        : "실제 증권사 주문 전송은 닫혀 있다. 추천이 생겨도 가상 매매 검증과 리스크 상태가 먼저다.",
      href: "/paper-trading" as Route,
      hrefLabel: "가상 매매 상태 보기",
    },
  ];
  const stockOutcome = stockDecisionOutcome(data, sourceGuardrail, hasPriceData);
  const stockNewsCount = data.recent_events.length + data.macro_flow_impacts.length;

  return (
    <div className="pageStack decision-page">
      <section className="decision-brief workspace-brief stock-command-deck reveal" aria-labelledby="stock-detail-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">종목 상세 · {data.market_code} · {data.as_of_date}</span>
          <h1 className="decision-brief-title" id="stock-detail-title">
            {stockOutcome.title}
          </h1>
          <p className="decision-brief-copy">
            {stockOutcome.body} 가격·추천·보유·뉴스·상위 흐름·투자 논리·가상 매매 상태를 한 종목 기준으로 대조한다.
          </p>
          <div className="decision-brief-meta" aria-label={`${data.symbol} 핵심 상태`}>
            <span>최신 종가 {hasPriceData ? formatCurrency(data.latest_price.close, data.currency_code) : "가격 미수집"}</span>
            <span>추천 {data.recommendation ? koCode(data.recommendation.action) : "없음"}</span>
            <span>보유 {data.position ? formatPercent(data.position.weight) : "미보유"}</span>
            <span>뉴스·흐름 {stockNewsCount.toLocaleString("ko-KR")}개</span>
            <span>시장 동조성 {marketCorrelationCount.toLocaleString("ko-KR")}개</span>
          </div>
        </div>
        <div className="decision-brief-grid workspace-command-grid" aria-label={`${data.symbol} 분석 목차`}>
          <Link className={data.recommendation ? "decision-card primary is-good" : "decision-card primary is-watch"} href={data.recommendation ? recommendationHref(data.recommendation.recommendation_id) : "/recommendations"}>
            <span>추천</span>
            <strong>{data.recommendation ? koCode(data.recommendation.action) : "추천 없음"}</strong>
            <small>{data.recommendation ? `점수 ${formatPercent(data.recommendation.score)} · ${koCode(data.recommendation.status)}` : "아직 추천 상세가 없다."}</small>
            <b>추천 근거</b>
          </Link>
          <Link className={data.position ? "decision-card is-good" : "decision-card is-watch"} href="/portfolio/coverage">
            <span>보유</span>
            <strong>{data.position ? formatPercent(data.position.weight) : "미보유"}</strong>
            <small>{data.position ? `${koLabel(data.position.portfolio_name)} · ${formatCurrency(data.position.market_value, data.currency_code)}` : "포트폴리오 스냅샷에 보유 포지션이 없다."}</small>
            <b>보유 상태</b>
          </Link>
          <a className={stockNewsCount > 0 ? "decision-card is-good" : "decision-card is-watch"} href={stockNewsCount > 0 ? "#stock-flow-impacts" : "/intelligence"}>
            <span>뉴스·흐름</span>
            <strong>{stockNewsCount.toLocaleString("ko-KR")}개 연결</strong>
            <small>직접 뉴스 {data.recent_events.length.toLocaleString("ko-KR")}개 · 상위 흐름 {data.macro_flow_impacts.length.toLocaleString("ko-KR")}개</small>
            <b>근거 보기</b>
          </a>
          <a className={marketCorrelationCount > 0 ? "decision-card is-good" : "decision-card is-watch"} href="#stock-market-correlations">
            <span>시장 동조성</span>
            <strong>{marketCorrelationCount.toLocaleString("ko-KR")}개 비교</strong>
            <small>지수·섹터·금리·달러·원자재와 최근 같이 움직였는지 본다. 원인 단정은 하지 않는다.</small>
            <b>리스크 보기</b>
          </a>
          <Link className={linkedThesisId ? "decision-card is-good" : "decision-card is-block"} href={linkedThesisId ? thesisHref(linkedThesisId) : "/portfolio/coverage"}>
            <span>투자 논리</span>
            <strong>{linkedThesisId ? "연결됨" : "없음"}</strong>
	            <small>{linkedThesisId ? "매수 이유, 유지 조건, 무효화 조건을 본다." : "중장기 판단 전 투자 논리 연결이 필요하다."}</small>
            <b>{linkedThesisId ? "논리 보기" : "보유 점검"}</b>
          </Link>
        </div>
      </section>

      <StockProfessionalEvidenceAuditPanel
        data={data}
        neighborhood={neighborhood}
        linkedThesisId={linkedThesisId}
        hasPriceData={hasPriceData}
      />

      <ProfessionalResearchFlow
        eyebrow="전문 리서치 읽는 순서"
        title={`${data.symbol} 분석은 종목 하나로 끝나지 않는다`}
        summary="중장기 투자 판단은 뉴스 하나로 끝나지 않는다. 사업, 재무, 비교군, 밸류에이션, 사이클, 투자 논리, 가상 매매 검증을 같은 순서로 본다."
        footer="저장된 데이터만 읽는다. 새 분석이나 주문 생성은 없다."
        steps={professionalResearchSteps}
      />

      <ProfessionalSourceGuardrailPanel guardrail={sourceGuardrail} symbol={data.symbol} />

      <FinancialStatementModelPanel model={financialStatementModel} symbol={data.symbol} />

      <FundInstrumentAnalysisPanel analysis={data.fund_instrument_analysis} />

      {hasEvidenceOnlyData ? (
        <section className="bento-card reveal delay-1" aria-label="가격 미수집 안내">
          <div className="section-heading stacked-heading">
            <span className="metric-sub">데이터 상태 구분</span>
            <h2>가격 데이터가 부족해 시장 흐름 노출부터 보여준다</h2>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: 0 }}>
            {data.symbol}은 현재 뉴스·테마 흐름에는 연결되어 있지만, 이 서버의 가격 캔들 수집 대상에는 아직 충분히
            포함되지 않았다. 따라서 가격 차트와 수익률은 판단하지 않고, 아래 상위 흐름/원천 뉴스만 본다.
          </p>
        </section>
      ) : null}

      <section className="bento-grid reveal delay-2" id="stock-price-data" aria-label="가격 데이터와 차트">
        <article className="bento-card span-3">
          <div className="section-heading">
            <div>
              <span className="metric-sub">1. 가격 데이터</span>
              <h2>가격 흐름은 데이터 출처와 추세가 먼저다</h2>
            </div>
            <Link className="btn btn-secondary" href="/data-health">
              수집 상태 보기
            </Link>
          </div>
          <CandlestickChart
            bars={data.candles}
            currencyCode={data.currency_code}
            provider={data.market_data_provider}
            tossEvidence={data.toss_provider_evidence}
          />
        </article>

        <article className="bento-card">
          <span className="metric-label">가격 데이터</span>
          <strong className="metric-value">{data.summary.bar_count.toLocaleString("ko-KR")}</strong>
          <span className="metric-sub">수집된 거래일 수</span>
          <div className="stock-meta-grid">
            <span>저가 종가</span>
            <strong>{formatCurrency(data.summary.low_close, data.currency_code)}</strong>
            <span>고가 종가</span>
            <strong>{formatCurrency(data.summary.high_close, data.currency_code)}</strong>
            <span>거래량</span>
            <strong>{formatNumber(data.latest_price.volume)}</strong>
          </div>
          <div className="stock-meta-grid" style={{ marginTop: "1rem" }}>
            <span>분석 기준</span>
            <strong>{data.market_data_provider.analysis_price_source.provider}</strong>
            <span>계산 반영</span>
            <strong>{data.market_data_provider.analysis_price_source.used_for_scoring ? "추천·사이클 사용" : "미사용"}</strong>
            <span>브로커 참고</span>
            <strong>{data.market_data_provider.broker_price_source.label}</strong>
            <span>토스 상태</span>
            <strong>{data.toss_provider_evidence.comparison.status_label}</strong>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: 0 }}>
            {data.market_data_provider.price_basis_note} 토스증권 가격은 계좌·호가 현실 확인용이며 총점에는 아직 반영하지 않는다.
          </p>
        </article>
      </section>

      <section className="bento-card span-4 reveal delay-2" id="stock-market-correlations" aria-label="시장 동조성">
        <div className="section-heading">
          <div>
            <span className="metric-sub">2. 시장 동조성</span>
            <h2>{data.symbol}이 어떤 시장 변수와 같이 움직였는지 본다</h2>
          </div>
          <Link className="btn btn-secondary" href="/market-map">
            시장 지도 보기
          </Link>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          상관관계는 최근 수익률이 같이 움직인 정도다. 원인을 단정하지 않고, 포트폴리오 집중·헤지 필요성·추천 리스크를 확인하는 보조 입력으로만 쓴다.
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
                  {formatPercent(correlation.confidence)}
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
            아직 이 종목의 시장 동조성이 계산되지 않았다. 장마감 후 상관관계 분석이 실행되면 지수·섹터·금리·달러·원자재와의 관계가 표시된다.
          </div>
        )}
      </section>

      <section className="bento-grid reveal delay-3" id="stock-recommendation-status" aria-label="추천과 보유 상태">
        <article className="bento-card span-2">
          <div className="section-heading">
            <div>
              <span className="metric-sub">3. 추천 판단</span>
              <h2>추천은 상세 근거가 있을 때만 읽는다</h2>
            </div>
            {data.recommendation ? (
              <Link className="btn btn-primary" href={recommendationHref(data.recommendation.recommendation_id)}>
                추천 상세
              </Link>
            ) : null}
          </div>
          {data.recommendation ? (
            <div className="stock-meta-grid">
              <span>판단</span>
              <strong>{koCode(data.recommendation.action)}</strong>
              <span>점수</span>
              <strong>{formatPercent(data.recommendation.score)}</strong>
              <span>상태</span>
              <strong>{koCode(data.recommendation.status)}</strong>
              <span>투자 논리</span>
              {data.recommendation.linked_thesis_id ? (
                <Link href={thesisHref(data.recommendation.linked_thesis_id)}>
                  투자 논리 열기
                </Link>
              ) : (
                <strong>없음</strong>
              )}
            </div>
          ) : (
            <div className="empty-state">이 종목은 아직 추천 점수와 투자 논리가 붙지 않았다.</div>
          )}
        </article>

        <article className="bento-card span-2">
          <div className="section-heading">
            <div>
              <span className="metric-sub">4. 보유 상태</span>
              <h2>보유 중이면 추천·투자 논리와 충돌하는지 본다</h2>
            </div>
            <Link className="btn btn-secondary" href="/portfolio/coverage">
              포트폴리오 보기
            </Link>
          </div>
          {data.position ? (
            <div className="stock-meta-grid">
              <span>포트폴리오</span>
              <strong>{koLabel(data.position.portfolio_name)}</strong>
              <span>수량</span>
              <strong>{formatNumber(data.position.quantity)}</strong>
              <span>평가액</span>
              <strong>{formatCurrency(data.position.market_value, data.currency_code)}</strong>
              <span>평가 가격</span>
              <strong>{formatCurrency(data.position.market_price, data.currency_code)}</strong>
            </div>
          ) : (
            <div className="empty-state">현재 포트폴리오 스냅샷에는 보유 포지션이 없다.</div>
          )}
        </article>
      </section>

      <div id="stock-valuation">
        <ValuationTargetRangeCard
          valuation={valuationTargetRange}
          eyebrow="전문 밸류에이션"
          title={`${data.symbol} 목표가 범위`}
        />
      </div>

      <section className="bento-card span-4 reveal delay-3" id="stock-equity-research" aria-label="기업 리서치 리포트">
        <div className="section-heading">
          <div>
            <span className="metric-sub">기업 리서치 리포트</span>
            <h2>{equityResearch ? userFacingStockText(equityResearch.title) : `${data.symbol} 기업 리서치가 아직 생성되지 않았다`}</h2>
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
              {userFacingStockText(equityResearch.korean_summary)}
            </p>
            <div className="status-rail compact-rail" aria-label="기업 리서치 범위">
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
                <small>투자 논리 재검토 기준</small>
              </div>
            </div>
            <div className="bento-grid" style={{ marginTop: "18px" }}>
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
                    <span>{valuationSensitivityLabel(item.key)}</span>
                    <strong>{userFacingStockText(item.value)}</strong>
                  </Fragment>
                ))}
              </div>
            ) : null}
            {equityResearch.source_document_ids.length > 0 ? (
              <div className="btn-row">
                {equityResearch.source_document_ids.slice(0, 3).map((documentId, index) => (
                  <Link className="btn btn-secondary" href={sourceDocumentHref(documentId) ?? "/data-health"} key={documentId}>
                    원천 문서 {index + 1}
                  </Link>
                ))}
              </div>
            ) : null}
            <p style={{ color: "var(--text-muted)", marginBottom: 0 }}>
              이 리포트는 저장된 읽기 전용 분석이다. 추천 점수와 주문은 직접 변경하지 않으며,
              추천 상세의 재무·밸류에이션 근거와 성과 평가는 별도로 본다.
            </p>
          </>
        ) : (
          <div className="empty-state">
            아직 이 종목의 기업 리서치 결과가 없다. 자동 분석이 완료되면 사업 설명, 핵심 재무 변화,
            촉매, 리스크, 무효화 조건, 밸류에이션 민감도가 이곳에 표시된다.
          </div>
        )}
      </section>

      <IndustryCompetitivePositionPanel position={industryPosition} symbol={data.symbol} />

      <EvidenceNeighborhoodPanel neighborhood={neighborhood} />

      <section className="bento-card span-4 reveal delay-4" id="stock-flow-impacts">
        <div className="section-heading">
          <div>
            <span className="metric-sub">5. 상위 흐름 전파</span>
            <h2>회사명이 없어도 거시·테마 흐름은 종목에 영향을 줄 수 있다</h2>
          </div>
          <Link className="btn btn-secondary" href="/intelligence">
            흐름 분석 보기
          </Link>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          회사가 직접 언급되지 않은 뉴스라도 금리, 에너지, AI 반도체 같은 상위 흐름이면 노출도에 따라 이 종목으로 영향이 전파된다.
        </p>
        <div className="bento-list">
          {data.macro_flow_impacts.length > 0 ? (
            data.macro_flow_impacts.map((flow) => {
              const evidence = evidenceHref(flow.ai_evidence_id);
              const sourceDocument = sourceDocumentHref(flow.source_document_id);
              const flowRationale = cleanFlowText(flow.rationale, {
                themeKey: flow.theme_key,
                symbol: data.symbol,
                impactDirection: flow.impact_direction,
              });
              return (
                <div className="bento-list-item" key={`${flow.event_id}-${flow.theme_key}`}>
                  <div>
                    <span className="metric-sub">
                      {formatDate(flow.event_at)} • {koCode(flow.theme_key)} • {koCode(flow.impact_direction)}
                    </span>
                    <NewsTitleBlock
                      title={flow.title}
                      koreanTitle={flow.korean_title}
                      koreanSummary={flow.korean_summary}
                      translationConfidence={flow.translation_confidence}
                      symbol={data.symbol}
                      themeKey={flow.theme_key}
                      impactDirection={flow.impact_direction}
                      impactScore={flow.impact_score}
                    />
                    <span>
                      전파 강도 {formatPercent(flow.impact_score)} · 노출도 {formatPercent(flow.exposure_weight)} · 신뢰도 {formatPercent(flow.confidence)}
                    </span>
                    {flowRationale ? <span className="flow-rationale">{flowRationale}</span> : null}
                  </div>
                  <div className="btn-row" style={{ marginTop: 0 }}>
                    <Link className="btn btn-secondary" href={`/themes/${encodeURIComponent(flow.theme_key)}?asOfDate=${encodeURIComponent(data.as_of_date)}` as Route}>
                      흐름 보기
                    </Link>
                    {evidence ? <Link className="btn btn-secondary" href={evidence}>근거 상세</Link> : null}
                    {sourceDocument ? <Link className="btn btn-secondary" href={sourceDocument}>근거 문서</Link> : null}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">
              아직 이 종목으로 전파된 상위 흐름이 없다. 직접 뉴스만 있거나 종목 민감도 연결이 부족한 상태다.
            </div>
          )}
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-4" id="stock-direct-events">
        <div className="section-heading">
          <div>
            <span className="metric-sub">6. 직접 뉴스</span>
            <h2>회사나 티커가 직접 연결된 뉴스만 따로 본다</h2>
          </div>
          <Link className="btn btn-secondary" href={`/events?symbol=${encodeURIComponent(data.symbol)}` as Route}>
            수집 뉴스
          </Link>
        </div>
        <div className="bento-list">
          {data.recent_events.length > 0 ? (
            data.recent_events.map((event) => {
              const evidence = evidenceHref(event.ai_evidence_id);
              const sourceDocument = sourceDocumentHref(event.source_document_id);
              return (
                <div className="bento-list-item" key={event.event_id}>
                  <div>
                    <span className="metric-sub">{formatDate(event.event_at)} • {koCode(event.event_type)}</span>
                    <NewsTitleBlock
                      title={event.title}
                      koreanTitle={event.korean_title}
                      koreanSummary={event.korean_summary}
                      translationConfidence={event.translation_confidence}
                      symbol={data.symbol}
                      impactDirection={event.impact_direction}
                      impactScore={event.impact_score}
                    />
                    <span>{koCode(event.impact_direction)} • 영향도 {formatPercent(event.impact_score)}</span>
                  </div>
                  <div className="btn-row" style={{ marginTop: 0 }}>
                    {evidence ? <Link className="btn btn-secondary" href={evidence}>근거 상세</Link> : null}
                    {sourceDocument ? <Link className="btn btn-secondary" href={sourceDocument}>근거 문서</Link> : null}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">아직 이 종목에 연결된 이벤트가 없다.</div>
          )}
        </div>
      </section>
    </div>
  );
}
