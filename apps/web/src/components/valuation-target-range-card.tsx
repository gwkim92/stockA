import type { ValuationTargetRange } from "@/lib/types";

type ValuationTargetRangeCardProps = {
  valuation: ValuationTargetRange;
  eyebrow?: string;
  title?: string;
  className?: string;
};

function formatCurrency(value: number | null, currencyCode: string) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode || "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number | null | undefined, signed = false) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  const text = `${Math.round(value * 1000) / 10}%`;
  return signed && value > 0 ? `+${text}` : text;
}

function assumptionText(value: Record<string, unknown>) {
  const description = value.method_description ?? value.pricing_basis ?? value.scenario_basis;
  return typeof description === "string" && description.trim() ? description : "가정 설명 없음";
}

export function ValuationTargetRangeCard({
  valuation,
  eyebrow = "밸류에이션",
  title = "목표가 범위와 안전마진",
  className = "bento-card span-4 reveal delay-3",
}: ValuationTargetRangeCardProps) {
  const available = valuation.status === "available";
  const currency = valuation.currency_code || "USD";

  return (
    <section className={className} aria-label="밸류에이션 목표가 범위">
      <div className="section-heading">
        <div>
          <span className="metric-sub">{eyebrow}</span>
          <h2>{title}</h2>
        </div>
        <span className={`risk-tag ${available ? "risk-low" : "risk-medium"}`}>
          {available ? `${valuation.method_count}개 방법` : "산출 대기"}
        </span>
      </div>

      <p style={{ color: "var(--text-secondary)", marginTop: 0, maxWidth: "860px" }}>
        {valuation.summary}
      </p>

      <div className="status-rail compact-rail" style={{ marginTop: "18px" }}>
        <div className="rail-cell">
          <span>현재가 기준</span>
          <strong>{formatCurrency(valuation.base_price, currency)}</strong>
          <small>{valuation.valuation_as_of_date || valuation.as_of_date || "기준일 없음"}</small>
        </div>
        <div className="rail-cell">
          <span>기준 목표가</span>
          <strong>{formatCurrency(valuation.target_base, currency)}</strong>
          <small>하단 {formatCurrency(valuation.target_low, currency)}</small>
        </div>
        <div className="rail-cell">
          <span>기준 상승여지</span>
          <strong>{formatPercent(valuation.upside_base, true)}</strong>
          <small>상단 {formatPercent(valuation.upside_high, true)}</small>
        </div>
        <div className="rail-cell">
          <span>안전마진</span>
          <strong>{formatPercent(valuation.margin_of_safety, true)}</strong>
          <small>신뢰도 {formatPercent(valuation.confidence)}</small>
        </div>
      </div>

      {available ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "14px", marginTop: "18px" }}>
          {valuation.methods.map((method) => (
            <article className="detail-path-card" key={`${method.method}-${method.as_of_date}`}>
              <span>{method.method_label}</span>
              <strong style={{ display: "block", fontSize: "1rem", marginTop: "4px" }}>
                {formatCurrency(method.fair_value_base, currency)}
              </strong>
              <div className="stock-meta-grid" style={{ marginTop: "12px" }}>
                <span>하단</span>
                <strong>{formatCurrency(method.fair_value_low, currency)}</strong>
                <span>상단</span>
                <strong>{formatCurrency(method.fair_value_high, currency)}</strong>
                <span>안전마진</span>
                <strong>{formatPercent(method.margin_of_safety, true)}</strong>
              </div>
              <p style={{ color: "var(--text-secondary)", lineHeight: 1.55, margin: "12px 0 0" }}>
                {assumptionText(method.assumptions)}
              </p>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state" style={{ marginTop: "18px" }}>
          목표가 범위가 없으면 좋은 뉴스와 사이클 근거가 있어도 가격 판단은 보류한다.
        </div>
      )}
    </section>
  );
}

