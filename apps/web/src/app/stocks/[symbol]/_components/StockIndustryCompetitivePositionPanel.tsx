import { Fragment } from "react";

import { koLabel } from "@/lib/korean-labels";
import type { StockDetailData } from "@/lib/types";

import { StockResearchList } from "./StockResearchList";
import { formatPercent, stockSourceLabel, stockText } from "./stock-detail-panel-format";

type IndustryCompetitivePosition = NonNullable<StockDetailData["industry_competitive_position"]>;

type StockIndustryCompetitivePositionPanelProps = {
  readonly position: IndustryCompetitivePosition | null;
  readonly symbol: string;
};

function competitivePositionLabel(value: string) {
  const labels: Record<string, string> = {
    leader: "경쟁 우위",
    advantaged: "우위 후보",
    in_line: "평균권",
    challenged: "열위 검토",
    insufficient_data: "데이터 부족",
  };
  return labels[value] ?? stockSourceLabel(value);
}

function competitivePositionSummary(position: IndustryCompetitivePosition, symbol: string) {
  const peerGroup = stockText(position.peer_group_name ?? position.peer_group_code ?? "비교군");
  const sector = stockText(position.sector_name ?? position.sector_code ?? "섹터 미분류");
  return `${symbol}은 ${peerGroup} 기준으로 ${competitivePositionLabel(position.competitive_position)} 상태다. ${sector} 안에서 수익성, 성장성, 재무 방어력, 가격 결정력 추정 지표를 함께 비교한다.`;
}

export function StockIndustryCompetitivePositionPanel({ position, symbol }: StockIndustryCompetitivePositionPanelProps) {
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
          <small>{stockSourceLabel(position.methodology)}</small>
        </div>
        <div className="rail-cell">
          <span>비교군</span>
          <strong>{stockText(position.peer_group_name ?? position.peer_group_code ?? "분류 대기")}</strong>
          <small>{position.peer_count.toLocaleString("ko-KR")}개 종목 기준</small>
        </div>
        <div className="rail-cell">
          <span>섹터</span>
          <strong>{stockText(position.sector_name ?? position.sector_code ?? "분류 대기")}</strong>
          <small>산업/테마 분류 기준</small>
        </div>
        <div className="rail-cell">
          <span>지표 커버리지</span>
          <strong>{position.metric_coverage_count.toLocaleString("ko-KR")}</strong>
          <small>{position.source_run_id ? "계산 이력 있음" : "계산 이력 없음"}</small>
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
        <StockResearchList title="강점" items={position.key_strengths} emptyText="강점이 아직 구조화되지 않았다." />
        <StockResearchList title="주의할 점" items={position.key_risks} emptyText="경쟁 리스크가 아직 구조화되지 않았다." />
      </div>

      {position.rationale ? (
        <p style={{ color: "var(--text-muted)", marginBottom: 0 }}>
          계산 근거: {koLabel(position.rationale)}
        </p>
      ) : null}
    </section>
  );
}
