import type { DataHealthData, PipelineRun, SchedulerActivation } from "./dataHealthTypes";

import { koCode } from "@/lib/korean-labels";

export function findPipelineRun(data: DataHealthData, jobId: string, pipelineName: string) {
  return (
    data.pipeline_runs.find((run) => run.job_id === jobId)
    ?? data.pipeline_runs.find((run) => run.pipeline_name === pipelineName)
    ?? null
  );
}

export function runStateLabel(run: PipelineRun | null) {
  if (!run) {
    return "실행 이력 없음";
  }
  if (run.latest_status === "succeeded" && run.health_status === "ok") {
    return "최근 실행 성공";
  }
  if (run.latest_status === "succeeded_with_fallback" || run.health_status === "degraded") {
    return "성공했지만 대체 처리 사용";
  }
  if (run.latest_status === "succeeded") {
    return `성공 · ${koCode(run.health_status)}`;
  }
  return `${koCode(run.latest_status)} · ${koCode(run.health_status)}`;
}

export function automationStateLabel(schedulerActivation: SchedulerActivation) {
  if (schedulerActivation.activation_allowed) {
    return schedulerActivation.scheduler_activation === "installed" ? "반복 실행 중" : "반복 실행 설정됨";
  }
  if (schedulerActivation.status === "pending_manual_approval") {
    return "반복 실행 미설정";
  }
  return koCode(schedulerActivation.status);
}

export function cadenceLabel(run: PipelineRun | null, fallback: string) {
  if (!run) {
    return fallback;
  }
  return `${koCode(run.cadence)} · ${run.expected_after_local}`;
}

export function finishedAtLabel(run: PipelineRun | null) {
  return run?.finished_at ?? "아직 완료 기록 없음";
}

export function runQualityExplanation(run: PipelineRun | null) {
  if (!run) {
    return "실행 이력이 없어 근거 신뢰도를 판단할 수 없다.";
  }
  if (run.latest_status === "succeeded_with_fallback" || run.health_status === "degraded") {
    return "작업은 멈추지 않았지만 일부 AI 분석이 중단되어 규칙 기반 대체 처리로 완료됐다. 추천 근거 신뢰도를 낮게 보고 오류 내용 확인이 필요합니다.";
  }
  if (run.latest_status === "succeeded" && run.health_status === "ok") {
    return "최근 실행은 정상 범위다.";
  }
  return "상태와 완료 시각을 기준으로 실행 로그 확인이 필요합니다.";
}
