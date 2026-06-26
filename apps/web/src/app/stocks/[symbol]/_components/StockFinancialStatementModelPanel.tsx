import { Fragment } from "react";

import type { StockDetailData } from "@/lib/types";

import {
  financialMetricTone,
  formatFinancialMetricValue,
  formatPercent,
  stockSourceLabel,
  stockText,
} from "./stock-detail-panel-format";

type FinancialStatementModel = StockDetailData["financial_statement_model"];

type StockFinancialStatementModelPanelProps = {
  readonly model: FinancialStatementModel;
  readonly symbol: string;
};

export function StockFinancialStatementModelPanel({ model, symbol }: StockFinancialStatementModelPanelProps) {
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
            ? stockText(model.summary)
            : "SEC 공시 재무 데이터 수집과 재무 정규화가 완료되면 매출 성장, 마진, 현금흐름, 부채, 이익 품질이 이곳에 표시된다. 이 데이터가 없으면 뉴스나 사이클만으로 장기 투자 판단을 확정하지 않는다."}
        </p>
        {sourceBlocker ? (
          <div className="status-rail compact-rail" aria-label="재무 원천 차단 사유" style={{ marginTop: "18px" }}>
            <div className="rail-cell">
              <span>부족한 근거</span>
              <strong>{stockText(sourceBlocker.label)}</strong>
              <small>{stockSourceLabel(sourceBlocker.blocker_code)}</small>
            </div>
            <div className="rail-cell">
              <span>원천 분류</span>
              <strong>{stockSourceLabel(sourceBlocker.source_pipeline)}</strong>
              <small>{sourceBlocker.source_run_id ? "수집 이력 있음" : "정적 분류"}</small>
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
        {stockText(model.summary)} 이 섹션은 기존 정규화 재무 지표를 읽는 화면이며, 추천 점수와 주문 가능 여부를 바꾸지 않는다.
      </p>

      <div className="status-rail compact-rail" aria-label="재무 모델 요약">
        <div className="rail-cell">
          <span>최근 재무 기간</span>
          <strong>{model.latest_period_end || "기간 없음"}</strong>
          <small>{model.statement_scope === "annual" ? "연간 기준" : stockSourceLabel(model.statement_scope)}</small>
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
            <span className="metric-sub">{stockText(section.title)}</span>
            <h3 style={{ margin: "6px 0 8px" }}>{stockText(section.description)}</h3>
            <div className="stock-meta-grid">
              {section.metrics.length > 0 ? (
                section.metrics.map((metric) => (
                  <Fragment key={metric.metric_code}>
                    <span>
                      {stockText(metric.label)}
                      <small style={{ display: "block", color: "var(--text-muted)" }}>{metric.period_end || "기간 없음"}</small>
                    </span>
                    <strong className={`risk-tag ${financialMetricTone(metric)}`}>{formatFinancialMetricValue(metric)}</strong>
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
