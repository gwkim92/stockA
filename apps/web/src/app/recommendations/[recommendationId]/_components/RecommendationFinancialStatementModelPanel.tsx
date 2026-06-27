import type { RecommendationDetailData } from "@/lib/types";

import {
  formatPanelCompactNumber,
  formatPanelOptionalPercent,
  formatPanelPercent,
  userFacingRecommendationText,
} from "./recommendation-panel-format";

type FinancialStatementModel = RecommendationDetailData["financial_statement_model"];
type FinancialMetricSnapshot = FinancialStatementModel["metrics"][number];

type RecommendationFinancialStatementModelPanelProps = {
  readonly model: FinancialStatementModel;
  readonly symbol: string;
};

function formatFinancialMetricValue(metric: FinancialMetricSnapshot) {
  if (metric.metric_value === null) {
    if (metric.metric_status === "insufficient_history") {
      return "비교 기간 부족";
    }
    return "원천 데이터 부족";
  }
  if (metric.metric_unit === "ratio") {
    return formatPanelPercent(metric.metric_value);
  }
  return formatPanelCompactNumber(metric.metric_value);
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

export function RecommendationFinancialStatementModelPanel({
  model,
  symbol,
}: RecommendationFinancialStatementModelPanelProps) {
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
              <small>투자 판단에 쓸 수 있는 표준 재무 원천이 들어오면 다시 연결된다.</small>
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
          <small>{model.statement_scope === "annual" ? "연간 기준" : userFacingRecommendationText(model.statement_scope)}</small>
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
          <strong>{formatPanelOptionalPercent(model.share_count.share_count_change_pct)}</strong>
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
