import Link from "next/link";
import type { Route } from "next";
import { Fragment } from "react";

import { NewsTitleBlock } from "@/components/news-title-block";
import { ProfessionalResearchFlow, type ResearchFlowStep } from "@/components/professional-research-flow";
import { ValuationTargetRangeCard } from "@/components/valuation-target-range-card";
import { getAiEvidenceNeighborhood, getStockDetail } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { AiEvidenceNeighborhoodData, StockDetailData, StockPrice } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "종목 상세" };

type StockDetailPageProps = {
  params: Promise<{ symbol: string }>;
};

type IndustryCompetitivePosition = NonNullable<StockDetailData["industry_competitive_position"]>;
type FinancialStatementModel = StockDetailData["financial_statement_model"];
type FinancialMetricSnapshot = FinancialStatementModel["metrics"][number];
type FundInstrumentAnalysis = StockDetailData["fund_instrument_analysis"];

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

function formatCost(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "비용 없음";
  }
  return `$${value.toFixed(4)}`;
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
    return "Codex OAuth AI 분석";
  }
  if (provider === "fixture") {
    return "검증용 샘플 분석";
  }
  return koCode(provider);
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
  const visibleSections = model.sections.filter((section) => section.metrics.length > 0 || section.status !== "missing");
  const sourceBlocker = model.source_data_blocker;

  if (model.status === "unavailable") {
    return (
      <section className="bento-card span-4 reveal delay-3" aria-label="재무제표 모델">
        <div className="section-heading stacked-heading">
          <span className="metric-sub">재무제표 모델</span>
          <h2>{sourceBlocker ? `${symbol} ${sourceBlocker.label}` : `${symbol} 재무 모델이 아직 준비되지 않았다`}</h2>
        </div>
        <p style={{ color: "var(--text-secondary)", marginBottom: 0 }}>
          {sourceBlocker
            ? model.summary
            : "SEC companyfacts 수집과 재무 정규화가 완료되면 매출 성장, 마진, 현금흐름, 부채, 이익 품질을 이곳에서 확인한다. 이 데이터가 없으면 뉴스나 사이클만으로 장기 투자 판단을 확정하지 않는다."}
        </p>
        {sourceBlocker ? (
          <div className="status-rail compact-rail" aria-label="재무 원천 차단 사유" style={{ marginTop: "18px" }}>
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
    <section className="bento-card span-4 reveal delay-3" aria-label="재무제표 모델">
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
        {model.summary} 이 섹션은 기존 정규화 재무 지표를 읽는 화면이며, 추천 점수와 주문 가능 여부를 바꾸지 않는다.
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
        원천 실행: {model.source_run_ids.length > 0 ? model.source_run_ids.join(", ") : "실행 기록 없음"} · 이 화면에서는
        주문을 만들지 않는다.
      </p>
    </section>
  );
}

function FundInstrumentAnalysisPanel({ analysis }: { analysis: FundInstrumentAnalysis }) {
  if (!analysis) {
    return null;
  }
  return (
    <section className="bento-card span-4 reveal delay-2" aria-label="ETF와 펀드형 상품 분석">
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
          <span>추적오차</span>
          <strong>{koCode(analysis.tracking_error.status)}</strong>
          <p>{analysis.tracking_error.summary}</p>
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
      <section className="bento-card span-4 reveal delay-3" aria-label="산업 경쟁 위치">
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
    <section className="bento-card span-4 reveal delay-3" aria-label="산업 경쟁 위치">
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
        피어 비교로 만든 추정 지표이며, 추천 총점을 직접 바꾸지 않는다.
      </p>

      <div className="status-rail compact-rail" aria-label="산업 경쟁 위치 요약">
        <div className="rail-cell">
          <span>경쟁 위치</span>
          <strong>{competitivePositionLabel(position.competitive_position)}</strong>
          <small>{koCode(position.methodology)}</small>
        </div>
        <div className="rail-cell">
          <span>비교군</span>
          <strong>{position.peer_group_name ?? position.peer_group_code ?? "미분류"}</strong>
          <small>{position.peer_count.toLocaleString("ko-KR")}개 종목 기준</small>
        </div>
        <div className="rail-cell">
          <span>섹터</span>
          <strong>{position.sector_name ?? position.sector_code ?? "미분류"}</strong>
          <small>산업/테마 분류 기준</small>
        </div>
        <div className="rail-cell">
          <span>지표 커버리지</span>
          <strong>{position.metric_coverage_count.toLocaleString("ko-KR")}</strong>
          <small>{position.source_run_id ?? "실행 번호 없음"}</small>
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
            <div className="bento-list-item" key={item}>{koLabel(item)}</div>
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
    return `${koCode(themeKey)} 흐름이 ${koCode(symbol)}에 ${koCode(impactDirection)} 방향으로 전파됐다. 노출도와 신뢰도는 위 수치를 기준으로 확인한다.`;
  }
  if (/flow propagated to/i.test(value) || /directly exposed/i.test(value)) {
    return `${koCode(themeKey)} 흐름이 ${koCode(symbol)}에 ${koCode(impactDirection)} 방향으로 전파됐다. 이 문장은 화면용 요약이며, 원문 AI 근거는 상세 버튼에서 확인한다.`;
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
    "이 화면은 읽기 전용이다. 추천 점수, 포지션, 주문을 변경하지 않는다.",
    "민감한 저장소 주소, DB 연결 정보, API 키는 화면에 노출하지 않는다.",
    "화면을 열 때 AI를 새로 호출하지 않고 배치가 저장한 근거만 보여준다.",
  ];
}

function PriceChart({ bars, currencyCode }: { bars: StockPrice[]; currencyCode: string }) {
  const plotted = bars.filter((bar) => typeof bar.adjusted_close === "number" && bar.adjusted_close !== null);
  if (plotted.length < 2) {
    return <div className="empty-state">차트를 그릴 만큼 가격 데이터가 아직 충분하지 않다.</div>;
  }

  const closes = plotted.map((bar) => bar.adjusted_close as number);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const points = plotted
    .map((bar, index) => {
      const x = 40 + (index / Math.max(plotted.length - 1, 1)) * 780;
      const y = 186 - (((bar.adjusted_close as number) - min) / range) * 142;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const first = plotted[0];
  const last = plotted[plotted.length - 1];

  return (
    <figure className="price-chart" aria-label="종가 차트">
      <svg viewBox="0 0 860 240" role="img" aria-labelledby="price-chart-title">
        <title id="price-chart-title">수집된 조정 종가 흐름</title>
        <line x1="40" x2="820" y1="44" y2="44" />
        <line x1="40" x2="820" y1="115" y2="115" />
        <line x1="40" x2="820" y1="186" y2="186" />
        <polyline points={points} />
        <circle cx="40" cy={186 - (((first.adjusted_close as number) - min) / range) * 142} r="4" />
        <circle cx="820" cy={186 - (((last.adjusted_close as number) - min) / range) * 142} r="5" />
        <text x="40" y="222">{first.trade_date}</text>
        <text x="820" y="222" textAnchor="end">{last.trade_date}</text>
        <text x="40" y="30">{formatCurrency(max, currencyCode)}</text>
        <text x="820" y="205" textAnchor="end">{formatCurrency(min, currencyCode)}</text>
      </svg>
      <figcaption>
        최근 {plotted.length.toLocaleString("ko-KR")}개 거래일 조정 종가 기준. 투자 판단용 확정 신호가 아니라
        수집된 가격 데이터의 상태를 보여준다.
      </figcaption>
    </figure>
  );
}

function EvidenceNeighborhoodPanel({ neighborhood }: { neighborhood: AiEvidenceNeighborhoodData }) {
  const firstTheme = neighborhood.themes[0];
  const firstArtifact = neighborhood.ai_artifacts[0];
  const firstThesis = neighborhood.theses[0];
  const firstRecommendation = neighborhood.recommendations[0];
  const storyGroups = neighborhood.story_groups ?? [];

  return (
    <section className="bento-grid reveal delay-4" aria-label="이 종목이 뉴스와 엮인 이유">
      <article className="bento-card span-4" style={{ background: "var(--bg-card-hover)", borderColor: "var(--border-focus)" }}>
        <div className="section-heading">
          <div>
            <span className="metric-sub">뉴스와 종목 연결 이유</span>
            <h2>이 종목이 어떤 뉴스·테마 때문에 움직일 수 있는지 본다</h2>
          </div>
          <span className="bento-badge" style={{ margin: 0 }}>
            저장된 근거만 읽음 · 실시간 AI 호출 없음
          </span>
        </div>

        <div className="status-rail compact-rail" aria-label="뉴스와 종목 연결 요약">
          <div className="rail-cell">
            <span>이벤트</span>
            <strong>{neighborhood.summary.event_count}</strong>
            <small>종목에 연결된 뉴스/공시</small>
          </div>
          <div className="rail-cell">
            <span>뉴스 묶음</span>
            <strong>{neighborhood.summary.story_group_count ?? storyGroups.length}</strong>
            <small>같은 이야기 후보</small>
          </div>
          <div className="rail-cell">
            <span>AI 근거</span>
            <strong>{neighborhood.summary.ai_artifact_count}</strong>
            <small>저장된 구조화 증거</small>
          </div>
          <div className="rail-cell">
            <span>원문 근거</span>
            <strong>{neighborhood.summary.evidence_chunk_count}</strong>
            <small>뉴스·공시 원문 연결</small>
          </div>
          <div className="rail-cell">
            <span>투자 연결</span>
            <strong>{neighborhood.summary.thesis_count + neighborhood.summary.recommendation_count}</strong>
            <small>논리/추천 연결 수</small>
          </div>
        </div>

        <div className="trace-chain" aria-label={`${neighborhood.symbol} 뉴스 근거 관계 흐름`}>
          <div className="trace-node">
            <span>발생</span>
            <strong>이벤트 {neighborhood.summary.event_count}개</strong>
            <p>
              {neighborhood.events[0]
                ? koLabel(neighborhood.events[0].title)
                : "아직 이 종목에 연결된 이벤트가 없다."}
            </p>
            <div className="mini-link-stack">
              <Link href={`/events?symbol=${encodeURIComponent(neighborhood.symbol)}` as Route}>수집 뉴스 보기</Link>
            </div>
          </div>

          <div className="trace-arrow" aria-hidden="true">→</div>

          <div className="trace-node">
            <span>테마</span>
            <strong>{firstTheme ? koCode(firstTheme.theme_key) : "테마 없음"}</strong>
            <p>
              {firstTheme
                ? `멤버십 ${koCode(firstTheme.membership_type)} · 신뢰도 ${formatPercent(firstTheme.confidence)}`
                : "테마 연결이 쌓이면 이 위치에 표시된다."}
            </p>
          </div>

          <div className="trace-arrow" aria-hidden="true">→</div>

          <div className="trace-node">
            <span>AI 근거</span>
            <strong>{firstArtifact ? koCode(firstArtifact.evidence_type) : "AI 근거 없음"}</strong>
            <p>
              {firstArtifact
                ? `${koCode(firstArtifact.provider)} · 신뢰도 ${formatPercent(firstArtifact.confidence)} · 비용 ${formatCost(firstArtifact.estimated_cost_usd)}`
                : "아직 저장된 AI 구조화 증거가 없다."}
            </p>
            <div className="mini-link-stack">
              {firstArtifact ? <Link href={evidenceHref(firstArtifact.evidence_id) as Route}>AI 근거 열기</Link> : <span>근거 대기</span>}
            </div>
          </div>

          <div className="trace-arrow" aria-hidden="true">→</div>

          <div className="trace-node trace-node-final">
            <span>판단</span>
            <strong>{firstRecommendation ? koCode(firstRecommendation.action) : firstThesis ? "투자 논리만 있음" : "판단 대기"}</strong>
            <p>
              {firstRecommendation
                ? `점수 ${formatPercent(firstRecommendation.total_score)} · 목표 비중 ${formatPercent(firstRecommendation.recommended_weight)}`
                : firstThesis
                  ? `${koLabel(firstThesis.title)} · 확신 ${formatPercent(firstThesis.conviction_score)}`
                  : "추천이나 보유 판단으로 연결되기 전 단계다."}
            </p>
            <div className="mini-link-stack">
              {firstRecommendation ? <Link href={recommendationHref(firstRecommendation.recommendation_id)}>추천 검토서</Link> : null}
              {firstThesis ? <Link href={thesisHref(firstThesis.thesis_id)}>투자 논리</Link> : null}
            </div>
          </div>
        </div>

        <div className="relationship-panel" aria-label={`${neighborhood.symbol} 뉴스 이야기 묶음`}>
          <span>같은 이야기로 묶인 뉴스와 이유</span>
          <div className="relationship-list">
            {storyGroups.slice(0, 4).map((group) => {
              const firstSource = sourceDocumentHref(group.source_document_ids[0] ?? null);
              return (
                <div className="relationship-chip" key={group.story_id}>
                  <span>{formatStoryBasis(group.basis)}</span>
                  <NewsTitleBlock
                    compact
                    title={group.title}
                    koreanTitle={group.korean_title}
                    koreanSummary={group.korean_summary}
                    translationConfidence={group.translation_confidence}
                    themeKey={group.theme_keys[0]}
                  />
                  <small>
                    이벤트 {group.event_count.toLocaleString("ko-KR")}개 · 원천 {group.source_document_count.toLocaleString("ko-KR")}개 ·
                    원문 근거 {group.linked_chunk_count.toLocaleString("ko-KR")}개 · 규칙 기반 신뢰도 {formatPercent(group.confidence)}
                  </small>
                  {group.relation_reasons.slice(0, 3).map((reason) => (
                    <small key={`${group.story_id}-${reason}`}>묶인 이유: {koLabel(reason)}</small>
                  ))}
                  {group.events.slice(0, 2).map((event) => (
                    <div className="nested-news-title" key={`${group.story_id}-${event.event_id}`}>
                      <small>대표 이벤트: {formatDate(event.event_at)} · {koCode(event.impact_direction)}</small>
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
                </div>
              );
            })}
            {storyGroups.length === 0 ? (
              <p className="relationship-empty">아직 같은 이야기로 묶을 수 있는 뉴스 근거가 없다.</p>
            ) : null}
          </div>
        </div>

        <div className="relationship-panel" aria-label={`${neighborhood.symbol} 저장된 원문 근거`}>
          <span>원문 근거 상태</span>
          <div className="relationship-list">
            {neighborhood.evidence_chunks.slice(0, 4).map((chunk) => {
              const document = sourceDocumentHref(chunk.source_document_id);
              const sourceKind =
                chunk.source_text_kind === "raw_html_text"
                  ? "원문 본문 추출"
                  : chunk.used_metadata_fallback
                    ? "본문 부족, 문서 정보 대체"
                    : "추출 상태 미확인";
              return (
                <div className="relationship-chip" key={chunk.chunk_id}>
                  <span>{chunk.used_metadata_fallback ? "요약 정보" : "원문 근거"}</span>
                  <strong>{evidenceChunkPreview(chunk.text_preview)}</strong>
                  <small>
                    {chunk.source_url_host || "출처 없음"} · {sourceKind} · 원문 확인 상태 {koCode(chunk.embedding_status)}
                  </small>
                  {document ? <Link href={document}>원천 문서 열기</Link> : null}
                </div>
              );
            })}
            {neighborhood.evidence_chunks.length === 0 ? (
              <p className="relationship-empty">아직 이 종목에 연결된 원문 근거가 없다.</p>
            ) : null}
          </div>
        </div>

        <ul style={{ margin: "18px 0 0", paddingLeft: "20px", color: "var(--text-secondary)", lineHeight: 1.6 }}>
          {stockGuardrails().map((guardrail) => (
            <li key={guardrail}>{koLabel(guardrail)}</li>
          ))}
        </ul>
      </article>
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
  const hasTargetRange = valuationTargetRange.status === "available";
  const valuationItems = equityResearch ? valuationSensitivityItems(equityResearch.valuation_sensitivity) : [];
  const hasEvidenceOnlyData =
    !hasPriceData && (data.macro_flow_impacts.length > 0 || data.recent_events.length > 0);
  const linkedThesisId = data.recommendation?.linked_thesis_id ?? neighborhood.theses[0]?.thesis_id ?? null;
  const professionalResearchSteps: ResearchFlowStep[] = [
    {
      id: "business",
      label: "01",
      title: "사업 개요",
      status: equityResearch ? "리서치 생성" : "리서치 대기",
      tone: equityResearch ? "ready" : "watch",
      body: equityResearch?.korean_summary
        ? equityResearch.korean_summary
        : "이 종목의 사업 설명 artifact가 아직 없다. 현재 화면에서는 가격, 뉴스, 상위 흐름까지만 신뢰할 수 있다.",
      facts: [
        { label: "종목", value: `${data.symbol} · ${data.name}` },
        { label: "시장", value: `${data.market_code} · ${data.currency_code}` },
      ],
    },
    {
      id: "financial-quality",
      label: "02",
      title: "재무 품질",
      status:
        financialStatementModel.status === "available" || financialStatementModel.status === "partial"
          ? `${financialStatementModel.computed_metric_count}개 지표`
          : "재무 모델 대기",
      tone:
        financialStatementModel.status === "available" || financialStatementModel.status === "partial"
          ? "ready"
          : "watch",
      body:
        financialStatementModel.status === "available" || financialStatementModel.status === "partial" || financialStatementModel.source_data_blocker
          ? financialStatementModel.summary
          : "매출, 마진, 현금흐름, 부채, 이익 품질을 확인할 정규화 재무 모델이 아직 충분하지 않다.",
      facts: [
        { label: "최근 기간", value: financialStatementModel.latest_period_end || "없음" },
        { label: "계산 지표", value: `${financialStatementModel.computed_metric_count}개` },
        { label: "데이터 공백", value: `${financialStatementModel.data_gap_count}개` },
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
        ? "현재가 대비 목표가 하단·기준·상단과 안전마진을 먼저 본다. 이 값은 추천 점수를 바로 바꾸지 않고 가격 검토 근거로만 쓴다."
        : valuationItems.length
          ? "DCF-lite, 상대 배수, 시나리오 범위가 추천 점수를 바로 바꾸지는 않지만, 비싸게 사는지 여부를 검토하는 핵심 입력이다."
        : "아직 target range, margin of safety, scenario sensitivity가 충분히 저장되지 않았다.",
      facts:
        hasTargetRange
          ? [
              { label: "기준 목표가", value: formatCurrency(valuationTargetRange.target_base, valuationTargetRange.currency_code) },
              { label: "기준 상승여지", value: formatPercent(valuationTargetRange.upside_base) },
              { label: "산출 방법", value: `${valuationTargetRange.method_count}개` },
            ]
          : valuationItems.length > 0
          ? valuationItems.slice(0, 3).map((item) => ({ label: koCode(item.key), value: koLabel(item.value) }))
          : [{ label: "상태", value: "밸류에이션 artifact 대기" }],
    },
    {
      id: "news-cycle",
      label: "05",
      title: "뉴스·사이클 영향",
      status: `${data.recent_events.length + data.macro_flow_impacts.length}개 연결`,
      tone: data.recent_events.length + data.macro_flow_impacts.length > 0 ? "ready" : "neutral",
      body:
        data.recent_events.length + data.macro_flow_impacts.length > 0
          ? "직접 종목 뉴스와 거시·테마 흐름 전파를 분리해서 본다. 상위 흐름은 회사명이 없어도 노출도 규칙으로 종목 영향이 계산된다."
          : "아직 이 종목에 연결된 직접 뉴스나 상위 흐름 전파가 없다.",
      facts: [
        { label: "직접 뉴스", value: `${data.recent_events.length}개` },
        { label: "상위 흐름", value: `${data.macro_flow_impacts.length}개` },
      ],
      href: "/intelligence" as Route,
      hrefLabel: "뉴스 AI 흐름 보기",
    },
    {
      id: "thesis",
      label: "06",
      title: "Thesis 생애주기",
      status: linkedThesisId ? "투자 논리 연결" : "투자 논리 없음",
      tone: linkedThesisId ? "ready" : "blocked",
      body: linkedThesisId
        ? "왜 사는지, 무엇이 맞아야 하는지, 무엇이 틀리면 나가는지를 thesis 화면에서 확인한다."
        : "중장기 투자 시스템에서는 thesis 없이 추천이나 보유 판단을 신뢰하면 안 된다.",
      href: linkedThesisId ? thesisHref(linkedThesisId) : undefined,
      hrefLabel: linkedThesisId ? "투자 논리 열기" : undefined,
    },
    {
      id: "paper-validation",
      label: "07",
      title: "페이퍼 검증·거래 경계",
      status: data.position ? "보유 상태 있음" : data.recommendation ? "추천 검토 중" : "거래 입력 전",
      tone: "neutral",
      body: "이 화면은 주문을 만들지 않는다. 실제 broker submit은 닫혀 있고, 추천이 생겨도 페이퍼 검증과 리스크 경계를 먼저 확인해야 한다.",
      href: "/paper-trading" as Route,
      hrefLabel: "페이퍼 거래 상태 보기",
    },
  ];

  return (
    <div className="pageStack">
      <section className="page-hero reveal" aria-labelledby="stock-detail-title">
        <div className="bento-badge">
          종목 상세 • {data.market_code} • {data.as_of_date}
        </div>
        <h1 id="stock-detail-title">
          {hasEvidenceOnlyData ? `${data.symbol} 시장 흐름과 수집 상태` : `${data.symbol} 데이터와 판단 근거`}
        </h1>
        <p>
          가격 차트, 추천 상태, 보유 상태, 직접 뉴스, 상위 흐름 전파를 함께 확인한다.
          주문 판단보다 먼저 근거가 충분한지 확인하는 화면이다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="종목 요약">
        <div className="rail-cell">
          <span>최신 종가</span>
          <strong>{hasPriceData ? formatCurrency(data.latest_price.close, data.currency_code) : "가격 미수집"}</strong>
          <small>{data.latest_price.trade_date || "가격일 없음"}</small>
        </div>
        <div className="rail-cell">
          <span>수집 기간 수익률</span>
          <strong>{formatPercent(data.summary.return_pct)}</strong>
          <small>{data.summary.first_trade_date || "시작일 없음"}부터</small>
        </div>
        <div className="rail-cell">
          <span>추천 상태</span>
          <strong>{data.recommendation ? koCode(data.recommendation.action) : "추천 없음"}</strong>
          <small>{data.recommendation?.as_of_date || "추천 생성 전"}</small>
        </div>
        <div className="rail-cell">
          <span>보유 비중</span>
          <strong>{data.position ? formatPercent(data.position.weight) : "미보유"}</strong>
          <small>{data.position?.snapshot_date || "스냅샷 없음"}</small>
        </div>
      </section>

      <ProfessionalResearchFlow
        eyebrow="전문 리서치 읽는 순서"
        title={`${data.symbol} 분석은 종목 하나로 끝나지 않는다`}
        summary="중장기 투자 판단은 뉴스 하나로 끝나지 않는다. 사업, 재무, 비교군, 밸류에이션, 사이클, thesis, 페이퍼 검증을 같은 순서로 확인한다."
        footer="현재 화면은 저장된 데이터만 읽는다. 화면 진입 중 실시간 AI 호출이나 주문 생성은 없다."
        steps={professionalResearchSteps}
      />

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
            포함되지 않았다. 따라서 가격 차트와 수익률은 판단하지 않고, 아래 상위 흐름/원천 뉴스만 검토한다.
          </p>
        </section>
      ) : null}

      <section className="bento-grid reveal delay-2">
        <article className="bento-card span-3">
          <div className="section-heading">
            <div>
              <span className="metric-sub">수집된 가격 차트</span>
              <h2>가격 흐름</h2>
            </div>
            <Link className="btn btn-secondary" href="/data-health">
              수집 상태 보기
            </Link>
          </div>
          <PriceChart bars={data.price_bars} currencyCode={data.currency_code} />
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
        </article>
      </section>

      <section className="bento-grid reveal delay-3">
        <article className="bento-card span-2">
          <div className="section-heading">
            <div>
              <span className="metric-sub">최근 추천</span>
              <h2>투자 판단 상태</h2>
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
              <span className="metric-sub">포트폴리오</span>
              <h2>보유 상태</h2>
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

      <ValuationTargetRangeCard
        valuation={valuationTargetRange}
        eyebrow="전문 밸류에이션"
        title={`${data.symbol} 목표가 범위`}
      />

      <section className="bento-card span-4 reveal delay-3" aria-label="AI 기업 분석 리포트">
        <div className="section-heading">
          <div>
            <span className="metric-sub">AI 기업 분석 리포트</span>
            <h2>{equityResearch?.title || `${data.symbol} 기업 리서치가 아직 생성되지 않았다`}</h2>
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
                <small>thesis 재검토 기준</small>
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
                    <span>{koCode(item.key)}</span>
                    <strong>{koLabel(item.value)}</strong>
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
              이 리포트는 배치 작업이 저장한 읽기 전용 분석이다. 추천 점수와 주문은 직접 변경하지 않으며,
              추천 상세의 재무·밸류에이션 근거와 성과 평가가 별도로 확인한다.
            </p>
          </>
        ) : (
          <div className="empty-state">
            아직 이 종목의 기업 리서치 artifact가 없다. `equity-research-reporting-daily` 배치가 실행되면
            사업 설명, 핵심 재무 변화, 촉매, 리스크, 무효화 조건, 밸류에이션 민감도가 이곳에 표시된다.
          </div>
        )}
      </section>

      <IndustryCompetitivePositionPanel position={industryPosition} symbol={data.symbol} />

      <EvidenceNeighborhoodPanel neighborhood={neighborhood} />

      <section className="bento-card span-4 reveal delay-4">
        <div className="section-heading">
          <div>
            <span className="metric-sub">상위 흐름 전파</span>
            <h2>시장·테마 뉴스가 이 종목에 준 영향</h2>
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
                    {evidence ? <Link className="btn btn-secondary" href={evidence}>AI 근거</Link> : null}
                    {sourceDocument ? <Link className="btn btn-secondary" href={sourceDocument}>원천 문서</Link> : null}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">
              아직 이 종목으로 전파된 상위 흐름이 없다. 직접 뉴스만 있거나 노출도 테이블에 연결되지 않은 상태다.
            </div>
          )}
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-4">
        <div className="section-heading">
          <div>
            <span className="metric-sub">직접 뉴스</span>
            <h2>이 종목이 직접 연결된 이벤트</h2>
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
                    {evidence ? <Link className="btn btn-secondary" href={evidence}>AI 근거</Link> : null}
                    {sourceDocument ? <Link className="btn btn-secondary" href={sourceDocument}>원천 문서</Link> : null}
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
