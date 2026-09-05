import { loadReviewReport } from "@/lib/review-workspace-data";
import { money, percent, portfolioProjection, record, weight } from "@/lib/review-workspace-model";
import { ReviewFrame, ReviewMetrics } from "@/components/review/ReviewFrame";
import { HoldingsReview } from "@/components/review/HoldingsReview";
import { RecordedPortfolioReview } from "@/components/review/ReviewEvidence";
export const dynamic = "force-dynamic";
export const metadata = { title: "보유 검토" };
export default async function PortfolioCoveragePage({ searchParams }: { searchParams: Promise<{ date?: string | string[] }> }) {
  const result = await loadReviewReport("portfolio", (await searchParams).date), report = result.report;
  const view = report ? portfolioProjection(report) : null;
  return <ReviewFrame kind="portfolio" result={result}>{report && view && <>
    <ReviewMetrics items={[
      { label: "측정 포지션 평가액", value: money(view.valuation.marketValue, view.currency), hint: `${view.valuation.measuredPositionCount}/${view.rows.length}개 · 현금 제외`, detail: "동일한 기준통화의 원가·평가액이 확인된 포지션만 포함" },
      { label: "측정 포지션 평가손익", value: money(view.valuation.unrealizedPnl, view.currency), hint: `${view.excluded}개 제외`, detail: `${view.excluded}개 평가자료 미확인·제외` },
      { label: "평가손익률", value: percent(view.valuation.returnPct), detail: "같은 기준통화·원가 확인분" },
      { label: "성과 측정 연결률", value: weight(record(report.raw.summary).weight_coverage_ratio), detail: `보고된 현금 비중 ${weight(record(report.raw.summary).cash_weight)}` },
    ]} note="위 금액은 측정 가능한 포지션의 소계이며 전체 계좌 잔고나 전략 수익률이 아닙니다. 목록 필터와는 별개입니다." />
    <HoldingsReview rows={view.rows} />
    <RecordedPortfolioReview report={report} />
  </>}</ReviewFrame>;
}
