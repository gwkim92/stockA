import { loadReviewReport } from "@/lib/review-workspace-data";
import { isoDate, outcome, performanceHeadline, percent, weight, words } from "@/lib/review-workspace-model";
import { ReviewFrame, ReviewMetrics } from "@/components/review/ReviewFrame";
import { OutcomeExplorer } from "@/components/review/OutcomeExplorer";
import { PerformanceEvidence } from "@/components/review/ReviewEvidence";
import styles from "@/components/review/ReviewWorkspace.module.css";
export const dynamic = "force-dynamic";
export const metadata = { title: "판단 성과" };
export default async function PerformancePage({ searchParams }: { searchParams: Promise<{ date?: string | string[] }> }) {
  const result = await loadReviewReport("performance", (await searchParams).date), report = result.report;
  const headline = report ? performanceHeadline(report) : null;
  return <ReviewFrame kind="performance" result={result}>{report && headline && <>
    <p className={styles.context}>보고서 측정 구간 {isoDate(report.raw.measurement_start_date) ?? "미확인"} ~ {isoDate(report.raw.measurement_end_date) ?? "미확인"} · 벤치마크 {words(report.raw.benchmark_code)}</p>
    <ReviewMetrics compact items={[
      { label: "측정 추천", value: headline.measured === null ? "미확인" : `${headline.measured}개`, detail: `수신된 결과 ${report.rows.length}개` },
      { label: "평균 초과수익", value: percent(headline.alpha, true), detail: "저장된 전체 보고서 기준" },
      { label: "보고된 적중률", value: weight(headline.hitRate), detail: "표본·평가 기준 함께 확인" },
      { label: "측정 제외 비중", value: weight(headline.excludedWeight), detail: "제외 사유는 아래 상세" },
    ]} note="요약은 저장된 전체 보고서 값입니다. 서로 다른 관찰 기간을 한 전략의 수익률로 해석하지 마세요." />
    <OutcomeExplorer rows={report.rows.map(outcome)} benchmark={words(report.raw.benchmark_code)} />
    <PerformanceEvidence report={report} />
  </>}</ReviewFrame>;
}
