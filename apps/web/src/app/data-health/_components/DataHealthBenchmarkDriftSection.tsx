import { koCode } from "@/lib/korean-labels";

import type { BenchmarkDriftQuality } from "./dataHealthTypes";
import {
  benchmarkDriftQualityExplanation,
  benchmarkDriftQualityTitle,
  benchmarkDriftQualityTone,
  executionIdLabel,
  formatPercent,
  operationCopy,
  orderBoundaryCopy,
} from "./dataHealthModel";

type BenchmarkDriftDecision = BenchmarkDriftQuality["outlier_decisions"][number];

type DataHealthBenchmarkDriftSectionProps = {
  readonly benchmarkDriftQuality: BenchmarkDriftQuality;
  readonly benchmarkDriftDecisionBySymbol: ReadonlyMap<string, BenchmarkDriftDecision>;
};

export function DataHealthBenchmarkDriftSection({
  benchmarkDriftQuality,
  benchmarkDriftDecisionBySymbol,
}: DataHealthBenchmarkDriftSectionProps) {
  return (
      <section
        className="feature-map-panel reveal delay-1"
        id="benchmark-drift-quality"
        aria-labelledby="benchmark-drift-quality-title"
      >
        <div className="section-heading stacked-heading">
          <span>벤치마크 괴리 품질</span>
          <h2 id="benchmark-drift-quality-title">SPY와 얼마나 다른지 보기 전 구성비 품질</h2>
        </div>
        <p className="board-intro">{benchmarkDriftQualityExplanation(benchmarkDriftQuality)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>판정</span>
            <strong className={`risk-tag ${benchmarkDriftQualityTone(benchmarkDriftQuality)}`}>
              {benchmarkDriftQualityTitle(benchmarkDriftQuality)}
            </strong>
            <small>{executionIdLabel(benchmarkDriftQuality.guardrail_eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>구성비 확인률</span>
            <strong>{formatPercent(benchmarkDriftQuality.composition_coverage_weight)}</strong>
            <small>{benchmarkDriftQuality.component_count}개 종목 구성비</small>
          </article>
          <article className="rail-cell">
            <span>구성 기준일</span>
            <strong>{benchmarkDriftQuality.source_as_of_date || "미확인"}</strong>
            <small>
              {benchmarkDriftQuality.source_age_days === null
                ? "나이 미확인"
                : `${benchmarkDriftQuality.source_age_days}일 전`}
            </small>
          </article>
          <article className="rail-cell">
            <span>전체 괴리</span>
            <strong>{formatPercent(benchmarkDriftQuality.active_share)}</strong>
            <small>{operationCopy(benchmarkDriftQuality.drift_status)}</small>
          </article>
          <article className="rail-cell">
            <span>큰 괴리 종목</span>
            <strong>{benchmarkDriftQuality.outlier_positions.length}</strong>
            <small>검토 후보 {benchmarkDriftQuality.review_candidate_count}개</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(benchmarkDriftQuality.order_boundary)}</strong>
            <small>자동 주문 {benchmarkDriftQuality.automatic_order_allowed ? "허용" : "금지"}</small>
          </article>
        </div>
        <div className="insight-grid">
          {benchmarkDriftQuality.checks.map((check) => (
            <article className="insight-card" key={check.check_key}>
              <span>{koCode(check.check_key)}</span>
              <strong>{koCode(check.status)}</strong>
              <p>{check.detail}</p>
            </article>
          ))}
        </div>
        {benchmarkDriftQuality.outlier_positions.length > 0 ? (
          <div className="feature-map-grid collection-map-grid">
            {benchmarkDriftQuality.outlier_positions.map((position) => {
              const decision = benchmarkDriftDecisionBySymbol.get(position.symbol);
              return (
                <article className="feature-map-card collection-map-card" key={position.symbol}>
                  <span>{position.symbol}</span>
                  <strong>{decision?.decision_label ?? `벤치마크 대비 ${formatPercent(position.active_weight)} 차이`}</strong>
                  <small>포트폴리오 비중 {formatPercent(position.portfolio_weight)}</small>
                  <small>벤치마크 비중 {formatPercent(position.benchmark_weight)}</small>
                  <small>괴리 {formatPercent(position.active_weight)}</small>
                  {decision?.next_review_action ? <p>{decision.next_review_action}</p> : null}
                  {decision?.related_recommendation_id ? (
                    <small>연결 추천 {decision.related_recommendation_id}</small>
                  ) : null}
                </article>
              );
            })}
          </div>
        ) : null}
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>
            {benchmarkDriftQuality.next_actions[0]
              ? operationCopy(benchmarkDriftQuality.next_actions[0])
              : "현재 추가 조치 없음"}
          </p>
        </div>
      </section>
  );
}
