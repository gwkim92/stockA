import { PortfolioReturnSummaryPanel } from "@/components/portfolio/PortfolioReturnSummaryPanel";
import { PageDecisionMap } from "@/components/research/PageDecisionMap";
import { getPortfolioCoverage, getTradingReadiness } from "@/lib/frontend-api";
import { buildPortfolioCoverageViewModel, calculatePortfolioReturnSummary, formatSignedPercent } from "@/lib/presentation";

import { PortfolioCoverageDeepPanels } from "./_components/PortfolioCoverageDeepPanels";
import {
  formatCoveragePercent,
  orderBoundaryLabel,
  recordNumber,
  recordString,
  riskBudgetLabel,
  userFacingText,
} from "./_components/portfolioCoverageFormat";

export const dynamic = "force-dynamic";
export const metadata = { title: "보유·리스크 상태" };

export default async function PortfolioCoveragePage() {
  const [response, tradingResponse] = await Promise.all([getPortfolioCoverage(), getTradingReadiness()]);
  const data = response.data;
  const riskGuardrail = tradingResponse.data.portfolio_risk_budget_guardrail;
  const benchmarkDrift = riskGuardrail.benchmark_drift;
  const benchmarkDriftCalculated = benchmarkDrift?.drift_calculated === true;
  const benchmarkCode = recordString(benchmarkDrift, "benchmark_code") || "벤치마크";
  const benchmarkActiveShare = recordNumber(benchmarkDrift, "active_share");
  const benchmarkSource = userFacingText(recordString(benchmarkDrift, "benchmark_source") || recordString(benchmarkDrift, "source_type"));
  const riskBudget = data.risk_budget;
  const candidateReview = riskBudget.rebalance_candidate_review;
  const positionSizingReview = riskBudget.position_sizing_review;
  const reviewCalibration = riskBudget.review_feedback_calibration;
  const concentration = riskBudget.concentration;
  const hasPositions = data.positions.length > 0;
  const portfolioReturn = calculatePortfolioReturnSummary(data.positions);
  const portfolioViewModel = buildPortfolioCoverageViewModel(data);
  const portfolioReturnLabel = formatSignedPercent(portfolioReturn.returnPct, {
    metricLabel: "평가손익률",
    upLabel: "수익",
    downLabel: "손실",
  });
  const portfolioMarketValueMetric = portfolioViewModel.metrics.find((metric) => metric.label === "평가금액");
  const portfolioPnlMetric = portfolioViewModel.metrics.find((metric) => metric.label === "평가손익");
  const investedWeight = Math.max(0, 1 - (data.summary.cash_weight ?? 0));
  const thesisCoverageRatio = investedWeight > 0
    ? Math.max(0, Math.min(1, (investedWeight - data.summary.missing_thesis_weight) / investedWeight))
    : 0;
  const thesisReady = hasPositions && data.summary.missing_thesis_count === 0;
  const outcomeCoverageRatio = data.summary.weight_coverage_ratio;
  const reviewCandidateTotal = candidateReview.candidate_count + positionSizingReview.review_required_count;
  const portfolioCommandCards = [
    {
      index: "01",
      label: "보유 상태",
      title: hasPositions ? `${data.summary.position_count}개 보유` : "보유 스냅샷 없음",
      metric: `평가손익률 ${portfolioReturnLabel.label} · 투자 논리 ${formatCoveragePercent(thesisCoverageRatio)}`,
      body: hasPositions
        ? "보유 종목별 투자 논리와 성과 측정 상태입니다. 투자 논리 공백이 있는 종목은 보유 근거가 약합니다."
        : "이 기준일에는 포지션 스냅샷이 없어 보유 상태를 만들 수 없습니다.",
      href: "#portfolio-return-summary",
      cta: "수익률 보기",
      tone: thesisReady ? "ready" : "watch",
    },
    {
      index: "02",
      label: "리스크 예산",
      title: riskBudgetLabel(riskBudget.status),
      metric: `한도 초과 ${riskBudget.over_single_position_limit_count}개 · 집중 초과 ${concentration.over_limit_count}개`,
      body: riskBudget.status === "needs_position_review" || concentration.over_limit_count > 0
        ? "단일 종목, 섹터 또는 테마 노출이 정책 한도와 충돌합니다."
        : "현재 정책 기준으로 큰 한도 초과는 없습니다.",
      href: "#portfolio-risk-budget",
      cta: "리스크 보기",
      tone: riskBudget.status === "needs_position_review" || concentration.over_limit_count > 0 ? "watch" : "ready",
    },
    {
      index: "03",
      label: "리밸런싱 검토 후보",
      title: reviewCandidateTotal > 0 ? `${reviewCandidateTotal}개 검토 후보` : "즉시 대상 없음",
      metric: `벤치마크 ${candidateReview.candidate_count}개 · 포지션 ${positionSizingReview.review_required_count}개`,
      body: reviewCandidateTotal > 0
        ? "SPY 대비 괴리 또는 포지션 크기 조정이 필요한 후보입니다."
        : "현재 기준으로 리밸런싱 검토 후보가 없습니다.",
      href: "#portfolio-rebalance-review",
      cta: "검토 후보 보기",
      tone: reviewCandidateTotal > 0 ? "watch" : "ready",
    },
    {
      index: "04",
      label: "성과 성숙 대기",
      title: reviewCalibration.weight_review_blocked ? "추천 산식 변경 금지" : "조건 확인 가능",
      metric: `성숙일 ${reviewCalibration.estimated_maturity_date || "미정"} · ${orderBoundaryLabel(reviewCalibration.guardrails.order_boundary)}`,
      body: reviewCalibration.weight_review_blocked
        ? "성과 표본이 성숙하기 전에는 추천 산식 반영 비중을 바꾸지 않는다."
        : "조건이 열려도 자동 비중 변경은 별도 승인 대상이다.",
      href: "#portfolio-outcome-boundary",
      cta: "상태 보기",
      tone: reviewCalibration.weight_review_blocked ? "block" : "watch",
    },
  ];

  return (
    <div className="pageStack decision-page">
      <PageDecisionMap
        eyebrow="화면 읽는 순서"
        title="수익률, 위험, 조정 후보만 먼저 본다"
        description="긴 표와 감사 기록을 모두 읽기 전에 포트폴리오 판단에 직접 필요한 다섯 지점으로 이동한다."
        steps={[
          {
            description: "평가손익률과 손익을 만든 포지션을 먼저 본다.",
            href: "#portfolio-return-summary",
            label: "수익률",
            status: portfolioReturnLabel.label,
            title: "평가손익",
            tone: portfolioReturn.returnPct !== null && portfolioReturn.returnPct < 0 ? "watch" : "ready",
          },
          {
            description: "단일 종목 한도, 집중도, 가상 매매 입력 차단 여부를 정리합니다.",
            href: "#portfolio-risk-budget",
            label: "위험",
            status: riskBudgetLabel(riskBudget.status),
            title: "위험 예산",
            tone: riskBudget.status === "needs_position_review" ? "watch" : "ready",
          },
          {
            description: "벤치마크와 크게 다른 종목이 투자 논리와 맞는지 비교합니다.",
            href: "#portfolio-rebalance-review",
            label: "조정 후보",
            status: reviewCandidateTotal > 0 ? `${reviewCandidateTotal}개 후보` : "후보 없음",
            title: "리밸런싱 검토",
            tone: reviewCandidateTotal > 0 ? "watch" : "ready",
          },
          {
            description: "작은 비중, 과대 비중, 보유 유지 조건을 종목별로 정리합니다.",
            href: "#portfolio-position-map",
            label: "보유",
            status: `${data.positions.length.toLocaleString("ko-KR")}개`,
            title: "보유 포지션",
            tone: data.positions.length > 0 ? "ready" : "watch",
          },
          {
            description: "성과 표본이 성숙하기 전에는 추천 산식과 주문이 바뀌지 않습니다.",
            href: "#portfolio-outcome-boundary",
            label: "경계",
            status: orderBoundaryLabel(reviewCalibration.guardrails.order_boundary),
            title: "성과·거래 경계",
            tone: "block",
          },
        ]}
      />

      <section className="decision-brief reveal" aria-labelledby="portfolio-coverage-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">
            보유·리스크 상태 · {userFacingText(data.portfolio_name)} · {userFacingText(data.strategy_name)} · {data.as_of_date}
          </span>
          <h1 className="decision-brief-title" id="portfolio-coverage-title">
            {reviewCandidateTotal > 0
              ? `${reviewCandidateTotal.toLocaleString("ko-KR")}개 보유 항목에 조정 검토가 필요합니다.`
              : `${portfolioViewModel.statusLabel} · ${portfolioReturnLabel.label}`}
          </h1>
          <p className="decision-brief-copy">
            {portfolioViewModel.investmentImpact} {portfolioViewModel.nextAction}
          </p>
          <div className="decision-brief-meta" aria-label="포트폴리오 핵심 상태">
            <span>포지션 {data.summary.position_count.toLocaleString("ko-KR")}개</span>
            <span>평가금액 {portfolioMarketValueMetric?.value ?? "미측정"}</span>
            <span>평가손익 {portfolioPnlMetric?.value ?? "미측정"}</span>
            <span>평가손익률 {portfolioReturnLabel.label}</span>
            <span>투자 논리 보강 {data.summary.missing_thesis_count.toLocaleString("ko-KR")}개</span>
            <span>측정 종료 {data.coverage_measurement_end_date}</span>
            <span>실거래 {orderBoundaryLabel(reviewCalibration.guardrails.order_boundary)}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          {portfolioCommandCards.map((card) => (
            <a
              className={`decision-card ${
                card.tone === "ready" ? "is-good" : card.tone === "watch" ? "is-watch" : "is-block"
              }`}
              href={card.href}
              key={card.index}
            >
              <span>{card.label}</span>
              <strong>{card.title}</strong>
              <small>{card.metric} · {card.body}</small>
              <b>{card.cta}</b>
            </a>
          ))}
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card">
          <span className="metric-label">포지션</span>
          <strong className="metric-value">{data.summary.position_count}</strong>
          <span className="metric-sub">
            {hasPositions
              ? `${data.summary.position_count - data.summary.missing_thesis_count}개 투자 논리 연결`
              : "해당 기준일 포지션 스냅샷 없음"}
          </span>
        </article>
        
        <article className="bento-card" style={{ borderColor: data.summary.missing_thesis_count > 0 ? "var(--accent-red)" : "var(--border-light)" }}>
          <span className="metric-label">투자 논리 보강</span>
          <strong className="metric-value" style={{ color: data.summary.missing_thesis_count > 0 ? "var(--accent-red)" : "var(--text-primary)" }}>
            {data.summary.missing_thesis_count}
          </strong>
          <span className="metric-sub">비중 {formatCoveragePercent(data.summary.missing_thesis_weight)}</span>
        </article>

        <article className="bento-card">
          <span className="metric-label">평가손익률</span>
          <strong className="metric-value">
            {portfolioReturnLabel.label}
          </strong>
          <span className="metric-sub">
            측정 포지션 {portfolioReturn.measuredPositionCount.toLocaleString("ko-KR")}개
          </span>
        </article>

        <article className="bento-card">
          <span className="metric-label">성과 측정 연결률</span>
          <strong className="metric-value">{formatCoveragePercent(outcomeCoverageRatio)}</strong>
          <span className="metric-sub">장기 성과 기준</span>
        </article>

        <article className="bento-card">
          <span className="metric-label">성과 측정 대기</span>
          <strong className="metric-value">{data.summary.missing_outcome_count}</strong>
          <span className="metric-sub">측정 종료 {data.coverage_measurement_end_date}</span>
        </article>

        <article className="bento-card">
          <span className="metric-label">현금 비중</span>
          <strong className="metric-value">{formatCoveragePercent(data.summary.cash_weight)}</strong>
          <span className="metric-sub">명시적 배분</span>
        </article>

        <PortfolioCoverageDeepPanels
          benchmarkActiveShare={benchmarkActiveShare}
          benchmarkCode={benchmarkCode}
          benchmarkDriftCalculated={benchmarkDriftCalculated}
          benchmarkSource={benchmarkSource}
          data={data}
          riskGuardrail={riskGuardrail}
        />

        <PortfolioReturnSummaryPanel positions={data.positions} baseCurrency={data.base_currency} />
      </section>
    </div>
  );
}
