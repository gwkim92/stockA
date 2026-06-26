import type { DataHealthData } from "../types";

import { portfolioCopy } from "./investment-copy";
import type { InvestmentViewModel } from "./view-model";

export function buildOperationsViewModel(data: DataHealthData): InvestmentViewModel {
  const failedRuns = data.pipeline_runs.filter((run) => run.health_status === "failed" || run.latest_status === "failed").length;
  const staleFreshness = data.freshness.filter((item) => item.status !== "fresh").length;
  const liveAi = data.live_ai_invocation_health;
  const openAiProvider = data.openai_provider_health;
  const aiAttention = Boolean(liveAi?.attention_required) || (openAiProvider?.status !== undefined && openAiProvider.status !== "ready");
  const aiStatus = liveAi?.status ?? openAiProvider?.status ?? "상태 미확인";
  const aiContext = liveAi?.latest_invocation_at ?? data.as_of_date;

  return {
    title: "운영 관리 · 데이터 상태",
    summary: `수집·분석 상태 ${portfolioCopy(data.overall_status)} · 실패 ${failedRuns.toLocaleString("ko-KR")}건 · 최신성 이슈 ${staleFreshness.toLocaleString("ko-KR")}건`,
    statusLabel: failedRuns > 0 || aiAttention ? "운영 점검" : "운영 정상",
    statusTone: failedRuns > 0 || aiAttention ? "watch" : "ready",
    investmentImpact: "투자 화면의 신뢰도에 영향을 주는 수집, 분석, AI, 스케줄러 상태만 먼저 요약합니다.",
    nextAction: failedRuns > 0 ? "최근 실패 실행과 다음 자동 재시도 시각을 먼저 확인합니다." : "세부 실행 기록은 접힘 영역에서 필요할 때만 봅니다.",
    sourceLimitReason: aiAttention && liveAi ? portfolioCopy(liveAi.next_action) : "자동 수집과 분석 루프가 투자 화면에 필요한 데이터를 공급 중입니다.",
    metrics: [
      { label: "수집 상태", value: portfolioCopy(data.overall_status), context: data.as_of_date },
      { label: "실패 실행", value: failedRuns.toLocaleString("ko-KR"), context: "최근 실행 기준" },
      { label: "스케줄러", value: portfolioCopy(data.scheduler.install_status), context: `${data.scheduler.profile_scheduler?.active_timer_count ?? 0}개 활성` },
      { label: "AI 상태", value: portfolioCopy(aiStatus), context: aiContext },
    ],
  };
}
