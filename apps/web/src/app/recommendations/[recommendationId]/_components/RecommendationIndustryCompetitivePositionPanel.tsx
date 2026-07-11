import { koCode } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";

import { formatPanelOptionalPercent, formatPanelPercent, userFacingRecommendationText } from "./recommendation-panel-format";
import { RecommendationResearchList } from "./RecommendationResearchList";
import styles from "./RecommendationIndustryCompetitivePositionPanel.module.css";

type ScoreComponent = RecommendationDetailData["score_components"][number];
type IndustryCompetitivePosition = NonNullable<RecommendationDetailData["industry_competitive_position"]>;

type RecommendationIndustryCompetitivePositionPanelProps = {
  readonly position: IndustryCompetitivePosition | null;
  readonly symbol: string;
  readonly peerComponent: ScoreComponent | undefined;
};

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

export function RecommendationIndustryCompetitivePositionPanel({
  position,
  symbol,
  peerComponent,
}: RecommendationIndustryCompetitivePositionPanelProps) {
  if (!position) {
    return (
      <section className="bento-card" aria-label="산업 경쟁 위치">
        <div className={styles.emptyHead}>
          <span className="metric-sub">산업 경쟁 위치</span>
          <h2 className={styles.title}>피어 기반 경쟁 위치 연결 대기</h2>
        </div>
        <p className={styles.emptyCopy}>
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
    <section className="bento-card" aria-label="산업 경쟁 위치">
      <div className={styles.head}>
        <div>
          <span className="metric-sub">산업 경쟁 위치</span>
          <h2 className={styles.title}>{symbol}이 같은 그룹 안에서 얼마나 강한가</h2>
          <p className={styles.summary}>
            {competitivePositionSummary(position, symbol)} 이 값은 무료 공개 재무 데이터와 피어 비교로 만든 추정 지표이며,
            최종 추천 점수에는 평가 전까지 직접 반영하지 않는다.
          </p>
        </div>
        <span className={`bento-badge ${styles.badge}`}>
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
          <strong>{peerComponent ? formatPanelPercent(peerComponent.value) : "미연결"}</strong>
          <small>{peerComponent ? "현재 최종 점수 미반영" : "추천 점수 항목 대기"}</small>
        </div>
        <div className="rail-cell">
          <span>지표 커버리지</span>
          <strong>{position.metric_coverage_count.toLocaleString("ko-KR")}</strong>
          <small>{position.source_run_id ? "계산 기록 있음" : "계산 기록 없음"}</small>
        </div>
      </div>

      <div className={styles.grid}>
        <article className={`detail-path-card ${styles.scoreCard}`}>
          <span>경쟁력 점수</span>
          {scoreRows.map((row) => (
            <p key={row.label}>{row.label}: {formatPanelOptionalPercent(row.value)}</p>
          ))}
        </article>
        <article className={`detail-path-card ${styles.scoreCard}`}>
          <span>경쟁 압력 리스크</span>
          {riskRows.map((row) => (
            <p key={row.label}>{row.label}: {formatPanelOptionalPercent(row.value)}</p>
          ))}
        </article>
        <RecommendationResearchList
          title="강점"
          items={position.key_strengths}
          emptyText="강점이 아직 구조화되지 않았다."
        />
        <RecommendationResearchList
          title="주의할 점"
          items={position.key_risks}
          emptyText="경쟁 리스크가 아직 구조화되지 않았다."
        />
      </div>

      {position.rationale ? (
        <p className={styles.rationale}>
          계산 근거: {userFacingRecommendationText(position.rationale)}
        </p>
      ) : null}
    </section>
  );
}
