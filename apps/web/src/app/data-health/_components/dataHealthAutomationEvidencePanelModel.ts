import type {
  DataHealthLocalWorkerPanel,
  DataHealthManualSmokePanel,
} from "@/components/operations/DataHealthAutomationDetailTypes";
import { koCode } from "@/lib/korean-labels";

import {
  errorLogLabel,
  evidenceLocationLabel,
  localWorkerExplanation,
  localWorkerNextAction,
  localWorkerTitle,
  manualSmokeExplanation,
  manualSmokeNextAction,
  manualSmokeTitle,
  operationCopy,
  summaryLocationLabel,
} from "./dataHealthModel";
import type { LocalIngestWorker, ManualIngestSmoke } from "./dataHealthTypes";

export function buildLocalWorkerPanel(
  localWorker: LocalIngestWorker,
  ec2SchedulerInstalled: boolean,
): DataHealthLocalWorkerPanel {
  return {
    cycleRows: localWorker.cycles.map((cycle) => ({
      artifactRunCountLabel: `${cycle.artifact_run_count}개 기록`,
      jobCountLabel: `${cycle.job_count}개 · 중단 ${cycle.failed_job_count}개`,
      smokeStatusLabel: koCode(cycle.smoke_status),
      startedAtLabel: cycle.started_at || "시각 없음",
      title: String(cycle.cycle_number),
    })),
    description: ec2SchedulerInstalled
      ? "이 기록은 서버 예약 실행기를 붙이기 전 로컬 MVP 단계의 점검 결과다. 현재 자동 실행 판단은 위의 서버 반복 실행기와 작업 실행 이력을 우선한다."
      : localWorkerExplanation(localWorker),
    eyebrow: ec2SchedulerInstalled ? "과거 로컬 워커 기록" : "최근 자동 실행 결과",
    factRows: [
      { label: "상태", value: koCode(localWorker.status) },
      { label: "실행 여부", value: localWorker.execute ? "실제 실행" : "미리보기" },
      { label: "생성 시각", value: localWorker.generated_at || "기록 없음" },
      {
        label: "완료 회차",
        value: `${localWorker.completed_cycle_count}/${localWorker.max_cycles || localWorker.completed_cycle_count}회`,
      },
      { label: "중단 회차", value: `${localWorker.failed_cycle_count}회` },
      { label: "오류 시 중단", value: localWorker.stop_on_failure ? "예" : "아니오" },
      {
        label: "대상 작업",
        value: localWorker.job_ids.length > 0
          ? localWorker.job_ids.map((jobId) => koCode(jobId)).join(" · ")
          : "연결된 작업 없음",
      },
      { label: "최신 수집 요약", value: summaryLocationLabel(localWorker.latest_smoke_output_path) },
      { label: "다음 조치", value: localWorkerNextAction(localWorker) },
    ],
    title: ec2SchedulerInstalled ? "현재 서버 자동화의 주 근거가 아니다" : localWorkerTitle(localWorker),
  };
}

export function buildManualSmokePanel(
  manualSmoke: ManualIngestSmoke,
  ec2SchedulerInstalled: boolean,
): DataHealthManualSmokePanel {
  return {
    artifactRows: manualSmoke.artifact_runs.map((run) => ({
      errorLabel: errorLogLabel(run.stderr_path),
      exitCodeLabel: String(run.exit_code),
      jobLabel: koCode(run.job_id),
      pipelineLabel: operationCopy(run.pipeline_name),
      statusLabel: koCode(run.status),
    })),
    description: ec2SchedulerInstalled
      ? "이 기록은 수동으로 데이터 수집 경로를 검증했던 증거다. 현재 서버 운영 상태는 서버 반복 실행기와 최신 작업 실행 이력으로 판단한다."
      : manualSmokeExplanation(manualSmoke),
    eyebrow: ec2SchedulerInstalled ? "과거 수동 점검 증거" : "최근 수동 점검 증거",
    factRows: [
      { label: "상태", value: koCode(manualSmoke.status) },
      { label: "실행 여부", value: manualSmoke.execute ? "실제 실행" : "미리보기" },
      { label: "생성 시각", value: manualSmoke.generated_at || "기록 없음" },
      { label: "실행 환경 상태", value: manualSmoke.runtime_status ? koCode(manualSmoke.runtime_status) : "미확인" },
      {
        label: "대상 작업",
        value: manualSmoke.planned_job_ids.length > 0
          ? manualSmoke.planned_job_ids.map((jobId) => koCode(jobId)).join(" · ")
          : "연결된 작업 없음",
      },
      {
        label: "실행 기록",
        value: `${manualSmoke.artifact_runs.length}개 기록 · 중단 ${manualSmoke.failed_job_count}개`,
      },
      { label: "결과 위치", value: evidenceLocationLabel(manualSmoke.artifact_root) },
      { label: "다음 조치", value: manualSmokeNextAction(manualSmoke) },
    ],
    title: ec2SchedulerInstalled ? "자동 운영 전 수동 검증 기록" : manualSmokeTitle(manualSmoke),
  };
}
