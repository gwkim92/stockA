import type { PipelineRun } from "./dataHealthModel";
import { runQualityExplanation } from "./dataHealthModel";

type DataHealthAiFallbackWarningProps = {
  readonly run: PipelineRun | null;
};

export function DataHealthAiFallbackWarning({ run }: DataHealthAiFallbackWarningProps) {
  if (run?.health_status !== "degraded" && run?.latest_status !== "succeeded_with_fallback") {
    return null;
  }

  return (
    <section className="flow-panel reveal delay-1" aria-labelledby="ai-fallback-warning-title">
      <div className="section-heading flow-heading">
        <span>AI 분석 경고</span>
        <h2 id="ai-fallback-warning-title">뉴스 AI 분석이 대체 처리로 끝난 실행이 있다</h2>
      </div>
      <p className="page-lede" style={{ marginTop: 0, maxWidth: "980px" }}>
        {runQualityExplanation(run)} 이 상태에서는 뉴스 수집과 이벤트 구조화는 계속 진행되지만, AI가 만든
        한국어 근거와 종목·테마 영향 검증 신뢰도는 낮아질 수 있다.
      </p>
    </section>
  );
}
