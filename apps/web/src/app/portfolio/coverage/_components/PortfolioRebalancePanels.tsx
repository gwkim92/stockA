import type { Route } from "next";
import Link from "next/link";

import type { PortfolioCoverageData } from "@/lib/types";

import {
  candidateDirectionLabel,
  candidateSeverityClass,
  formatCoveragePercent,
  formatScore,
  orderBoundaryLabel,
  orderSubmitLabel,
  sizingBandClass,
  userFacingText,
} from "./portfolioCoverageFormat";

type PortfolioRebalancePanelsProps = {
  readonly benchmarkCode: string;
  readonly benchmarkSource: string;
  readonly candidateReview: PortfolioCoverageData["risk_budget"]["rebalance_candidate_review"];
  readonly positionSizingReview: PortfolioCoverageData["risk_budget"]["position_sizing_review"];
};

export function PortfolioRebalancePanels({
  benchmarkCode,
  benchmarkSource,
  candidateReview,
  positionSizingReview,
}: PortfolioRebalancePanelsProps) {
  const candidateDecisionCounts = candidateReview.decision_counts ?? {};

  return (
    <>
      <article
        id="portfolio-rebalance-review"
        className="bento-card span-4"
        style={{ borderColor: candidateReview.candidate_count > 0 ? "var(--accent-red)" : "var(--border-light)" }}
      >
        <div className="section-heading">
          <div>
            <span className="metric-sub">벤치마크 대비 리밸런싱 확인</span>
            <h2>SPY와 비교해 비중 차이가 큰 종목</h2>
          </div>
          <span className={`risk-tag ${candidateReview.candidate_count > 0 ? "risk-high" : "risk-low"}`}>
            {candidateReview.candidate_count > 0 ? "검토 후보 있음" : "큰 괴리 없음"}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          이 표는 주문 지시가 아닙니다. {candidateReview.benchmark_code || benchmarkCode} 기준 벤치마크 대비 괴리가 큰 종목을
          투자 논리, 세금/비용, 섹터 집중도와 함께 확인하기 위한 읽기 전용 목록입니다.
        </p>
        <div className="status-rail compact-rail" aria-label="벤치마크 리밸런싱 확인 요약" style={{ marginBottom: "20px" }}>
          <article className="rail-cell">
            <span>전체 괴리</span>
            <strong>{formatCoveragePercent(candidateReview.active_share)}</strong>
            <small>{userFacingText(candidateReview.benchmark_source || benchmarkSource || "근거 없음")}</small>
          </article>
          <article className="rail-cell">
            <span>구성비 확인률</span>
            <strong>{formatCoveragePercent(candidateReview.composition_coverage_weight)}</strong>
            <small>{candidateReview.source_as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>검토 후보</span>
            <strong>{candidateReview.candidate_count}</strong>
            <small>
              축소 {candidateDecisionCounts.reduce_watch ?? 0} · 미보유 확인{" "}
              {candidateDecisionCounts.needs_thesis_update ?? 0}
            </small>
          </article>
          <article className="rail-cell">
            <span>실거래 상태</span>
            <strong>{orderBoundaryLabel(candidateReview.order_boundary)}</strong>
            <small>{orderSubmitLabel(candidateReview.broker_submit_allowed)}</small>
          </article>
        </div>
        {candidateReview.candidates.length === 0 ? (
          <p className="empty-state" style={{ margin: 0 }}>
            현재 기준에서 별도 리밸런싱 검토 후보가 없습니다.
          </p>
        ) : (
          <div className="portfolio-review-card-grid" aria-label="벤치마크 리밸런싱 확인 후보">
            {candidateReview.candidates.map((candidate) => (
              <article className="portfolio-review-card" key={`${candidate.priority}-${candidate.symbol}-${candidate.direction}`}>
                <div className="portfolio-review-card-head">
                  <span>우선순위 {candidate.priority.toString().padStart(2, "0")}</span>
                  <strong>{candidate.symbol}</strong>
                  <b className={`risk-tag ${candidateSeverityClass(candidate.severity)}`}>
                    {userFacingText(candidate.decision_label)}
                  </b>
                </div>
                <p>
                  {candidateDirectionLabel(candidate.direction)} · {userFacingText(candidate.next_review_action)}
                </p>
                <dl className="portfolio-review-metrics">
                  <div>
                    <dt>현재 비중</dt>
                    <dd>{formatCoveragePercent(candidate.current_weight)}</dd>
                  </div>
                  <div>
                    <dt>벤치마크</dt>
                    <dd>{formatCoveragePercent(candidate.benchmark_weight)}</dd>
                  </div>
                  <div>
                    <dt>괴리</dt>
                    <dd>{formatCoveragePercent(candidate.active_weight)}</dd>
                  </div>
                </dl>
                <div className="portfolio-review-evidence">
                  <div>
                    <span>연결 근거</span>
                    {candidate.related_recommendation_id && candidate.links.recommendation ? (
                      <Link href={candidate.links.recommendation as Route}>{candidate.related_recommendation_id}</Link>
                    ) : (
                      <strong>추천 연결 없음</strong>
                    )}
                    <small>
                      {candidate.related_thesis_id ? `투자 논리 ${candidate.related_thesis_id}` : "투자 논리 필요"}
                    </small>
                  </div>
                  <div>
                    <span>왜 보는가</span>
                    <strong>{userFacingText(candidate.rationale)}</strong>
                    <small>{orderBoundaryLabel(candidate.order_boundary)} · {orderSubmitLabel(candidate.broker_submit_allowed)}</small>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </article>

      <article
        className="bento-card span-4"
        style={{ borderColor: positionSizingReview.review_required_count > 0 ? "var(--accent-amber)" : "var(--border-light)" }}
      >
        <div className="section-heading">
          <div>
            <span className="metric-sub">포지션 크기 상태</span>
            <h2>포지션 확대·유지·축소 판단</h2>
          </div>
          <span className={`risk-tag ${positionSizingReview.review_required_count > 0 ? "risk-medium" : "risk-low"}`}>
            {userFacingText(positionSizingReview.status)}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          현재 보유 비중과 투자 논리, 기업 분석, 밸류에이션, 벤치마크 괴리를 함께 표시합니다.
          이 값은 주문 목표가 아니라 증액 금지, 축소 필요성과 유지 상태를 구분하는 읽기 전용 판단입니다.
        </p>
        <div className="status-rail compact-rail" aria-label="포지션 크기 상태 요약" style={{ marginBottom: "20px" }}>
          <article className="rail-cell rail-critical">
            <span>축소 필요성</span>
            <strong>{positionSizingReview.reduce_review_count}</strong>
            <small>한도 또는 벤치마크 괴리</small>
          </article>
          <article className="rail-cell">
            <span>증거 보강 전 증액 금지</span>
            <strong>{positionSizingReview.add_blocked_until_evidence_count}</strong>
            <small>논리·재무·밸류에이션 공백</small>
          </article>
          <article className="rail-cell">
            <span>작은 비중 관찰</span>
            <strong>{positionSizingReview.watch_small_position_count}</strong>
            <small>{formatCoveragePercent(positionSizingReview.min_rebalance_target_weight)} 미만</small>
          </article>
          <article className="rail-cell">
            <span>실거래 상태</span>
            <strong>{orderBoundaryLabel(positionSizingReview.order_boundary)}</strong>
            <small>{orderSubmitLabel(positionSizingReview.broker_submit_allowed)}</small>
          </article>
        </div>
        {positionSizingReview.candidates.length === 0 ? (
          <p className="empty-state" style={{ margin: 0 }}>
            보유 포지션이 없어 포지션 크기 상태를 만들 수 없습니다.
          </p>
        ) : (
          <div className="portfolio-review-card-grid" aria-label="포지션 크기 확인 후보">
            {positionSizingReview.candidates.map((candidate) => (
              <article className="portfolio-review-card" key={`${candidate.priority}-${candidate.symbol}-${candidate.review_band}`}>
                <div className="portfolio-review-card-head">
                  <span>우선순위 {candidate.priority.toString().padStart(2, "0")}</span>
                  <strong>{candidate.symbol}</strong>
                  <b className={`risk-tag ${sizingBandClass(candidate.review_band)}`}>
                    {userFacingText(candidate.review_band)}
                  </b>
                </div>
                <p>{userFacingText(candidate.rationale)}</p>
                <dl className="portfolio-review-metrics">
                  <div>
                    <dt>현재 비중</dt>
                    <dd>{formatCoveragePercent(candidate.current_weight)}</dd>
                  </div>
                  <div>
                    <dt>벤치마크</dt>
                    <dd>{formatCoveragePercent(candidate.benchmark_weight)}</dd>
                  </div>
                  <div>
                    <dt>확대 상한</dt>
                    <dd>{formatCoveragePercent(candidate.review_ceiling_weight)}</dd>
                  </div>
                </dl>
                <div className="portfolio-review-evidence">
                  <div>
                    <span>기업 근거</span>
                    <strong>
                      재무 {formatScore(candidate.fundamental_quality_score)} · 밸류 {formatScore(candidate.valuation_margin_score)}
                    </strong>
                    <small>
                      안전마진 {formatCoveragePercent(candidate.valuation_margin_of_safety)} · 기업 리서치{" "}
                      {candidate.equity_research_artifact_id ? "있음" : "없음"}
                    </small>
                  </div>
                  <div>
                    <span>판단 조건</span>
                    <strong>{userFacingText(candidate.professional_analysis_status)}</strong>
                    <small>
                      막는 이유: {candidate.blocking_factors.map((factor) => userFacingText(factor)).join(", ") || "없음"}
                    </small>
                    <small>
                      받치는 근거: {candidate.supporting_factors.map((factor) => userFacingText(factor)).join(", ") || "없음"}
                    </small>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </article>
    </>
  );
}
