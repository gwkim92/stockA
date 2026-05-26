import type { Route } from "next";
import { DecisionReviewStrip } from "@/components/decision-review-strip";
import { getDataHealth } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import type { DataHealthData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "데이터 수집" };

type PipelineRun = DataHealthData["pipeline_runs"][number];
type SchedulerActivation = DataHealthData["scheduler"]["activation"];
type SchedulerStatus = DataHealthData["scheduler"];
type ProfileSchedulerStatus = NonNullable<DataHealthData["scheduler"]["profile_scheduler"]>;
type ManualIngestSmoke = DataHealthData["manual_local_ingest_smoke"];
type LocalIngestWorker = DataHealthData["local_ingest_worker"];
type CycleAiQualityAudit = DataHealthData["cycle_ai_quality_audit"];
type BenchmarkDriftQuality = DataHealthData["benchmark_drift_quality"];
type RecommendationOutcomeCalibration = DataHealthData["recommendation_outcome_calibration"];
type RecommendationOutcomeMaturity = DataHealthData["recommendation_outcome_maturity"];
type RecommendationWeightReviewReadiness = DataHealthData["recommendation_weight_review_readiness"];
type ProfessionalSourceGapPrioritization = DataHealthData["professional_source_gap_prioritization"];
type ProfileTimer = ProfileSchedulerStatus["timers"][number];

function statusRiskClass(value: string) {
  if (
    value === "healthy"
    || value === "succeeded"
    || value === "configured"
    || value === "not_due"
    || value === "low"
    || value === "watch"
  ) {
    return "risk-low";
  }
  if (
    value === "attention_required"
    || value === "stale"
    || value === "degraded"
    || value === "succeeded_with_fallback"
    || value === "medium"
  ) {
    return "risk-medium";
  }
  return "risk-high";
}

function findPipelineRun(data: DataHealthData, jobId: string, pipelineName: string) {
  return (
    data.pipeline_runs.find((run) => run.job_id === jobId)
    ?? data.pipeline_runs.find((run) => run.pipeline_name === pipelineName)
    ?? null
  );
}

function runStateLabel(run: PipelineRun | null) {
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

function automationStateLabel(schedulerActivation: SchedulerActivation) {
  if (schedulerActivation.activation_allowed) {
    return schedulerActivation.scheduler_activation === "installed" ? "자동 반복 실행 중" : "반복 실행 설정됨";
  }
  if (schedulerActivation.status === "pending_manual_approval") {
    return "자동 반복 실행 미설정";
  }
  return koCode(schedulerActivation.status);
}

function cadenceLabel(run: PipelineRun | null, fallback: string) {
  if (!run) {
    return fallback;
  }
  return `${koCode(run.cadence)} · ${run.expected_after_local}`;
}

function finishedAtLabel(run: PipelineRun | null) {
  return run?.finished_at ?? "아직 완료 기록 없음";
}

function runQualityExplanation(run: PipelineRun | null) {
  if (!run) {
    return "실행 이력이 없어 근거 신뢰도를 판단할 수 없다.";
  }
  if (run.latest_status === "succeeded_with_fallback" || run.health_status === "degraded") {
    return "작업은 멈추지 않았지만 일부 AI 분석이 실패해 규칙 기반 대체 처리로 완료됐다. 추천 근거 신뢰도를 낮게 보고 오류 내용을 확인해야 한다.";
  }
  if (run.latest_status === "succeeded" && run.health_status === "ok") {
    return "최근 실행은 정상 범위다.";
  }
  return "상태와 완료 시각을 기준으로 실행 로그를 확인해야 한다.";
}

function schedulerReadinessTitle(scheduler: SchedulerStatus) {
  const activation = scheduler.activation;
  if (activation.approval_gate === "installed_on_ec2_systemd") {
    return "EC2 반복 실행기 작동 중";
  }
  if (activation.activation_allowed && activation.scheduler_activation !== "not_installed") {
    return "반복 실행기 연결 가능";
  }
  if (activation.status === "pending_manual_approval") {
    return "반복 실행기는 아직 연결되지 않음";
  }
  if (scheduler.install_status === "not_installed") {
    return "반복 실행기는 아직 연결되지 않음";
  }
  return koCode(activation.status);
}

function schedulerReadinessExplanation(scheduler: SchedulerStatus) {
  const activation = scheduler.activation;
  const profileScheduler = scheduler.profile_scheduler;
  if (activation.approval_gate === "installed_on_ec2_systemd") {
    const activeCount = profileScheduler?.active_timer_count ?? 0;
    const timerCount = profileScheduler?.timer_count ?? 0;
    return `EC2 서버의 예약 실행기가 데이터 수집과 분석 작업을 주기별로 호출한다. 현재 반복 실행기는 ${activeCount}/${timerCount}개가 활성 상태다.`;
  }
  if (activation.activation_allowed && activation.scheduler_activation !== "not_installed") {
    return "승인 조건과 실행기 상태가 반복 실행을 허용한다. EC2 예약 실행기가 작업별 주기에 맞춰 수집과 분석을 호출한다.";
  }
  if (activation.status === "pending_manual_approval") {
    return "최근 작업 실행은 성공했지만 자동 반복 실행기는 아직 연결되지 않았다. 이 상태에서는 사람이 수동으로 실행해야 데이터가 갱신된다.";
  }
  if (activation.status === "not_configured") {
    return "반복 실행 결과가 연결되지 않아 자동 실행 여부를 판단할 수 없다.";
  }
  if (activation.status === "invalid_report") {
    return "반복 실행 결과 형식이 맞지 않아 운영 근거로 사용할 수 없다.";
  }
  return "현재 반복 실행 상태는 화면의 승인 조건과 다음 단계 값을 기준으로 다시 확인해야 한다.";
}

function isEc2ProfileSchedulerInstalled(scheduler: SchedulerStatus) {
  return scheduler.activation.approval_gate === "installed_on_ec2_systemd"
    && scheduler.profile_scheduler?.status === "installed";
}

function timerPurpose(profileId: string) {
  if (profileId === "news-intraday") {
    return "뉴스 수집, 한국어 번역, AI 구조화, 상위 흐름 전파를 짧은 주기로 갱신한다.";
  }
  if (profileId === "market-daily") {
    return "장 마감 후 무료 가격 데이터 한도 안에서 일봉 캔들을 보강한다.";
  }
  if (profileId === "decision-daily") {
    return "가격, 뉴스, 사이클, 보유 상태를 합쳐 추천과 보유 검토를 갱신한다.";
  }
  if (profileId === "market-universe-weekly") {
    return "감시 종목군과 기본 가격 커버리지를 주간 단위로 정리한다.";
  }
  if (profileId === "macro-weekly") {
    return "거시 지표를 주간 단위로 보강해 큰 시장 사이클 판단에 사용한다.";
  }
  if (profileId === "sec-filings-weekly") {
    return "SEC 공시 기반 기업 이벤트를 주간 단위로 보강한다.";
  }
  if (profileId === "performance-monthly") {
    return "추천과 thesis 성과를 월간 단위로 측정한다.";
  }
  return "운영 프로파일에 등록된 데이터 작업을 정해진 주기로 실행한다.";
}

function timerStatusTone(timer: ProfileTimer) {
  if (timer.active_state === "active" && timer.last_result === "success") {
    return "risk-low";
  }
  if (timer.active_state === "active") {
    return "risk-medium";
  }
  return "risk-high";
}

function schedulerNextStepLabel(activation: SchedulerActivation) {
  if (activation.manual_next_step === "data-operations-live-scheduler-activation-request") {
    return "반복 실행 설정 전에 수동 수집 순서와 결과를 먼저 확인한다.";
  }
  if (activation.manual_next_step === "configure_scheduler_activation_gate_report") {
    return "저장소 밖 반복 실행 결과 경로를 설정한다.";
  }
  if (activation.manual_next_step === "regenerate_scheduler_activation_gate_report") {
    return "깨진 반복 실행 결과 파일을 다시 생성한다.";
  }
  return koCode(activation.manual_next_step);
}

function schedulerInstallLabel(value: string) {
  if (value === "not_installed") {
    return "반복 실행기 미설정";
  }
  return koCode(value);
}

function schedulerApprovalGateLabel(value: string) {
  if (value === "installed_on_ec2_systemd") {
    return "EC2 반복 실행 설치 완료";
  }
  if (value === "blocked_pending_manual_approval" || value === "pending_manual_approval") {
    return "자동 반복 실행 전 조건 닫힘";
  }
  return koCode(value);
}

function manualSmokeTitle(smoke: ManualIngestSmoke) {
  if (smoke.status === "passed") {
    return "최근 수동 수집 성공";
  }
  if (smoke.status === "failed") {
    return "최근 수동 수집 실패";
  }
  if (smoke.status === "preview_not_executed") {
    return "수동 수집 계획만 확인됨";
  }
  if (smoke.status === "not_configured") {
    return "최근 수동 수집 결과 미연결";
  }
  if (smoke.status === "missing_report") {
    return "최근 수동 수집 결과 파일 없음";
  }
  return koCode(smoke.status);
}

function manualSmokeExplanation(smoke: ManualIngestSmoke) {
  if (smoke.status === "passed") {
    return "가격, 뉴스, AI 분석 단발 작업이 실행됐고 실패 작업이 없다는 뜻이다. 반복 자동화 상태는 별도로 확인한다.";
  }
  if (smoke.status === "failed") {
    return "단발 실행 중 실패한 작업이 있다. 실행 요약의 오류 내용과 작업 정보를 먼저 확인해야 한다.";
  }
  if (smoke.status === "preview_not_executed") {
    return "실제 저장이나 외부 데이터 제공자 호출 없이 실행 계획만 생성한 상태다. 무료 API 한도를 쓰지 않고 어떤 작업이 돌지 확인한 것이다.";
  }
  if (smoke.status === "not_configured") {
    return "서버에 최근 수동 수집 결과 경로가 연결되지 않아 화면에서 읽을 수 없다.";
  }
  if (smoke.status === "missing_report") {
    return "환경변수는 설정됐지만 해당 요약 파일을 읽을 수 없다. 저장소 밖 경로에 요약 파일을 다시 생성해야 한다.";
  }
    return "수동 수집 상태를 확인하려면 결과 파일 형식과 생성 시각을 점검해야 한다.";
}

function manualSmokeNextAction(smoke: ManualIngestSmoke) {
  return smoke.next_actions[0] ? koCode(smoke.next_actions[0]) : "다음 조치 없음";
}

function localWorkerTitle(worker: LocalIngestWorker) {
  if (worker.status === "completed") {
    return "반복 실행 최근 성공";
  }
  if (worker.status === "failed") {
    return "반복 실행 최근 실패";
  }
  if (worker.status === "preview_not_executed") {
    return "반복 실행 계획만 확인됨";
  }
  if (worker.status === "not_configured") {
    return "반복 실행 결과 미연결";
  }
  if (worker.status === "missing_report") {
    return "반복 실행 결과 파일 없음";
  }
  return koCode(worker.status);
}

function localWorkerExplanation(worker: LocalIngestWorker) {
  if (worker.status === "completed") {
    return "정해진 반복 실행 주기가 끝났고 실패 주기가 없다는 뜻이다. EC2의 예약 실행과 함께 자동 운영 상태를 판단한다.";
  }
  if (worker.status === "failed") {
    return "반복 실행 중 실패가 있었다. 최신 실행 요약과 오류 내용을 먼저 확인해야 한다.";
  }
  if (worker.status === "preview_not_executed") {
    return "실제 저장이나 외부 데이터 제공자 호출 없이 반복 실행 계획만 확인한 상태다.";
  }
  if (worker.status === "not_configured") {
    return "서버에 반복 실행 결과 경로가 연결되지 않아 화면에서 읽을 수 없다.";
  }
  if (worker.status === "missing_report") {
    return "환경변수는 설정됐지만 반복 실행 결과 파일을 읽을 수 없다. 저장소 밖 경로에 결과를 다시 생성해야 한다.";
  }
  return "반복 실행 상태를 판단하려면 결과 파일 형식과 생성 시각을 점검해야 한다.";
}

function localWorkerNextAction(worker: LocalIngestWorker) {
  return worker.next_actions[0] ? koCode(worker.next_actions[0]) : "다음 조치 없음";
}

function qualityAuditTitle(audit: CycleAiQualityAudit) {
  if (audit.status === "ok") {
    return "품질 감사 통과";
  }
  if (audit.status === "degraded") {
    return "품질 감사 일부 부족";
  }
  if (audit.status === "attention_required") {
    return "오염 의심 항목 확인 필요";
  }
  if (audit.status === "not_ready") {
    return "감사할 데이터 부족";
  }
  if (audit.status === "not_configured") {
    return "품질 감사 결과 미연결";
  }
  return koCode(audit.status);
}

function qualityAuditExplanation(audit: CycleAiQualityAudit) {
  if (audit.status === "ok") {
    return "중복 뉴스, 잘못된 테마 연결, 원문 근거 없는 종목 연결이 현재 감사 기준에서 발견되지 않았다.";
  }
  if (audit.status === "degraded") {
    return "큰 오염은 없지만 번역, AI 분석, 전파, 사이클 스냅샷 중 일부 근거가 아직 부족하다.";
  }
  if (audit.status === "attention_required") {
    return "추천 판단 전에 중복 뉴스, 종목 근거, 잘못된 테마 연결을 먼저 확인해야 한다.";
  }
  if (audit.status === "not_ready") {
    return "뉴스 수집부터 AI 분석, 전파, 사이클 스냅샷까지 한 번 더 실행한 뒤 판단해야 한다.";
  }
  if (audit.status === "not_configured") {
    return "서버에 최근 품질 감사 요약 파일 경로가 연결되지 않아 화면에서 읽을 수 없다.";
  }
  return "품질 감사 결과 파일의 상태와 생성 시각을 다시 확인해야 한다.";
}

function qualityAuditTone(audit: CycleAiQualityAudit) {
  if (audit.status === "ok") {
    return "risk-low";
  }
  if (audit.status === "degraded" || audit.status === "not_configured") {
    return "risk-medium";
  }
  return "risk-high";
}

function qualityMetric(audit: CycleAiQualityAudit, key: string) {
  const value = audit.metrics[key] ?? audit.checks[key] ?? 0;
  return typeof value === "number" ? value : Number(value || 0);
}

function formatPercent(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "미계산";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function benchmarkDriftQualityTitle(quality: BenchmarkDriftQuality) {
  if (quality.status === "ok") {
    return "벤치마크 구성 신뢰 가능";
  }
  if (quality.status === "partial_composition") {
    return "부분 구성비로만 계산됨";
  }
  if (quality.status === "stale_composition") {
    return "구성 기준일 오래됨";
  }
  if (quality.status === "missing_benchmark_composition") {
    return "벤치마크 구성비 없음";
  }
  if (quality.status === "drift_outlier_review") {
    return "큰 괴리 종목 확인 필요";
  }
  if (quality.status === "missing_guardrail") {
    return "위험 예산 평가 없음";
  }
  return koCode(quality.status);
}

function benchmarkDriftQualityExplanation(quality: BenchmarkDriftQuality) {
  if (quality.status === "ok") {
    return "구성비 커버리지와 기준일이 충분해 active share를 보조 위험 지표로 볼 수 있다. 추천 weight는 자동 변경하지 않는다.";
  }
  if (quality.status === "partial_composition") {
    return "현재 benchmark holdings가 일부만 들어와 있다. active share 숫자는 계산됐지만 전체 SPY 대비 괴리로 해석하면 안 된다.";
  }
  if (quality.status === "stale_composition") {
    return "벤치마크 구성 기준일이 오래되어 최신 지수 구성과 다를 수 있다. holdings 파일을 다시 적재해야 한다.";
  }
  if (quality.status === "missing_benchmark_composition") {
    return "벤치마크 구성비가 없어 포트폴리오가 SPY와 얼마나 다른지 계산하지 못했다.";
  }
  if (quality.status === "drift_outlier_review") {
    return "active share 또는 개별 active weight가 커서 포트폴리오 위험 예산 검토가 필요하다.";
  }
  if (quality.status === "missing_guardrail") {
    return "위험 예산 평가가 아직 없어 벤치마크 drift 품질도 판단할 수 없다.";
  }
  return "벤치마크 drift 품질 상태를 확인해야 한다.";
}

function benchmarkDriftQualityTone(quality: BenchmarkDriftQuality) {
  if (quality.status === "ok") {
    return "risk-low";
  }
  if (quality.status === "partial_composition" || quality.status === "stale_composition") {
    return "risk-medium";
  }
  return "risk-high";
}

function outcomeCalibrationTitle(calibration: RecommendationOutcomeCalibration) {
  if (calibration.status === "ready_for_manual_weight_review") {
    return "성과 표본 검토 가능";
  }
  if (calibration.status === "collect_more_outcomes_keep_weights") {
    return "성과 표본 축적 중";
  }
  if (calibration.status === "backfill_candidates_remain") {
    return "성과 산출 후보 남음";
  }
  if (calibration.status === "price_history_gaps_remain") {
    return "가격 이력 보강 필요";
  }
  if (calibration.status === "no_due_outcome_window") {
    return "성과 측정일 대기";
  }
  if (calibration.status === "missing") {
    return "성과 보정 결과 없음";
  }
  return koCode(calibration.status);
}

function outcomeCalibrationExplanation(calibration: RecommendationOutcomeCalibration) {
  if (calibration.status === "ready_for_manual_weight_review") {
    return "성과 표본과 전문 분석 coverage 기준을 통과했다. 그래도 자동 weight 변경은 금지이고 별도 검토 task가 필요하다.";
  }
  if (calibration.status === "collect_more_outcomes_keep_weights") {
    return "성과 표본은 있지만 추천 산식 weight를 바꾸기에는 아직 더 많은 outcome과 실패 사례가 필요하다.";
  }
  if (calibration.status === "backfill_candidates_remain") {
    return "이미 수집된 가격 이력으로 성과를 더 산출할 수 있다. 추천 품질 평가 전에 backfill runner를 다시 실행해야 한다.";
  }
  if (calibration.status === "price_history_gaps_remain") {
    return "성과를 계산해야 할 추천은 있지만 entry/exit 가격 이력이 부족하다. 캔들 보강이 먼저다.";
  }
  if (calibration.status === "no_due_outcome_window") {
    return "선택한 중장기 horizon의 성과 측정일이 아직 오지 않았다. 추천 weight는 그대로 두고 표본이 쌓일 때까지 기다린다.";
  }
  if (calibration.status === "missing") {
    return "추천 성과 표본과 컴포넌트 보정 진단이 아직 생성되지 않았다.";
  }
  return "추천 성과 보정 상태를 확인해야 한다.";
}

function outcomeCalibrationTone(calibration: RecommendationOutcomeCalibration) {
  if (calibration.status === "ready_for_manual_weight_review") {
    return "risk-low";
  }
  if (calibration.status === "collect_more_outcomes_keep_weights") {
    return "risk-medium";
  }
  return "risk-high";
}

function outcomeMaturityTitle(maturity: RecommendationOutcomeMaturity) {
  if (maturity.status === "not_due") {
    return "성과 측정일 대기";
  }
  if (maturity.status === "due_outcomes_ready") {
    return "성과 산출 가능";
  }
  if (maturity.status === "overdue_outcomes_ready") {
    return "성과 산출 지연";
  }
  if (maturity.status === "blocked_by_price_gaps") {
    return "가격 이력 보강 필요";
  }
  if (maturity.status === "complete_current_window") {
    return "현재 창 측정 완료";
  }
  return koCode(maturity.status);
}

function outcomeMaturityExplanation(maturity: RecommendationOutcomeMaturity) {
  if (maturity.status === "not_due") {
    return maturity.next_due_date
      ? `${maturity.next_due_date}에 ${maturity.next_due_count}개 추천×기간 성과 측정창이 처음 열린다. 그 전까지 weight 검토는 대기한다.`
      : "아직 성과 측정 가능한 추천×기간이 없다. weight 검토는 대기한다.";
  }
  if (maturity.status === "due_outcomes_ready") {
    return `${maturity.ready_for_backfill_count}개 추천×기간 성과를 산출할 수 있다. outcome backfill과 calibration을 먼저 실행해야 한다.`;
  }
  if (maturity.status === "overdue_outcomes_ready") {
    return `${maturity.overdue_count}개 추천×기간 성과 산출이 지연됐다. 추천 weight 검토 전에 outcome backfill을 실행해야 한다.`;
  }
  if (maturity.status === "blocked_by_price_gaps") {
    return `${maturity.price_gap_count}개 추천×기간은 가격 이력 부족으로 성과 계산이 막혔다. 캔들 보강이 먼저다.`;
  }
  if (maturity.status === "complete_current_window") {
    return "현재 측정 가능한 성과창은 모두 처리됐다. 다음 측정일 전까지 weight 변경은 하지 않는다.";
  }
  return "추천 성과 측정창 상태를 확인한다.";
}

function outcomeMaturityTone(maturity: RecommendationOutcomeMaturity) {
  if (maturity.status === "not_due" || maturity.status === "complete_current_window") {
    return "risk-medium";
  }
  if (maturity.status === "due_outcomes_ready") {
    return "risk-medium";
  }
  return "risk-high";
}

function professionalSourceGapTitle(gaps: ProfessionalSourceGapPrioritization) {
  if (gaps.status === "ok") {
    return "전문 분석 소스 정상";
  }
  if (gaps.status === "source_blockers_present") {
    return "원천 차단 종목 있음";
  }
  if (gaps.status === "high_priority_gaps") {
    return "우선 보강 소스 있음";
  }
  if (gaps.status === "fund_source_gaps") {
    return "펀드 분석 소스 보강 필요";
  }
  if (gaps.status === "fund_company_model_not_applicable") {
    return "펀드는 기업 재무 모델 제외";
  }
  if (gaps.status === "coverage_gaps_present") {
    return "분석 layer 누락 있음";
  }
  return koCode(gaps.status);
}

function professionalSourceGapExplanation(gaps: ProfessionalSourceGapPrioritization) {
  if (gaps.status === "ok") {
    return "active recommendation 기준으로 핵심 재무·밸류에이션·리서치 source gap이 없다.";
  }
  if (gaps.status === "source_blockers_present") {
    return "SEC companyfacts나 원천 공시 연결이 막힌 종목이 있다. 합성 재무를 만들지 말고 원천 가능 여부부터 확인해야 한다.";
  }
  if (gaps.status === "high_priority_gaps") {
    return "추천 또는 보유 노출이 있는 종목의 재무·피어·밸류에이션·리서치 근거가 비어 있다. 이 종목부터 보강한다.";
  }
  if (gaps.status === "fund_source_gaps") {
    return "ETF·펀드형 상품은 기업 재무제표가 아니라 보유종목, 비용, NAV, 추적차이 source가 판단 근거다.";
  }
  if (gaps.status === "fund_company_model_not_applicable") {
    return "ETF·펀드형 상품은 기업 재무 모델 실패가 아니다. 별도 fund analysis 근거로 검토한다.";
  }
  return "전문가식 분석에 필요한 source layer 중 일부가 비어 있어 추천 weight 검토 전 보강해야 한다.";
}

function professionalSourceGapTone(gaps: ProfessionalSourceGapPrioritization) {
  if (gaps.status === "ok" || gaps.status === "fund_company_model_not_applicable") {
    return "risk-low";
  }
  if (gaps.status === "coverage_gaps_present" || gaps.status === "fund_source_gaps") {
    return "risk-medium";
  }
  return "risk-high";
}

function executionIdLabel(value: string | null | undefined) {
  if (!value) {
    return "실행 기록 없음";
  }
  if (value.startsWith("pipeline-run-")) {
    return `실행 #${value.replace("pipeline-run-", "")}`;
  }
  return koCode(value);
}

function evidenceLocationLabel(value: string | null | undefined) {
  return value ? "저장소 밖 결과 경로 연결됨" : "결과 경로 없음";
}

function summaryLocationLabel(value: string | null | undefined) {
  return value ? "요약 파일 연결됨" : "요약 경로 없음";
}

function errorLogLabel(value: string | null | undefined) {
  return value ? "오류 내용 있음" : "없음";
}

const DEFAULT_MANUAL_SMOKE: ManualIngestSmoke = {
  status: "not_configured",
  execute: false,
  generated_at: "",
  runtime_status: "",
  artifact_root: "",
  job_count: 0,
  planned_job_ids: [],
  artifact_runs: [],
  failed_job_count: 0,
  next_actions: ["run manual-local-ingest-smoke --output outside the repository"],
  source: "not_configured",
};

const DEFAULT_LOCAL_WORKER: LocalIngestWorker = {
  status: "not_configured",
  execute: false,
  generated_at: "",
  completed_cycle_count: 0,
  failed_cycle_count: 0,
  max_cycles: 0,
  interval_seconds: 0,
  stop_on_failure: true,
  job_ids: [],
  latest_smoke_output_path: "",
  cycles: [],
  next_actions: ["run local-ingest-worker-run --output outside the repository"],
  source: "not_configured",
};

const DEFAULT_CYCLE_AI_QUALITY_AUDIT: CycleAiQualityAudit = {
  status: "not_configured",
  execute: false,
  generated_at: "",
  as_of_date: "",
  lookback_days: 0,
  audit_score: 0,
  issue_count: 0,
  readiness_gap_count: 0,
  metrics: {},
  checks: {},
  samples: {},
  next_actions: ["cycle-ai-quality-audit-run 실행 결과를 연결한다."],
  source: "not_configured",
};

const DEFAULT_BENCHMARK_DRIFT_QUALITY: BenchmarkDriftQuality = {
  status: "missing_guardrail",
  guardrail_status: "missing",
  guardrail_eval_run_id: "eval-run-unknown",
  guardrail_as_of_date: "",
  drift_status: "missing",
  drift_calculated: false,
  benchmark_code: "",
  benchmark_source: "",
  source_type: "",
  source_as_of_date: "",
  source_age_days: null,
  component_count: 0,
  composition_coverage_weight: 0,
  active_share: null,
  total_absolute_drift: null,
  top_active_positions: [],
  outlier_positions: [],
  checks: [],
  next_actions: ["portfolio-risk-budget-guardrail-run을 먼저 실행한다."],
};

const DEFAULT_RECOMMENDATION_OUTCOME_CALIBRATION: RecommendationOutcomeCalibration = {
  status: "missing",
  eval_run_id: "eval-run-unknown",
  created_at: "",
  as_of_date: "",
  horizon_days: [],
  quality_status: "unknown",
  sample_status: "unknown",
  recommendation_horizon_count: 0,
  recommendation_count: 0,
  outcome_count: 0,
  outcome_coverage_rate: 0,
  ready_for_backfill_count: 0,
  missing_entry_price_count: 0,
  missing_exit_price_count: 0,
  missing_reason_counts: {},
  component_diagnostic_count: 0,
  next_action: "recommendation-outcome-calibration-sample-expansion-run을 실행한다.",
  recommendation_scoring_mutated: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
};

const DEFAULT_RECOMMENDATION_OUTCOME_MATURITY: RecommendationOutcomeMaturity = {
  status: "missing",
  as_of_date: "",
  source_calibration_eval_run_id: "eval-run-unknown",
  horizon_days: [],
  recommendation_horizon_count: 0,
  recommendation_count: 0,
  outcome_count: 0,
  not_due_count: 0,
  ready_for_backfill_count: 0,
  due_today_count: 0,
  overdue_count: 0,
  price_gap_count: 0,
  missing_entry_price_count: 0,
  missing_exit_price_count: 0,
  next_due_date: "",
  next_due_count: 0,
  examples: [],
  cadence_action: {
    status: "inspect_outcome_maturity_state",
    action_type: "inspect",
    scheduler_job_id: "recommendation-outcome-backfill-daily",
    pipeline_name: "recommendation_outcome_calibration_sample_expansion",
    should_run_now: false,
    should_wait: false,
    requires_price_backfill: false,
    wait_until: "",
    command: "stockanalysis-operations recommendation-outcome-calibration-sample-expansion-run --env-file <ENV> --as-of-date <YYYY-MM-DD> --execute",
    label: "성과 측정창 상태를 먼저 확인한다.",
    reason: "maturity monitor 결과가 아직 없다.",
    blocks_weight_review: true,
    automatic_weight_change_allowed: false,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
  },
  recommendation_scoring_mutated: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
};

const DEFAULT_RECOMMENDATION_WEIGHT_REVIEW_READINESS: RecommendationWeightReviewReadiness = {
  status: "missing",
  eval_run_id: "eval-run-unknown",
  created_at: "",
  decision: "missing_recommendation_weight_review_readiness",
  manual_weight_review_allowed: false,
  source_quality_status: "unknown",
  source_eval_run_id: "eval-run-unknown",
  outcome_calibration_status: "missing",
  outcome_calibration_eval_run_id: "eval-run-unknown",
  blocker_code: "missing_recommendation_weight_review_readiness",
  blocker_message: "recommendation-weight-review-readiness-audit-run을 실행한다.",
  next_action: "recommendation-weight-review-readiness-audit-run을 실행한다.",
  automatic_weight_change_allowed: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
};

const DEFAULT_PROFESSIONAL_SOURCE_GAP_PRIORITIZATION: ProfessionalSourceGapPrioritization = {
  status: "missing",
  as_of_date: "",
  gap_count: 0,
  high_priority_count: 0,
  source_blocker_count: 0,
  fund_not_applicable_count: 0,
  fund_source_gap_count: 0,
  coverage_gap_count: 0,
  top_priority_score: 0,
  gaps: [],
  next_action: "전문 분석 source gap을 먼저 계산한다.",
  recommendation_scoring_mutated: false,
  automatic_weight_change_allowed: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
};

const DEFAULT_PROFILE_SCHEDULER: ProfileSchedulerStatus = {
  status: "not_configured",
  install_status: "not_installed",
  scheduler_type: "",
  timer_count: 0,
  active_timer_count: 0,
  generated_at: "",
  source: "not_configured",
  timers: [],
};

export default async function DataHealthPage() {
  const response = await getDataHealth();
  const data = response.data;
  const providerBudget = data.provider_budget;
  const schedulerActivation = data.scheduler.activation;
  const profileScheduler = data.scheduler.profile_scheduler ?? DEFAULT_PROFILE_SCHEDULER;
  const ec2SchedulerInstalled = isEc2ProfileSchedulerInstalled(data.scheduler);
  const manualSmoke = data.manual_local_ingest_smoke ?? DEFAULT_MANUAL_SMOKE;
  const localWorker = data.local_ingest_worker ?? DEFAULT_LOCAL_WORKER;
  const qualityAudit = data.cycle_ai_quality_audit ?? DEFAULT_CYCLE_AI_QUALITY_AUDIT;
  const benchmarkDriftQuality = data.benchmark_drift_quality ?? DEFAULT_BENCHMARK_DRIFT_QUALITY;
  const outcomeCalibration =
    data.recommendation_outcome_calibration ?? DEFAULT_RECOMMENDATION_OUTCOME_CALIBRATION;
  const outcomeMaturity = data.recommendation_outcome_maturity ?? DEFAULT_RECOMMENDATION_OUTCOME_MATURITY;
  const weightReviewReadiness =
    data.recommendation_weight_review_readiness ?? DEFAULT_RECOMMENDATION_WEIGHT_REVIEW_READINESS;
  const professionalSourceGaps =
    data.professional_source_gap_prioritization ?? DEFAULT_PROFESSIONAL_SOURCE_GAP_PRIORITIZATION;
  const marketPriceRun = findPipelineRun(data, "market-price-daily", "market_price_upsert");
  const newsRun = findPipelineRun(data, "news-rss-daily", "news_rss_upsert");
  const newsEnrichmentRun = findPipelineRun(
    data,
    "news-rss-enrichment-intraday",
    "news_rss_event_enrichment",
  );
  const aiRun = findPipelineRun(data, "event-intelligence-weekly", "event_intelligence_llm_extract");
  const decisionRun = findPipelineRun(data, "cycle-recommendation-weekly", "cycle_state_snapshot");
  const remediationRun = findPipelineRun(
    data,
    "portfolio-remediation-daily",
    "portfolio_remediation_daily_automation",
  );
  const budgetUsage =
    providerBudget.daily_budget > 0
      ? Math.round((providerBudget.used_request_count / providerBudget.daily_budget) * 100)
      : 0;
  const failedPipelines = data.pipeline_runs.filter((run) =>
    ["missing", "stale", "failed"].includes(run.health_status),
  ).length;
  const decisionCards = [
    {
      label: "지금 판단",
      title:
        failedPipelines > 0
          ? "수집 문제 먼저 해결"
          : data.overall_status === "healthy"
            ? "수집 상태 정상"
            : "주의 항목 확인",
      body:
        failedPipelines > 0
          ? "실패 또는 오래된 작업이 있어 추천·보유 판단보다 수집 복구가 먼저다."
          : "캔들, 뉴스, AI 분석, 추천 갱신이 현재 화면 기준으로 읽을 수 있는 상태다.",
      href: "#execution-log",
      cta: "실행 이력 보기",
      tone: failedPipelines > 0 ? "risk-high" : "risk-low",
    },
    {
      label: "자동화",
      title: `${profileScheduler.active_timer_count}/${profileScheduler.timer_count}개 예약 실행`,
      body: "뉴스/AI, 장마감 캔들, 추천 갱신, 주간 기준 데이터가 서로 다른 주기로 돈다.",
      href: "#scheduler-detail",
      cta: "스케줄 보기",
      tone: profileScheduler.active_timer_count === profileScheduler.timer_count ? "risk-low" : "risk-medium",
    },
    {
      label: "무료 API 예산",
      title: `${providerBudget.remaining_request_count}/${providerBudget.daily_budget}회 남음`,
      body: "가격 데이터는 무료 호출 한도 안에서 보강한다. 예산이 부족하면 캔들 보강을 줄여야 한다.",
      href: "#provider-budget",
      cta: "예산 보기",
      tone: providerBudget.remaining_request_count > 0 ? "risk-low" : "risk-high",
    },
    {
      label: "품질 감사",
      title: qualityAuditTitle(qualityAudit),
      body: qualityAuditExplanation(qualityAudit),
      href: "#quality-audit",
      cta: "오염 점검 보기",
      tone: qualityAuditTone(qualityAudit),
    },
    {
      label: "벤치마크 drift",
      title: benchmarkDriftQualityTitle(benchmarkDriftQuality),
      body: benchmarkDriftQualityExplanation(benchmarkDriftQuality),
      href: "#benchmark-drift-quality",
      cta: "벤치마크 품질 보기",
      tone: benchmarkDriftQualityTone(benchmarkDriftQuality),
    },
    {
      label: "성과검증",
      title: outcomeCalibrationTitle(outcomeCalibration),
      body: outcomeCalibrationExplanation(outcomeCalibration),
      href: "#outcome-calibration",
      cta: "표본 상태 보기",
      tone: outcomeCalibrationTone(outcomeCalibration),
    },
    {
      label: "전문 분석 소스",
      title: professionalSourceGapTitle(professionalSourceGaps),
      body: professionalSourceGapExplanation(professionalSourceGaps),
      href: "#professional-source-gaps",
      cta: "소스 공백 보기",
      tone: professionalSourceGapTone(professionalSourceGaps),
    },
  ];
  const automationCards = [
    {
      title: "주식 캔들 수집",
      run: marketPriceRun,
      fallbackCadence: "일간 · 18:30",
      description: "무료 가격 데이터 제공자의 한도를 확인한 뒤 일봉 캔들을 서버에 저장한다.",
      detail: `최근 가격 관측일 ${data.freshness.find((item) => item.dataset === "market.daily_price_bar")?.latest_observation_date ?? "미확인"} · 제공자 ${koCode(providerBudget.provider)}`,
    },
    {
      title: "뉴스 수집",
      run: newsRun,
      fallbackCadence: "일간 · 08:30",
      description: "저장소 밖 RSS 설정의 무료 뉴스 피드를 읽고 원문과 뉴스 이벤트로 저장한다.",
      detail: "뉴스는 이벤트, 종목 상세, 분석 지도, 추천 근거 점검으로 연결된다.",
    },
    {
      title: "AI 분석",
      run: aiRun,
      fallbackCadence: "장중 · 2시간마다",
      description: "수집 문서를 구조화하고 AI 근거 기록을 남긴다. 중요 뉴스는 Codex OAuth 배치 후보로 분석하고, 뉴스 묶음은 무료 로컬 규칙 보조 증거로 남긴다.",
      detail: "AI는 근거를 정리하지만 매수·매도·주문 결론을 자동 실행하지 않는다.",
    },
  ];
  const newsAfterAnalysisSteps = [
    {
      index: "01",
      title: "뉴스 원문 수집",
      run: newsRun,
      owner: "news-rss-daily",
      output: "RSS/Atom 문서를 원문 저장소와 실행 기록에 저장한다.",
      next: "중복과 원천 링크를 남긴 뒤 이벤트 구조화 단계로 넘긴다.",
    },
    {
      index: "02",
      title: "이벤트 구조화",
      run: newsEnrichmentRun,
      owner: "news-rss-enrichment-intraday",
      output: "헤드라인과 본문을 종목·테마·영향 방향이 있는 뉴스 이벤트로 정리한다.",
      next: "동일 테마/종목 관계를 만들고 뉴스, 종목, 뉴스·AI 화면이 읽는다.",
    },
    {
      index: "03",
      title: "AI 근거 생성",
      run: aiRun,
      owner: "event-intelligence-weekly",
      output: "중요 뉴스만 Codex OAuth 배치로 분석해 종목·테마·방향·근거 후보를 AI 분석 기록에 남긴다.",
      next: "검증을 통과한 근거만 표준 뉴스 영향으로 반영한다. 매수·매도·주문 결론은 여기서 만들지 않는다.",
    },
    {
      index: "04",
      title: "신호와 추천 후보 갱신",
      run: decisionRun,
      owner: "decision-daily",
      output: "가격, 테마 연결, 이벤트 강도, 사이클 상태를 합쳐 추천 후보와 투자 논리 입력을 만든다.",
      next: "결정 로직은 재현 가능한 점수 계산이다. AI 근거는 설명 가능한 보조 근거로 붙는다.",
    },
    {
      index: "05",
      title: "보유 검토와 운영 큐",
      run: remediationRun,
      owner: "portfolio-remediation-daily",
      output: "보유 투자 논리 유지 여부, 빈 가격/논리/성과 항목, 가상 거래 검증 문제를 큐로 만든다.",
      next: "추천, 투자 논리, 보유 검토, 가상 거래 화면에서 사람이 검토한다.",
    },
  ];
  const collectionStatusCards = [
    {
      index: "01",
      title: "주식 캔들",
      run: marketPriceRun,
      purpose: "종목 가격과 차트, 모멘텀 지표의 원천이다.",
      check: `최근 가격일 ${
        data.freshness.find((item) => item.dataset === "market.daily_price_bar")?.latest_observation_date ?? "미확인"
      }`,
    },
    {
      index: "02",
      title: "뉴스 원문",
      run: newsRun,
      purpose: "수집된 뉴스와 원문 화면의 원천이다.",
      check: "수집 뉴스는 뉴스 화면에서 시간순으로 본다.",
    },
    {
      index: "03",
      title: "1차 분류 태깅",
      run: newsEnrichmentRun,
      purpose: "뉴스를 종목, 테마, 방향 태그로 1차 정리한다.",
      check: "AI 전 단계이므로 틀릴 수 있고, 이후 AI 분석과 검증이 보강한다.",
    },
    {
      index: "04",
      title: "Codex OAuth 분석",
      run: aiRun,
      purpose: "중요 뉴스를 구조화해 근거 후보를 만든다.",
      check: "화면을 열 때마다 AI를 새로 호출하지 않고 저장된 결과만 읽는다.",
    },
    {
      index: "05",
      title: "AI 결과 검증",
      run: aiRun,
      purpose: "낮은 신뢰도, 알 수 없는 종목/테마, 저신호 뉴스를 차단한다.",
      check: "차단 후보는 AI 차단 후보 화면에서 본다.",
    },
    {
      index: "06",
      title: "추천 신호",
      run: decisionRun,
      purpose: "가격, 뉴스, 사이클, 상위 흐름을 추천 점수로 합친다.",
      check: "추천은 주문이 아니라 사람이 볼 검토서다.",
    },
    {
      index: "07",
      title: "보유 검토",
      run: remediationRun,
      purpose: "투자 논리 공백, 성과 미측정, 보유 충돌을 운영 큐로 만든다.",
      check: "보유 검토와 가상 거래 검증으로 이어진다.",
    },
  ];
  const decisionSteps = [
    {
      index: "01",
      title: "수집 상태",
      question: "데이터가 믿을 만한가",
      status: failedPipelines > 0 ? `문제 ${failedPipelines}개` : koCode(data.overall_status),
      body: "캔들, 뉴스, AI 분석, 추천 갱신이 최근에 성공했는지 확인한다.",
      href: "/data-health" as Route,
      cta: "현재 화면",
      tone: failedPipelines > 0 ? "block" as const : "ok" as const,
    },
    {
      index: "02",
      title: "뉴스·AI 근거",
      question: "새 뉴스가 무엇을 말하나",
      status: runStateLabel(aiRun),
      body: "원천 뉴스, 한국어 번역, AI 구조화, 차단 후보를 이어서 본다.",
      href: "/intelligence" as Route,
      cta: "뉴스 AI 보기",
      tone:
        aiRun?.health_status === "degraded" || aiRun?.latest_status === "succeeded_with_fallback"
          ? "watch" as const
          : "ok" as const,
    },
    {
      index: "03",
      title: "상위 흐름",
      question: "거시 흐름이 어디로 내려가나",
      status: runStateLabel(decisionRun),
      body: "거시·도메인·테마 흐름이 어떤 종목군으로 전파되는지 확인한다.",
      href: "/cycle-map" as Route,
      cta: "흐름 지도",
      tone: decisionRun?.health_status === "ok" ? "ok" as const : "watch" as const,
    },
    {
      index: "04",
      title: "추천·보유",
      question: "판단 입력이 충분한가",
      status: runStateLabel(remediationRun),
      body: "추천 신호와 보유 논리, 미측정 성과, 보완 큐를 확인한다.",
      href: "/recommendations" as Route,
      cta: "추천 보기",
      tone: remediationRun?.health_status === "ok" ? "ok" as const : "watch" as const,
    },
    {
      index: "05",
      title: "페이퍼 안전",
      question: "실거래 전 단계가 막혔나",
      status: `${qualityMetric(qualityAudit, "paper_validation_passed_count")}회 통과`,
      body: "가상 검증과 거래 안전 조건을 보고 실제 주문과 분리되어 있는지 확인한다.",
      href: "/paper-trading" as Route,
      cta: "페이퍼 상태",
      tone: qualityMetric(qualityAudit, "paper_validation_passed_count") > 0 ? "ok" as const : "watch" as const,
    },
  ];

  return (
    <div className="terminal-page">
      <section className="page-hero reveal" aria-labelledby="data-health-title">
        <div>
          <div className="bento-badge">데이터 수집 상태</div>
          <h1 className="page-title" id="data-health-title">
            데이터 수집과 자동 실행이 정상인지 먼저 확인한다.
          </h1>
        </div>
        <p className="page-lede">
          뉴스는 짧은 주기, 주식 캔들은 장 마감 후, 추천·보유검토는 데이터 보강 뒤에 돈다.
          이 화면이 정상이 아니면 추천과 성과 해석도 신뢰하지 않는다.
        </p>
      </section>

      <DecisionReviewStrip
        activeIndex="01"
        title="수집 상태가 통과해야 뒤 판단으로 넘어간다"
        description="이 화면은 운영 로그가 아니라 판단 게이트다. 문제가 있으면 뉴스·추천·페이퍼 해석보다 수집 복구가 먼저다."
        steps={decisionSteps}
      />

      <section className="status-rail compact-rail reveal delay-1" aria-label="데이터 상태 요약">
        <article className="rail-cell">
          <span>01 전체 상태</span>
          <strong>{koCode(data.overall_status)}</strong>
          <small>{data.as_of_date}</small>
        </article>
        <article className="rail-cell rail-critical">
          <span>02 실패 작업</span>
          <strong>{failedPipelines}</strong>
          <small>{data.pipeline_runs.length}개 중</small>
        </article>
        <article className="rail-cell">
          <span>03 반복 실행</span>
          <strong>{automationStateLabel(schedulerActivation)}</strong>
          <small>{schedulerActivation.job_id ? koCode(schedulerActivation.job_id) : "조건 미설정"}</small>
        </article>
        <article className="rail-cell">
          <span>04 열린 조건</span>
          <strong>{data.open_gates.length}</strong>
          <small>운영 전제</small>
        </article>
        <article className="rail-cell">
          <span>05 호출 예산</span>
          <strong className="rail-ratio-value">
            {providerBudget.remaining_request_count}/{providerBudget.daily_budget}
          </strong>
          <small>{koCode(providerBudget.provider)}</small>
        </article>
      </section>

      <section className="decision-brief-grid reveal delay-1" aria-label="데이터 수집 판단 요약">
        {decisionCards.map((card) => (
          <a className="decision-brief-card data-decision-card" href={card.href} key={card.label}>
            <span>{card.label}</span>
            <strong className={`risk-tag ${card.tone}`}>{card.title}</strong>
            <p>{card.body}</p>
            <small>{card.cta}</small>
          </a>
        ))}
      </section>

      <section className="feature-map-panel reveal delay-1" id="quality-audit" aria-labelledby="quality-audit-title">
        <div className="section-heading stacked-heading">
          <span>품질 감사</span>
          <h2 id="quality-audit-title">수집·번역·AI·전파·추천 입력이 오염되지 않았는지 확인한다.</h2>
        </div>
        <p className="board-intro">{qualityAuditExplanation(qualityAudit)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>감사 결과</span>
            <strong className={`risk-tag ${qualityAuditTone(qualityAudit)}`}>{qualityAuditTitle(qualityAudit)}</strong>
            <small>{qualityAudit.generated_at || "최근 결과 없음"}</small>
          </article>
          <article className="rail-cell">
            <span>감사 점수</span>
            <strong>{qualityAudit.audit_score}</strong>
            <small>{qualityAudit.lookback_days ? `${qualityAudit.lookback_days}일 기준` : "기간 미확인"}</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>오염 의심</span>
            <strong>{qualityAudit.issue_count}</strong>
            <small>중복·오분류·근거 없음</small>
          </article>
          <article className="rail-cell">
            <span>한국어 번역</span>
            <strong>
              {qualityMetric(qualityAudit, "translated_document_count")}/
              {qualityMetric(qualityAudit, "rss_document_count")}
            </strong>
            <small>원천 뉴스</small>
          </article>
          <article className="rail-cell">
            <span>페이퍼 검증</span>
            <strong>{qualityMetric(qualityAudit, "paper_validation_passed_count")}</strong>
            <small>{qualityMetric(qualityAudit, "paper_validation_count")}회 중 통과</small>
          </article>
        </div>
        <div className="insight-grid">
          <article className="insight-card">
            <span>중복 뉴스 묶음</span>
            <strong>{qualityMetric(qualityAudit, "duplicate_title_count")}</strong>
            <p>같은 제목이 반복 수집되어 같은 뉴스가 여러 근거처럼 보일 위험이다.</p>
          </article>
          <article className="insight-card">
            <span>근거 없는 종목 연결</span>
            <strong>{qualityMetric(qualityAudit, "ungrounded_direct_ticker_count")}</strong>
            <p>원문 제목이나 요약에서 확인되지 않는 직접 종목 영향이다.</p>
          </article>
          <article className="insight-card">
            <span>양자→에너지 오분류</span>
            <strong>{qualityMetric(qualityAudit, "quantum_energy_mislink_count")}</strong>
            <p>양자컴퓨팅 뉴스가 에너지 테마나 XOM/XLE로 잘못 묶인 사례다.</p>
          </article>
          <article className="insight-card">
            <span>정상 거시 흐름</span>
            <strong>{qualityMetric(qualityAudit, "normal_macro_flow_count")}</strong>
            <p>종목을 억지로 붙이지 않고 상위 흐름으로 남겨둔 뉴스다.</p>
          </article>
        </div>
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{qualityAudit.next_actions[0] ? koCode(qualityAudit.next_actions[0]) : "현재 추가 조치 없음"}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="outcome-calibration"
        aria-labelledby="outcome-calibration-title"
      >
        <div className="section-heading stacked-heading">
          <span>추천 성과검증</span>
          <h2 id="outcome-calibration-title">추천 weight를 바꾸기 전에 outcome 표본과 실패 사례를 먼저 확인한다.</h2>
        </div>
        <p className="board-intro">{outcomeCalibrationExplanation(outcomeCalibration)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>판정</span>
            <strong className={`risk-tag ${outcomeCalibrationTone(outcomeCalibration)}`}>
              {outcomeCalibrationTitle(outcomeCalibration)}
            </strong>
            <small>{executionIdLabel(outcomeCalibration.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>성과 표본</span>
            <strong>
              {outcomeCalibration.outcome_count}/{outcomeCalibration.recommendation_horizon_count}
            </strong>
            <small>추천×기간 기준</small>
          </article>
          <article className="rail-cell">
            <span>표본 커버리지</span>
            <strong>{formatPercent(outcomeCalibration.outcome_coverage_rate)}</strong>
            <small>{outcomeCalibration.horizon_days.join(" · ") || "기간 미확인"}일</small>
          </article>
          <article className="rail-cell">
            <span>추가 산출 후보</span>
            <strong>{outcomeCalibration.ready_for_backfill_count}</strong>
            <small>가격 이력으로 계산 가능</small>
          </article>
          <article className="rail-cell">
            <span>컴포넌트 진단</span>
            <strong>{outcomeCalibration.component_diagnostic_count}</strong>
            <small>zero-weight 전문 지표</small>
          </article>
        </div>
        <div className="insight-grid">
          <article className="insight-card">
            <span>성과 측정창</span>
            <strong className={`risk-tag ${outcomeMaturityTone(outcomeMaturity)}`}>
              {outcomeMaturityTitle(outcomeMaturity)}
            </strong>
            <p>{outcomeMaturityExplanation(outcomeMaturity)}</p>
          </article>
          <article className="insight-card">
            <span>다음 측정일</span>
            <strong>{outcomeMaturity.next_due_date || "대기 없음"}</strong>
            <p>
              다음에 열릴 추천×기간 {outcomeMaturity.next_due_count}개 · 아직 대기{" "}
              {outcomeMaturity.not_due_count}개 · 산출 가능 {outcomeMaturity.ready_for_backfill_count}개
            </p>
          </article>
          <article className="insight-card">
            <span>지연/가격 보강</span>
            <strong>{outcomeMaturity.overdue_count + outcomeMaturity.price_gap_count}</strong>
            <p>
              지연 {outcomeMaturity.overdue_count}개, 가격 이력 부족 {outcomeMaturity.price_gap_count}개다. 이 값이
              있으면 weight 검토보다 outcome 보강이 먼저다.
            </p>
          </article>
          <article className="insight-card">
            <span>실행 액션</span>
            <strong>{koCode(outcomeMaturity.cadence_action.status)}</strong>
            <p>{outcomeMaturity.cadence_action.reason}</p>
            <small>{outcomeMaturity.cadence_action.command}</small>
          </article>
          <article className="insight-card">
            <span>추천 weight</span>
            <strong>{outcomeCalibration.recommendation_scoring_mutated ? "변경 감지" : "변경 없음"}</strong>
            <p>성과 검증은 추천 산식 변경이 아니다. weight 조정은 별도 승인된 pilot task 전까지 막는다.</p>
          </article>
          <article className="insight-card">
            <span>가격 이력 부족</span>
            <strong>
              {outcomeCalibration.missing_entry_price_count + outcomeCalibration.missing_exit_price_count}
            </strong>
            <p>entry 또는 exit 가격이 없어 성과 산출이 막힌 추천×기간 수다.</p>
          </article>
          <article className="insight-card">
            <span>품질 평가</span>
            <strong>{koCode(outcomeCalibration.quality_status)}</strong>
            <p>전문 분석 coverage와 outcome 표본이 weight 검토 기준을 충족하는지 본다.</p>
          </article>
          <article className="insight-card">
            <span>수동 weight 검토</span>
            <strong>{weightReviewReadiness.manual_weight_review_allowed ? "검토 가능" : "차단"}</strong>
            <p>
              {weightReviewReadiness.blocker_message
                ? koCode(weightReviewReadiness.blocker_message)
                : koCode(weightReviewReadiness.next_action)}
            </p>
          </article>
          <article className="insight-card">
            <span>주문 경계</span>
            <strong>{koCode(outcomeCalibration.order_boundary)}</strong>
            <p>성과검증은 주문 생성이나 증권사 제출을 허용하지 않는다.</p>
          </article>
        </div>
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{outcomeMaturity.cadence_action.label}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="professional-source-gaps"
        aria-labelledby="professional-source-gaps-title"
      >
        <div className="section-heading stacked-heading">
          <span>전문 분석 소스 공백</span>
          <h2 id="professional-source-gaps-title">
            추천·보유 판단에 필요한 재무, 밸류에이션, 펀드 source가 어디서 막혔는지 본다.
          </h2>
        </div>
        <p className="board-intro">{professionalSourceGapExplanation(professionalSourceGaps)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>판정</span>
            <strong className={`risk-tag ${professionalSourceGapTone(professionalSourceGaps)}`}>
              {professionalSourceGapTitle(professionalSourceGaps)}
            </strong>
            <small>{professionalSourceGaps.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>우선 보강</span>
            <strong>{professionalSourceGaps.high_priority_count}</strong>
            <small>추천·보유 노출 큰 공백</small>
          </article>
          <article className="rail-cell">
            <span>원천 차단</span>
            <strong>{professionalSourceGaps.source_blocker_count}</strong>
            <small>SEC/companyfacts 등</small>
          </article>
          <article className="rail-cell">
            <span>펀드 비적용</span>
            <strong>{professionalSourceGaps.fund_not_applicable_count}</strong>
            <small>기업 재무 모델 제외</small>
          </article>
          <article className="rail-cell">
            <span>전체 공백</span>
            <strong>{professionalSourceGaps.gap_count}</strong>
            <small>상위 {professionalSourceGaps.gaps.length}개 표시</small>
          </article>
        </div>

        {professionalSourceGaps.gaps.length > 0 ? (
          <div className="ledger-table-wrap" style={{ marginTop: "18px" }}>
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">우선순위</th>
                  <th scope="col">대상</th>
                  <th scope="col">무엇이 비었나</th>
                  <th scope="col">왜 막혔나</th>
                  <th scope="col">다음 조치</th>
                </tr>
              </thead>
              <tbody>
                {professionalSourceGaps.gaps.map((gap) => (
                  <tr key={`${gap.priority_rank}-${gap.symbol}`}>
                    <td>
                      <strong>#{gap.priority_rank}</strong>
                      <small className={`risk-tag ${statusRiskClass(gap.priority_band)}`}>
                        {koCode(gap.priority_band)}
                      </small>
                    </td>
                    <td>
                      <strong>
                        <a href={gap.detail_href}>{gap.symbol}</a>
                      </strong>
                      <small>{gap.product_type === "fund_or_etf" ? "ETF·펀드형" : "개별 기업"}</small>
                      <small>
                        추천 {gap.active_recommendation_count}개 · 보유 {formatPercent(gap.current_weight)}
                      </small>
                    </td>
                    <td>
                      <strong>{gap.missing_layer_count}개 layer</strong>
                      <small>
                        {gap.missing_layer_labels.length > 0
                          ? gap.missing_layer_labels.join(" · ")
                          : "기업 재무 모델 비적용만 표시"}
                      </small>
                    </td>
                    <td>
                      <strong>{gap.blocker_label}</strong>
                      <small>{gap.blocker_code || koCode(gap.blocker_type)}</small>
                      {gap.source_run_id ? <small>{executionIdLabel(gap.source_run_id)}</small> : null}
                    </td>
                    <td>
                      <strong>{gap.remediation_action}</strong>
                      {gap.remediation_command ? <small>{gap.remediation_command}</small> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            active recommendation 기준으로 표시할 전문 분석 source 공백이 없다.
          </div>
        )}
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{professionalSourceGaps.next_action}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="benchmark-drift-quality"
        aria-labelledby="benchmark-drift-quality-title"
      >
        <div className="section-heading stacked-heading">
          <span>벤치마크 drift 품질</span>
          <h2 id="benchmark-drift-quality-title">SPY와 얼마나 다른지 보기 전에 구성비 품질을 먼저 확인한다.</h2>
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
            <span>구성비 커버리지</span>
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
            <span>Active share</span>
            <strong>{formatPercent(benchmarkDriftQuality.active_share)}</strong>
            <small>{koCode(benchmarkDriftQuality.drift_status)}</small>
          </article>
          <article className="rail-cell">
            <span>큰 괴리 종목</span>
            <strong>{benchmarkDriftQuality.outlier_positions.length}</strong>
            <small>active weight 10%p 이상</small>
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
            {benchmarkDriftQuality.outlier_positions.map((position) => (
              <article className="feature-map-card collection-map-card" key={position.symbol}>
                <span>{position.symbol}</span>
                <strong>벤치마크 대비 {formatPercent(position.active_weight)} 차이</strong>
                <small>포트폴리오 비중 {formatPercent(position.portfolio_weight)}</small>
                <small>벤치마크 비중 {formatPercent(position.benchmark_weight)}</small>
              </article>
            ))}
          </div>
        ) : null}
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>
            {benchmarkDriftQuality.next_actions[0]
              ? koCode(benchmarkDriftQuality.next_actions[0])
              : "현재 추가 조치 없음"}
          </p>
        </div>
      </section>

      <section className="feature-map-panel reveal delay-1" aria-labelledby="scheduler-profile-title">
        <div className="section-heading stacked-heading">
          <span>자동 실행 주기</span>
          <h2 id="scheduler-profile-title">
            {ec2SchedulerInstalled ? "현재 EC2에서 실제로 도는 작업" : "자동 실행 연결 상태"}
          </h2>
        </div>
        <p className="board-intro">
          웹 화면은 작업을 직접 실행하지 않고 저장된 결과를 읽는다. 실제 수집과 분석은 아래 프로파일들이 각자 다른 주기로 실행한다.
        </p>
        {profileScheduler.timers.length > 0 ? (
          <div className="scheduler-timer-grid">
            {profileScheduler.timers.map((timer) => (
              <article className="scheduler-timer-card" key={timer.profile_id}>
                <span>{koCode(timer.profile_id)}</span>
                <strong>{timerPurpose(timer.profile_id)}</strong>
                <small>{timer.schedule || "스케줄 미확인"}</small>
                <dl>
                  <div>
                    <dt>상태</dt>
                    <dd>
                      <span className={`risk-tag ${timerStatusTone(timer)}`}>
                        {koCode(timer.active_state)} · {koCode(timer.last_result || "unknown")}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt>다음 실행</dt>
                    <dd>{timer.next_elapse || "미확인"}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            아직 화면에 연결된 EC2 프로파일 스케줄이 없다. 수동 실행 결과와 실행 로그만 참고한다.
          </div>
        )}
      </section>

      <section className="feature-map-panel reveal delay-1" aria-labelledby="collection-status-title">
        <div className="section-heading stacked-heading">
          <span>수집/분석별 상태</span>
          <h2 id="collection-status-title">무엇이 언제 돌았고, 어디에 쓰이는지 한 번에 본다</h2>
        </div>
        <p className="board-intro">
          이 영역만 보면 “어떤 데이터가 최신인지”를 먼저 판단할 수 있다. 아래 상세 증거는 문제가 있을 때만 펼쳐서 본다.
        </p>
        <div className="feature-map-grid collection-map-grid">
          {collectionStatusCards.map((card) => (
            <article className="feature-map-card collection-map-card" key={card.index}>
              <span>{card.index}</span>
              <strong>{card.title}</strong>
              <em className={`risk-tag ${statusRiskClass(card.run?.health_status ?? "missing")}`}>
                {runStateLabel(card.run)}
              </em>
              <small>{card.purpose}</small>
              <small>{card.check}</small>
              <small>최근 완료: {finishedAtLabel(card.run)}</small>
            </article>
          ))}
        </div>
      </section>

      {aiRun?.health_status === "degraded" || aiRun?.latest_status === "succeeded_with_fallback" ? (
        <section className="flow-panel reveal delay-1" aria-labelledby="ai-fallback-warning-title">
          <div className="section-heading flow-heading">
            <span>AI 분석 경고</span>
            <h2 id="ai-fallback-warning-title">뉴스 AI 분석이 대체 처리로 끝난 실행이 있다</h2>
          </div>
          <p className="page-lede" style={{ marginTop: 0, maxWidth: "980px" }}>
            {runQualityExplanation(aiRun)} 이 상태에서는 뉴스 수집과 이벤트 구조화는 계속 진행되지만,
            AI가 만든 한국어 근거와 종목·테마 영향 검증 신뢰도는 낮아질 수 있다.
          </p>
        </section>
      ) : null}

      <details className="operator-details-panel reveal delay-2">
        <summary>
          <span>운영자용 상세 보기</span>
          <strong>스케줄, 실행 요약, 수동 점검, 작업별 실행 구조</strong>
        </summary>

      <section className="flow-panel details-inner" aria-labelledby="automation-summary-title">
        <div className="section-heading flow-heading">
          <span>자동 수집 / 분석 상태</span>
          <h2 id="automation-summary-title">최근 실행과 실제 반복 자동화를 분리해서 본다</h2>
        </div>
        <p className="page-lede" style={{ marginTop: 0, maxWidth: "980px" }}>
          아래 작업은 최근 실행 이력과 반복 실행 상태를 같이 보여준다. 현재 반복 실행은{" "}
          {automationStateLabel(schedulerActivation)} 상태이며, 수집 성공과 추천 근거는 별도로 검토한다.
        </p>

        <article className="ledger-panel" id="scheduler-detail" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>자동 반복 실행 상태</span>
            <h3>{schedulerReadinessTitle(data.scheduler)}</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            {schedulerReadinessExplanation(data.scheduler)}
          </p>
          <dl className="fact-list compact-facts">
            <div>
              <dt>승인 조건</dt>
              <dd>{schedulerApprovalGateLabel(schedulerActivation.approval_gate)}</dd>
            </div>
            <div>
              <dt>활성화 허용</dt>
              <dd>{schedulerActivation.activation_allowed ? "예" : "아니오"}</dd>
            </div>
            <div>
              <dt>반복 실행 상태</dt>
              <dd>{schedulerInstallLabel(schedulerActivation.scheduler_activation)}</dd>
            </div>
            <div>
              <dt>근거 생성 시각</dt>
              <dd>{schedulerActivation.generated_at || "미확인"}</dd>
            </div>
            <div>
              <dt>결과 위치</dt>
              <dd>{evidenceLocationLabel(data.scheduler.latest_artifact_root)}</dd>
            </div>
            <div>
              <dt>다음 조치</dt>
              <dd>{schedulerNextStepLabel(schedulerActivation)}</dd>
            </div>
          </dl>
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>실제 실행 구조</span>
            <h3>웹 화면은 저장된 결과를 읽고, EC2 예약 작업이 수집·분석을 실행한다</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            FastAPI와 Next.js는 저장된 결과를 읽어 보여준다. 뉴스 수집, 캔들 보강, AI 분석, 추천 갱신은
            EC2 예약 실행기가 백그라운드 작업 실행기를 호출해 수행하고, 결과는 서버 저장 기록과 실행 요약에 남긴다.
          </p>
          <dl className="fact-list compact-facts">
            <div>
              <dt>화면</dt>
              <dd>Next.js 운영 화면</dd>
            </div>
            <div>
              <dt>읽기 API</dt>
              <dd>FastAPI 읽기 전용 백엔드</dd>
            </div>
            <div>
              <dt>작업 실행</dt>
              <dd>EC2 예약 실행 → 백그라운드 작업 실행기</dd>
            </div>
            <div>
              <dt>상태 저장</dt>
              <dd>서버 저장 기록 + 저장소 밖 실행 요약</dd>
            </div>
          </dl>
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>EC2 반복 실행기</span>
            <h3>
              {profileScheduler.active_timer_count}/{profileScheduler.timer_count}개 예약 실행 활성
            </h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            수집기는 하나로 묶여 있지 않다. 뉴스/AI는 짧은 주기, 캔들은 장 마감 후, 신호/추천은 캔들 이후,
            거시·SEC·성과는 느린 주기로 분리되어 돈을 아끼면서도 필요한 데이터가 갱신되게 한다.
          </p>
          <div className="scheduler-timer-grid">
            {profileScheduler.timers.map((timer) => (
              <div className="scheduler-timer-card" key={timer.profile_id}>
                <span>{koCode(timer.profile_id)}</span>
                <strong>{koCode(timer.active_state)}</strong>
                <small>{timer.schedule || "스케줄 미확인"}</small>
                <dl>
                  <div>
                    <dt>다음 실행</dt>
                    <dd>{timer.next_elapse || "미확인"}</dd>
                  </div>
                  <div>
                    <dt>마지막 결과</dt>
                    <dd>{koCode(timer.last_result || "unknown")}</dd>
                  </div>
                </dl>
              </div>
            ))}
          </div>
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>뉴스 분석 이후 운영 흐름</span>
            <h3>AI 근거 이후에는 추천·투자 논리·보유 검토로 넘어간다</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            뉴스 분석은 끝점이 아니다. 수집된 뉴스는 이벤트와 AI 근거가 되고, 이후 가격·테마·사이클 데이터와
            결합되어 중장기 추천 후보, 투자 논리, 보유 검토 큐를 만든다. 주문은 자동 실행하지 않는다.
          </p>
          <div className="operating-flow-grid">
            {newsAfterAnalysisSteps.map((step) => (
            <div className="operating-flow-card" key={step.index}>
              <b>{step.index}</b>
              <span>{koCode(step.owner)}</span>
              <strong>{step.title}</strong>
              <p>{step.output}</p>
              <small>{step.next}</small>
              {step.run?.health_status === "degraded" || step.run?.latest_status === "succeeded_with_fallback" ? (
                <small>{runQualityExplanation(step.run)}</small>
              ) : null}
              <dl>
                  <div>
                    <dt>상태</dt>
                    <dd>{runStateLabel(step.run)}</dd>
                  </div>
                  <div>
                    <dt>최근 완료</dt>
                    <dd>{finishedAtLabel(step.run)}</dd>
                  </div>
                </dl>
              </div>
            ))}
          </div>
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>{ec2SchedulerInstalled ? "과거 로컬 워커 기록" : "최근 자동 실행 결과"}</span>
            <h3>{ec2SchedulerInstalled ? "현재 EC2 자동화의 주 근거가 아니다" : localWorkerTitle(localWorker)}</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            {ec2SchedulerInstalled
              ? "이 기록은 EC2 systemd 프로파일 스케줄러를 붙이기 전 로컬 MVP 단계의 점검 결과다. 현재 자동 실행 판단은 위의 EC2 반복 실행기와 작업 실행 이력을 우선한다."
              : localWorkerExplanation(localWorker)}
          </p>
          <dl className="fact-list compact-facts">
            <div>
              <dt>상태</dt>
              <dd>{koCode(localWorker.status)}</dd>
            </div>
            <div>
              <dt>실행 여부</dt>
              <dd>{localWorker.execute ? "실제 실행" : "미리보기"}</dd>
            </div>
            <div>
              <dt>생성 시각</dt>
              <dd>{localWorker.generated_at || "기록 없음"}</dd>
            </div>
            <div>
              <dt>완료 회차</dt>
              <dd>
                {localWorker.completed_cycle_count}/{localWorker.max_cycles || localWorker.completed_cycle_count}회
              </dd>
            </div>
            <div>
              <dt>실패 회차</dt>
              <dd>{localWorker.failed_cycle_count}회</dd>
            </div>
            <div>
              <dt>실패 시 중단</dt>
              <dd>{localWorker.stop_on_failure ? "예" : "아니오"}</dd>
            </div>
            <div>
              <dt>대상 작업</dt>
              <dd>
                {localWorker.job_ids.length > 0
                  ? localWorker.job_ids.map((jobId) => koCode(jobId)).join(" · ")
                  : "연결된 작업 없음"}
              </dd>
            </div>
            <div>
              <dt>최신 수집 요약</dt>
              <dd>{summaryLocationLabel(localWorker.latest_smoke_output_path)}</dd>
            </div>
            <div>
              <dt>다음 조치</dt>
              <dd>{localWorkerNextAction(localWorker)}</dd>
            </div>
          </dl>
          {localWorker.cycles.length > 0 ? (
            <div className="ledger-table-wrap" style={{ marginTop: "16px" }}>
              <table className="ledger-table data-health-table">
                <thead>
                  <tr>
                    <th scope="col">회차</th>
                    <th scope="col">단발 점검</th>
                    <th scope="col">작업</th>
                    <th scope="col">결과 기록</th>
                  </tr>
                </thead>
                <tbody>
                  {localWorker.cycles.map((cycle) => (
                    <tr key={`${cycle.cycle_number}-${cycle.started_at}`}>
                      <td>
                        <strong>{cycle.cycle_number}</strong>
                        <small>{cycle.started_at || "시각 없음"}</small>
                      </td>
                      <td>{koCode(cycle.smoke_status)}</td>
                      <td>
                        {cycle.job_count}개 · 실패 {cycle.failed_job_count}개
                      </td>
                      <td>{cycle.artifact_run_count}개</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>{ec2SchedulerInstalled ? "과거 수동 점검 증거" : "최근 수동 점검 증거"}</span>
            <h3>{ec2SchedulerInstalled ? "자동 운영 전 수동 검증 기록" : manualSmokeTitle(manualSmoke)}</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            {ec2SchedulerInstalled
              ? "이 기록은 수동으로 데이터 수집 경로를 검증했던 증거다. 현재 서버 운영 상태를 판단할 때는 EC2 반복 실행기와 최신 pipeline run을 먼저 본다."
              : manualSmokeExplanation(manualSmoke)}
          </p>
          <dl className="fact-list compact-facts">
            <div>
              <dt>상태</dt>
              <dd>{koCode(manualSmoke.status)}</dd>
            </div>
            <div>
              <dt>실행 여부</dt>
              <dd>{manualSmoke.execute ? "실제 실행" : "미리보기"}</dd>
            </div>
            <div>
              <dt>생성 시각</dt>
              <dd>{manualSmoke.generated_at || "기록 없음"}</dd>
            </div>
            <div>
              <dt>실행 환경 상태</dt>
              <dd>{manualSmoke.runtime_status ? koCode(manualSmoke.runtime_status) : "미확인"}</dd>
            </div>
            <div>
              <dt>대상 작업</dt>
              <dd>
                {manualSmoke.planned_job_ids.length > 0
                  ? manualSmoke.planned_job_ids.map((jobId) => koCode(jobId)).join(" · ")
                  : "연결된 작업 없음"}
              </dd>
            </div>
            <div>
              <dt>실행 기록</dt>
              <dd>
                {manualSmoke.artifact_runs.length}개 기록 · 실패 {manualSmoke.failed_job_count}개
              </dd>
            </div>
            <div>
              <dt>결과 위치</dt>
              <dd>{evidenceLocationLabel(manualSmoke.artifact_root)}</dd>
            </div>
            <div>
              <dt>다음 조치</dt>
              <dd>{manualSmokeNextAction(manualSmoke)}</dd>
            </div>
          </dl>
          {manualSmoke.artifact_runs.length > 0 ? (
            <div className="ledger-table-wrap" style={{ marginTop: "16px" }}>
              <table className="ledger-table data-health-table">
                <thead>
                  <tr>
                    <th scope="col">작업</th>
                    <th scope="col">상태</th>
                    <th scope="col">종료 코드</th>
                    <th scope="col">오류 내용</th>
                  </tr>
                </thead>
                <tbody>
                  {manualSmoke.artifact_runs.map((run) => (
                    <tr key={`${run.job_id}-${run.artifact_dir || run.exit_code}`}>
                      <td>
                        <strong>{koCode(run.job_id)}</strong>
                        <small>{koCode(run.pipeline_name)}</small>
                      </td>
                      <td>{koCode(run.status)}</td>
                      <td>{run.exit_code}</td>
                      <td>{errorLogLabel(run.stderr_path)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </article>

        <div className="flow-steps data-health-summary-grid" style={{ marginTop: "18px" }}>
          {automationCards.map((card) => (
            <article className="flow-step" key={card.title}>
              <span>{card.title}</span>
              <strong>{runStateLabel(card.run)}</strong>
              <p>{card.description}</p>
              <dl className="fact-list compact-facts" style={{ marginTop: "14px" }}>
                <div>
                  <dt>반복 기준</dt>
                  <dd>{cadenceLabel(card.run, card.fallbackCadence)}</dd>
                </div>
                <div>
                  <dt>최근 완료</dt>
                  <dd>{finishedAtLabel(card.run)}</dd>
                </div>
                <div>
                  <dt>자동화</dt>
                  <dd>{automationStateLabel(schedulerActivation)}</dd>
                </div>
                <div>
                  <dt>사용처</dt>
                  <dd>{card.detail}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>
      </details>

      <details className="operator-details-panel reveal delay-2" id="execution-log">
        <summary>
          <span>실행 로그와 예산 상세</span>
          <strong>작업 이력, 무료 API 예산, 조건/최신성</strong>
        </summary>

      <section className="split-ledger details-inner">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
            <span>실행 이력</span>
            <h2>작업 실행 이력</h2>
          </div>
          <div className="ledger-table-wrap">
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">작업</th>
                  <th scope="col">도메인</th>
                  <th scope="col">상태</th>
                  <th scope="col">최신성</th>
                  <th scope="col">최근 실행</th>
                  <th scope="col">완료 시각</th>
                </tr>
              </thead>
              <tbody>
                {data.pipeline_runs.map((run) => (
                  <tr key={run.latest_run_id}>
                    <td>
                      <strong>{koCode(run.pipeline_name)}</strong>
                      <small>{koCode(run.cadence)}</small>
                    </td>
                    <td>{koCode(run.domain)}</td>
                    <td>
                      <span className={`risk-tag ${statusRiskClass(run.latest_status)}`}>
                        {koCode(run.latest_status)}
                      </span>
                    </td>
                    <td>{koCode(run.health_status)}</td>
                    <td>{executionIdLabel(run.latest_run_id)}</td>
                    <td>{run.finished_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <aside className="side-ledger">
          <article className="ledger-panel" id="provider-budget">
            <div className="section-heading stacked-heading">
              <span>무료 API 예산</span>
              <h2>데이터 제공자 호출 예산</h2>
            </div>
            <div className="budget-meter" aria-label={`호출 예산 사용률 ${budgetUsage}%`}>
              <div style={{ width: `${Math.min(100, Math.max(0, budgetUsage))}%` }} />
            </div>
            <dl className="fact-list">
              <div>
                <dt>상태</dt>
                <dd>{koCode(providerBudget.status)}</dd>
              </div>
              <div>
                <dt>사용</dt>
                <dd>{providerBudget.used_request_count}회</dd>
              </div>
              <div>
                <dt>기준일</dt>
                <dd>{providerBudget.budget_date}</dd>
              </div>
              <div>
                <dt>최근 실행</dt>
                <dd>{providerBudget.latest_run?.started_at ?? "오늘 실행 없음"}</dd>
              </div>
            </dl>
          </article>

          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>조건과 최신성</span>
              <h2>조건과 데이터 최신성</h2>
            </div>
            <div className="tag-ledger">
              {data.open_gates.map((gate) => (
                <span className="risk-tag risk-medium" key={gate}>
                  {koCode(gate)}
                </span>
              ))}
            </div>
            <dl className="fact-list compact-facts">
              {data.freshness.map((item) => (
                <div key={item.dataset}>
                  <dt>{koCode(item.dataset)}</dt>
                  <dd>
                    {koCode(item.status)} · {item.latest_observation_date}
                  </dd>
                </div>
              ))}
            </dl>
          </article>

          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>자동 반복 실행</span>
              <h2>반복 실행 준비 상태</h2>
            </div>
            <dl className="fact-list">
              <div>
                <dt>자동 실행기</dt>
                <dd>{schedulerInstallLabel(data.scheduler.install_status)}</dd>
              </div>
              <div>
                <dt>환경</dt>
                <dd>{koCode(data.scheduler.runtime_env_readiness)}</dd>
              </div>
              <div>
                <dt>승인 상태</dt>
                <dd>{automationStateLabel(schedulerActivation)}</dd>
              </div>
              <div>
                <dt>대상 작업</dt>
                <dd>{koCode(schedulerActivation.job_id)}</dd>
              </div>
              <div>
                <dt>승인 조건</dt>
                <dd>{schedulerApprovalGateLabel(schedulerActivation.approval_gate)}</dd>
              </div>
              <div>
                <dt>활성화 가능</dt>
                <dd>{schedulerActivation.activation_allowed ? "예" : "아니오"}</dd>
              </div>
              <div>
                <dt>다음 단계</dt>
                <dd>{schedulerNextStepLabel(schedulerActivation)}</dd>
              </div>
              <div>
                <dt>휴장일 처리</dt>
                <dd>{koCode(data.scheduler.holiday_skip_mode)}</dd>
              </div>
            </dl>
          </article>
        </aside>
      </section>
      </details>
    </div>
  );
}
