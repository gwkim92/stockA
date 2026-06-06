import type { Route } from "next";
import { getDataHealth } from "@/lib/frontend-api";
import { koCode, koReason } from "@/lib/korean-labels";
import type { DataHealthData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "데이터·자동화 상태" };

type PipelineRun = DataHealthData["pipeline_runs"][number];
type SchedulerActivation = DataHealthData["scheduler"]["activation"];
type SchedulerStatus = DataHealthData["scheduler"];
type ProfileSchedulerStatus = NonNullable<DataHealthData["scheduler"]["profile_scheduler"]>;
type ProductionApiServer = DataHealthData["production_api_server"];
type AuthRbac = DataHealthData["auth_rbac"];
type AlertDestination = DataHealthData["alert_destination"];
type ManualIngestSmoke = DataHealthData["manual_local_ingest_smoke"];
type LocalIngestWorker = DataHealthData["local_ingest_worker"];
type CycleAiQualityAudit = DataHealthData["cycle_ai_quality_audit"];
type NewsAiEvalQuality = DataHealthData["news_ai_eval_quality"];
type LiveAiInvocationHealth = DataHealthData["live_ai_invocation_health"];
type DataOperationsArtifactRunner = DataHealthData["data_operations_artifact_runner"];
type ActiveRecommendationPriceFreshness = DataHealthData["active_recommendation_price_freshness"];
type BenchmarkDriftQuality = DataHealthData["benchmark_drift_quality"];
type PortfolioReviewDecisionHistory = DataHealthData["portfolio_review_decision_history"];
type PortfolioReviewDecisionFeedback = DataHealthData["portfolio_review_decision_feedback"];
type PortfolioReviewFeedbackCalibration = DataHealthData["portfolio_review_feedback_calibration"];
type PortfolioReviewFeedbackCadence = DataHealthData["portfolio_review_feedback_cadence"];
type PortfolioReviewFeedbackActionRouter = DataHealthData["portfolio_review_feedback_action_router"];
type RecommendationOutcomeCalibration = DataHealthData["recommendation_outcome_calibration"];
type RecommendationOutcomeMaturity = DataHealthData["recommendation_outcome_maturity"];
type RecommendationOutcomeDueActionRouter = DataHealthData["recommendation_outcome_due_action_router"];
type RecommendationWeightReviewReadiness = DataHealthData["recommendation_weight_review_readiness"];
type OutcomeMaturityWaitMonitor = DataHealthData["outcome_maturity_wait_monitor"];
type ProfessionalSourceGapPrioritization = DataHealthData["professional_source_gap_prioritization"];
type ProfessionalAnalysisQuality = DataHealthData["professional_analysis_quality"];
type ProfessionalRecommendationCoverageAudit = DataHealthData["professional_recommendation_coverage_audit"];
type ProfessionalAnalysisNextAction = DataHealthData["professional_analysis_next_action"];
type ProfessionalAnalysisDepth = DataHealthData["professional_analysis_depth"];
type OpenGateDetail = NonNullable<DataHealthData["open_gate_details"]>[number];
type ProfileTimer = ProfileSchedulerStatus["timers"][number];
type AuditSampleRecord = Record<string, unknown>;
type TimerGroupDefinition = {
  key: string;
  label: string;
  title: string;
  description: string;
  profileIds: string[];
};
type SchedulerCadenceGroup = TimerGroupDefinition & {
  timers: ProfileTimer[];
  activeCount: number;
  successCount: number;
  problemCount: number;
};
type GateTriageBucket = {
  key: string;
  label: string;
  title: string;
  description: string;
  tone: "risk-low" | "risk-medium" | "risk-high";
  href: string;
  gates: OpenGateDetail[];
};

function isRecord(value: unknown): value is AuditSampleRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

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

function gateSeverityTone(severity: string) {
  if (severity === "low") {
    return "risk-low";
  }
  if (severity === "medium") {
    return "risk-medium";
  }
  return "risk-high";
}

function gateTriageKey(gate: OpenGateDetail) {
  const text = `${gate.gate_id} ${gate.category} ${gate.label} ${gate.summary} ${gate.next_action}`.toLowerCase();
  if (text.includes("outcome") || text.includes("성과") || text.includes("wait")) {
    return "managed-wait";
  }
  if (gate.category === "source_limit" || text.includes("source") || text.includes("원천")) {
    return "source-limit";
  }
  if (
    gate.category === "investment_review"
    || text.includes("benchmark")
    || text.includes("portfolio")
    || text.includes("벤치마크")
    || text.includes("포트폴리오")
  ) {
    return "investment-review";
  }
  if (gate.severity === "high") {
    return "fix-now";
  }
  return "watch";
}

const GATE_TRIAGE_BUCKETS: Omit<GateTriageBucket, "gates">[] = [
  {
    key: "fix-now",
    label: "즉시 조치",
    title: "수집·AI·접근 장애",
    description: "서비스 신뢰도를 직접 낮추는 항목이다. 추천 화면을 보기 전에 먼저 닫는다.",
    tone: "risk-high",
    href: "#runtime-boundary",
  },
  {
    key: "managed-wait",
    label: "관리된 대기",
    title: "성과 측정일까지 기다림",
    description: "문제가 아니라 설계된 대기다. 표본이 성숙하기 전까지 추천 산식 변경을 막는다.",
    tone: "risk-medium",
    href: "#outcome-maturity-wait-monitor",
  },
  {
    key: "source-limit",
    label: "원천 한계",
    title: "원천 데이터 부족",
    description: "합성 재무를 만들지 않고 전문 판단·가상 매매 입력에서 제외한 항목이다.",
    tone: "risk-medium",
    href: "#professional-source-gaps",
  },
  {
    key: "investment-review",
    label: "투자 검토",
    title: "포트폴리오·벤치마크 확인",
    description: "자동 주문이 아니라 검토 기록과 사후 성과 대조가 필요한 항목이다.",
    tone: "risk-medium",
    href: "#investment-quality-details",
  },
  {
    key: "watch",
    label: "관찰",
    title: "운영 확인 항목",
    description: "즉시 장애는 아니지만 다음 배치와 최신 실행 기록을 계속 본다.",
    tone: "risk-low",
    href: "#execution-log",
  },
];

function buildGateTriageBuckets(gates: OpenGateDetail[]) {
  const buckets = GATE_TRIAGE_BUCKETS.map((bucket) => ({ ...bucket, gates: [] as OpenGateDetail[] }));
  for (const gate of gates) {
    const key = gateTriageKey(gate);
    const bucket = buckets.find((candidate) => candidate.key === key) ?? buckets[buckets.length - 1];
    bucket.gates.push(gate);
  }
  return buckets;
}

function gateTriageSummary(buckets: GateTriageBucket[], rawOpenGateCount: number) {
  const fixNowCount = buckets.find((bucket) => bucket.key === "fix-now")?.gates.length ?? 0;
  const managedWaitCount = buckets.find((bucket) => bucket.key === "managed-wait")?.gates.length ?? 0;
  const sourceLimitCount = buckets.find((bucket) => bucket.key === "source-limit")?.gates.length ?? 0;
  if (fixNowCount > 0) {
    return `즉시 조치 ${fixNowCount}개가 있다. 수집·AI·접근 장애를 먼저 닫아야 한다.`;
  }
  if (sourceLimitCount > 0) {
    return `열린 항목 ${rawOpenGateCount}개 중 핵심은 원천 한계다. 합성 재무를 만들지 않고 판단 입력에서 차단한 상태다.`;
  }
  if (managedWaitCount > 0) {
    return `열린 항목 ${rawOpenGateCount}개는 대부분 성과 측정일까지 기다리는 관리된 대기다.`;
  }
  if (rawOpenGateCount > 0) {
    return `열린 확인 항목 ${rawOpenGateCount}개가 있다. 아래 분류에서 조치 위치를 확인한다.`;
  }
  return "현재 열린 확인 항목은 없다. 세부 실행 이력과 최신성만 필요할 때 확인하면 된다.";
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
    return schedulerActivation.scheduler_activation === "installed" ? "반복 실행 중" : "반복 실행 설정됨";
  }
  if (schedulerActivation.status === "pending_manual_approval") {
    return "반복 실행 미설정";
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
    return "서버 반복 실행기 작동 중";
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
    return `서버 예약 실행기가 데이터 수집과 분석 작업을 주기별로 호출한다. 현재 반복 실행기는 ${activeCount}/${timerCount}개가 활성 상태다.`;
  }
  if (activation.activation_allowed && activation.scheduler_activation !== "not_installed") {
    return "승인 조건과 실행기 상태가 반복 실행을 허용한다. 서버 예약 실행기가 작업별 주기에 맞춰 수집과 분석을 호출한다.";
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
    return "가격, 뉴스, 사이클, 보유 상태를 합쳐 추천과 보유 상태 판단을 갱신한다.";
  }
  if (profileId === "market-universe-weekly") {
    return "감시 종목군과 기본 가격 연결 상태를 주간 단위로 정리한다.";
  }
  if (profileId === "macro-weekly") {
    return "거시 지표를 주간 단위로 보강해 큰 시장 사이클 판단에 사용한다.";
  }
  if (profileId === "sec-filings-weekly") {
    return "SEC 공시 기반 기업 이벤트를 주간 단위로 보강한다.";
  }
  if (profileId === "performance-monthly") {
    return "추천과 투자 논리 성과를 월간 단위로 측정한다.";
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

const TIMER_GROUP_DEFINITIONS: TimerGroupDefinition[] = [
  {
    key: "news-ai",
    label: "장중 반복",
    title: "뉴스·AI 분석",
    description: "뉴스 수집, 한국어 번역, AI 구조화, 상위 흐름 전파를 짧은 주기로 갱신한다.",
    profileIds: ["news-intraday"],
  },
  {
    key: "market",
    label: "가격 보강",
    title: "캔들·감시 종목",
    description: "장 마감 후 가격 캔들을 보강하고 감시 종목군의 기본 연결 상태를 확인한다.",
    profileIds: ["market-daily", "market-universe-weekly"],
  },
  {
    key: "decision",
    label: "일간 판단",
    title: "추천·보유 상태",
    description: "가격, 뉴스, 사이클, 보유 상태를 합쳐 추천과 보유 검토 입력을 갱신한다.",
    profileIds: ["decision-daily"],
  },
  {
    key: "macro-disclosure",
    label: "주간 보강",
    title: "거시·공시 데이터",
    description: "거시 지표와 SEC 공시를 보강해 큰 사이클과 기업 이벤트 판단 근거로 쓴다.",
    profileIds: ["macro-weekly", "sec-filings-weekly"],
  },
  {
    key: "performance",
    label: "월간 검증",
    title: "성과 측정",
    description: "추천과 투자 논리의 사후 성과를 측정한다. 추천 산식 변경은 별도 승인 전까지 막는다.",
    profileIds: ["performance-monthly"],
  },
];

function buildSchedulerCadenceGroups(timers: ProfileTimer[]): SchedulerCadenceGroup[] {
  const groups = TIMER_GROUP_DEFINITIONS.map((definition) => ({
    ...definition,
    timers: [] as ProfileTimer[],
  }));
  const otherGroup = {
    key: "other",
    label: "기타",
    title: "기타 예약 작업",
    description: "정의된 운영 묶음에 아직 들어가지 않은 보조 예약 작업이다.",
    profileIds: [] as string[],
    timers: [] as ProfileTimer[],
  };

  for (const timer of timers) {
    const group = groups.find((candidate) => candidate.profileIds.includes(timer.profile_id));
    if (group) {
      group.timers.push(timer);
    } else {
      otherGroup.profileIds.push(timer.profile_id);
      otherGroup.timers.push(timer);
    }
  }

  return [...groups, otherGroup]
    .filter((group) => group.timers.length > 0)
    .map((group) => {
      const activeCount = group.timers.filter((timer) => timer.active_state === "active").length;
      const successCount = group.timers.filter((timer) => timer.last_result === "success").length;
      return {
        ...group,
        activeCount,
        successCount,
        problemCount: group.timers.length - Math.min(activeCount, successCount),
      };
    });
}

function schedulerGroupTone(group: SchedulerCadenceGroup) {
  if (group.problemCount === 0 && group.activeCount === group.timers.length) {
    return "risk-low";
  }
  if (group.activeCount > 0) {
    return "risk-medium";
  }
  return "risk-high";
}

function schedulerGroupStatusLabel(group: SchedulerCadenceGroup) {
  if (group.problemCount === 0 && group.activeCount === group.timers.length) {
    return "정상 대기";
  }
  if (group.activeCount > 0) {
    return "결과 확인 필요";
  }
  return "예약 꺼짐";
}

function schedulerGroupNextElapse(group: SchedulerCadenceGroup) {
  return group.timers.find((timer) => timer.next_elapse)?.next_elapse ?? "다음 실행 미확인";
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
    return "서버 반복 실행 설치 완료";
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
    return "정해진 반복 실행 주기가 끝났고 실패 주기가 없다는 뜻이다. 서버 예약 실행과 함께 자동 운영 상태를 판단한다.";
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
    if (audit.readiness_gaps.length > 0) {
      return `큰 오염은 없지만 ${audit.readiness_gaps[0].label} 단계가 비어 있다. 이 단계가 채워져야 추천 근거 흐름을 끝까지 신뢰할 수 있다.`;
    }
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

function auditSampleRecords(audit: CycleAiQualityAudit, key: string) {
  const value = audit.samples[key];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(isRecord).slice(0, 5);
}

function auditSampleValue(record: AuditSampleRecord, key: string) {
  const value = record[key];
  if (Array.isArray(value)) {
    return value
      .map((item) => auditSampleScalar(item))
      .filter(Boolean)
      .join(", ");
  }
  return auditSampleScalar(value);
}

function auditSampleScalar(value: unknown) {
  if (typeof value === "string") {
    return value.trim();
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "";
}

function auditSampleHeadline(record: AuditSampleRecord) {
  const eventId = auditSampleValue(record, "event_id");
  return (
    auditSampleValue(record, "event_title")
    || auditSampleValue(record, "title")
    || (eventId ? `이벤트 ${eventId}` : "제목 미확인")
  );
}

function auditSampleMeta(record: AuditSampleRecord) {
  const symbol = auditSampleValue(record, "symbol");
  const instrumentName = auditSampleValue(record, "instrument_name");
  const nodeCodes = auditSampleValue(record, "node_codes");
  const nodeCode = auditSampleValue(record, "node_code");
  const direction = auditSampleValue(record, "impact_direction")
    || auditSampleValue(record, "impact_directions");
  const repeatedCount = auditSampleValue(record, "repeated_count");
  return [
    symbol ? `종목 ${symbol}` : "",
    instrumentName ? instrumentName : "",
    nodeCodes ? `흐름 ${nodeCodes.split(", ").map(koCode).join(", ")}` : "",
    nodeCode ? `흐름 ${koCode(nodeCode)}` : "",
    direction ? `방향 ${direction.split(", ").map(koCode).join(", ")}` : "",
    repeatedCount ? `반복 ${repeatedCount}회` : "",
  ].filter(Boolean).join(" · ");
}

function qualityAuditSampleGroups(audit: CycleAiQualityAudit) {
  return [
    {
      key: "duplicate_titles",
      label: "중복 뉴스",
      description: "같은 제목이 반복 수집되어 근거가 부풀려질 수 있는 후보.",
    },
    {
      key: "ungrounded_direct_tickers",
      label: "근거 없는 종목",
      description: "원문 제목·요약에서 종목 근거가 확인되지 않는 직접 연결 후보.",
    },
    {
      key: "macro_false_tickers",
      label: "거시 뉴스 종목 오부착",
      description: "거시 흐름으로 남겨야 하는 뉴스에 직접 종목이 붙은 후보.",
    },
    {
      key: "quantum_energy_mislinks",
      label: "테마 오분류",
      description: "양자컴퓨팅 뉴스가 에너지 흐름이나 XLE/XOM으로 잘못 연결된 후보.",
    },
    {
      key: "normal_macro_flows",
      label: "정상 거시 흐름",
      description: "종목을 억지로 붙이지 않고 상위 흐름으로 처리한 정상 샘플.",
    },
  ].map((group) => ({
    ...group,
    records: auditSampleRecords(audit, group.key),
  })).filter((group) => group.records.length > 0);
}

function newsAiEvalTitle(evalQuality: NewsAiEvalQuality) {
  if (evalQuality.status === "passed" || evalQuality.overall_pass) {
    return "AI 기준 평가 통과";
  }
  if (evalQuality.status === "failed_regression") {
    return "AI 기준 평가 실패";
  }
  if (evalQuality.status === "missing") {
    return "AI 기준 평가 없음";
  }
  return koCode(evalQuality.status);
}

function newsAiEvalExplanation(evalQuality: NewsAiEvalQuality) {
  if (evalQuality.status === "passed" || evalQuality.overall_pass) {
    return "기준 정답 뉴스 세트에서 테마 분류, 직접 종목 근거, 거시 뉴스 종목 오부착, 양자→에너지 오분류, 한국어 번역 기준을 통과했다.";
  }
  if (evalQuality.status === "failed_regression") {
    return "AI 구조화나 자동 검증이 기준 세트에서 실패했다. 이 상태에서는 새 AI 근거를 추천 입력으로 신뢰하기 전에 실패 항목을 먼저 확인해야 한다.";
  }
  if (evalQuality.status === "missing") {
    return "최근 기준 정답 뉴스 평가가 저장되지 않았다. 뉴스 AI 분석이 좋아 보이더라도 기준 세트 통과 여부를 아직 증명하지 못했다.";
  }
  return "뉴스 AI 평가 기록의 상태와 실패 사례를 확인해야 한다.";
}

function newsAiEvalTone(evalQuality: NewsAiEvalQuality) {
  if (evalQuality.status === "passed" || evalQuality.overall_pass) {
    return "risk-low";
  }
  if (evalQuality.status === "missing") {
    return "risk-medium";
  }
  return "risk-high";
}

function liveAiInvocationTitle(health: LiveAiInvocationHealth) {
  if (health.status === "healthy") {
    return "실제 AI 호출 정상";
  }
  if (health.status === "critical_ai_failed") {
    return "실제 AI 호출 실패";
  }
  if (health.status === "degraded") {
    return "일부 AI 호출 실패";
  }
  if (health.status === "recovered_with_recent_failures") {
    return "AI 호출 복구됨";
  }
  if (health.status === "missing_recent_invocations") {
    return "최근 AI 호출 없음";
  }
  return koCode(health.status);
}

function liveAiInvocationExplanation(health: LiveAiInvocationHealth) {
  if (health.status === "healthy") {
    return "최근 실제 Codex OAuth 호출이 성공했다. 기준 세트 평가뿐 아니라 운영 배치 AI 호출도 살아 있다.";
  }
  if (health.status === "critical_ai_failed") {
    return "뉴스 한국어 번역이나 뉴스 AI 구조화 같은 핵심 Codex OAuth 호출이 실패했다. 화면의 뉴스 해석은 규칙 기반 대체 결과일 수 있다.";
  }
  if (health.status === "degraded") {
    return "일부 Codex OAuth 작업의 최신 실행이 실패했다. 성공한 작업과 실패한 작업을 나눠 보고 인증, 토큰, CLI 오류를 확인해야 한다.";
  }
  if (health.status === "recovered_with_recent_failures") {
    return "최근 48시간 안에 실패 이력은 남아 있지만, monitored AI 작업의 최신 실행은 성공했다. 현재 장애가 아니라 복구 후 관찰 상태다.";
  }
  if (health.status === "missing_recent_invocations") {
    return "최근 운영 배치에서 실제 AI 호출 증거가 없다. 뉴스가 없는 것인지, 배치 호출이 멈춘 것인지 확인해야 한다.";
  }
  return "실제 AI 호출 상태를 확인해야 한다.";
}

function liveAiInvocationTone(health: LiveAiInvocationHealth) {
  if (health.status === "healthy") {
    return "risk-low";
  }
  if (health.status === "recovered_with_recent_failures") {
    return "risk-low";
  }
  if (health.status === "degraded" || health.status === "missing_recent_invocations") {
    return "risk-medium";
  }
  return "risk-high";
}

function liveAiCurrentFailureCount(health: LiveAiInvocationHealth) {
  const currentCriticalFailures = Number(health.critical_latest_unhealthy_count ?? 0);
  const currentFailures = Number(health.latest_unhealthy_count ?? 0);
  if (Number.isFinite(currentCriticalFailures) && currentCriticalFailures > 0) {
    return currentCriticalFailures;
  }
  if (Number.isFinite(currentFailures) && currentFailures > 0) {
    return currentFailures;
  }
  return 0;
}

function liveAiInvocationQualityMetric(health: LiveAiInvocationHealth, evalQuality: NewsAiEvalQuality) {
  const regressionText = `기준 실패 ${evalQuality.failed_case_count}개`;
  if (health.status === "recovered_with_recent_failures") {
    return `최신 실행 성공 · 과거 실패 기록 ${health.recent_failed_count}건 · ${regressionText}`;
  }
  if (health.attention_required) {
    return `현재 실패 작업 ${liveAiCurrentFailureCount(health)}개 · 최근 실패 ${health.recent_failed_count}건 · ${regressionText}`;
  }
  if (health.status === "healthy") {
    return `최신 실행 성공 · 최근 실패 ${health.recent_failed_count}건 · ${regressionText}`;
  }
  return `최근 호출 ${health.recent_invocation_count}건 · 최근 실패 ${health.recent_failed_count}건 · ${regressionText}`;
}

function liveAiInvocationHistoryLabel(health: LiveAiInvocationHealth) {
  if (health.status === "recovered_with_recent_failures") {
    return `성공 ${health.recent_success_count} · 과거 실패 기록 ${health.recent_failed_count}`;
  }
  return `성공 ${health.recent_success_count} · 실패 ${health.recent_failed_count}`;
}

function liveAiCurrentFailureDetail(health: LiveAiInvocationHealth) {
  if (health.status === "recovered_with_recent_failures") {
    return `현재 실패 0 · 최근 ${health.window_hours}시간 누적 핵심 실패 ${health.critical_failed_count}`;
  }
  return `번역/뉴스 구조화 기준 · 최근 누적 ${health.critical_failed_count}`;
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
  if (!quality.attention_required && quality.status === "drift_outlier_review") {
    return "큰 괴리 검토 관리 중";
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
    return "구성비 확인률과 기준일이 충분해 벤치마크 대비 괴리를 보조 위험 지표로 볼 수 있다. 추천 산식 반영 비중은 자동 변경하지 않는다.";
  }
  if (!quality.attention_required && quality.status === "drift_outlier_review") {
    return quality.managed_review_reason || "큰 벤치마크 괴리는 확인 대상으로 저장됐고 자동 주문 없이 성과 관찰을 기다린다.";
  }
  if (quality.status === "partial_composition") {
    return "현재 벤치마크 보유종목 일부만 들어와 있다. 괴리 숫자는 계산됐지만 전체 SPY 대비 괴리로 해석하면 안 된다.";
  }
  if (quality.status === "stale_composition") {
    return "벤치마크 구성 기준일이 오래되어 최신 지수 구성과 다를 수 있다. holdings 파일을 다시 적재해야 한다.";
  }
  if (quality.status === "missing_benchmark_composition") {
    return "벤치마크 구성비가 없어 포트폴리오가 SPY와 얼마나 다른지 계산하지 못했다.";
  }
  if (quality.status === "drift_outlier_review") {
    return "벤치마크 대비 전체 괴리 또는 개별 종목 괴리가 커서 포트폴리오 위험 예산 검토가 필요하다.";
  }
  if (quality.status === "missing_guardrail") {
    return "위험 예산 평가가 아직 없어 벤치마크 괴리 품질도 판단할 수 없다.";
  }
  return "벤치마크 괴리 품질 상태를 확인해야 한다.";
}

function benchmarkDriftQualityTone(quality: BenchmarkDriftQuality) {
  if (!quality.attention_required && quality.status === "drift_outlier_review") {
    return "risk-medium";
  }
  if (quality.status === "ok") {
    return "risk-low";
  }
  if (quality.status === "partial_composition" || quality.status === "stale_composition") {
    return "risk-medium";
  }
  return "risk-high";
}

function decisionSeverityClass(severity: string) {
  if (severity === "high") {
    return "risk-high";
  }
  if (severity === "medium") {
    return "risk-medium";
  }
  return "risk-low";
}

function feedbackStatusClass(status: string) {
  if (status === "has_contradictions" || status === "contradicted") {
    return "risk-high";
  }
  if (status === "needs_more_data" || status === "too_early" || status === "missing" || status === "missing_history") {
    return "risk-medium";
  }
  return "risk-low";
}

function calibrationStatusClass(status: string) {
  if (status === "contradiction_review_required") {
    return "risk-high";
  }
  if (
    status === "insufficient_history"
    || status === "collect_more_feedback"
    || status === "missing"
  ) {
    return "risk-medium";
  }
  return "risk-low";
}

function cadenceStatusClass(status: string) {
  if (status === "missing_evidence_review_required") {
    return "risk-high";
  }
  if (status === "run_feedback_now" || status === "run_calibration_now" || status === "missing") {
    return "risk-medium";
  }
  return "risk-low";
}

function actionRouterStatusClass(status: string) {
  if (status.startsWith("blocked_")) {
    return "risk-high";
  }
  if (status === "missing" || status.endsWith("_ready")) {
    return "risk-medium";
  }
  return "risk-low";
}

function actionRouterTitle(router: PortfolioReviewFeedbackActionRouter) {
  if (router.child_runner.executed) {
    return router.route_action === "execute_calibration" ? "누적평가 실행됨" : "사후평가 실행됨";
  }
  if (router.action_status.startsWith("blocked_")) {
    return "가드레일 차단";
  }
  if (router.action_status === "no_op_wait_for_outcome_window") {
    return "성과 관찰 기간 대기";
  }
  if (router.action_status === "no_op_calibration_current") {
    return "최신 평가 유지";
  }
  return koCode(router.action_status);
}

function outcomeCalibrationTitle(calibration: RecommendationOutcomeCalibration) {
  if (calibration.status === "ready_for_manual_weight_review") {
    return "성과 표본 충족";
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
    return "성과 표본과 전문 분석 근거 연결률 기준을 통과했다. 그래도 자동 추천 산식 변경은 금지이고 별도 검토 작업이 필요하다.";
  }
  if (calibration.status === "collect_more_outcomes_keep_weights") {
    return "성과 표본은 있지만 추천 산식 반영 비중을 바꾸기에는 아직 더 많은 성과와 실패 사례가 필요하다.";
  }
  if (calibration.status === "backfill_candidates_remain") {
    return "이미 수집된 가격 이력으로 성과를 더 산출할 수 있다. 추천 품질 평가 전에 성과 보강 작업을 다시 실행해야 한다.";
  }
  if (calibration.status === "price_history_gaps_remain") {
    return "성과를 계산해야 할 추천은 있지만 entry/exit 가격 이력이 부족하다. 캔들 보강이 먼저다.";
  }
  if (calibration.status === "no_due_outcome_window") {
    return "선택한 중장기 기간의 성과 측정일이 아직 오지 않았다. 추천 산식 반영 비중은 그대로 두고 표본이 쌓일 때까지 기다린다.";
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
      ? `${maturity.next_due_date}에 ${maturity.next_due_count}개 추천×기간 성과 측정창이 처음 열린다. 그 전까지 추천 산식 검토는 대기한다.`
      : "아직 성과 측정 가능한 추천×기간이 없다. 추천 산식 검토는 대기한다.";
  }
  if (maturity.status === "due_outcomes_ready") {
    return `${maturity.ready_for_backfill_count}개 추천×기간 성과를 산출할 수 있다. 성과 보강과 누적평가를 먼저 실행해야 한다.`;
  }
  if (maturity.status === "overdue_outcomes_ready") {
    return `${maturity.overdue_count}개 추천×기간 성과 산출이 지연됐다. 추천 산식 검토 전에 성과 보강을 실행해야 한다.`;
  }
  if (maturity.status === "blocked_by_price_gaps") {
    return `${maturity.price_gap_count}개 추천×기간은 가격 이력 부족으로 성과 계산이 막혔다. 캔들 보강이 먼저다.`;
  }
  if (maturity.status === "complete_current_window") {
    return "현재 측정 가능한 성과창은 모두 처리됐다. 다음 측정일 전까지 추천 산식 변경은 하지 않는다.";
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

function outcomeDueActionRouterTitle(router: RecommendationOutcomeDueActionRouter) {
  if (router.child_runner.executed) {
    return "성과 보정 실행됨";
  }
  if (router.action_status === "execute_outcome_calibration_ready") {
    return "성과 보정 실행 대기";
  }
  if (router.action_status === "blocked_by_price_gaps") {
    return "가격 이력 때문에 차단";
  }
  if (router.action_status === "no_op_wait_until_next_due_date") {
    return "다음 측정일까지 대기";
  }
  if (router.action_status === "no_op_current_window_complete") {
    return "현재 측정창 처리 완료";
  }
  if (router.action_status.startsWith("blocked_")) {
    return "가드레일 차단";
  }
  return koCode(router.action_status);
}

function outcomeWaitMonitorTone(monitor: OutcomeMaturityWaitMonitor) {
  if (monitor.status === "action_due" || monitor.status === "blocked_or_missing_evidence") {
    return "risk-high";
  }
  if (monitor.status === "manual_weight_review_possible") {
    return "risk-low";
  }
  return "risk-medium";
}

function professionalSourceGapTitle(gaps: ProfessionalSourceGapPrioritization) {
  if (gaps.status === "ok") {
    return "전문 분석 소스 정상";
  }
  if (!gaps.attention_required && gaps.source_blocker_count > 0) {
    return "원천 한계 관리 중";
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
    return "분석 근거 누락 있음";
  }
  return koCode(gaps.status);
}

function professionalSourceGapExplanation(gaps: ProfessionalSourceGapPrioritization) {
  if (gaps.status === "ok") {
    return "활성 추천 기준으로 핵심 재무·밸류에이션·리서치 원천 공백이 없다.";
  }
  if (!gaps.attention_required && gaps.source_blocker_count > 0) {
    return "원천 데이터가 부족한 종목은 남겨두되, 전문 판단과 가상 매매 검증 입력에서는 이미 차단했다. 새 정기 공시나 전용 parser가 생기면 다시 확인한다.";
  }
  if (gaps.status === "source_blockers_present") {
    return "SEC companyfacts나 원천 공시 연결이 막힌 종목이 있다. 합성 재무를 만들지 말고 원천 가능 여부부터 확인해야 한다.";
  }
  if (gaps.status === "high_priority_gaps") {
    return "추천 또는 보유 노출이 있는 종목의 재무·피어·밸류에이션·리서치 근거가 비어 있다. 이 종목부터 보강한다.";
  }
  if (gaps.status === "fund_source_gaps") {
    return "ETF·펀드형 상품은 기업 재무제표가 아니라 보유종목, 비용, NAV, 추적차이 원천이 판단 근거다.";
  }
  if (gaps.status === "fund_company_model_not_applicable") {
    return "ETF·펀드형 상품은 기업 재무 모델 실패가 아니다. 별도 fund analysis 근거로 검토한다.";
  }
  return "전문가식 분석에 필요한 원천 근거 중 일부가 비어 있어 추천 산식 검토 전 보강해야 한다.";
}

function professionalSourceGapTone(gaps: ProfessionalSourceGapPrioritization) {
  if (!gaps.attention_required) {
    return "risk-low";
  }
  if (gaps.status === "ok" || gaps.status === "fund_company_model_not_applicable") {
    return "risk-low";
  }
  if (gaps.status === "coverage_gaps_present" || gaps.status === "fund_source_gaps") {
    return "risk-medium";
  }
  return "risk-high";
}

function professionalNextActionTone(nextAction: ProfessionalAnalysisNextAction) {
  if (
    nextAction.status === "managed_outcome_wait"
    || nextAction.status === "professional_inputs_ready"
    || nextAction.status === "manual_weight_review_possible"
  ) {
    return "risk-low";
  }
  if (nextAction.status === "outcome_or_weight_review_blocked") {
    return "risk-medium";
  }
  return "risk-high";
}

function professionalQualityTone(quality: ProfessionalAnalysisQuality) {
  if (
    quality.status === "ready_waiting_outcome"
    || quality.status === "ready_for_manual_review"
    || quality.status === "managed_source_limited"
  ) {
    return "risk-low";
  }
  if (quality.status === "coverage_gaps_present") {
    return "risk-medium";
  }
  return "risk-high";
}

function professionalRecommendationAuditTone(audit: ProfessionalRecommendationCoverageAudit) {
  if (audit.status === "ready_for_review") {
    return "risk-low";
  }
  if (audit.status === "paper_validation_pending" || audit.status === "coverage_gaps_present") {
    return "risk-medium";
  }
  return "risk-high";
}

function professionalDepthTitle(depth: ProfessionalAnalysisDepth) {
  if (depth.status === "complete") {
    return "전문 분석 근거 충족";
  }
  if (depth.status === "mostly_covered") {
    return "대부분 갖춰짐";
  }
  if (depth.status === "source_limited") {
    return "원천 한계 포함";
  }
  if (depth.status === "coverage_gaps_present") {
    return "분석 근거 보강 필요";
  }
  if (depth.status === "missing_active_candidates") {
    return "활성 후보 없음";
  }
  return koCode(depth.status);
}

function professionalDepthTone(depth: ProfessionalAnalysisDepth) {
  if (depth.status === "complete" || depth.status === "mostly_covered") {
    return "risk-low";
  }
  if (depth.status === "source_limited") {
    return "risk-medium";
  }
  return "risk-high";
}

function professionalDepthStatusLabel(status: string) {
  if (status === "complete") {
    return "완비";
  }
  if (status === "mostly_covered") {
    return "대부분 완비";
  }
  if (status === "source_blocked") {
    return "원천 차단";
  }
  if (status === "partial") {
    return "일부 부족";
  }
  if (status === "fund_source_ready") {
    return "펀드 근거 준비";
  }
  return koCode(status);
}

function professionalDepthItemTone(status: string) {
  if (status === "complete" || status === "fund_source_ready") {
    return "risk-low";
  }
  if (status === "mostly_covered" || status === "partial") {
    return "risk-medium";
  }
  return "risk-high";
}

function professionalRecommendationAuditItemTone(status: string) {
  if (status === "ready_for_review") {
    return "risk-low";
  }
  if (status === "paper_validation_pending" || status === "coverage_gap") {
    return "risk-medium";
  }
  return "risk-high";
}

function executionIdLabel(value: string | null | undefined) {
  if (!value || value.includes("unknown")) {
    return "실행 기록 없음";
  }
  if (value.startsWith("eval-run-")) {
    return `평가 #${value.replace("eval-run-", "")}`;
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

function operationCopy(value: string) {
  const oldHoldingReviewCompact = ["보유", "검토"].join("");
  const oldHoldingReview = ["보유", "검토"].join(" ");
  const oldReviewCandidate = ["검토", "후보"].join(" ");
  const oldReviewDocument = ["검토", "서"].join("");
  const oldPaper = ["페", "이퍼"].join("");
  return koCode(value)
    .replaceAll("news-ai-eval-run --provider fixture --execute를 실행해 기준 정답 뉴스 세트 회귀평가를 저장한다.", "뉴스 AI 기준 세트 평가를 실행해 최근 평가 결과를 저장한다.")
    .replaceAll("fixture/gold", "기준 정답")
    .replaceAll("fixture", "기준 세트")
    .replaceAll("fallback", "대체 처리")
    .replaceAll("validator", "자동 검증")
    .replaceAll("ticker", "종목 코드")
    .replaceAll("unknown theme", "알 수 없는 테마")
    .replaceAll("case", "평가 항목")
    .replaceAll("EC2", "서버")
    .replaceAll("artifact runner", "실행 증거 저장기")
    .replaceAll("artifact", "실행 증거")
    .replaceAll("profile scheduler", "프로파일 예약 실행기")
    .replaceAll("pipeline run health", "작업 실행 상태")
    .replaceAll("data operation", "데이터 작업")
    .replaceAll("recommendation weight", "추천 산식 반영 비중")
    .replaceAll("weight review", "추천 산식 검토")
    .replaceAll("weight", "추천 산식 반영 비중")
    .replaceAll("broker submit", "실거래 주문 제출")
    .replaceAll("broker", "증권사 연결")
    .replaceAll("outcome", "성과")
    .replaceAll("paper validation", "가상 매매 검증")
    .replaceAll("thesis", "투자 논리")
    .replaceAll("feedback", "사후평가")
    .replaceAll("calibration", "누적평가")
    .replaceAll("cadence", "실행 주기")
    .replaceAll("router", "실행 분기")
    .replaceAll("child runner", "후속 실행")
    .replaceAll("open gate", "열린 확인 항목")
    .replaceAll("review candidate", "확인 대상")
    .replaceAll("candidate", "대상")
    .replaceAll(oldHoldingReviewCompact, "보유 상태 판단")
    .replaceAll(oldHoldingReview, "보유 상태 판단")
    .replaceAll(oldReviewCandidate, "확인 대상")
    .replaceAll(oldReviewDocument, "상세 근거")
    .replaceAll("guardrail", "안전 조건")
    .replaceAll("source gap", "원천 공백")
    .replaceAll("source blocker", "원천 차단")
    .replaceAll("quality eval", "품질 평가")
    .replaceAll("managed wait", "관리된 대기")
    .replaceAll("coverage", "근거 연결률")
    .replaceAll("커버리지", "연결률")
    .replaceAll(oldPaper, "가상 매매")
    .replaceAll("가중치", "반영 비중")
    .replaceAll("drift", "괴리")
    .replaceAll("주문 경계", "실거래 상태")
    .replaceAll("active", "활성")
    .replaceAll("boundary", "경계")
    .replaceAll("managed", "관리됨")
    .replaceAll("source", "원천")
    .replaceAll("job", "작업")
    .replaceAll("원천 차단 count가 있는 종목", "원천 차단 종목")
    .replaceAll("원천 차단 count", "원천 차단 수")
    .replaceAll("degraded", "주의");
}

function openGateCopy(value: string) {
  return operationCopy(value)
    .replaceAll("_", " ")
    .replace(/\bcount\b/g, "수")
    .replaceAll("원천 차단 수가 있는 종목", "원천 차단 종목");
}

function aiInvocationErrorCopy(value: string, code = "") {
  if (!value) {
    return "최근 오류 없음";
  }
  if (
    code === "codex_oauth_auth_invalid"
    || code === "codex_oauth_auth_invalidated"
    || value.includes("token_invalidated")
    || value.includes("refresh_token_reused")
    || value.includes("401 Unauthorized")
  ) {
    return "Codex OAuth 인증 토큰이 만료되었거나 재사용되어 실패했다. 서버에서 다시 로그인한 뒤 실제 호출 점검을 실행해야 한다.";
  }
  if (code === "codex_oauth_timeout" || value.includes("timeout")) {
    return "Codex OAuth 호출 시간이 초과됐다. limit와 timeout, 네트워크 상태를 확인해야 한다.";
  }
  return operationCopy(value);
}

function orderSubmitCopy(allowed: boolean) {
  return `실거래 주문 ${allowed ? "허용" : "금지"}`;
}

function orderBoundaryCopy(value: string | null | undefined) {
  if (!value) {
    return "실거래 상태 미확인";
  }
  if (value === "read_only_no_order") {
    return "읽기 전용, 실거래 주문 차단";
  }
  return operationCopy(value);
}

function recordLabel(value: string | null | undefined) {
  return value ? "기록 있음" : "기록 없음";
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
  readiness_gaps: [],
  metrics: {},
  checks: {},
  samples: {},
  next_actions: ["cycle-ai-quality-audit-run 실행 결과를 연결한다."],
  source: "not_configured",
};

const DEFAULT_NEWS_AI_EVAL_QUALITY: NewsAiEvalQuality = {
  status: "missing",
  eval_run_id: "eval-run-unknown",
  created_at: "",
  eval_name: "news_ai_extraction_quality",
  dataset_version: "news-ai-eval-v1",
  provider: "fixture",
  model_name: "news-ai-eval-fixture-v1",
  overall_pass: false,
  case_count: 0,
  passed_case_count: 0,
  failed_case_count: 0,
  theme_precision: 0,
  direct_ticker_grounding_precision: 0,
  macro_only_false_ticker_rate: 0,
  macro_only_false_ticker_count: 0,
  quantum_energy_misclassification_count: 0,
  blocked_candidate_correctness: 0,
  korean_translation_availability: 0,
  metrics: {},
  pass_thresholds: {},
  case_results: [],
  next_action: "news-ai-eval-run --provider fixture --execute를 실행해 기준 정답 뉴스 세트 회귀평가를 저장한다.",
};

const DEFAULT_LIVE_AI_INVOCATION_HEALTH: LiveAiInvocationHealth = {
  status: "missing_recent_invocations",
  attention_required: true,
  window_hours: 48,
  recent_invocation_count: 0,
  recent_success_count: 0,
  recent_failed_count: 0,
  critical_failed_count: 0,
  critical_success_count: 0,
  latest_unhealthy_count: 0,
  critical_latest_unhealthy_count: 0,
  latest_invocation_at: "",
  latest_failed_at: "",
  latest_failed_task_name: "",
  latest_error_summary: "",
  latest_error_code: "",
  task_health: [],
  next_action: "최근 실제 AI 호출 증거가 없다. 뉴스 AI 배치가 실제로 호출됐는지 확인한다.",
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
  outlier_decisions: [],
  review_candidate_count: 0,
  review_decision_counts: {},
  attention_required: true,
  managed_review_status: "source_or_guardrail_gap",
  managed_review_reason: "위험 예산 평가가 아직 없어 벤치마크 drift 관리 상태를 판단할 수 없다.",
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
  checks: [],
  next_actions: ["portfolio-risk-budget-guardrail-run을 먼저 실행한다."],
};

const DEFAULT_PORTFOLIO_REVIEW_DECISION_HISTORY: PortfolioReviewDecisionHistory = {
  status: "missing",
  eval_run_id: "eval-run-unknown",
  created_at: "",
  eval_name: "portfolio_review_decision_history",
  dataset_version: "portfolio-review-decision-history-v1",
  as_of_date: "",
  portfolio_name: "Long Term Paper",
  source_portfolio_coverage_as_of_date: "",
  coverage_measurement_end_date: "",
  decision_status: "missing",
  decision_count: 0,
  review_required_count: 0,
  benchmark_decision_count: 0,
  position_sizing_decision_count: 0,
  decision_counts: {},
  attention_required: true,
  managed_review_status: "unmanaged_or_missing",
  managed_review_reason: "검토 이력, 안전 조건, 또는 후속 실행 분기 상태를 확인해야 한다.",
  top_decision: null,
  latest_decisions: [],
  guardrails: {
    recommendation_scoring_mutated: false,
    benchmark_definition_mutated: false,
    portfolio_position_mutated: false,
    automatic_rebalance_allowed: false,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
  },
  next_action: "portfolio-review-decision-history-run을 실행해 최신 포트폴리오 검토 결정을 이력화한다.",
};

const DEFAULT_PORTFOLIO_REVIEW_DECISION_FEEDBACK: PortfolioReviewDecisionFeedback = {
  status: "missing",
  eval_run_id: "eval-run-unknown",
  created_at: "",
  eval_name: "portfolio_review_decision_outcome_feedback",
  dataset_version: "portfolio-review-decision-outcome-feedback-v1",
  as_of_date: "",
  portfolio_name: "Long Term Paper",
  source_history_eval_run_id: "eval-run-unknown",
  source_history_as_of_date: "",
  min_horizon_days: 30,
  history_age_days: 0,
  feedback_status: "missing",
  decision_count: 0,
  too_early_count: 0,
  validated_count: 0,
  contradicted_count: 0,
  needs_more_data_count: 0,
  status_counts: {},
  paper_validation: {
    paper_validation_run_id: "paper-validation-unknown",
    validation_date: "",
    status: "missing",
    recommendation_count: 0,
    conflict_count: 0,
    approved_action_count: 0,
  },
  top_feedback: null,
  latest_items: [],
  guardrails: {
    recommendation_scoring_mutated: false,
    benchmark_definition_mutated: false,
    portfolio_position_mutated: false,
    automatic_rebalance_allowed: false,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
  },
  next_action: "portfolio-review-decision-outcome-feedback-run을 실행해 저장된 검토 결정이 후속 성과와 맞는지 확인한다.",
};

const DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CALIBRATION: PortfolioReviewFeedbackCalibration = {
  status: "missing",
  eval_run_id: "eval-run-unknown",
  created_at: "",
  eval_name: "portfolio_review_feedback_calibration",
  dataset_version: "portfolio-review-feedback-calibration-v1",
  as_of_date: "",
  portfolio_name: "Long Term Paper",
  lookback_days: 0,
  min_feedback_runs: 0,
  min_mature_decisions: 0,
  max_contradiction_rate: 0,
  calibration_status: "missing",
  maturity_status: "missing_calibration",
  feedback_run_count: 0,
  decision_count: 0,
  mature_decision_count: 0,
  too_early_count: 0,
  validated_count: 0,
  contradicted_count: 0,
  needs_more_data_count: 0,
  contradiction_rate: 0,
  validated_rate: 0,
  feedback_run_gap: 0,
  mature_decision_gap: 0,
  estimated_maturity_date: "",
  days_until_maturity: null,
  attention_required: true,
  managed_wait: false,
  managed_gate_status: "unmanaged_attention",
  managed_gate_reason: "",
  weight_review_blocked: true,
  weight_review_block_reason: "검토 성과 누적평가 기록이 없어 추천 산식 검토를 막는다.",
  status_counts: {},
  family_summaries: [],
  decision_type_summaries: [],
  symbol_summaries: [],
  latest_feedback_runs: [],
  guardrails: {
    recommendation_scoring_mutated: false,
    benchmark_definition_mutated: false,
    portfolio_position_mutated: false,
    automatic_rebalance_allowed: false,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
  },
  next_action: "포트폴리오 검토 누적평가를 실행해 누적 검토 사후평가 신뢰도를 집계한다.",
  next_calibration_action: "검토 이력과 사후평가를 먼저 누적한다.",
};

const DEFAULT_PROFESSIONAL_ANALYSIS_NEXT_ACTION: ProfessionalAnalysisNextAction = {
  status: "missing",
  title: "전문 분석 상태 없음",
  summary: "전문 분석 원천 공백, 성과 사후평가, 추천 산식 검토 상태를 아직 읽지 못했다.",
  next_action: "전문 분석 data-health payload를 먼저 생성한다.",
  as_of_date: "",
  source_gap_count: 0,
  source_blocker_count: 0,
  average_coverage_ratio: 0,
  guarded_source_blocked_recommendation_count: 0,
  managed_wait: false,
  weight_review_blocked: true,
  manual_weight_review_allowed: false,
  estimated_maturity_date: "",
  days_until_maturity: null,
  next_symbol: "",
  next_symbol_href: "",
  next_symbol_reason: "",
  readiness_items: [],
  order_boundary: "read_only_no_order",
  automatic_weight_change_allowed: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
};

const DEFAULT_PROFESSIONAL_ANALYSIS_QUALITY: ProfessionalAnalysisQuality = {
  status: "missing",
  title: "전문 분석 품질 상태 없음",
  summary: "재무·피어·밸류에이션·산업·AI 리서치 근거 연결 상태를 아직 읽지 못했다.",
  as_of_date: "",
  active_candidate_count: 0,
  complete_candidate_count: 0,
  source_blocked_count: 0,
  average_coverage_ratio: 0,
  layer_checks: [],
  quality_checks: [],
  next_action: "전문 분석 품질 payload를 먼저 생성한다.",
  manual_weight_review_allowed: false,
  automatic_weight_change_allowed: false,
  recommendation_scoring_mutated: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
};

const DEFAULT_PROFESSIONAL_RECOMMENDATION_COVERAGE_AUDIT: ProfessionalRecommendationCoverageAudit = {
  status: "missing",
  title: "추천별 전문 감사 상태 없음",
  summary: "active 추천별 재무·피어·밸류에이션·산업·AI 리서치 연결 상태를 아직 읽지 못했다.",
  as_of_date: "",
  recommendation_count: 0,
  ready_for_review_count: 0,
  coverage_gap_count: 0,
  source_blocked_count: 0,
  paper_validation_pending_count: 0,
  average_coverage_ratio: 0,
  items: [],
  next_action: "추천별 전문 분석 coverage audit payload를 먼저 생성한다.",
  recommendation_scoring_mutated: false,
  automatic_weight_change_allowed: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
};

const DEFAULT_PROFESSIONAL_ANALYSIS_DEPTH: ProfessionalAnalysisDepth = {
  status: "missing",
  as_of_date: "",
  active_candidate_count: 0,
  complete_candidate_count: 0,
  source_blocked_count: 0,
  fund_like_candidate_count: 0,
  operating_company_candidate_count: 0,
  average_coverage_ratio: 0,
  weakest_coverage_ratio: 0,
  layer_coverage: [],
  items: [],
  next_action: "활성 추천의 전문 분석 깊이를 먼저 계산한다.",
  recommendation_scoring_mutated: false,
  automatic_weight_change_allowed: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
};

const DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CADENCE: PortfolioReviewFeedbackCadence = {
  status: "missing",
  eval_run_id: "eval-run-unknown",
  created_at: "",
  eval_name: "portfolio_review_feedback_cadence",
  dataset_version: "portfolio-review-feedback-cadence-v1",
  as_of_date: "",
  portfolio_name: "Long Term Paper",
  min_horizon_days: 30,
  cadence_status: "missing",
  action_type: "inspect",
  should_run_now: false,
  should_wait: false,
  wait_until: "",
  command: "포트폴리오 검토 실행 주기를 계산해 다음 사후평가/누적평가 작업을 판단한다.",
  follow_up_command: "",
  label: "검토 사후평가 실행 주기 상태를 먼저 계산한다.",
  reason: "아직 포트폴리오 검토 사후평가 실행 주기 기록이 없다.",
  history: {
    status: "missing",
    eval_run_id: "eval-run-unknown",
    created_at: "",
    as_of_date: "",
    decision_status: "missing",
    decision_count: 0,
    review_required_count: 0,
  },
  feedback: {
    status: "missing",
    eval_run_id: "eval-run-unknown",
    created_at: "",
    as_of_date: "",
    source_history_eval_run_id: "eval-run-unknown",
    source_history_as_of_date: "",
    feedback_status: "missing",
    decision_count: 0,
    too_early_count: 0,
    validated_count: 0,
    contradicted_count: 0,
    needs_more_data_count: 0,
  },
  calibration: {
    status: "missing",
    eval_run_id: "eval-run-unknown",
    created_at: "",
    as_of_date: "",
    calibration_status: "missing",
    feedback_run_count: 0,
    decision_count: 0,
    mature_decision_count: 0,
    too_early_count: 0,
    validated_count: 0,
    contradicted_count: 0,
    needs_more_data_count: 0,
    latest_feedback_run_ids: [],
  },
  evidence: {
    history_age_days: 0,
    decision_count: 0,
    recommendation_link_count: 0,
    recommendation_outcome_count: 0,
    price_evidence_count: 0,
    paper_validation: {
      paper_validation_run_id: "paper-validation-unknown",
      validation_date: "",
      status: "missing",
      recommendation_count: 0,
      conflict_count: 0,
      approved_action_count: 0,
    },
  },
  blocks_weight_review: true,
  recommendation_scoring_mutated: false,
  benchmark_definition_mutated: false,
  portfolio_position_mutated: false,
  automatic_weight_change_allowed: false,
  automatic_rebalance_allowed: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
  next_action: "포트폴리오 검토 실행 주기를 계산해 다음 사후평가/누적평가 작업을 판단한다.",
};

const DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_ACTION_ROUTER: PortfolioReviewFeedbackActionRouter = {
  status: "missing",
  eval_run_id: "eval-run-unknown",
  created_at: "",
  eval_name: "portfolio_review_feedback_action_router",
  dataset_version: "portfolio-review-feedback-action-router-v1",
  as_of_date: "",
  portfolio_name: "Long Term Paper",
  source_cadence_status: "missing",
  source_cadence_eval_run_id: "eval-run-unknown",
  source_cadence_created_at: "",
  source_cadence_as_of_date: "",
  cadence_status: "missing",
  source_action_type: "inspect",
  source_should_run_now: false,
  route_action: "no_op",
  action_status: "missing",
  reason: "아직 포트폴리오 검토 실행 분기 기록이 없다.",
  history_eval_run_id: "eval-run-unknown",
  feedback_eval_run_id: "eval-run-unknown",
  calibration_eval_run_id: "eval-run-unknown",
  source_cadence: {
    as_of_date: "",
    cadence_status: "missing",
    action_type: "inspect",
    should_run_now: false,
    should_wait: false,
    command: "",
    follow_up_command: "",
  },
  child_runner: {
    executed: false,
    report_name: "",
    status: "not_run",
    run_id: "pipeline-run-unknown",
    eval_run_id: "eval-run-unknown",
    feedback_status: "",
    calibration_status: "",
  },
  recommendation_scoring_mutated: false,
  benchmark_definition_mutated: false,
  portfolio_position_mutated: false,
  automatic_weight_change_allowed: false,
  automatic_rebalance_allowed: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
  next_action: "포트폴리오 검토 실행 분기를 실행해 실행 주기 판단을 안전한 후속 작업으로 연결한다.",
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

const DEFAULT_RECOMMENDATION_OUTCOME_DUE_ACTION_ROUTER: RecommendationOutcomeDueActionRouter = {
  status: "missing",
  eval_run_id: "eval-run-unknown",
  created_at: "",
  eval_name: "recommendation_outcome_due_action_router",
  dataset_version: "recommendation-outcome-due-action-router-v1",
  as_of_date: "",
  source_calibration_status: "missing",
  source_calibration_eval_run_id: "eval-run-unknown",
  source_calibration_created_at: "",
  source_calibration_summary: {
    as_of_date: "",
    status: "missing",
    quality_status: "unknown",
    sample_status: "unknown",
    next_action: "",
    recommendation_scoring_mutated: false,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
  },
  route_action: "no_op",
  action_status: "missing",
  reason: "아직 추천 성과 실행 분기 기록이 없다.",
  wait_until: "",
  sample_audit_summary: {
    recommendation_horizon_count: 0,
    recommendation_count: 0,
    outcome_count: 0,
    ready_for_backfill_count: 0,
    not_due_count: 0,
    missing_entry_price_count: 0,
    missing_exit_price_count: 0,
    price_gap_count: 0,
    outcome_coverage_rate: 0,
  },
  missing_reason_counts: {},
  missing_examples: [],
  child_runner: {
    executed: false,
    report_name: "",
    status: "not_run",
    run_id: "pipeline-run-unknown",
    eval_run_id: "eval-run-unknown",
    calibration_status: "",
    quality_status: "",
    sample_status: "",
  },
  recommendation_scoring_mutated: false,
  benchmark_definition_mutated: false,
  portfolio_position_mutated: false,
  automatic_weight_change_allowed: false,
  automatic_rebalance_allowed: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
  next_action: "recommendation-outcome-due-action-router-run을 실행한다.",
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
  blocker_message: "추천 산식 검토 준비 감사 작업을 실행한다.",
  next_action: "추천 산식 검토 준비 감사 작업을 실행한다.",
  automatic_weight_change_allowed: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
};

const DEFAULT_OUTCOME_MATURITY_WAIT_MONITOR: OutcomeMaturityWaitMonitor = {
  status: "missing",
  title: "성과 성숙 상태 없음",
  summary: "추천 성과와 포트폴리오 사후평가 성숙 상태를 아직 읽지 못했다.",
  next_action: "성과 성숙 데이터 상태 기록을 먼저 생성한다.",
  as_of_date: "",
  recommendation_next_due_date: "",
  recommendation_next_due_count: 0,
  recommendation_maturity_status: "missing",
  recommendation_action_status: "missing",
  recommendation_ready_for_backfill_count: 0,
  recommendation_overdue_count: 0,
  recommendation_price_gap_count: 0,
  portfolio_feedback_maturity_date: "",
  portfolio_feedback_status: "missing",
  portfolio_feedback_run_gap: 0,
  portfolio_mature_decision_gap: 0,
  earliest_action_date: "",
  wait_item_count: 0,
  wait_items: [],
  weight_review_blocked: true,
  weight_review_block_reason: "성과 성숙 상태가 없어 추천 산식 검토를 막는다.",
  manual_weight_review_allowed: false,
  recommendation_scoring_mutated: false,
  benchmark_definition_mutated: false,
  portfolio_position_mutated: false,
  automatic_weight_change_allowed: false,
  automatic_rebalance_allowed: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
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
  guarded_source_blocked_recommendation_count: 0,
  attention_required: false,
  top_priority_score: 0,
  gaps: [],
  next_action: "전문 분석 원천 공백을 먼저 계산한다.",
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

const DEFAULT_PRODUCTION_API_SERVER: ProductionApiServer = {
  status: "missing_runtime_evidence",
  attention_required: true,
  service: "frontend-api-server",
  runtime_profile: "unknown",
  source_mode: "unknown",
  auth_mode: "unknown",
  read_auth_required: false,
  read_token_configured: false,
  allowed_origin_configured: false,
  database_configured: false,
  connection_boundary: "missing_executor",
  request_timeout_seconds: 30,
  read_only: true,
  missing_conditions: ["runtime_profile_production", "read_token_auth", "psycopg_pool_boundary"],
  order_boundary: "read_only_no_order",
  automatic_action_allowed: false,
  next_action: "읽기 서버 실행 환경, 조회 권한, 허용 출처, DB 설정, DB 연결 경계를 확인한다.",
};

const DEFAULT_AUTH_RBAC: AuthRbac = {
  status: "missing_rbac_evidence",
  attention_required: true,
  mode: "disabled",
  auth_mode: "unknown",
  read_role: "viewer",
  read_allowed_roles: ["viewer", "analyst", "operator", "admin"],
  read_token_configured: false,
  role_valid: true,
  protected_paths: ["/__endpoints", "/api/*"],
  public_paths: ["/__live", "/__health", "/__ready"],
  allowed_methods: ["GET", "HEAD", "OPTIONS"],
  write_methods_allowed: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
  missing_conditions: ["production_api_ready", "bearer_read_token", "read_only_rbac_mode"],
  summary: "읽기 서버의 읽기 토큰, 조회 역할, 쓰기/주문 차단 경계 증거가 아직 부족하다.",
  next_action: "읽기 서버 준비, 읽기 토큰, 조회 역할, 쓰기 요청 차단, 증권사 주문 차단을 확인한다.",
};

const DEFAULT_ALERT_DESTINATION: AlertDestination = {
  status: "missing_destination",
  attention_required: true,
  mode: "missing",
  destination_type: "unknown",
  external_destination: false,
  local_only: false,
  target_configured: false,
  status_artifact_configured: false,
  status_artifact_loaded: false,
  last_test_status: "missing",
  last_tested_at: "",
  test_recent: false,
  test_age_hours: null,
  max_test_age_hours: 168,
  missing_conditions: ["external_alert_destination", "alert_target_configured", "alert_test_passed"],
  summary: "예약 실행 실패와 데이터 오염을 받을 외부 알림 목적지가 설정되지 않았다.",
  next_action: "무료 webhook, email, Telegram, Slack, Discord 중 하나를 저장소 밖 환경 파일에 설정하고 테스트 기록을 남긴다.",
  order_boundary: "read_only_no_order",
  automatic_action_allowed: false,
};

const DEFAULT_DATA_OPERATIONS_ARTIFACT_RUNNER: DataOperationsArtifactRunner = {
  status: "missing_pipeline_evidence",
  attention_required: true,
  job_count: 0,
  artifact_policy_count: 0,
  latest_run_count: 0,
  failed_or_missing_count: 0,
  degraded_count: 0,
  profile_scheduler_installed: false,
  timer_count: 0,
  active_timer_count: 0,
  manual_smoke_status: "missing",
  local_worker_status: "missing",
  latest_artifact_root: "",
  order_boundary: "read_only_no_order",
  automatic_action_allowed: false,
  next_action: "실행 증거 저장기를 통해 성공한 데이터 작업 기록을 먼저 생성한다.",
};

const DEFAULT_ACTIVE_RECOMMENDATION_PRICE_FRESHNESS: ActiveRecommendationPriceFreshness = {
  status: "missing",
  attention_required: true,
  active_symbol_count: 0,
  fresh_symbol_count: 0,
  stale_symbol_count: 0,
  missing_symbol_count: 0,
  stale_recommendation_count: 0,
  missing_recommendation_count: 0,
  global_latest_trade_date: "",
  stale_after_days: 7,
  max_days_behind_latest: 0,
  stale_symbols: [],
  next_action: "active 추천 종목 가격 최신성 감사를 먼저 생성한다.",
  recommendation_scoring_mutated: false,
  automatic_order_allowed: false,
  broker_submit_allowed: false,
  order_boundary: "read_only_no_order",
};

export default async function DataHealthPage() {
  const response = await getDataHealth();
  const data = response.data;
  const providerBudget = data.provider_budget;
  const productionApiServer = data.production_api_server ?? DEFAULT_PRODUCTION_API_SERVER;
  const authRbac = data.auth_rbac ?? DEFAULT_AUTH_RBAC;
  const alertDestination = data.alert_destination ?? DEFAULT_ALERT_DESTINATION;
  const artifactRunner = data.data_operations_artifact_runner ?? DEFAULT_DATA_OPERATIONS_ARTIFACT_RUNNER;
  const activeRecommendationPriceFreshness =
    data.active_recommendation_price_freshness ?? DEFAULT_ACTIVE_RECOMMENDATION_PRICE_FRESHNESS;
  const schedulerActivation = data.scheduler.activation;
  const profileScheduler = data.scheduler.profile_scheduler ?? DEFAULT_PROFILE_SCHEDULER;
  const ec2SchedulerInstalled = isEc2ProfileSchedulerInstalled(data.scheduler);
  const manualSmoke = data.manual_local_ingest_smoke ?? DEFAULT_MANUAL_SMOKE;
  const localWorker = data.local_ingest_worker ?? DEFAULT_LOCAL_WORKER;
  const qualityAudit = data.cycle_ai_quality_audit ?? DEFAULT_CYCLE_AI_QUALITY_AUDIT;
  const qualityAuditSamples = qualityAuditSampleGroups(qualityAudit);
  const newsAiEvalQuality = data.news_ai_eval_quality ?? DEFAULT_NEWS_AI_EVAL_QUALITY;
  const liveAiInvocationHealth = data.live_ai_invocation_health ?? DEFAULT_LIVE_AI_INVOCATION_HEALTH;
  const benchmarkDriftQuality = data.benchmark_drift_quality ?? DEFAULT_BENCHMARK_DRIFT_QUALITY;
  const portfolioReviewHistory =
    data.portfolio_review_decision_history ?? DEFAULT_PORTFOLIO_REVIEW_DECISION_HISTORY;
  const portfolioReviewFeedback =
    data.portfolio_review_decision_feedback ?? DEFAULT_PORTFOLIO_REVIEW_DECISION_FEEDBACK;
  const portfolioReviewCalibration =
    data.portfolio_review_feedback_calibration ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CALIBRATION;
  const portfolioReviewCadence =
    data.portfolio_review_feedback_cadence ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CADENCE;
  const portfolioReviewActionRouter =
    data.portfolio_review_feedback_action_router ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_ACTION_ROUTER;
  const benchmarkDriftDecisionBySymbol = new Map(
    benchmarkDriftQuality.outlier_decisions.map((decision) => [decision.symbol, decision]),
  );
  const outcomeCalibration =
    data.recommendation_outcome_calibration ?? DEFAULT_RECOMMENDATION_OUTCOME_CALIBRATION;
  const outcomeMaturity = data.recommendation_outcome_maturity ?? DEFAULT_RECOMMENDATION_OUTCOME_MATURITY;
  const outcomeDueActionRouter =
    data.recommendation_outcome_due_action_router ?? DEFAULT_RECOMMENDATION_OUTCOME_DUE_ACTION_ROUTER;
  const weightReviewReadiness =
    data.recommendation_weight_review_readiness ?? DEFAULT_RECOMMENDATION_WEIGHT_REVIEW_READINESS;
  const outcomeWaitMonitor =
    data.outcome_maturity_wait_monitor ?? DEFAULT_OUTCOME_MATURITY_WAIT_MONITOR;
  const professionalSourceGaps =
    data.professional_source_gap_prioritization ?? DEFAULT_PROFESSIONAL_SOURCE_GAP_PRIORITIZATION;
  const professionalQuality =
    data.professional_analysis_quality ?? DEFAULT_PROFESSIONAL_ANALYSIS_QUALITY;
  const professionalRecommendationAudit =
    data.professional_recommendation_coverage_audit ?? DEFAULT_PROFESSIONAL_RECOMMENDATION_COVERAGE_AUDIT;
  const professionalDepth =
    data.professional_analysis_depth ?? DEFAULT_PROFESSIONAL_ANALYSIS_DEPTH;
  const professionalNextAction =
    data.professional_analysis_next_action ?? DEFAULT_PROFESSIONAL_ANALYSIS_NEXT_ACTION;
  const openGateDetails = data.open_gate_details ?? [];
  const gateTriageBuckets = buildGateTriageBuckets(openGateDetails);
  const visibleGateTriageBuckets = gateTriageBuckets.filter((bucket) => bucket.gates.length > 0);
  const gateTriageStatus = gateTriageSummary(gateTriageBuckets, data.open_gates.length);
  const openGateChips = openGateDetails.length > 0
    ? openGateDetails.map((gate) => ({
        key: gate.gate_id,
        label: gate.label,
        tone: gateSeverityTone(gate.severity),
      }))
    : data.open_gates.map((gate) => ({
        key: gate,
        label: operationCopy(koCode(gate)).replaceAll("_", " "),
        tone: "risk-medium",
      }));
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
  const schedulerCadenceGroups = buildSchedulerCadenceGroups(profileScheduler.timers);
  const accessAttention =
    productionApiServer.attention_required || authRbac.attention_required || alertDestination.attention_required;
  const allTimersActive =
    profileScheduler.timer_count > 0 && profileScheduler.active_timer_count === profileScheduler.timer_count;
  const dataQualityReady =
    qualityAuditTone(qualityAudit) === "risk-low"
    && newsAiEvalTone(newsAiEvalQuality) === "risk-low"
    && liveAiInvocationTone(liveAiInvocationHealth) === "risk-low";
  const safeInvestmentBoundary =
    outcomeWaitMonitor.weight_review_blocked
    && !outcomeWaitMonitor.automatic_weight_change_allowed
    && !outcomeWaitMonitor.broker_submit_allowed;
  const operationVerdictCards = [
    {
      index: "01",
      label: "서비스 접근",
      title: accessAttention ? "접근 경계 확인 필요" : "읽기 전용 접근 정상",
      body: accessAttention
        ? "읽기 서버, 조회 권한, 알림 목적지 중 주의 항목이 있다. 투자 판단 화면보다 접근 경계 확인이 먼저다."
        : "읽기 전용 API, 역할 기반 조회 권한, 무료 알림 목적지가 연결되어 있고 주문/쓰기 경계는 닫혀 있다.",
      metric: authRbac.read_role ? `역할 ${koCode(authRbac.read_role)}` : "읽기 역할 확인",
      href: "#execution-log",
      cta: "접근 경계 보기",
      tone: accessAttention ? "watch" : "ready",
    },
    {
      index: "02",
      label: "자동 수집",
      title: allTimersActive && failedPipelines === 0 ? "자동 수집 작동 중" : "수집 상태 확인 필요",
      body: allTimersActive
        ? "뉴스, 가격, 추천, 성과 측정 작업이 서버 예약 실행기로 분리되어 돈다."
        : "예약 실행기 일부가 꺼졌거나 실행 증거가 부족하다. 어떤 작업 묶음이 멈췄는지 확인해야 한다.",
      metric: `${profileScheduler.active_timer_count}/${profileScheduler.timer_count}개 활성 · 실패 ${failedPipelines}개`,
      href: "#scheduler-detail",
      cta: "자동화 보기",
      tone: allTimersActive && failedPipelines === 0 ? "ready" : "watch",
    },
    {
      index: "03",
      label: "데이터·AI 품질",
      title: dataQualityReady
        ? "품질 기준 통과"
        : liveAiInvocationHealth.attention_required
          ? "실제 AI 호출 확인 필요"
        : qualityAudit.issue_count > 0 || newsAiEvalQuality.failed_case_count > 0
          ? "오염 의심 확인 필요"
          : "품질 근거 보강 중",
      body: dataQualityReady
        ? "뉴스 오염 감사, AI 기준 평가, 실제 Codex OAuth 호출이 모두 통과했다. 벤치마크 괴리 품질과 세부 샘플은 아래에서 확인한다."
        : liveAiInvocationHealth.attention_required
          ? "기준 세트 평가가 통과해도 실제 AI 호출이 실패하면 뉴스 번역과 AI 구조화는 규칙 기반 대체 결과일 수 있다. 실제 호출 상태를 먼저 본다."
        : qualityAudit.issue_count > 0 || newsAiEvalQuality.failed_case_count > 0
          ? "중복 뉴스, 오분류, AI 기준 평가 실패, 벤치마크 괴리 품질 중 확인할 항목이 있다. 추천 입력 전에 품질 근거를 본다."
          : "큰 오염은 없지만 번역, 전파, 사이클 스냅샷, 가상 매매 검증 근거가 아직 부족하다. 벤치마크 괴리 품질도 함께 본다.",
      metric: liveAiInvocationQualityMetric(liveAiInvocationHealth, newsAiEvalQuality),
      href: "#quality-audit",
      cta: "품질 감사 보기",
      tone: dataQualityReady ? "ready" : "watch",
    },
    {
      index: "04",
      label: "투자 경계",
      title: safeInvestmentBoundary ? "추천 산식·실거래 차단" : "투자 경계 확인 필요",
      body: safeInvestmentBoundary
        ? "성과 표본이 성숙하기 전까지 추천 산식 반영 비중 변경과 실거래 주문 제출은 막혀 있다."
        : "추천 산식 검토나 실거래 상태 조건이 예상과 다르다. 추천 산식/거래 안전 상태를 먼저 확인한다.",
      metric: outcomeWaitMonitor.weight_review_blocked ? "실거래 상태: 주문 차단" : "실거래 상태 확인",
      href: "#outcome-maturity-wait-monitor",
      cta: "투자 경계 보기",
      tone: safeInvestmentBoundary ? "ready" : "block",
    },
  ];
	  const decisionCards = [
    {
      label: "지금 판단",
      title:
        productionApiServer.attention_required
          ? "읽기 서버 확인 필요"
          : authRbac.attention_required
          ? "조회 권한 확인 필요"
          : alertDestination.attention_required
          ? "운영 알림 확인 필요"
          : failedPipelines > 0
          ? "수집 문제 먼저 해결"
          : data.overall_status === "healthy"
            ? "수집 상태 정상"
            : "주의 항목 확인",
      body:
        productionApiServer.attention_required
	          ? operationCopy(productionApiServer.next_action)
	          : authRbac.attention_required
	          ? operationCopy(authRbac.next_action)
	          : alertDestination.attention_required
	          ? operationCopy(alertDestination.next_action)
          : failedPipelines > 0
          ? "실패 또는 오래된 작업이 있어 추천·보유 판단보다 수집 복구가 먼저다."
          : "캔들, 뉴스, AI 분석, 추천 갱신이 현재 화면 기준으로 읽을 수 있는 상태다.",
      href: productionApiServer.attention_required || authRbac.attention_required || alertDestination.attention_required ? "#scheduler-detail" : "#execution-log",
      cta: productionApiServer.attention_required
        ? "읽기 서버 보기"
        : authRbac.attention_required
          ? "권한 경계 보기"
        : alertDestination.attention_required
          ? "알림 설정 보기"
          : "실행 이력 보기",
      tone: productionApiServer.attention_required
        ? "risk-high"
        : authRbac.attention_required
          ? "risk-high"
        : alertDestination.attention_required
          ? "risk-medium"
          : failedPipelines > 0
            ? "risk-high"
            : "risk-low",
    },
    {
      label: "자동화",
      title: artifactRunner.attention_required
        ? "실행 증거 확인 필요"
        : `${profileScheduler.active_timer_count}/${profileScheduler.timer_count}개 예약 실행`,
      body: artifactRunner.attention_required
        ? operationCopy(artifactRunner.next_action)
        : `실행 증거 저장기가 ${artifactRunner.latest_run_count}개 최신 실행 증거와 ${artifactRunner.artifact_policy_count}/${artifactRunner.job_count}개 저장 정책을 남기고 있다.`,
      href: "#scheduler-detail",
      cta: "스케줄 보기",
      tone: artifactRunner.attention_required
        ? "risk-medium"
        : profileScheduler.active_timer_count === profileScheduler.timer_count ? "risk-low" : "risk-medium",
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
      label: "추천 가격",
      title: activeRecommendationPriceFreshness.attention_required
        ? `${activeRecommendationPriceFreshness.stale_symbol_count + activeRecommendationPriceFreshness.missing_symbol_count}개 가격 보강 필요`
        : "추천 종목 가격 최신",
      body: activeRecommendationPriceFreshness.attention_required
        ? `추천에 쓰이는 종목 가격이 최신 가격일 ${activeRecommendationPriceFreshness.global_latest_trade_date || "미확인"}보다 뒤처져 있다. 가격 보강 전에는 성과·가상 매매 검증 해석 신뢰도가 낮아진다.`
        : `활성 추천 ${activeRecommendationPriceFreshness.active_symbol_count}개 종목 가격이 최신 가격일 ${activeRecommendationPriceFreshness.global_latest_trade_date || "미확인"} 기준으로 맞춰져 있다.`,
      href: "#active-recommendation-price-freshness",
      cta: "가격 최신성 보기",
      tone: activeRecommendationPriceFreshness.attention_required ? "risk-high" : "risk-low",
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
      label: "실제 AI 호출",
      title: liveAiInvocationTitle(liveAiInvocationHealth),
      body: liveAiInvocationExplanation(liveAiInvocationHealth),
      href: "#live-ai-invocation-health",
      cta: "실제 호출 보기",
      tone: liveAiInvocationTone(liveAiInvocationHealth),
    },
    {
      label: "AI 기준 평가",
      title: newsAiEvalTitle(newsAiEvalQuality),
      body: newsAiEvalExplanation(newsAiEvalQuality),
      href: "#news-ai-eval-quality",
      cta: "평가 항목 보기",
      tone: newsAiEvalTone(newsAiEvalQuality),
    },
    {
      label: "벤치마크 괴리",
      title: benchmarkDriftQualityTitle(benchmarkDriftQuality),
      body: benchmarkDriftQualityExplanation(benchmarkDriftQuality),
      href: "#benchmark-drift-quality",
      cta: "벤치마크 품질 보기",
      tone: benchmarkDriftQualityTone(benchmarkDriftQuality),
    },
    {
      label: "포트폴리오 검토 이력",
      title:
        portfolioReviewHistory.status === "loaded"
          ? portfolioReviewHistory.attention_required
            ? `${portfolioReviewHistory.decision_count}개 결정 저장됨`
            : "검토 이력 관리 중"
          : "검토 결정 이력 없음",
      body:
        portfolioReviewHistory.status === "loaded"
          ? portfolioReviewHistory.attention_required
            ? `최신 ${portfolioReviewHistory.as_of_date} 기준으로 벤치마크 ${portfolioReviewHistory.benchmark_decision_count}개, 포지션 크기 ${portfolioReviewHistory.position_sizing_decision_count}개 결정을 감사 이력으로 남겼다.`
            : operationCopy(portfolioReviewHistory.managed_review_reason)
	          : "현재 화면의 확인 대상은 보이지만 저장된 확인 이력으로는 아직 남지 않았다.",
      href: "#portfolio-review-history",
      cta: "검토 이력 보기",
      tone: portfolioReviewHistory.attention_required ? "risk-medium" : "risk-low",
    },
    {
      label: "검토 사후평가",
      title:
        portfolioReviewFeedback.status === "loaded"
          ? `${portfolioReviewFeedback.validated_count}개 검증 · ${portfolioReviewFeedback.contradicted_count}개 반박`
          : "사후평가 없음",
      body:
        portfolioReviewFeedback.status === "loaded"
	          ? `저장된 검토 결정 ${portfolioReviewFeedback.decision_count}개를 후속 성과, 가상 매매 검증, 가격 변화와 대조했다.`
	          : "검토 결정 이력은 저장됐지만 아직 이후 성과와 대조한 사후평가 기록이 없다.",
      href: "#portfolio-review-feedback",
      cta: "사후평가 보기",
      tone:
        portfolioReviewFeedback.feedback_status === "has_contradictions"
          ? "risk-high"
          : portfolioReviewFeedback.feedback_status === "needs_more_data"
            ? "risk-medium"
            : "risk-low",
    },
    {
      label: "검토 신뢰도",
      title:
        portfolioReviewCalibration.status === "loaded"
          ? portfolioReviewCalibration.managed_wait
            ? "관리된 대기"
            : portfolioReviewCalibration.weight_review_blocked
              ? "추천 산식 변경 금지"
              : "성과 표본 충족"
          : "누적평가 없음",
      body:
        portfolioReviewCalibration.status === "loaded"
	          ? `성숙 표본 ${portfolioReviewCalibration.mature_decision_count}/${portfolioReviewCalibration.min_mature_decisions}개, 사후평가 ${portfolioReviewCalibration.feedback_run_count}/${portfolioReviewCalibration.min_feedback_runs}회. ${portfolioReviewCalibration.estimated_maturity_date ? `예상 성숙일은 ${portfolioReviewCalibration.estimated_maturity_date}이다.` : operationCopy(portfolioReviewCalibration.weight_review_block_reason)}`
	          : "단일 사후평가만으로 추천 산식 반영 비중을 바꾸지 않기 위해 누적평가가 필요하다.",
      href: "#portfolio-review-calibration",
      cta: "신뢰도 보기",
      tone: portfolioReviewCalibration.managed_wait
        ? "risk-low"
        : calibrationStatusClass(portfolioReviewCalibration.calibration_status),
    },
    {
      label: "검토 실행시점",
      title:
        portfolioReviewCadence.should_run_now
          ? "지금 실행 필요"
          : portfolioReviewCadence.should_wait
            ? "대기"
            : "상태 확인",
      body:
        portfolioReviewCadence.status === "loaded"
	          ? operationCopy(portfolioReviewCadence.reason)
          : "사후평가와 누적평가를 언제 다시 돌릴지 아직 계산되지 않았다.",
      href: "#portfolio-review-cadence",
      cta: "실행시점 보기",
      tone: cadenceStatusClass(portfolioReviewCadence.cadence_status),
    },
    {
      label: "검토 실행 라우터",
      title: actionRouterTitle(portfolioReviewActionRouter),
      body:
        portfolioReviewActionRouter.status === "loaded"
	          ? operationCopy(portfolioReviewActionRouter.reason)
	          : "실행 주기 판단을 실제 사후평가/누적평가 실행 또는 대기로 변환한 기록이 아직 없다.",
      href: "#portfolio-review-action-router",
      cta: "라우터 판단 보기",
      tone: actionRouterStatusClass(portfolioReviewActionRouter.action_status),
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
      label: "성과 실행 라우터",
      title: outcomeDueActionRouterTitle(outcomeDueActionRouter),
      body:
        outcomeDueActionRouter.status === "loaded"
	          ? operationCopy(outcomeDueActionRouter.reason)
	          : "성과 측정창 상태를 실제 누적평가 실행 또는 대기로 변환한 기록이 아직 없다.",
      href: "#outcome-calibration",
      cta: "라우터 보기",
      tone: actionRouterStatusClass(outcomeDueActionRouter.action_status),
    },
    {
      label: "전문 분석 소스",
      title: professionalSourceGapTitle(professionalSourceGaps),
      body: professionalSourceGapExplanation(professionalSourceGaps),
      href: "#professional-source-gaps",
      cta: "소스 공백 보기",
      tone: professionalSourceGapTone(professionalSourceGaps),
    },
    {
      label: "전문 분석 품질",
      title: professionalQuality.title,
      body: operationCopy(professionalQuality.summary),
      href: "#professional-analysis-quality",
      cta: "품질 판정 보기",
      tone: professionalQualityTone(professionalQuality),
    },
    {
      label: "추천별 전문 감사",
      title: professionalRecommendationAudit.title,
      body: operationCopy(professionalRecommendationAudit.summary),
      href: "#professional-recommendation-coverage-audit",
      cta: "추천별 감사 보기",
      tone: professionalRecommendationAuditTone(professionalRecommendationAudit),
    },
    {
      label: "전문 분석 다음 행동",
      title: professionalNextAction.title,
      body: operationCopy(professionalNextAction.summary),
      href: "#professional-next-action",
      cta: "다음 행동 보기",
      tone: professionalNextActionTone(professionalNextAction),
    },
    {
	      label: "전문 분석 깊이",
	      title: professionalDepthTitle(professionalDepth),
		      body: `활성 후보 ${professionalDepth.active_candidate_count}개 중 ${professionalDepth.complete_candidate_count}개가 필요한 전문 분석 근거를 채웠고, 평균 연결률은 ${formatPercent(professionalDepth.average_coverage_ratio)}이다.`,
	      href: "#professional-analysis-depth",
	      cta: "깊이 보기",
	      tone: professionalDepthTone(professionalDepth),
	    },
	  ];
	  const priorityDecisionLabels = new Set([
	    "지금 판단",
	    "자동화",
	    "무료 API 예산",
	    "추천 가격",
	    "품질 감사",
	    "AI 기준 평가",
	  ]);
	  const priorityDecisionCards = decisionCards.filter((card) => priorityDecisionLabels.has(card.label));
	  const detailDecisionCards = decisionCards.filter((card) => !priorityDecisionLabels.has(card.label));
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
      description: "수집 문서를 구조화하고 AI 근거 기록을 남긴다. 중요 뉴스는 AI 배치 분석 후보로 처리하고, 뉴스 묶음은 무료 로컬 규칙 보조 증거로 남긴다.",
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
      output: "중요 뉴스만 AI 배치 분석으로 처리해 종목·테마·방향·근거 항목을 AI 분석 기록에 남긴다.",
      next: "검증을 통과한 근거만 표준 뉴스 영향으로 반영한다. 매수·매도·주문 결론은 여기서 만들지 않는다.",
    },
    {
      index: "04",
      title: "신호와 추천 항목 갱신",
      run: decisionRun,
      owner: "decision-daily",
      output: "가격, 테마 연결, 이벤트 강도, 사이클 상태를 합쳐 추천 항목과 투자 논리 입력을 만든다.",
      next: "결정 로직은 재현 가능한 점수 계산이다. AI 근거는 설명 가능한 보조 근거로 붙는다.",
    },
    {
      index: "05",
      title: "보유 상태와 운영 큐",
      run: remediationRun,
      owner: "portfolio-remediation-daily",
      output: "보유 투자 논리 유지 여부, 빈 가격/논리/성과 항목, 가상 거래 검증 문제를 큐로 만든다.",
      next: "추천 상세, 투자 논리, 보유 상태, 가상 매매 화면에서 확인한다.",
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
      title: "AI 배치 분석",
      run: aiRun,
      purpose: "중요 뉴스를 구조화해 근거 항목을 만든다.",
      check: "화면을 열 때마다 AI를 새로 호출하지 않고 저장된 결과만 읽는다.",
    },
    {
      index: "05",
      title: "AI 결과 검증",
      run: aiRun,
      purpose: "낮은 신뢰도, 알 수 없는 종목/테마, 저신호 뉴스를 차단한다.",
      check: "차단 항목은 AI 차단 항목 화면에서 본다.",
    },
    {
      index: "06",
      title: "추천 신호",
      run: decisionRun,
      purpose: "가격, 뉴스, 사이클, 상위 흐름을 추천 점수로 합친다.",
      check: "추천은 주문이 아니라 확인해야 할 상세 근거다.",
    },
    {
      index: "07",
      title: "보유 상태",
      run: remediationRun,
      purpose: "투자 논리 공백, 성과 미측정, 보유 충돌을 운영 큐로 만든다.",
      check: "보유 상태와 가상 매매 검증으로 이어진다.",
    },
  ];
  return (
    <div className="terminal-page decision-page">
      <section className="decision-brief reveal" aria-labelledby="data-health-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">데이터·자동화 · {data.as_of_date}</span>
          <h1 className="decision-brief-title" id="data-health-title">
            수집 상태는 {koCode(data.overall_status)}, 실패 작업은 {failedPipelines.toLocaleString("ko-KR")}개다.
          </h1>
          <p className="decision-brief-copy">
            이 화면의 첫 판단은 단순하다. 데이터가 정상인지, 자동 실행이 살아 있는지, 무료 API 예산과 AI 품질이
            추천 화면을 믿을 수 있는 상태인지 먼저 본다.
          </p>
          <div className="decision-brief-meta" aria-label="데이터 상태 핵심 수치">
            <span>자동 실행 {automationStateLabel(schedulerActivation)}</span>
            <span>확인 필요 항목 {data.open_gates.length.toLocaleString("ko-KR")}개</span>
            <span>호출 예산 {providerBudget.remaining_request_count}/{providerBudget.daily_budget}</span>
            <span>실거래 상태 {koCode(outcomeWaitMonitor.order_boundary)}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          {operationVerdictCards.map((card) => (
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

      <section className="feature-map-panel reveal delay-1" aria-labelledby="priority-status-title">
        <div className="section-heading stacked-heading">
          <span>오늘 조치</span>
          <h2 id="priority-status-title">문제가 있으면 여기서 바로 갈라진다</h2>
          <p>
	            상단 판정판에서 이상이 보이면 아래 카드가 실제 조치 위치로 보낸다. 성과·포트폴리오·전문분석 상세는
	            접힌 영역에서 이어서 본다.
	          </p>
	        </div>
	        <div className="decision-brief-grid" aria-label="데이터 수집 우선 판단 요약">
	          {priorityDecisionCards.map((card) => (
	            <a className="decision-brief-card data-decision-card" href={card.href} key={card.label}>
	              <span>{card.label}</span>
	              <strong className={`risk-tag ${card.tone}`}>{card.title}</strong>
	              <p>{card.body}</p>
	              <small>{card.cta}</small>
	            </a>
          ))}
        </div>
      </section>

      <section className="feature-map-panel reveal delay-1" aria-labelledby="open-gate-triage-title">
        <div className="section-heading stacked-heading">
          <span>열린 확인 항목</span>
          <h2 id="open-gate-triage-title">장애인지, 기다릴 상태인지, 원천 한계인지 분리해서 본다</h2>
          <p>{gateTriageStatus}</p>
        </div>
        {visibleGateTriageBuckets.length > 0 ? (
          <div className="data-health-triage-grid">
            {visibleGateTriageBuckets.map((bucket) => (
              <article className="data-health-triage-card" key={bucket.key}>
                <div className="data-health-triage-head">
                  <span>{bucket.label}</span>
                  <strong className={`risk-tag ${bucket.tone}`}>{bucket.gates.length}개</strong>
                </div>
                <h3>{bucket.title}</h3>
                <p>{bucket.description}</p>
                <div className="data-health-triage-list">
                  {bucket.gates.map((gate) => (
                    <a href={bucket.href} key={gate.gate_id}>
                      <span className={`risk-tag ${gateSeverityTone(gate.severity)}`}>{gate.status_label}</span>
                      <strong>{gate.label}</strong>
                      <small>{operationCopy(gate.summary)}</small>
                      <small>다음 확인: {openGateCopy(gate.next_action)}</small>
                    </a>
                  ))}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <strong>열린 확인 항목 없음</strong>
            <p>현재 상단 기준에서 즉시 조치할 장애, 관리되지 않은 대기, 원천 한계가 없다.</p>
          </div>
        )}
      </section>

      <section className="feature-map-panel reveal delay-1" aria-labelledby="collection-status-title">
        <div className="section-heading stacked-heading">
          <span>수집/분석별 상태</span>
          <h2 id="collection-status-title">무엇이 언제 돌았고, 어디에 쓰이는지 먼저 본다</h2>
	        </div>
	        <p className="board-intro">
	          주식 캔들, 뉴스 원문, 1차 분류, AI 분석, 추천 갱신, 보유 상태 판단이 각각 따로 돈다.
	          문제가 있는 데이터가 있으면 해당 화면의 판단을 낮게 신뢰해야 한다.
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
            <span>가상 매매 검증</span>
            <strong>{qualityMetric(qualityAudit, "paper_validation_passed_count")}</strong>
            <small>{qualityMetric(qualityAudit, "paper_validation_count")}회 중 통과</small>
          </article>
        </div>
        <div className="insight-grid">
          <article className="insight-card">
            <span>누락 실행 단계</span>
            <strong>{qualityAudit.readiness_gap_count}</strong>
            <p>
              {qualityAudit.readiness_gaps[0]
                ? `${qualityAudit.readiness_gaps[0].label} 때문에 감사 상태가 낮아졌다.`
                : "감사 기준에 필요한 수집·분석·전파·스냅샷 누락 수다."}
            </p>
          </article>
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
        {qualityAudit.readiness_gaps.length > 0 ? (
          <div className="relationship-panel">
            <span>부족한 실행 단계</span>
            <div className="relationship-list">
              {qualityAudit.readiness_gaps.map((gap) => (
                <article className="relationship-chip" key={gap.gap_key}>
                  <span>{gap.label}</span>
                  <strong>
                    {gap.metric_key}: {String(gap.current_value ?? 0)}
                  </strong>
                  <small>다음 조치: {operationCopy(gap.next_action)}</small>
                </article>
              ))}
            </div>
          </div>
        ) : null}
        {qualityAuditSamples.length > 0 ? (
          <div className="relationship-panel">
            <span>감사 샘플</span>
            <div className="relationship-list">
              {qualityAuditSamples.map((group) => (
                <article className="relationship-chip" key={group.key}>
                  <span>{group.label}</span>
                  <strong>{group.description}</strong>
                  {group.records.map((record, index) => (
                    <small key={`${group.key}-${auditSampleValue(record, "event_id") || index}`}>
                      {auditSampleHeadline(record)}
                      {auditSampleMeta(record) ? ` · ${auditSampleMeta(record)}` : ""}
                    </small>
                  ))}
                </article>
              ))}
            </div>
          </div>
        ) : null}
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{qualityAudit.next_actions[0] ? operationCopy(qualityAudit.next_actions[0]) : "현재 추가 조치 없음"}</p>
        </div>
      </section>

	      <section
	        className="feature-map-panel reveal delay-1"
	        id="live-ai-invocation-health"
	        aria-labelledby="live-ai-invocation-health-title"
	      >
	        <div className="section-heading stacked-heading">
	          <span>실제 AI 호출 상태</span>
	          <h2 id="live-ai-invocation-health-title">
	            기준 세트 통과와 별개로, 운영 배치가 실제 Codex OAuth를 호출했는지 본다.
	          </h2>
	        </div>
	        <p className="board-intro">{liveAiInvocationExplanation(liveAiInvocationHealth)}</p>
	        <div className="status-rail compact-rail">
	          <article className="rail-cell">
	            <span>판정</span>
	            <strong className={`risk-tag ${liveAiInvocationTone(liveAiInvocationHealth)}`}>
	              {liveAiInvocationTitle(liveAiInvocationHealth)}
	            </strong>
	            <small>최근 {liveAiInvocationHealth.window_hours}시간</small>
	          </article>
	          <article className="rail-cell">
	            <span>최근 호출</span>
	            <strong>{liveAiInvocationHealth.recent_invocation_count}</strong>
	            <small>{liveAiInvocationHistoryLabel(liveAiInvocationHealth)}</small>
	          </article>
	          <article className="rail-cell">
	            <span>현재 실패 작업</span>
	            <strong>{liveAiCurrentFailureCount(liveAiInvocationHealth)}</strong>
	            <small>{liveAiCurrentFailureDetail(liveAiInvocationHealth)}</small>
	          </article>
	          <article className="rail-cell">
	            <span>최신 실패 작업</span>
	            <strong>{koCode(liveAiInvocationHealth.latest_failed_task_name) || "없음"}</strong>
	            <small>{liveAiInvocationHealth.latest_failed_at || "최근 실패 없음"}</small>
	          </article>
	        </div>
	        <div className="simple-table-wrap">
	          <table className="simple-table">
	            <thead>
	              <tr>
	                <th>작업</th>
	                <th>최근 상태</th>
	                <th>성공/실패</th>
	                <th>최신 오류</th>
	              </tr>
	            </thead>
	            <tbody>
	              {liveAiInvocationHealth.task_health.map((task) => (
	                <tr key={task.task_name}>
	                  <td>
	                    <strong>{task.label || koCode(task.task_name)}</strong>
	                    <small>{task.critical ? "핵심 AI 작업" : "보조 AI 작업"}</small>
	                  </td>
	                  <td>{koCode(task.latest_status)}</td>
	                  <td>{task.recent_success_count}/{task.recent_failed_count}</td>
	                  <td>
	                    {task.latest_error_summary
	                      ? aiInvocationErrorCopy(task.latest_error_summary, task.latest_error_code)
	                      : task.latest_created_at || "최근 호출 없음"}
	                  </td>
	                </tr>
	              ))}
	              {liveAiInvocationHealth.task_health.length === 0 ? (
	                <tr>
	                  <td colSpan={4}>최근 실제 AI 호출 기록이 없다.</td>
	                </tr>
	              ) : null}
	            </tbody>
	          </table>
	        </div>
	        <div className="empty-state">
	          <strong>다음 조치</strong>
	          <p>{operationCopy(liveAiInvocationHealth.next_action)}</p>
	        </div>
	      </section>

	      <section
	        className="feature-map-panel reveal delay-1"
	        id="news-ai-eval-quality"
        aria-labelledby="news-ai-eval-quality-title"
      >
        <div className="section-heading stacked-heading">
	          <span>뉴스 AI 기준 평가</span>
          <h2 id="news-ai-eval-quality-title">
            AI가 뉴스에서 테마와 종목을 잘못 뽑기 시작했는지 기준 세트로 확인한다.
          </h2>
        </div>
        <p className="board-intro">{newsAiEvalExplanation(newsAiEvalQuality)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>평가 결과</span>
            <strong className={`risk-tag ${newsAiEvalTone(newsAiEvalQuality)}`}>
              {newsAiEvalTitle(newsAiEvalQuality)}
            </strong>
            <small>{newsAiEvalQuality.created_at || "최근 결과 없음"}</small>
          </article>
          <article className="rail-cell">
            <span>통과 항목</span>
            <strong>
              {newsAiEvalQuality.passed_case_count}/{newsAiEvalQuality.case_count}
            </strong>
            <small>{executionIdLabel(newsAiEvalQuality.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>테마 정밀도</span>
            <strong>{formatPercent(newsAiEvalQuality.theme_precision)}</strong>
            <small>금리·양자·에너지 등</small>
          </article>
          <article className="rail-cell">
            <span>종목 근거 정밀도</span>
            <strong>{formatPercent(newsAiEvalQuality.direct_ticker_grounding_precision)}</strong>
            <small>원문 없는 종목 코드 차단</small>
          </article>
          <article className="rail-cell">
            <span>한국어 준비</span>
            <strong>{formatPercent(newsAiEvalQuality.korean_translation_availability)}</strong>
            <small>제목·요약 기준</small>
          </article>
        </div>
        <div className="insight-grid">
          <article className="insight-card">
            <span>거시 뉴스 종목 오부착</span>
            <strong>{newsAiEvalQuality.macro_only_false_ticker_count}</strong>
            <p>금리·물가 같은 상위 흐름 뉴스를 억지로 개별 종목에 붙이면 추천 근거가 오염된다.</p>
          </article>
          <article className="insight-card">
            <span>양자→에너지 오분류</span>
            <strong>{newsAiEvalQuality.quantum_energy_misclassification_count}</strong>
            <p>양자컴퓨팅 정책 뉴스가 XOM/XLE 또는 에너지 테마로 잘못 흐르는지 확인한다.</p>
          </article>
          <article className="insight-card">
            <span>차단 후보 정확도</span>
            <strong>{formatPercent(newsAiEvalQuality.blocked_candidate_correctness)}</strong>
            <p>자동 검증이 낮은 신뢰도, 원문 근거 없는 종목 코드, 알 수 없는 테마를 제대로 막는지 본다.</p>
          </article>
          <article className="insight-card">
            <span>평가 방식</span>
            <strong>{koCode(newsAiEvalQuality.provider)}</strong>
	            <p>기본 평가는 무료 기준 정답 뉴스 세트로 돈다. 실시간 유료 AI 호출이 아니라 저장된 기준 세트 검증이다.</p>
          </article>
        </div>
        <div className="simple-table-wrap">
          <table className="simple-table">
            <thead>
              <tr>
                <th>평가 항목</th>
                <th>결과</th>
                <th>테마</th>
                <th>직접 종목</th>
                <th>차단/오류</th>
              </tr>
            </thead>
            <tbody>
              {newsAiEvalQuality.case_results.slice(0, 6).map((item) => (
                <tr key={item.case_id}>
                  <td>
                    <strong>{koCode(item.case_id)}</strong>
                    <small>{koCode(item.category)}</small>
                  </td>
                  <td>{item.passed ? "통과" : "실패"}</td>
                  <td>{item.accepted_theme_codes.map(koCode).join(" · ") || "없음"}</td>
                  <td>{item.accepted_direct_symbols.join(" · ") || "없음"}</td>
                  <td>
                    {[
                      ...item.missing_theme_codes,
                      ...item.missing_direct_symbols,
                      ...item.forbidden_theme_hits,
                      ...item.forbidden_symbol_hits,
                      ...item.blocked_symbols_accepted,
                    ]
                      .map(koCode)
                      .join(" · ") || "없음"}
                  </td>
                </tr>
              ))}
              {newsAiEvalQuality.case_results.length === 0 ? (
                <tr>
                  <td colSpan={5}>저장된 평가 항목이 없다.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(newsAiEvalQuality.next_action)}</p>
	        </div>
	      </section>

	      <details className="operator-details-panel reveal delay-2">
	        <summary>
	          <span>세부 판단 카드</span>
	          <strong>성과, 포트폴리오 검토, 전문 분석 세부 상태 {detailDecisionCards.length}개</strong>
	        </summary>
	        <div className="decision-brief-grid details-inner" aria-label="데이터 수집 세부 판단 요약">
	          {detailDecisionCards.map((card) => (
	            <a className="decision-brief-card data-decision-card" href={card.href} key={card.label}>
	              <span>{card.label}</span>
	              <strong className={`risk-tag ${card.tone}`}>{card.title}</strong>
	              <p>{card.body}</p>
	              <small>{card.cta}</small>
	            </a>
	          ))}
	        </div>
	      </details>

	      <details className="operator-details-panel reveal delay-2" id="investment-quality-details">
	        <summary>
	          <span>투자 품질·성과 상세</span>
	          <strong>성과검증, 전문 분석, 포트폴리오 검토 기록</strong>
	        </summary>
	        <div className="details-inner">

	      <section
	        className="feature-map-panel reveal delay-1"
	        id="outcome-maturity-wait-monitor"
        aria-labelledby="outcome-maturity-wait-monitor-title"
      >
        <div className="section-heading stacked-heading">
          <span>성과 성숙 대기 모니터</span>
          <h2 id="outcome-maturity-wait-monitor-title">
	            추천 성과와 포트폴리오 사후평가가 성숙하기 전에는 추천 산식 반영 비중을 바꾸지 않는다.
          </h2>
        </div>
        <p className="board-intro">
          {operationCopy(outcomeWaitMonitor.summary)} {operationCopy(outcomeWaitMonitor.next_action)}
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>현재 결론</span>
            <strong className={`risk-tag ${outcomeWaitMonitorTone(outcomeWaitMonitor)}`}>
              {outcomeWaitMonitor.title}
            </strong>
            <small>{outcomeWaitMonitor.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell">
	            <span>추천 성과</span>
            <strong>{outcomeWaitMonitor.recommendation_next_due_date || "대기일 없음"}</strong>
            <small>
              다음 창 {outcomeWaitMonitor.recommendation_next_due_count}개 · 상태{" "}
              {koCode(outcomeWaitMonitor.recommendation_maturity_status)}
            </small>
          </article>
          <article className="rail-cell">
	            <span>포트폴리오 사후평가</span>
            <strong>{outcomeWaitMonitor.portfolio_feedback_maturity_date || "성숙일 없음"}</strong>
            <small>
              성숙 판단 부족 {outcomeWaitMonitor.portfolio_mature_decision_gap}개 · 실행 부족{" "}
              {outcomeWaitMonitor.portfolio_feedback_run_gap}회
            </small>
          </article>
          <article className="rail-cell rail-critical">
            <span>추천 산식 검토</span>
            <strong>{outcomeWaitMonitor.weight_review_blocked ? "변경 차단" : "성과 표본 충족"}</strong>
            <small>실거래 상태 {orderBoundaryCopy(outcomeWaitMonitor.order_boundary)}</small>
          </article>
        </div>
        <div className="insight-grid">
          {outcomeWaitMonitor.wait_items.map((item) => (
            <article className="insight-card" key={item.scope}>
              <span>{item.label}</span>
              <strong>{item.wait_until || "날짜 미정"}</strong>
              <p>{operationCopy(item.reason)}</p>
              <small>
                {koCode(item.status)} · {koCode(item.action_status)} · 대상 {item.count}개
              </small>
            </article>
          ))}
          <article className="insight-card">
            <span>추천 산식 차단 이유</span>
            <strong>{outcomeWaitMonitor.manual_weight_review_allowed ? "성과 표본 충족" : "성과 표본 대기"}</strong>
            <p>{operationCopy(outcomeWaitMonitor.weight_review_block_reason)}</p>
          </article>
          <article className="insight-card">
            <span>안전 경계</span>
            <strong>{outcomeWaitMonitor.automatic_weight_change_allowed ? "자동 변경 허용" : "자동 변경 금지"}</strong>
            <p>
              추천 점수 변경 {outcomeWaitMonitor.recommendation_scoring_mutated ? "감지" : "없음"} ·
              {orderSubmitCopy(outcomeWaitMonitor.broker_submit_allowed)}
            </p>
          </article>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="outcome-calibration"
        aria-labelledby="outcome-calibration-title"
      >
        <div className="section-heading stacked-heading">
          <span>추천 성과검증</span>
          <h2 id="outcome-calibration-title">추천 산식 반영 비중을 바꾸기 전에 성과 표본과 실패 사례를 먼저 확인한다.</h2>
        </div>
        <p className="board-intro">{outcomeCalibrationExplanation(outcomeCalibration)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>판정</span>
            <strong className={`risk-tag ${outcomeCalibrationTone(outcomeCalibration)}`}>
              {outcomeCalibrationTitle(outcomeCalibration)}
            </strong>
            <small>{recordLabel(outcomeCalibration.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>성과 표본</span>
            <strong>
              {outcomeCalibration.outcome_count}/{outcomeCalibration.recommendation_horizon_count}
            </strong>
            <small>추천×기간 기준</small>
          </article>
          <article className="rail-cell">
            <span>표본 연결률</span>
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
	              있으면 추천 산식 검토보다 성과 보강이 먼저다.
            </p>
          </article>
          <article className="insight-card">
            <span>실행 액션</span>
            <strong>{koCode(outcomeMaturity.cadence_action.status)}</strong>
            <p>{operationCopy(outcomeMaturity.cadence_action.reason)}</p>
            <small>{operationCopy(outcomeMaturity.cadence_action.label)}</small>
          </article>
          <article className="insight-card">
            <span>성과 실행 라우터</span>
            <strong className={`risk-tag ${actionRouterStatusClass(outcomeDueActionRouter.action_status)}`}>
              {outcomeDueActionRouterTitle(outcomeDueActionRouter)}
            </strong>
            <p>{operationCopy(outcomeDueActionRouter.reason || "저장된 실행 분기 판단이 없다.")}</p>
            <small>{recordLabel(outcomeDueActionRouter.eval_run_id)}</small>
          </article>
          <article className="insight-card">
            <span>후속 실행</span>
            <strong>{outcomeDueActionRouter.child_runner.executed ? "실행됨" : "실행 안 함"}</strong>
            <p>
              {outcomeDueActionRouter.child_runner.executed
                ? `${operationCopy(outcomeDueActionRouter.child_runner.report_name)} · ${recordLabel(outcomeDueActionRouter.child_runner.eval_run_id)}`
                : "측정일 대기, 가격 이력 차단, 또는 안전 조건 때문에 누적평가 실행을 시작하지 않았다."}
            </p>
          </article>
          <article className="insight-card">
            <span>추천 산식 반영 비중</span>
            <strong>{outcomeCalibration.recommendation_scoring_mutated ? "변경 감지" : "변경 없음"}</strong>
            <p>성과 검증은 추천 산식 변경이 아니다. 반영 비중 조정은 별도 승인된 시험 작업 전까지 막는다.</p>
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
            <p>전문 분석 연결률과 성과 표본이 추천 산식 검토 기준을 충족하는지 본다.</p>
          </article>
          <article className="insight-card">
            <span>추천 산식 변경 조건</span>
            <strong>{weightReviewReadiness.manual_weight_review_allowed ? "성과 표본 충족" : "변경 차단"}</strong>
            <p>
              {weightReviewReadiness.blocker_message
                ? operationCopy(weightReviewReadiness.blocker_message)
                : operationCopy(weightReviewReadiness.next_action)}
            </p>
          </article>
          <article className="insight-card">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(outcomeCalibration.order_boundary)}</strong>
            <p>성과검증은 주문 생성이나 실거래 제출을 허용하지 않는다.</p>
          </article>
        </div>
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(outcomeDueActionRouter.next_action || outcomeMaturity.cadence_action.label)}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="professional-analysis-quality"
        aria-labelledby="professional-analysis-quality-title"
      >
        <div className="section-heading stacked-heading">
          <span>전문 분석 품질</span>
          <h2 id="professional-analysis-quality-title">
            재무·피어·밸류에이션·산업·AI 리서치 근거가 추천 판단에 붙었는지 확인한다.
          </h2>
        </div>
        <p className="board-intro">{operationCopy(professionalQuality.summary)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>품질 판정</span>
            <strong className={`risk-tag ${professionalQualityTone(professionalQuality)}`}>
              {professionalQuality.title}
            </strong>
            <small>{professionalQuality.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell">
            <span>활성 후보</span>
            <strong>{professionalQuality.active_candidate_count}</strong>
            <small>전문 분석 품질 점검 대상</small>
          </article>
          <article className="rail-cell">
            <span>근거 연결 완료</span>
            <strong>{professionalQuality.complete_candidate_count}</strong>
            <small>필수 근거 충족 후보</small>
          </article>
          <article className="rail-cell">
            <span>평균 연결률</span>
            <strong>{formatPercent(professionalQuality.average_coverage_ratio)}</strong>
            <small>재무·피어·밸류에이션·산업·리서치</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>원천 차단</span>
            <strong>{professionalQuality.source_blocked_count}</strong>
            <small>합성 재무 금지</small>
          </article>
          <article className="rail-cell rail-critical">
	            <span>추천 산식/실거래 상태</span>
	            <strong>{professionalQuality.automatic_weight_change_allowed ? "추천 산식 변경 허용" : "추천 산식 변경 금지"}</strong>
            <small>{orderBoundaryCopy(professionalQuality.order_boundary)}</small>
          </article>
        </div>
        <div className="insight-grid">
          {professionalQuality.layer_checks.map((layer) => (
            <article className="insight-card" key={layer.layer_key}>
              <span>{operationCopy(layer.label)}</span>
              <strong>{operationCopy(layer.status)}</strong>
              <p>
                {layer.available_count}/{layer.expected_count}개 후보 연결 · 근거 연결률 {formatPercent(layer.coverage_ratio)}
              </p>
            </article>
          ))}
        </div>
        <div className="flow-steps data-health-summary-grid">
          {professionalQuality.quality_checks.map((check) => (
            <article className="flow-step" key={check.key}>
              <span>{operationCopy(check.label)}</span>
              <strong>{operationCopy(check.status)}</strong>
	              <p>{operationCopy(check.detail)}</p>
            </article>
          ))}
        </div>
        <div className="empty-state">
          <strong>다음 조치</strong>
	          <p>{operationCopy(professionalQuality.next_action)}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="professional-recommendation-coverage-audit"
        aria-labelledby="professional-recommendation-coverage-audit-title"
      >
        <div className="section-heading stacked-heading">
          <span>추천별 전문 감사</span>
          <h2 id="professional-recommendation-coverage-audit-title">
            active 추천마다 전문 분석 근거가 실제로 붙었는지 본다.
          </h2>
        </div>
        <p className="board-intro">{operationCopy(professionalRecommendationAudit.summary)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>감사 판정</span>
            <strong className={`risk-tag ${professionalRecommendationAuditTone(professionalRecommendationAudit)}`}>
              {professionalRecommendationAudit.title}
            </strong>
            <small>{professionalRecommendationAudit.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell">
	            <span>활성 추천</span>
            <strong>{professionalRecommendationAudit.recommendation_count}</strong>
	            <small>검토 대상</small>
          </article>
          <article className="rail-cell">
            <span>전문 근거 충족</span>
            <strong>{professionalRecommendationAudit.ready_for_review_count}</strong>
            <small>전문 근거와 가상 매매 검증 통과</small>
          </article>
          <article className="rail-cell">
            <span>근거 부족</span>
            <strong>{professionalRecommendationAudit.coverage_gap_count}</strong>
            <small>재무·피어·밸류에이션·산업·리서치</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>원천 차단</span>
            <strong>{professionalRecommendationAudit.source_blocked_count}</strong>
            <small>합성 재무 금지</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
	            <strong>{professionalRecommendationAudit.broker_submit_allowed ? "제출 가능" : "제출 금지"}</strong>
            <small>{orderBoundaryCopy(professionalRecommendationAudit.order_boundary)}</small>
          </article>
        </div>

        {professionalRecommendationAudit.items.length > 0 ? (
          <div className="feature-map-grid collection-map-grid">
            {professionalRecommendationAudit.items.map((item) => (
              <article className="feature-map-card collection-map-card" key={item.recommendation_id}>
                <span>
                  #{item.rank} · {item.product_type === "fund_or_etf" ? "ETF·펀드형" : "개별 기업"}
                </span>
                <strong>
                  <a href={item.detail_href}>{item.symbol}</a> · {operationCopy(item.audit_status)}
                </strong>
                <small>{item.instrument_name || "종목명 미확인"}</small>
                <small>
                  추천 점수 {formatPercent(item.recommendation_score)} · 목표 비중 {formatPercent(item.recommended_weight)}
                </small>
                <small>
	                  연결률 {formatPercent(item.coverage_ratio)} · 근거 {item.available_layer_count}/{item.expected_layer_count}
                </small>
                <small className={`risk-tag ${professionalRecommendationAuditItemTone(item.audit_status)}`}>
                  {operationCopy(item.professional_decision_status)}
                </small>
                <div className="tag-ledger">
                  {item.layer_checks.map((check) => (
                    <span className={`risk-tag ${check.status === "complete" || check.status === "passed" ? "risk-low" : check.status === "not_applicable" ? "risk-medium" : "risk-high"}`} key={check.key}>
                      {operationCopy(check.label)}: {operationCopy(check.status)}
                    </span>
                  ))}
                </div>
                {item.missing_layer_labels.length > 0 ? (
                  <p>부족 근거: {item.missing_layer_labels.join(" · ")}</p>
                ) : (
                  <p>표시할 부족 근거가 없다.</p>
                )}
                <dl className="fact-list compact-facts">
                  <div>
	                    <dt>투자 논리</dt>
                    <dd>{item.has_active_thesis ? "연결됨" : "없음"}</dd>
                  </div>
                  <div>
                    <dt>가상 매매 검증</dt>
                    <dd>{operationCopy(item.paper_validation_status)}</dd>
                  </div>
                  <div>
                    <dt>주문</dt>
                    <dd>{item.broker_submit_allowed ? "제출 가능" : "제출 금지"}</dd>
                  </div>
                </dl>
	                {item.remediation_action ? <p>{operationCopy(item.remediation_action)}</p> : null}
                <a href={item.stock_href}>종목 상세 보기</a>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">추천별 전문 분석 감사 대상이 없다.</div>
        )}

        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(professionalRecommendationAudit.next_action)}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="professional-next-action"
        aria-labelledby="professional-next-action-title"
      >
        <div className="section-heading stacked-heading">
          <span>전문 분석 다음 행동</span>
          <h2 id="professional-next-action-title">재무·밸류에이션·원천 공백·성과 표본 중 지금 무엇을 봐야 하는지 정리한다.</h2>
        </div>
        <p className="board-intro">{operationCopy(professionalNextAction.summary)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>현재 판단</span>
            <strong className={`risk-tag ${professionalNextActionTone(professionalNextAction)}`}>
              {professionalNextAction.title}
            </strong>
            <small>{professionalNextAction.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell">
            <span>원천 공백</span>
            <strong>{professionalNextAction.source_gap_count}</strong>
            <small>원천 차단 {professionalNextAction.source_blocker_count}개</small>
          </article>
          <article className="rail-cell">
            <span>전문 판단 차단</span>
            <strong>{professionalNextAction.guarded_source_blocked_recommendation_count}</strong>
            <small>원천 없으면 합성 재무 금지</small>
          </article>
          <article className="rail-cell">
            <span>평균 연결률</span>
            <strong>{formatPercent(professionalNextAction.average_coverage_ratio)}</strong>
            <small>활성 후보 기준</small>
          </article>
          <article className="rail-cell">
            <span>성과 표본</span>
            <strong>{professionalNextAction.managed_wait ? "관리된 대기" : koCode(professionalNextAction.status)}</strong>
            <small>
              {professionalNextAction.estimated_maturity_date
                ? `${professionalNextAction.estimated_maturity_date} 이후 재평가`
                : "성숙일 미확인"}
            </small>
          </article>
          <article className="rail-cell rail-critical">
            <span>추천 산식/실거래 상태</span>
            <strong>{professionalNextAction.weight_review_blocked ? "추천 산식 변경 금지" : "성과 표본 충족"}</strong>
            <small>{orderBoundaryCopy(professionalNextAction.order_boundary)}</small>
          </article>
        </div>
        <div className="insight-grid">
          {professionalNextAction.readiness_items.map((item) => (
            <article className="insight-card" key={item.key}>
              <span>{operationCopy(item.label)}</span>
              <strong>{operationCopy(item.status)}</strong>
	              <p>{operationCopy(item.detail)}</p>
            </article>
          ))}
          {professionalNextAction.readiness_items.length === 0 ? (
            <article className="insight-card">
              <span>상태 없음</span>
              <strong>data-health payload 대기</strong>
	              <p>전문 분석 요약을 만들 원천 공백, 성과 사후평가, 추천 산식 검토 근거가 아직 없다.</p>
            </article>
          ) : null}
        </div>
        <div className="empty-state">
          <strong>다음 조치</strong>
	          <p>{operationCopy(professionalNextAction.next_action)}</p>
          {professionalNextAction.next_symbol ? (
            <p>
              우선 확인 대상{" "}
              {professionalNextAction.next_symbol_href ? (
                <a href={professionalNextAction.next_symbol_href}>{professionalNextAction.next_symbol}</a>
              ) : (
                professionalNextAction.next_symbol
              )}
	              {professionalNextAction.next_symbol_reason ? ` · ${operationCopy(professionalNextAction.next_symbol_reason)}` : ""}
            </p>
          ) : null}
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="professional-analysis-depth"
        aria-labelledby="professional-analysis-depth-title"
      >
        <div className="section-heading stacked-heading">
          <span>전문 분석 깊이</span>
          <h2 id="professional-analysis-depth-title">
            활성 후보가 재무·피어·밸류에이션·리서치 근거를 얼마나 갖췄는지 본다.
          </h2>
        </div>
        <p className="board-intro">
          이 영역은 추천 점수를 바꾸지 않는다. 어떤 종목이 전문 분석서로 충분히 설명 가능한지, 어떤 종목은 원천 데이터 부족으로
          판단 입력에서 제외해야 하는지만 보여준다.
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>판정</span>
            <strong className={`risk-tag ${professionalDepthTone(professionalDepth)}`}>
              {professionalDepthTitle(professionalDepth)}
            </strong>
            <small>{professionalDepth.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell">
	            <span>활성 후보</span>
            <strong>{professionalDepth.active_candidate_count}</strong>
            <small>개별 기업 {professionalDepth.operating_company_candidate_count} · ETF/펀드 {professionalDepth.fund_like_candidate_count}</small>
          </article>
          <article className="rail-cell">
            <span>완비 후보</span>
            <strong>{professionalDepth.complete_candidate_count}</strong>
	            <small>필요 근거 충족</small>
          </article>
          <article className="rail-cell">
	            <span>평균 연결률</span>
            <strong>{formatPercent(professionalDepth.average_coverage_ratio)}</strong>
            <small>최저 {formatPercent(professionalDepth.weakest_coverage_ratio)}</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>원천 차단</span>
            <strong>{professionalDepth.source_blocked_count}</strong>
            <small>합성 재무 금지</small>
          </article>
          <article className="rail-cell rail-critical">
	            <span>추천 산식/실거래 상태</span>
	            <strong>{professionalDepth.automatic_weight_change_allowed ? "추천 산식 변경 허용" : "추천 산식 변경 금지"}</strong>
            <small>{orderBoundaryCopy(professionalDepth.order_boundary)}</small>
          </article>
        </div>

        <div className="insight-grid">
          {professionalDepth.layer_coverage.map((layer) => (
            <article className="insight-card" key={layer.layer_key}>
              <span>{operationCopy(layer.label)}</span>
              <strong>{formatPercent(layer.coverage_ratio)}</strong>
              <p>
                {layer.available_count}/{layer.expected_count}개 후보가 이 근거를 갖췄다.
              </p>
            </article>
          ))}
          {professionalDepth.layer_coverage.length === 0 ? (
            <article className="insight-card">
	              <span>근거 없음</span>
              <strong>계산 대기</strong>
	              <p>활성 후보별 재무·피어·밸류에이션·리서치 연결률을 아직 계산하지 못했다.</p>
            </article>
          ) : null}
        </div>

        {professionalDepth.items.length > 0 ? (
          <div className="feature-map-grid collection-map-grid">
            {professionalDepth.items.map((item) => (
              <article className="feature-map-card collection-map-card" key={`${item.rank}-${item.symbol}`}>
                <span>
                  #{item.rank} · {item.product_type === "fund_or_etf" ? "ETF·펀드형" : "개별 기업"}
                </span>
                <strong>
                  <a href={item.detail_href}>{item.symbol}</a> · {professionalDepthStatusLabel(item.depth_status)}
                </strong>
                <small>{item.instrument_name || "종목명 미확인"}</small>
                <small>
                  근거 연결률 {formatPercent(item.coverage_ratio)} · 근거 {item.available_layer_count}/{item.expected_layer_count}
                </small>
                <small>추천 연결 {item.active_recommendation_count}개 · 보유 {formatPercent(item.current_weight)}</small>
                <small className={`risk-tag ${professionalDepthItemTone(item.depth_status)}`}>
                  {professionalDepthStatusLabel(item.depth_status)}
                </small>
                {item.missing_layer_labels.length > 0 ? (
                  <p>부족 근거: {item.missing_layer_labels.join(" · ")}</p>
                ) : (
                  <p>현재 기준에서 표시할 부족 근거가 없다.</p>
                )}
                {item.blocker_code ? <small>차단 사유 {koCode(item.blocker_code)}</small> : null}
                {item.remediation_action ? <p>{operationCopy(item.remediation_action)}</p> : null}
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            활성 추천 기준으로 표시할 전문 분석 후보가 없다.
          </div>
        )}

        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(professionalDepth.next_action)}</p>
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
            추천·보유 판단에 필요한 재무, 밸류에이션, 펀드 원천이 어디서 막혔는지 본다.
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
          <article className="rail-cell rail-critical">
            <span>추천 차단 적용</span>
            <strong>{professionalSourceGaps.guarded_source_blocked_recommendation_count}</strong>
            <small>전문 판단·가상 매매 입력 차단</small>
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
                      {gap.active_recommendation_professional_use_blocked ? (
                        <small className="risk-tag risk-high">추천 전문 판단 차단됨</small>
                      ) : null}
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
            활성 추천 기준으로 표시할 전문 분석 원천 공백이 없다.
          </div>
        )}
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(professionalSourceGaps.next_action)}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="benchmark-drift-quality"
        aria-labelledby="benchmark-drift-quality-title"
      >
        <div className="section-heading stacked-heading">
          <span>벤치마크 괴리 품질</span>
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
            <small>확인 대상 {benchmarkDriftQuality.review_candidate_count}개</small>
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

      <section
        className="feature-map-panel reveal delay-1"
        id="portfolio-review-history"
        aria-labelledby="portfolio-review-history-title"
      >
        <div className="section-heading stacked-heading">
          <span>포트폴리오 검토 결정 이력</span>
          <h2 id="portfolio-review-history-title">화면에서 본 판단이 나중에도 추적되는지 확인한다.</h2>
        </div>
        <p className="board-intro">
          {portfolioReviewHistory.attention_required
            ? "벤치마크 괴리와 포지션 크기 검토는 주문 지시가 아니다. 이 섹션은 그 판단 후보가 언제 어떤 근거로 저장됐는지 보여주는 감사 이력이다."
            : operationCopy(portfolioReviewHistory.managed_review_reason)}
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>상태</span>
            <strong className={`risk-tag ${portfolioReviewHistory.attention_required ? "risk-medium" : "risk-low"}`}>
              {portfolioReviewHistory.attention_required ? koCode(portfolioReviewHistory.decision_status) : "관리 중"}
            </strong>
            <small>{recordLabel(portfolioReviewHistory.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>기준일</span>
            <strong>{portfolioReviewHistory.as_of_date || "미저장"}</strong>
            <small>{portfolioReviewHistory.created_at || "생성 시각 없음"}</small>
          </article>
          <article className="rail-cell">
            <span>저장된 결정</span>
            <strong>{portfolioReviewHistory.decision_count}</strong>
            <small>확인 필요 {portfolioReviewHistory.review_required_count}개</small>
          </article>
          <article className="rail-cell">
            <span>벤치마크 / 포지션</span>
            <strong>
              {portfolioReviewHistory.benchmark_decision_count} / {portfolioReviewHistory.position_sizing_decision_count}
            </strong>
	            <small>판단군 분리 저장</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(portfolioReviewHistory.guardrails.order_boundary)}</strong>
	            <small>{orderSubmitCopy(portfolioReviewHistory.guardrails.broker_submit_allowed)}</small>
          </article>
        </div>
        {portfolioReviewHistory.latest_decisions.length > 0 ? (
          <div className="ledger-table-wrap">
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">순위</th>
                  <th scope="col">종목</th>
                  <th scope="col">결정</th>
	                  <th scope="col">판단군</th>
                  <th scope="col">근거</th>
                </tr>
              </thead>
              <tbody>
                {portfolioReviewHistory.latest_decisions.slice(0, 8).map((decision) => (
                  <tr key={`${decision.decision_family}-${decision.priority}-${decision.symbol}`}>
                    <td>{decision.priority.toString().padStart(2, "0")}</td>
                    <td>
                      <strong>{decision.symbol}</strong>
                      <small>{decision.related_recommendation_id || "추천 연결 없음"}</small>
                    </td>
                    <td>
                      <span className={`risk-tag ${decisionSeverityClass(decision.severity)}`}>
                        {decision.decision_label || koCode(decision.decision_type)}
                      </span>
                      <small>{operationCopy(koReason(decision.next_review_action))}</small>
                    </td>
                    <td>{operationCopy(decision.decision_family)}</td>
                    <td>
	                      <small>{operationCopy(koReason(decision.rationale || "저장된 설명 없음"))}</small>
	                      <small>{orderBoundaryCopy(decision.order_boundary)} · {orderSubmitCopy(decision.broker_submit_allowed)}</small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            아직 저장된 포트폴리오 검토 결정 이력이 없다. 최신 후보를 이력화하려면 검토 이력 저장 작업을 실행해야 한다.
          </div>
        )}
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(portfolioReviewHistory.next_action)}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="portfolio-review-feedback"
        aria-labelledby="portfolio-review-feedback-title"
      >
        <div className="section-heading stacked-heading">
          <span>포트폴리오 검토 사후평가</span>
          <h2 id="portfolio-review-feedback-title">저장한 판단이 나중의 성과와 맞았는지 본다.</h2>
        </div>
        <p className="board-intro">
	          이 섹션은 검토 결정을 추천 산식 반영 비중으로 바로 바꾸지 않는다. 저장된 축소 검토, 증액 금지, 유지 검토가
	          이후 추천 성과, 투자 논리 성과, 가상 매매 검증, 가격 변화와 맞았는지만 읽기 전용으로 평가한다.
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>평가 상태</span>
            <strong className={`risk-tag ${feedbackStatusClass(portfolioReviewFeedback.feedback_status)}`}>
              {koCode(portfolioReviewFeedback.feedback_status)}
            </strong>
            <small>{recordLabel(portfolioReviewFeedback.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>검증 / 반박</span>
            <strong>
              {portfolioReviewFeedback.validated_count} / {portfolioReviewFeedback.contradicted_count}
            </strong>
            <small>전체 {portfolioReviewFeedback.decision_count}개 결정</small>
          </article>
          <article className="rail-cell">
            <span>아직 이른 항목</span>
            <strong>{portfolioReviewFeedback.too_early_count}</strong>
            <small>{portfolioReviewFeedback.min_horizon_days}일 최소 관찰</small>
          </article>
          <article className="rail-cell">
            <span>근거 부족</span>
            <strong>{portfolioReviewFeedback.needs_more_data_count}</strong>
	            <small>성과/가상 매매/가격 보강 필요</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(portfolioReviewFeedback.guardrails.order_boundary)}</strong>
	            <small>{orderSubmitCopy(portfolioReviewFeedback.guardrails.broker_submit_allowed)}</small>
          </article>
        </div>
        {portfolioReviewFeedback.latest_items.length > 0 ? (
          <div className="ledger-table-wrap">
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">종목</th>
                  <th scope="col">원래 결정</th>
                  <th scope="col">사후평가</th>
                  <th scope="col">후속 근거</th>
                  <th scope="col">해석</th>
                </tr>
              </thead>
              <tbody>
                {portfolioReviewFeedback.latest_items.slice(0, 8).map((item) => (
                  <tr key={`${item.decision_index}-${item.symbol}-${item.feedback_status}`}>
                    <td>
                      <strong>{item.symbol}</strong>
                      <small>{item.source_decision.related_recommendation_id || "추천 연결 없음"}</small>
                    </td>
                    <td>
                      <span className={`risk-tag ${decisionSeverityClass(item.source_decision.severity)}`}>
                        {item.decision_label || koCode(item.decision_type)}
                      </span>
	                      <small>{operationCopy(koReason(item.source_decision.rationale || "원래 판단 설명 없음"))}</small>
                    </td>
                    <td>
                      <span className={`risk-tag ${feedbackStatusClass(item.feedback_status)}`}>
                        {koCode(item.feedback_status)}
                      </span>
	                      <small>{item.evidence.recommendation_outcome.outcome_label || "성과 미측정"}</small>
                    </td>
                    <td>
                      <small>
	                        초과수익 {formatPercent(item.evidence.recommendation_outcome.alpha_pct)} · 가격{" "}
                        {formatPercent(item.evidence.price_evidence.price_return_pct)}
                      </small>
                      <small>
	                        가상 매매 {operationCopy(item.evidence.paper_validation.status)} · 투자 논리 {operationCopy(item.evidence.thesis.status || "없음")}
                      </small>
                    </td>
                    <td>
	                      <small>{operationCopy(koReason(item.feedback_reason))}</small>
	                      <small>{orderBoundaryCopy(item.order_boundary)} · {orderSubmitCopy(item.broker_submit_allowed)}</small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
	            아직 검토 결정 사후평가가 없다. 먼저 검토 결정 이력을 저장하고, 이후 성과 측정 기간이 끝나면 사후평가를 실행한다.
          </div>
        )}
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(portfolioReviewFeedback.next_action)}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="portfolio-review-calibration"
        aria-labelledby="portfolio-review-calibration-title"
      >
        <div className="section-heading stacked-heading">
          <span>포트폴리오 검토 신뢰도 누적평가</span>
	          <h2 id="portfolio-review-calibration-title">성과 표본이 성숙하기 전에는 추천 산식 반영 비중을 바꾸지 않는다.</h2>
        </div>
        <p className="board-intro">
	          검토 결정은 최소 관찰 기간을 지난 뒤 실제 성과와 대조해야 한다. 이 섹션은 지금 추천 산식 변경이 왜
          막혀 있는지, 어떤 표본이 부족한지, 언제 다시 사후평가를 실행해야 하는지를 보여주는 읽기 전용 안전장치다.
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
	            <span>추천 산식 검토 상태</span>
            <strong className={`risk-tag ${portfolioReviewCalibration.managed_wait ? "risk-low" : portfolioReviewCalibration.weight_review_blocked ? "risk-medium" : "risk-low"}`}>
              {portfolioReviewCalibration.managed_wait
                ? "관리된 대기"
                : portfolioReviewCalibration.weight_review_blocked
                  ? "변경 금지"
                  : "성과 표본 충족"}
            </strong>
            <small>{operationCopy(portfolioReviewCalibration.maturity_status)} · {recordLabel(portfolioReviewCalibration.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
	            <span>사후평가 실행</span>
            <strong>
              {portfolioReviewCalibration.feedback_run_count}/{portfolioReviewCalibration.min_feedback_runs}
            </strong>
	            <small>부족 {portfolioReviewCalibration.feedback_run_gap}회 · {portfolioReviewCalibration.lookback_days || "기간 미확인"}일 관찰</small>
          </article>
          <article className="rail-cell">
            <span>성숙한 판단</span>
            <strong>
              {portfolioReviewCalibration.mature_decision_count}/{portfolioReviewCalibration.min_mature_decisions}
            </strong>
            <small>부족 {portfolioReviewCalibration.mature_decision_gap}개 · 전체 판단 {portfolioReviewCalibration.decision_count}개</small>
          </article>
          <article className="rail-cell">
            <span>예상 성숙일</span>
            <strong>{portfolioReviewCalibration.estimated_maturity_date || "계산 불가"}</strong>
            <small>
              {portfolioReviewCalibration.days_until_maturity === null
                ? "다음 실행 조건 미확인"
                : portfolioReviewCalibration.days_until_maturity > 0
                  ? `${portfolioReviewCalibration.days_until_maturity}일 대기`
                  : "다시 평가 가능일 도달"}
            </small>
          </article>
          <article className="rail-cell">
            <span>검증 / 반박률</span>
            <strong>
              {portfolioReviewCalibration.validated_count} / {formatPercent(portfolioReviewCalibration.contradiction_rate)}
            </strong>
            <small>허용 반박률 {formatPercent(portfolioReviewCalibration.max_contradiction_rate)}</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(portfolioReviewCalibration.guardrails.order_boundary)}</strong>
	            <small>{orderSubmitCopy(portfolioReviewCalibration.guardrails.broker_submit_allowed)}</small>
          </article>
        </div>
        <div className="empty-state">
	          <strong>{portfolioReviewCalibration.managed_wait ? "왜 열린 문제로 보지 않는가" : "왜 막혀 있나"}</strong>
          <p>
            {portfolioReviewCalibration.managed_wait
	              ? operationCopy(portfolioReviewCalibration.managed_gate_reason)
	              : operationCopy(portfolioReviewCalibration.weight_review_block_reason)}
          </p>
        </div>
        <div className="insight-grid">
          {portfolioReviewCalibration.family_summaries.slice(0, 3).map((summary) => (
            <article className="insight-card" key={`family-${summary.decision_family}`}>
	              <span>판단군</span>
              <strong>{koCode(summary.decision_family || "unknown")}</strong>
              <p>
                전체 {summary.decision_count}개 · 성숙 {summary.mature_decision_count}개 · 반박{" "}
                {summary.contradicted_count}개 · 아직 이른 판단 {summary.too_early_count}개
              </p>
            </article>
          ))}
          {portfolioReviewCalibration.symbol_summaries.slice(0, 3).map((summary) => (
            <article className="insight-card" key={`symbol-${summary.symbol}`}>
	              <span>종목별 사후평가</span>
              <strong>{summary.symbol || "미분류"}</strong>
              <p>
                성숙 {summary.mature_decision_count}개 · 검증 {summary.validated_count}개 · 반박률{" "}
                {formatPercent(summary.contradiction_rate)}
              </p>
            </article>
          ))}
          {portfolioReviewCalibration.family_summaries.length === 0
            && portfolioReviewCalibration.symbol_summaries.length === 0 ? (
              <article className="insight-card">
                <span>누적 자료 없음</span>
	                <strong>사후평가를 더 쌓아야 함</strong>
	                <p>검토 이력과 사후평가가 여러 번 쌓여야 별도 추천 산식 검토로 넘어갈 수 있다.</p>
              </article>
            ) : null}
        </div>
        {portfolioReviewCalibration.latest_feedback_runs.length > 0 ? (
          <div className="ledger-table-wrap">
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">평가 기록</th>
                  <th scope="col">기준일</th>
                  <th scope="col">상태</th>
                  <th scope="col">검증/반박</th>
                  <th scope="col">아직 이른 판단</th>
                </tr>
              </thead>
              <tbody>
                {portfolioReviewCalibration.latest_feedback_runs.map((run) => (
                  <tr key={`${run.eval_run_id}-${run.as_of_date}`}>
                    <td>{recordLabel(run.eval_run_id)}</td>
                    <td>{run.as_of_date || "기준일 없음"}</td>
                    <td>
                      <span className={`risk-tag ${feedbackStatusClass(run.feedback_status)}`}>
                        {koCode(run.feedback_status)}
                      </span>
                    </td>
                    <td>{run.validated_count} / {run.contradicted_count}</td>
                    <td>{run.too_early_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        <div className="empty-state">
          <strong>다음 조치</strong>
	          <p>{operationCopy(portfolioReviewCalibration.next_calibration_action || portfolioReviewCalibration.next_action)}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="portfolio-review-cadence"
        aria-labelledby="portfolio-review-cadence-title"
      >
        <div className="section-heading stacked-heading">
          <span>포트폴리오 검토 실행시점</span>
          <h2 id="portfolio-review-cadence-title">사후평가와 누적평가를 언제 다시 돌릴지 판단한다.</h2>
        </div>
        <p className="board-intro">
	          검토 이력, 성과 측정 기간, 가격·가상 매매 검증 근거, 최신 사후평가, 최신 누적평가의 연결 상태를 보고
	          기다릴지, 사후평가를 실행할지, 누적평가를 실행할지 결정한다. 이 판단도 주문이나 추천 산식 변경이 아니다.
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
	            <span>실행 주기 상태</span>
            <strong className={`risk-tag ${cadenceStatusClass(portfolioReviewCadence.cadence_status)}`}>
              {koCode(portfolioReviewCadence.cadence_status)}
            </strong>
            <small>{recordLabel(portfolioReviewCadence.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>실행 여부</span>
            <strong>{portfolioReviewCadence.should_run_now ? "지금 실행" : "즉시 실행 아님"}</strong>
            <small>{portfolioReviewCadence.should_wait ? "대기 필요" : "대기 조건 없음"}</small>
          </article>
          <article className="rail-cell">
            <span>검토 이력 나이</span>
            <strong>{portfolioReviewCadence.evidence.history_age_days}일</strong>
            <small>최소 {portfolioReviewCadence.min_horizon_days}일 관찰</small>
          </article>
          <article className="rail-cell">
            <span>근거 연결률</span>
            <strong>
              {portfolioReviewCadence.evidence.recommendation_outcome_count}/
              {portfolioReviewCadence.evidence.recommendation_link_count}
            </strong>
	            <small>성과 연결 · 가격 {portfolioReviewCadence.evidence.price_evidence_count}개</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(portfolioReviewCadence.order_boundary)}</strong>
	            <small>{orderSubmitCopy(portfolioReviewCadence.broker_submit_allowed)}</small>
          </article>
        </div>
        <div className="insight-grid">
          <article className="insight-card">
            <span>다음 명령</span>
            <strong>{koCode(portfolioReviewCadence.action_type)}</strong>
	            <p>{operationCopy(portfolioReviewCadence.label)}</p>
	            <small>{operationCopy(portfolioReviewCadence.reason)}</small>
          </article>
          <article className="insight-card">
            <span>후속 명령</span>
            <strong>{portfolioReviewCadence.follow_up_command ? "있음" : "없음"}</strong>
            <p>{portfolioReviewCadence.follow_up_command || "현재 후속 명령은 없다."}</p>
          </article>
          <article className="insight-card">
	            <span>검토 이력 → 사후평가</span>
            <strong>
              {recordLabel(portfolioReviewCadence.history.eval_run_id)} → {recordLabel(portfolioReviewCadence.feedback.eval_run_id)}
            </strong>
            <p>
	              이력 {portfolioReviewCadence.history.decision_count}개 · 사후평가{" "}
              {portfolioReviewCadence.feedback.decision_count}개 · 상태{" "}
              {koCode(portfolioReviewCadence.feedback.feedback_status)}
            </p>
          </article>
          <article className="insight-card">
	            <span>사후평가 → 누적평가</span>
            <strong>
              {recordLabel(portfolioReviewCadence.feedback.eval_run_id)} → {recordLabel(portfolioReviewCadence.calibration.eval_run_id)}
            </strong>
            <p>
	              누적 사후평가 {portfolioReviewCadence.calibration.feedback_run_count}회 · 성숙 판단{" "}
              {portfolioReviewCadence.calibration.mature_decision_count}개
            </p>
          </article>
          <article className="insight-card">
	            <span>가상 매매 검증</span>
            <strong>{operationCopy(portfolioReviewCadence.evidence.paper_validation.status)}</strong>
            <p>
              검증일 {portfolioReviewCadence.evidence.paper_validation.validation_date || "없음"} · 충돌{" "}
              {portfolioReviewCadence.evidence.paper_validation.conflict_count}개
            </p>
          </article>
          <article className="insight-card">
	            <span>추천 산식 반영 비중</span>
            <strong>{portfolioReviewCadence.automatic_weight_change_allowed ? "변경 허용" : "변경 금지"}</strong>
	            <p>실행 주기 판단은 실행 순서만 정한다. 추천 점수와 포트폴리오 비중은 바꾸지 않는다.</p>
          </article>
        </div>
        <div className="empty-state">
          <strong>다음 조치</strong>
	          <p>{operationCopy(portfolioReviewCadence.next_action)}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="portfolio-review-action-router"
        aria-labelledby="portfolio-review-action-router-title"
      >
        <div className="section-heading stacked-heading">
	          <span>포트폴리오 검토 실행 분기</span>
          <h2 id="portfolio-review-action-router-title">대기할지, 사후평가를 돌릴지, 누적평가를 돌릴지 기록한다.</h2>
        </div>
        <p className="board-intro">
	          실행 주기는 “언제 실행해야 하는가”를 판단하고, 실행 분기는 그 판단을 안전한 후속 작업으로 바꾼다.
	          이 실행 분기가 동작해도 추천 산식 반영 비중, 보유 비중, 주문 전송은 자동으로 바뀌지 않는다.
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
	            <span>실행 분기 결과</span>
            <strong className={`risk-tag ${actionRouterStatusClass(portfolioReviewActionRouter.action_status)}`}>
              {actionRouterTitle(portfolioReviewActionRouter)}
            </strong>
            <small>{recordLabel(portfolioReviewActionRouter.eval_run_id)}</small>
          </article>
          <article className="rail-cell">
	            <span>원천 실행 주기</span>
            <strong>{koCode(portfolioReviewActionRouter.cadence_status)}</strong>
            <small>{recordLabel(portfolioReviewActionRouter.source_cadence_eval_run_id)}</small>
          </article>
          <article className="rail-cell">
            <span>라우팅</span>
            <strong>{koCode(portfolioReviewActionRouter.route_action)}</strong>
            <small>요청 작업 {koCode(portfolioReviewActionRouter.source_action_type)}</small>
          </article>
          <article className="rail-cell">
            <span>실행한 작업</span>
            <strong>{portfolioReviewActionRouter.child_runner.executed ? "있음" : "없음"}</strong>
            <small>
              {portfolioReviewActionRouter.child_runner.executed
                ? `${operationCopy(portfolioReviewActionRouter.child_runner.report_name)} · ${recordLabel(portfolioReviewActionRouter.child_runner.eval_run_id)}`
	                : "성과 관찰 또는 안전 조건 때문에 후속 실행을 시작하지 않았다."}
            </small>
          </article>
          <article className="rail-cell rail-critical">
            <span>실거래 상태</span>
            <strong>{orderBoundaryCopy(portfolioReviewActionRouter.order_boundary)}</strong>
	            <small>{orderSubmitCopy(portfolioReviewActionRouter.broker_submit_allowed)}</small>
          </article>
        </div>
        <div className="insight-grid">
          <article className="insight-card">
            <span>왜 이 결론인가</span>
            <strong>{koCode(portfolioReviewActionRouter.action_status)}</strong>
	            <p>{operationCopy(portfolioReviewActionRouter.reason || "저장된 설명 없음")}</p>
          </article>
          <article className="insight-card">
            <span>검토 이력 연결</span>
            <strong>{recordLabel(portfolioReviewActionRouter.history_eval_run_id)}</strong>
            <p>
	              사후평가 {recordLabel(portfolioReviewActionRouter.feedback_eval_run_id)} · 누적평가{" "}
              {recordLabel(portfolioReviewActionRouter.calibration_eval_run_id)}
            </p>
          </article>
          <article className="insight-card">
	            <span>후속 실행 상태</span>
            <strong>{koCode(portfolioReviewActionRouter.child_runner.status)}</strong>
            <p>
              실행 기록 {recordLabel(portfolioReviewActionRouter.child_runner.run_id)}
	              {portfolioReviewActionRouter.child_runner.feedback_status
	                ? ` · 사후평가 ${koCode(portfolioReviewActionRouter.child_runner.feedback_status)}`
	                : ""}
	              {portfolioReviewActionRouter.child_runner.calibration_status
	                ? ` · 누적평가 ${koCode(portfolioReviewActionRouter.child_runner.calibration_status)}`
	                : ""}
            </p>
          </article>
          <article className="insight-card">
            <span>안전 장치</span>
	            <strong>{portfolioReviewActionRouter.automatic_weight_change_allowed ? "추천 산식 변경 허용" : "추천 산식 변경 금지"}</strong>
            <p>
              리밸런싱 {portfolioReviewActionRouter.automatic_rebalance_allowed ? "허용" : "금지"} · 주문{" "}
              {portfolioReviewActionRouter.automatic_order_allowed ? "허용" : "금지"}
            </p>
          </article>
        </div>
	        <div className="empty-state">
	          <strong>다음 조치</strong>
	          <p>{operationCopy(portfolioReviewActionRouter.next_action)}</p>
	        </div>
	      </section>

	        </div>
	      </details>

	      <section className="feature-map-panel reveal delay-1" aria-labelledby="scheduler-profile-title">
        <div className="section-heading stacked-heading">
          <span>자동 실행 주기</span>
          <h2 id="scheduler-profile-title">
            {ec2SchedulerInstalled ? "현재 서버에서 실제로 도는 작업" : "자동 실행 연결 상태"}
          </h2>
        </div>
        <p className="board-intro">
          웹 화면은 작업을 직접 실행하지 않고 저장된 결과를 읽는다. 실제 수집과 분석은 아래 작업들이 각자 다른 주기로 실행한다.
        </p>
        {schedulerCadenceGroups.length > 0 ? (
          <div className="cadence-group-grid">
            {schedulerCadenceGroups.map((group) => (
              <article className="cadence-group-card" key={group.key}>
                <div className="cadence-group-head">
                  <span>{group.label}</span>
                  <strong>{group.title}</strong>
                  <small>{group.description}</small>
                </div>
                <dl className="cadence-group-metrics">
                  <div>
                    <dt>상태</dt>
                    <dd>
                      <span className={`risk-tag ${schedulerGroupTone(group)}`}>
                        {schedulerGroupStatusLabel(group)}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt>예약</dt>
                    <dd>
                      {group.activeCount}/{group.timers.length}개 활성 · 성공 {group.successCount}개
                    </dd>
                  </div>
                  <div>
                    <dt>다음 실행</dt>
                    <dd>{schedulerGroupNextElapse(group)}</dd>
                  </div>
                </dl>
                <div className="timer-chip-list" aria-label={`${group.title} 세부 예약`}>
                  {group.timers.map((timer) => (
                    <div className="timer-chip" key={timer.profile_id}>
                      <b>{koCode(timer.profile_id)}</b>
                      <span>{timer.schedule || "스케줄 미확인"}</span>
                      <small>
                        {koCode(timer.active_state)} · {koCode(timer.last_result || "unknown")}
                      </small>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            아직 화면에 연결된 서버 예약 실행 스케줄이 없다. 수동 실행 결과와 실행 로그만 참고한다.
          </div>
        )}
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
          <span>상세 운영 기록</span>
          <strong>스케줄, 실행 요약, 수동 점검, 작업별 실행 구조를 필요할 때만 펼친다</strong>
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
            <h3>웹 화면은 저장된 결과를 읽고, 서버 예약 작업이 수집·분석을 실행한다</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            FastAPI와 Next.js는 저장된 결과를 읽어 보여준다. 뉴스 수집, 캔들 보강, AI 분석, 추천 갱신은
            서버 예약 실행기가 백그라운드 작업 실행기를 호출해 수행하고, 결과는 서버 저장 기록과 실행 요약에 남긴다.
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
              <dd>서버 예약 실행 → 백그라운드 작업 실행기</dd>
            </div>
            <div>
              <dt>상태 저장</dt>
              <dd>서버 저장 기록 + 저장소 밖 실행 요약</dd>
            </div>
          </dl>
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>서버 반복 실행기</span>
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
            <h3>AI 근거 이후에는 추천·투자 논리·보유 상태로 넘어간다</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            뉴스 분석은 끝점이 아니다. 수집된 뉴스는 이벤트와 AI 근거가 되고, 이후 가격·테마·사이클 데이터와
            결합되어 중장기 추천 항목, 투자 논리, 보유 상태 큐를 만든다. 주문은 자동 실행하지 않는다.
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
	            <h3>{ec2SchedulerInstalled ? "현재 서버 자동화의 주 근거가 아니다" : localWorkerTitle(localWorker)}</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            {ec2SchedulerInstalled
              ? "이 기록은 서버 예약 실행기를 붙이기 전 로컬 MVP 단계의 점검 결과다. 현재 자동 실행 판단은 위의 서버 반복 실행기와 작업 실행 이력을 우선한다."
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
                    <td>{cycle.artifact_run_count}개 기록</td>
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
              ? "이 기록은 수동으로 데이터 수집 경로를 검증했던 증거다. 현재 서버 운영 상태를 판단할 때는 서버 반복 실행기와 최신 작업 실행 이력을 먼저 본다."
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
                        <small>{operationCopy(run.pipeline_name)}</small>
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
                      <strong>{operationCopy(run.pipeline_name)}</strong>
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

          <article className="ledger-panel" id="active-recommendation-price-freshness">
            <div className="section-heading stacked-heading">
              <span>추천 종목 가격</span>
              <h2>추천에 쓰는 가격이 최신인지 확인</h2>
              <p>
                추천, 성과 측정, 가상 매매 검증은 종목별 가격을 읽는다. 여기서 오래된 종목이 보이면 가격 보강이 먼저다.
              </p>
            </div>
            <dl className="fact-list">
              <div>
                <dt>상태</dt>
                <dd>
                  <span className={`risk-tag ${activeRecommendationPriceFreshness.attention_required ? "risk-high" : "risk-low"}`}>
                    {activeRecommendationPriceFreshness.attention_required ? "가격 보강 필요" : "최신성 확인"}
                  </span>
                </dd>
              </div>
              <div>
                <dt>추천 종목</dt>
                <dd>
                  {activeRecommendationPriceFreshness.fresh_symbol_count}/{activeRecommendationPriceFreshness.active_symbol_count}개 최신
                </dd>
              </div>
              <div>
                <dt>최신 가격일</dt>
                <dd>{activeRecommendationPriceFreshness.global_latest_trade_date || "미확인"}</dd>
              </div>
              <div>
                <dt>뒤처진 종목</dt>
                <dd>
                  오래됨 {activeRecommendationPriceFreshness.stale_symbol_count}개 · 없음{" "}
                  {activeRecommendationPriceFreshness.missing_symbol_count}개
                </dd>
              </div>
              <div>
                <dt>거래 경계</dt>
                <dd>{orderBoundaryCopy(activeRecommendationPriceFreshness.order_boundary)}</dd>
              </div>
            </dl>
            <p className="panel-copy">{operationCopy(activeRecommendationPriceFreshness.next_action)}</p>
            {activeRecommendationPriceFreshness.stale_symbols.length > 0 ? (
              <div className="flow-steps data-health-summary-grid">
                {activeRecommendationPriceFreshness.stale_symbols.slice(0, 8).map((item) => (
                  <a className="flow-step" href={item.detail_href || `/stocks/${item.symbol}`} key={item.symbol}>
                    <span>{koCode(item.status)}</span>
                    <strong>{item.symbol}</strong>
                    <p>
                      최근 가격 {item.latest_trade_date || "없음"} · 최신 기준보다 {item.days_behind_latest}일 뒤처짐 ·
                      연결 추천 {item.active_recommendation_count}개
                    </p>
                  </a>
                ))}
              </div>
            ) : null}
          </article>

          <article className="ledger-panel" id="runtime-boundary">
            <div className="section-heading stacked-heading">
              <span>조건과 최신성</span>
              <h2>조건과 데이터 최신성</h2>
            </div>
            {openGateDetails.length > 0 ? (
              <div className="flow-steps data-health-summary-grid" style={{ marginBottom: "18px" }}>
                {openGateDetails.map((gate) => (
                  <div className="flow-step" key={gate.gate_id}>
                    <span>{gate.category_label}</span>
                    <strong>{gate.label}</strong>
                    <p>{gate.summary}</p>
                    <dl className="fact-list compact-facts">
                      <div>
                        <dt>상태</dt>
                        <dd>
                          <span className={`risk-tag risk-${gate.severity}`}>{gate.status_label}</span>
                        </dd>
                      </div>
                      <div>
                        <dt>다음 행동</dt>
                        <dd>{openGateCopy(gate.next_action)}</dd>
                      </div>
                      <div>
                        <dt>실거래 상태</dt>
                        <dd>{orderBoundaryCopy(gate.order_boundary)}</dd>
                      </div>
                    </dl>
                  </div>
                ))}
              </div>
            ) : null}
            <div className="tag-ledger">
              {openGateChips.map((gate) => (
                <span className={`risk-tag ${gate.tone}`} key={gate.key}>
                  {gate.label}
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
                <dt>읽기 서버</dt>
                <dd>{productionApiServer.attention_required ? "확인 필요" : "운영 준비 확인"}</dd>
              </div>
              <div>
                <dt>데이터 연결</dt>
                <dd>
                  {koCode(productionApiServer.runtime_profile)} · {koCode(productionApiServer.source_mode)} ·{" "}
                  {koCode(productionApiServer.connection_boundary)}
                </dd>
              </div>
              <div>
                <dt>읽기 보호</dt>
                <dd>
                  {koCode(productionApiServer.auth_mode)} · 읽기 토큰{" "}
                  {productionApiServer.read_token_configured ? "설정됨" : "미설정"} · 허용 출처{" "}
                  {productionApiServer.allowed_origin_configured ? "명시됨" : "미설정"}
                </dd>
              </div>
              <div>
                <dt>조회 권한</dt>
                <dd>{authRbac.attention_required ? "확인 필요" : "읽기 전용 권한 확인"}</dd>
              </div>
              <div>
                <dt>읽기 범위</dt>
                <dd>
                  {koCode(authRbac.read_role)} · 보호된 화면 {authRbac.protected_paths.length.toLocaleString("ko-KR")}개 · 읽기 요청만 허용
                </dd>
              </div>
              <div>
                <dt>주문/쓰기 차단</dt>
                <dd>
                  쓰기 {authRbac.write_methods_allowed ? "허용됨" : "차단됨"} · 주문{" "}
                  {authRbac.broker_submit_allowed ? "허용됨" : "차단됨"} · {orderBoundaryCopy(authRbac.order_boundary)}
                </dd>
              </div>
              <div>
                <dt>권한 다음 조치</dt>
                <dd>{operationCopy(authRbac.next_action)}</dd>
              </div>
              <div>
                <dt>API 다음 조치</dt>
                <dd>{operationCopy(productionApiServer.next_action)}</dd>
              </div>
              <div>
                <dt>알림 목적지</dt>
                <dd>{alertDestination.attention_required ? "확인 필요" : "외부 알림 검증됨"}</dd>
              </div>
              <div>
                <dt>알림 방식</dt>
                <dd>
                  {koCode(alertDestination.mode)} · 목적지{" "}
                  {alertDestination.target_configured ? "설정됨" : "미설정"} · 테스트{" "}
                  {alertDestination.last_test_status === "passed" && alertDestination.test_recent
                    ? "통과"
                    : "미검증"}
                </dd>
              </div>
              <div>
                <dt>알림 다음 조치</dt>
                <dd>{operationCopy(alertDestination.next_action)}</dd>
              </div>
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
	            <div>
	              <dt>실행 증거</dt>
	              <dd>{artifactRunner.attention_required ? "확인 필요" : "운영 증거 확인됨"}</dd>
	            </div>
	            <div>
	              <dt>저장 정책</dt>
	              <dd>
	                {artifactRunner.artifact_policy_count}/{artifactRunner.job_count}개 · 최신 실행{" "}
	                {artifactRunner.latest_run_count}개
	              </dd>
	            </div>
	            <div>
	              <dt>실행 증거 경로</dt>
	              <dd>{artifactRunner.latest_artifact_root || "경로 미표시"}</dd>
	            </div>
	            <div>
	              <dt>실행 증거 다음 조치</dt>
	              <dd>{operationCopy(artifactRunner.next_action)}</dd>
	            </div>
            </dl>
          </article>
        </aside>
      </section>
      </details>
    </div>
  );
}
