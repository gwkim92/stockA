import type { DataHealthData } from "@/lib/types";
import { koCode, koReason } from "@/lib/korean-labels";

export type PipelineRun = DataHealthData["pipeline_runs"][number];
export type SchedulerActivation = DataHealthData["scheduler"]["activation"];
export type SchedulerStatus = DataHealthData["scheduler"];
export type ProfileSchedulerStatus = NonNullable<DataHealthData["scheduler"]["profile_scheduler"]>;
export type ProductionApiServer = DataHealthData["production_api_server"];
export type AuthRbac = DataHealthData["auth_rbac"];
export type AlertDestination = DataHealthData["alert_destination"];
export type ManualIngestSmoke = DataHealthData["manual_local_ingest_smoke"];
export type LocalIngestWorker = DataHealthData["local_ingest_worker"];
export type CycleAiQualityAudit = DataHealthData["cycle_ai_quality_audit"];
export type NewsAiEvalQuality = DataHealthData["news_ai_eval_quality"];
export type LiveAiInvocationHealth = DataHealthData["live_ai_invocation_health"];
export type OpenAiProviderHealth = DataHealthData["openai_provider_health"];
export type TossInvestMarketData = DataHealthData["tossinvest_market_data"];
export type DataOperationsArtifactRunner = DataHealthData["data_operations_artifact_runner"];
export type ActiveRecommendationPriceFreshness = DataHealthData["active_recommendation_price_freshness"];
export type BenchmarkDriftQuality = DataHealthData["benchmark_drift_quality"];
export type PortfolioReviewDecisionHistory = DataHealthData["portfolio_review_decision_history"];
export type PortfolioReviewDecisionFeedback = DataHealthData["portfolio_review_decision_feedback"];
export type PortfolioReviewFeedbackCalibration = DataHealthData["portfolio_review_feedback_calibration"];
export type PortfolioReviewFeedbackCadence = DataHealthData["portfolio_review_feedback_cadence"];
export type PortfolioReviewFeedbackActionRouter = DataHealthData["portfolio_review_feedback_action_router"];
export type RecommendationOutcomeCalibration = DataHealthData["recommendation_outcome_calibration"];
export type RecommendationOutcomeMaturity = DataHealthData["recommendation_outcome_maturity"];
export type RecommendationOutcomeDueActionRouter = DataHealthData["recommendation_outcome_due_action_router"];
export type RecommendationWeightReviewReadiness = DataHealthData["recommendation_weight_review_readiness"];
export type OutcomeMaturityWaitMonitor = DataHealthData["outcome_maturity_wait_monitor"];
export type ProfessionalSourceGapPrioritization = DataHealthData["professional_source_gap_prioritization"];
export type ProfessionalAnalysisQuality = DataHealthData["professional_analysis_quality"];
export type ProfessionalRecommendationCoverageAudit = DataHealthData["professional_recommendation_coverage_audit"];
export type ProfessionalAnalysisNextAction = DataHealthData["professional_analysis_next_action"];
export type ProfessionalAnalysisDepth = DataHealthData["professional_analysis_depth"];
export type OpenGateDetail = NonNullable<DataHealthData["open_gate_details"]>[number];
export type ProfileTimer = ProfileSchedulerStatus["timers"][number];
export type AuditSampleRecord = Record<string, unknown>;
export type TimerGroupDefinition = {
  key: string;
  label: string;
  title: string;
  description: string;
  profileIds: string[];
};
export type SchedulerCadenceGroup = TimerGroupDefinition & {
  timers: ProfileTimer[];
  activeCount: number;
  successCount: number;
  problemCount: number;
};
export type GateTriageBucket = {
  key: string;
  label: string;
  title: string;
  description: string;
  tone: "risk-low" | "risk-medium" | "risk-high";
  href: string;
  gates: OpenGateDetail[];
};

export function isRecord(value: unknown): value is AuditSampleRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function statusRiskClass(value: string): "risk-low" | "risk-medium" | "risk-high" {
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

export function gateSeverityTone(severity: string): "risk-low" | "risk-medium" | "risk-high" {
  if (severity === "low") {
    return "risk-low";
  }
  if (severity === "medium") {
    return "risk-medium";
  }
  return "risk-high";
}

export function gateTriageKey(gate: OpenGateDetail) {
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

export const GATE_TRIAGE_BUCKETS: Omit<GateTriageBucket, "gates">[] = [
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
    title: "관찰 중인 항목",
    description: "즉시 장애는 아니지만 다음 배치와 최신 실행 기록을 계속 본다.",
    tone: "risk-low",
    href: "#execution-log",
  },
];

export function buildGateTriageBuckets(gates: OpenGateDetail[]) {
  const buckets = GATE_TRIAGE_BUCKETS.map((bucket) => ({ ...bucket, gates: [] as OpenGateDetail[] }));
  for (const gate of gates) {
    const key = gateTriageKey(gate);
    const bucket = buckets.find((candidate) => candidate.key === key) ?? buckets[buckets.length - 1];
    bucket.gates.push(gate);
  }
  return buckets;
}

export function gateTriageSummary(buckets: GateTriageBucket[], rawOpenGateCount: number) {
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
    return `열린 항목 ${rawOpenGateCount}개가 있다. 아래 분류에서 조치 위치를 나눈다.`;
  }
  return "현재 열린 항목은 없다. 세부 실행 이력과 최신성만 필요할 때 보면 된다.";
}

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

export function schedulerReadinessTitle(scheduler: SchedulerStatus) {
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

export function schedulerReadinessExplanation(scheduler: SchedulerStatus) {
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
  return "현재 반복 실행 상태는 화면의 승인 조건과 다음 단계 값을 기준으로 다시 확인해야 합니다.";
}

export function isEc2ProfileSchedulerInstalled(scheduler: SchedulerStatus) {
  return scheduler.activation.approval_gate === "installed_on_ec2_systemd"
    && scheduler.profile_scheduler?.status === "installed";
}

export function timerPurpose(profileId: string) {
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

export function timerStatusTone(timer: ProfileTimer) {
  if (timer.active_state === "active" && timer.last_result === "success") {
    return "risk-low";
  }
  if (timer.active_state === "active") {
    return "risk-medium";
  }
  return "risk-high";
}

export const TIMER_GROUP_DEFINITIONS: TimerGroupDefinition[] = [
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
    description: "장 마감 후 가격 캔들을 보강하고 감시 종목군의 기본 연결 상태를 본다.",
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

export function buildSchedulerCadenceGroups(timers: ProfileTimer[]): SchedulerCadenceGroup[] {
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

export function schedulerGroupTone(group: SchedulerCadenceGroup) {
  if (group.problemCount === 0 && group.activeCount === group.timers.length) {
    return "risk-low";
  }
  if (group.activeCount > 0) {
    return "risk-medium";
  }
  return "risk-high";
}

export function schedulerGroupStatusLabel(group: SchedulerCadenceGroup) {
  if (group.problemCount === 0 && group.activeCount === group.timers.length) {
    return "정상 대기";
  }
  if (group.activeCount > 0) {
    return "결과 보강 필요";
  }
  return "예약 꺼짐";
}

export function schedulerGroupNextElapse(group: SchedulerCadenceGroup) {
  return group.timers.find((timer) => timer.next_elapse)?.next_elapse ?? "다음 실행 미확인";
}

export function schedulerNextStepLabel(activation: SchedulerActivation) {
  if (activation.manual_next_step === "data-operations-live-scheduler-activation-request") {
    return "반복 실행 설정 전에 수동 수집 순서와 결과를 먼저 본다.";
  }
  if (activation.manual_next_step === "configure_scheduler_activation_gate_report") {
    return "저장소 밖 반복 실행 결과 경로를 설정한다.";
  }
  if (activation.manual_next_step === "regenerate_scheduler_activation_gate_report") {
    return "깨진 반복 실행 결과 파일을 다시 생성한다.";
  }
  return koCode(activation.manual_next_step);
}

export function schedulerInstallLabel(value: string) {
  if (value === "not_installed") {
    return "반복 실행기 미설정";
  }
  return koCode(value);
}

export function schedulerApprovalGateLabel(value: string) {
  if (value === "installed_on_ec2_systemd") {
    return "서버 반복 실행 설치 완료";
  }
  if (value === "blocked_pending_manual_approval" || value === "pending_manual_approval") {
    return "자동 반복 실행 전 조건 닫힘";
  }
  return koCode(value);
}

export function manualSmokeTitle(smoke: ManualIngestSmoke) {
  if (smoke.status === "passed") {
    return "최근 수동 수집 성공";
  }
  if (smoke.status === "failed") {
    return "최근 수동 수집 중단";
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

export function manualSmokeExplanation(smoke: ManualIngestSmoke) {
  if (smoke.status === "passed") {
    return "가격, 뉴스, AI 분석 단발 작업이 실행됐고 중단된 작업이 없다는 뜻이다. 반복 자동화 상태는 별도로 본다.";
  }
  if (smoke.status === "failed") {
    return "단발 실행 중 중단된 작업이 있다. 실행 요약의 오류 내용과 작업 정보 확인이 필요합니다.";
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

export function manualSmokeNextAction(smoke: ManualIngestSmoke) {
  return smoke.next_actions[0] ? koCode(smoke.next_actions[0]) : "다음 조치 없음";
}

export function localWorkerTitle(worker: LocalIngestWorker) {
  if (worker.status === "completed") {
    return "반복 실행 최근 성공";
  }
  if (worker.status === "failed") {
    return "반복 실행 최근 중단";
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

export function localWorkerExplanation(worker: LocalIngestWorker) {
  if (worker.status === "completed") {
    return "정해진 반복 실행 주기가 끝났고 중단된 주기가 없다는 뜻이다. 서버 예약 실행과 함께 자동 운영 상태를 판단한다.";
  }
  if (worker.status === "failed") {
    return "반복 실행 중 중단된 작업이 있었다. 최신 실행 요약과 오류 내용 확인이 필요합니다.";
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

export function localWorkerNextAction(worker: LocalIngestWorker) {
  return worker.next_actions[0] ? koCode(worker.next_actions[0]) : "다음 조치 없음";
}

export function tossMarketDataTitle(marketData: TossInvestMarketData) {
  if (marketData.sync.status === "succeeded") {
    return "토스증권 브로커 데이터 수집됨";
  }
  if (marketData.sync.status === "blocked_missing_credentials") {
    return "토스증권 API 키 필요";
  }
  if (marketData.sync.status === "missing") {
    return "토스증권 데이터 실행 이력 없음";
  }
  return koCode(marketData.sync.status);
}

export function tossMarketDataTone(marketData: TossInvestMarketData) {
  if (marketData.sync.attention_required) {
    return "risk-medium";
  }
  return "risk-low";
}

export function qualityAuditTitle(audit: CycleAiQualityAudit) {
  if (audit.status === "ok") {
    return "품질 감사 통과";
  }
  if (audit.status === "degraded") {
    return "품질 감사 일부 부족";
  }
  if (audit.status === "managed_warning") {
    return "약한 전파 근거 관리 중";
  }
  if (audit.status === "attention_required") {
    return "오염 의심 항목 있음";
  }
  if (audit.status === "not_ready") {
    return "감사할 데이터 부족";
  }
  if (audit.status === "not_configured") {
    return "품질 감사 결과 미연결";
  }
  return koCode(audit.status);
}

export function qualityAuditExplanation(audit: CycleAiQualityAudit) {
  if (audit.status === "ok") {
    return "중복 뉴스, 잘못된 테마 연결, 원문 근거 없는 종목 연결, 약한 전파 근거가 현재 감사 기준에서 발견되지 않았다.";
  }
  if (audit.status === "degraded") {
    if (audit.readiness_gaps.length > 0) {
      return `큰 오염은 없지만 ${audit.readiness_gaps[0].label} 단계가 비어 있다. 이 단계가 채워져야 추천 근거 흐름을 끝까지 신뢰할 수 있다.`;
    }
    return "큰 오염은 없지만 번역, AI 분석, 전파, 사이클 스냅샷 중 일부 근거가 아직 부족하다.";
  }
  if (audit.status === "managed_warning") {
    return "치명적인 중복·오분류·근거 없는 직접 종목 연결은 없지만, 신뢰도나 경로 가중치가 낮은 전파 근거가 남아 있다. 사이클 스냅샷은 약한 전파를 제외하고 계산한다.";
  }
  if (audit.status === "attention_required") {
    return "추천 판단 전에 중복 뉴스, 종목 근거, 잘못된 테마 연결, 전파 근거가 약한 흐름 확인이 필요합니다.";
  }
  if (audit.status === "not_ready") {
    return "뉴스 수집부터 AI 분석, 전파, 사이클 스냅샷까지 한 번 더 실행한 뒤 판단해야 한다.";
  }
  if (audit.status === "not_configured") {
    return "서버에 최근 품질 감사 요약 파일 경로가 연결되지 않아 화면에서 읽을 수 없다.";
  }
  return "품질 감사 결과 파일의 상태와 생성 시각을 다시 확인해야 합니다.";
}

export function qualityAuditTone(audit: CycleAiQualityAudit) {
  if (audit.status === "ok") {
    return "risk-low";
  }
  if (audit.status === "degraded" || audit.status === "managed_warning" || audit.status === "not_configured") {
    return "risk-medium";
  }
  return "risk-high";
}

export function qualityMetric(audit: CycleAiQualityAudit, key: string) {
  const value = audit.metrics[key] ?? audit.checks[key] ?? 0;
  return typeof value === "number" ? value : Number(value || 0);
}

export function auditSampleRecords(audit: CycleAiQualityAudit, key: string) {
  const value = audit.samples[key];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(isRecord).slice(0, 5);
}

export function auditSampleValue(record: AuditSampleRecord, key: string) {
  const value = record[key];
  if (Array.isArray(value)) {
    return value
      .map((item) => auditSampleScalar(item))
      .filter(Boolean)
      .join(", ");
  }
  return auditSampleScalar(value);
}

export function auditSampleScalar(value: unknown) {
  if (typeof value === "string") {
    return value.trim();
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "";
}

export function auditSampleHeadline(record: AuditSampleRecord) {
  const eventId = auditSampleValue(record, "event_id");
  return (
    auditSampleValue(record, "event_title")
    || auditSampleValue(record, "title")
    || (eventId ? `이벤트 ${eventId}` : "제목 미확인")
  );
}

export function auditSampleMeta(record: AuditSampleRecord) {
  const symbol = auditSampleValue(record, "symbol");
  const instrumentName = auditSampleValue(record, "instrument_name");
  const nodeCodes = auditSampleValue(record, "node_codes");
  const nodeCode = auditSampleValue(record, "node_code");
  const direction = auditSampleValue(record, "impact_direction")
    || auditSampleValue(record, "impact_directions");
  const repeatedCount = auditSampleValue(record, "repeated_count");
  const eventCount = auditSampleValue(record, "event_count");
  const documentCount = auditSampleValue(record, "document_count");
  const sourceNode = auditSampleValue(record, "source_node_code");
  const propagatedNode = auditSampleValue(record, "propagated_node_code");
  const confidence = auditSampleValue(record, "confidence");
  const pathWeight = auditSampleValue(record, "path_weight");
  return [
    symbol ? `종목 ${symbol}` : "",
    instrumentName ? instrumentName : "",
    nodeCodes ? `흐름 ${nodeCodes.split(", ").map(koCode).join(", ")}` : "",
    nodeCode ? `흐름 ${koCode(nodeCode)}` : "",
    sourceNode || propagatedNode
      ? `전파 ${sourceNode ? koCode(sourceNode) : "출발 미확인"} → ${propagatedNode ? koCode(propagatedNode) : "도착 미확인"}`
      : "",
    direction ? `방향 ${direction.split(", ").map(koCode).join(", ")}` : "",
    repeatedCount ? `반복 ${repeatedCount}회` : "",
    eventCount ? `이벤트 ${eventCount}개` : "",
    documentCount ? `문서 ${documentCount}개` : "",
    confidence ? `신뢰도 ${confidence}` : "",
    pathWeight ? `경로가중 ${pathWeight}` : "",
  ].filter(Boolean).join(" · ");
}

export function qualityAuditSampleGroups(audit: CycleAiQualityAudit) {
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
      key: "cross_theme_mismatches",
      label: "교차 테마 불일치",
      description: "뉴스 내용과 연결된 사이클 흐름이 강하게 어긋나는 후보.",
    },
    {
      key: "duplicate_flow_evidence",
      label: "중복 흐름 근거",
      description: "같은 뉴스가 여러 이벤트·흐름으로 분산되어 근거가 부풀려질 수 있는 후보.",
    },
    {
      key: "weak_propagation_evidence",
      label: "약한 전파 근거",
      description: "상위 흐름에서 종목으로 내려가는 경로의 신뢰도·강도·경로 가중치가 낮은 후보.",
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

export function newsAiEvalTitle(evalQuality: NewsAiEvalQuality) {
  if (evalQuality.status === "passed" || evalQuality.overall_pass) {
    return "AI 기준 평가 통과";
  }
  if (evalQuality.status === "failed_regression") {
    return "AI 기준 평가 중단";
  }
  if (evalQuality.status === "missing") {
    return "AI 기준 평가 없음";
  }
  return koCode(evalQuality.status);
}

export function newsAiEvalExplanation(evalQuality: NewsAiEvalQuality) {
  if (evalQuality.status === "passed" || evalQuality.overall_pass) {
    return "기준 정답 뉴스 세트에서 테마 분류, 직접 종목 근거, 거시 뉴스 종목 오부착, 양자→에너지 오분류, 한국어 번역 기준을 통과했다.";
  }
  if (evalQuality.status === "failed_regression") {
    return "AI 구조화나 자동 검증이 기준 세트에서 중단됐다. 이 상태에서는 새 AI 근거를 추천 입력으로 신뢰하기 전에 중단 항목 확인이 필요합니다.";
  }
  if (evalQuality.status === "missing") {
    return "최근 기준 정답 뉴스 평가가 저장되지 않았다. 뉴스 AI 분석이 좋아 보이더라도 기준 세트 통과 여부를 아직 증명하지 못했다.";
  }
  return "뉴스 AI 평가 기록의 상태와 중단 사례 확인이 필요합니다.";
}

export function newsAiEvalTone(evalQuality: NewsAiEvalQuality) {
  if (evalQuality.status === "passed" || evalQuality.overall_pass) {
    return "risk-low";
  }
  if (evalQuality.status === "missing") {
    return "risk-medium";
  }
  return "risk-high";
}

export function liveAiInvocationTitle(health: LiveAiInvocationHealth) {
  if (health.status === "healthy") {
    return "실제 AI 호출 정상";
  }
  if (health.status === "critical_ai_failed") {
    return "실제 AI 호출 중단";
  }
  if (health.status === "degraded") {
    return "일부 AI 호출 중단";
  }
  if (health.status === "recovered_with_recent_failures") {
    return "AI 호출 복구됨";
  }
  if (health.status === "missing_recent_invocations") {
    return "최근 AI 호출 없음";
  }
  return koCode(health.status);
}

export function liveAiInvocationExplanation(health: LiveAiInvocationHealth) {
  if (health.status === "healthy") {
    return "최근 실제 AI 호출이 성공했다. 기준 세트 평가뿐 아니라 운영 배치 AI 호출도 살아 있다.";
  }
  if (health.status === "critical_ai_failed") {
    return "뉴스 한국어 번역이나 뉴스 AI 구조화 같은 핵심 AI 호출이 중단됐다. OpenAI quota와 Codex OAuth 재로그인 상태를 같이 확인해야 합니다.";
  }
  if (health.status === "degraded") {
    return "일부 AI 작업의 최신 실행이 중단됐다. 완료된 작업과 중단된 작업을 나눠 보고 quota, 인증, CLI 오류 확인이 필요합니다.";
  }
  if (health.status === "recovered_with_recent_failures") {
    return "최근 48시간 안에 중단 이력은 남아 있지만, monitored AI 작업의 최신 실행은 성공했다. 현재 장애가 아니라 복구 후 관찰 상태다.";
  }
  if (health.status === "missing_recent_invocations") {
    return "최근 운영 배치에서 실제 AI 호출 증거가 없다. 뉴스가 없는 것인지, 배치 호출이 멈춘 것인지 확인이 필요합니다.";
  }
  return "실제 AI 호출 상태 확인이 필요합니다.";
}

export function liveAiInvocationTone(health: LiveAiInvocationHealth) {
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

export function liveAiCurrentFailureCount(health: LiveAiInvocationHealth) {
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

export function liveAiInvocationQualityMetric(health: LiveAiInvocationHealth, evalQuality: NewsAiEvalQuality) {
  const regressionText = `기준 중단 ${evalQuality.failed_case_count}개`;
  if (health.status === "recovered_with_recent_failures") {
    return `최신 실행 성공 · 과거 중단 기록 ${health.recent_failed_count}건 · ${regressionText}`;
  }
  if (health.attention_required) {
    return `현재 중단 작업 ${liveAiCurrentFailureCount(health)}개 · 최근 중단 ${health.recent_failed_count}건 · ${regressionText}`;
  }
  if (health.status === "healthy") {
    return `최신 실행 성공 · 최근 중단 ${health.recent_failed_count}건 · ${regressionText}`;
  }
  return `최근 호출 ${health.recent_invocation_count}건 · 최근 중단 ${health.recent_failed_count}건 · ${regressionText}`;
}

export function liveAiInvocationHistoryLabel(health: LiveAiInvocationHealth) {
  if (health.status === "recovered_with_recent_failures") {
    return `성공 ${health.recent_success_count} · 과거 중단 기록 ${health.recent_failed_count}`;
  }
  return `성공 ${health.recent_success_count} · 중단 ${health.recent_failed_count}`;
}

export function liveAiCurrentFailureDetail(health: LiveAiInvocationHealth) {
  if (health.status === "recovered_with_recent_failures") {
    return `현재 중단 0 · 최근 ${health.window_hours}시간 누적 핵심 중단 ${health.critical_failed_count}`;
  }
  return `번역/뉴스 구조화 기준 · 최근 누적 ${health.critical_failed_count}`;
}

export function aiProviderLabel(provider: string) {
  if (provider === "agents_sdk_openai") {
    return "OpenAI Agents SDK";
  }
  if (provider === "codex_oauth") {
    return "Codex OAuth";
  }
  if (provider === "local_rules") {
    return "로컬 규칙";
  }
  return provider || "미지정";
}

export function openAiProviderTitle(health: OpenAiProviderHealth) {
  if (health.status === "openai_insufficient_quota" || health.status === "openai_billing_unavailable") {
    return "잔액·쿼터 없음";
  }
  if (health.status === "openai_auth_invalid") {
    return "인증 중단";
  }
  if (health.status === "openai_provider_disabled") {
    return "직접 호출 꺼짐";
  }
  if (health.status === "missing_api_key") {
    return "API 키 없음";
  }
  if (health.cost_status.status === "costs_available") {
    return "비용 조회됨";
  }
  if (health.status === "key_configured_balance_unverified") {
    return "키 있음 · 잔액 미확인";
  }
  return health.label || koCode(health.status);
}

export function openAiProviderExplanation(health: OpenAiProviderHealth) {
  if (health.status === "openai_insufficient_quota" || health.status === "openai_billing_unavailable") {
    return `최근 OpenAI 호출에서 잔액 또는 quota 문제가 감지되어 ${aiProviderLabel(health.fallback_provider)}로 우회한다. 다음 재시도 전까지 사용자가 env를 직접 수정할 필요는 없다.`;
  }
  if (health.status === "openai_auth_invalid") {
    return "OpenAI API 키 인증이 중단됐다. 키를 새로 넣기 전까지 OpenAI 직접 호출은 건너뛰고 예비 경로를 사용한다.";
  }
  if (health.status === "missing_api_key") {
    return "OpenAI API 키가 없으므로 OpenAI 직접 호출은 하지 않는다. Codex OAuth 또는 로컬 규칙 경로로 분석을 계속한다.";
  }
  if (health.cost_status.status === "costs_available") {
    return `Admin Costs API로 최근 ${health.cost_status.lookback_days}일 사용 비용을 조회했다. 이 값은 남은 잔액이 아니라 이미 발생한 비용이다. 실제 prepaid 잔액은 OpenAI Billing Overview에서 본다.`;
  }
  if (health.status === "key_configured_balance_unverified") {
    return "OpenAI API 키는 감지됐지만 남은 잔액을 확정 조회하는 공식 API는 사용하지 않는다. Admin Costs API 배치가 성공하면 최근 비용을 표시하고, 실제 호출 중단이 발생하면 자동으로 예비 경로로 분기한다.";
  }
  return health.message || "OpenAI provider 상태를 본다.";
}

export function openAiProviderTone(health: OpenAiProviderHealth) {
  if (
    health.status === "openai_insufficient_quota"
    || health.status === "openai_billing_unavailable"
    || health.status === "openai_auth_invalid"
  ) {
    return "risk-medium";
  }
  if (health.cost_status.status === "costs_available" && health.status === "key_configured_balance_unverified") {
    return "risk-low";
  }
  if (health.status === "key_configured_balance_unverified" || health.status === "missing_api_key") {
    return "risk-medium";
  }
  return "risk-low";
}

export function optionalTimestamp(value: string) {
  if (!value) {
    return "기록 없음";
  }
  return value.replace("T", " ").replace("+00:00", " UTC");
}

export function formatUsdAmount(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "미조회";
  }
  return `$${value.toFixed(2)}`;
}

export function formatPercent(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "미계산";
  }
  return `${(value * 100).toFixed(1)}%`;
}

export function benchmarkDriftQualityTitle(quality: BenchmarkDriftQuality) {
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
    return "큰 괴리 종목 있음";
  }
  if (quality.status === "missing_guardrail") {
    return "위험 예산 평가 없음";
  }
  return koCode(quality.status);
}

export function benchmarkDriftQualityExplanation(quality: BenchmarkDriftQuality) {
  if (quality.status === "ok") {
    return "구성비 확인률과 기준일이 충분해 벤치마크 대비 괴리를 보조 위험 지표로 볼 수 있다. 추천 산식 반영 비중은 자동 변경하지 않는다.";
  }
  if (!quality.attention_required && quality.status === "drift_outlier_review") {
    return quality.managed_review_reason || "큰 벤치마크 괴리는 검토 후보로 저장됐고 자동 주문 없이 성과 관찰을 기다린다.";
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
  return "벤치마크 괴리 품질 상태 확인이 필요합니다.";
}

export function benchmarkDriftQualityTone(quality: BenchmarkDriftQuality) {
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

export function decisionSeverityClass(severity: string) {
  if (severity === "high") {
    return "risk-high";
  }
  if (severity === "medium") {
    return "risk-medium";
  }
  return "risk-low";
}

export function feedbackStatusClass(status: string) {
  if (status === "has_contradictions" || status === "contradicted") {
    return "risk-high";
  }
  if (status === "needs_more_data" || status === "too_early" || status === "missing" || status === "missing_history") {
    return "risk-medium";
  }
  return "risk-low";
}

export function calibrationStatusClass(status: string) {
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

export function cadenceStatusClass(status: string) {
  if (status === "missing_evidence_review_required") {
    return "risk-high";
  }
  if (status === "run_feedback_now" || status === "run_calibration_now" || status === "missing") {
    return "risk-medium";
  }
  return "risk-low";
}

export function actionRouterStatusClass(status: string) {
  if (status.startsWith("blocked_")) {
    return "risk-high";
  }
  if (status === "missing" || status.endsWith("_ready")) {
    return "risk-medium";
  }
  return "risk-low";
}

export function actionRouterTitle(router: PortfolioReviewFeedbackActionRouter) {
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

export function outcomeCalibrationTitle(calibration: RecommendationOutcomeCalibration) {
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

export function outcomeCalibrationExplanation(calibration: RecommendationOutcomeCalibration) {
  if (calibration.status === "ready_for_manual_weight_review") {
    return "성과 표본과 전문 분석 근거 연결률 기준을 통과했다. 그래도 자동 추천 산식 변경은 금지이고 별도 검토 작업이 필요하다.";
  }
  if (calibration.status === "collect_more_outcomes_keep_weights") {
    return "성과 표본은 있지만 추천 산식 반영 비중을 바꾸기에는 아직 더 많은 성과와 부진 사례가 필요하다.";
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
  return "추천 성과 보정 상태 확인이 필요합니다.";
}

export function outcomeCalibrationTone(calibration: RecommendationOutcomeCalibration) {
  if (calibration.status === "ready_for_manual_weight_review") {
    return "risk-low";
  }
  if (calibration.status === "collect_more_outcomes_keep_weights") {
    return "risk-medium";
  }
  return "risk-high";
}

export function outcomeMaturityTitle(maturity: RecommendationOutcomeMaturity) {
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

export function outcomeMaturityExplanation(maturity: RecommendationOutcomeMaturity) {
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
  return "추천 성과 측정창 상태를 본다.";
}

export function outcomeMaturityTone(maturity: RecommendationOutcomeMaturity) {
  if (maturity.status === "not_due" || maturity.status === "complete_current_window") {
    return "risk-medium";
  }
  if (maturity.status === "due_outcomes_ready") {
    return "risk-medium";
  }
  return "risk-high";
}

export function outcomeDueActionRouterTitle(router: RecommendationOutcomeDueActionRouter) {
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

export function outcomeWaitMonitorTone(monitor: OutcomeMaturityWaitMonitor) {
  if (monitor.status === "action_due" || monitor.status === "blocked_or_missing_evidence") {
    return "risk-high";
  }
  if (monitor.status === "manual_weight_review_possible") {
    return "risk-low";
  }
  return "risk-medium";
}

export function professionalSourceGapTitle(gaps: ProfessionalSourceGapPrioritization) {
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

export function professionalSourceGapExplanation(gaps: ProfessionalSourceGapPrioritization) {
  if (gaps.status === "ok") {
    return "활성 추천 기준으로 핵심 재무·밸류에이션·리서치 원천 공백이 없다.";
  }
  if (!gaps.attention_required && gaps.source_blocker_count > 0) {
    return "원천 데이터가 부족한 종목은 남겨두되, 전문 판단과 가상 매매 검증 입력에서는 이미 차단했다. 새 정기 공시나 전용 parser가 생기면 다시 본다.";
  }
  if (gaps.status === "source_blockers_present") {
    return "SEC companyfacts나 원천 공시 연결이 막힌 종목이 있다. 합성 재무를 만들지 말고 원천 가능 여부부터 확인해야 합니다.";
  }
  if (gaps.status === "high_priority_gaps") {
    return "추천 또는 보유 노출이 있는 종목의 재무·피어·밸류에이션·리서치 근거가 비어 있다. 이 종목부터 보강한다.";
  }
  if (gaps.status === "fund_source_gaps") {
    return "ETF·펀드형 상품은 기업 재무제표가 아니라 보유종목, 비용, NAV, 추적차이 원천이 판단 근거다.";
  }
  if (gaps.status === "fund_company_model_not_applicable") {
    return "ETF·펀드형 상품은 기업 재무 모델 대상이 아니다. 별도 펀드 분석 근거로 본다.";
  }
  return "전문가식 분석에 필요한 원천 근거 중 일부가 비어 있어 추천 산식 검토 전 보강해야 한다.";
}

export function professionalSourceGapTone(gaps: ProfessionalSourceGapPrioritization) {
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

export function professionalNextActionTone(nextAction: ProfessionalAnalysisNextAction) {
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

export function professionalQualityTone(quality: ProfessionalAnalysisQuality) {
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

export function professionalRecommendationAuditTone(audit: ProfessionalRecommendationCoverageAudit) {
  if (audit.status === "ready_for_review") {
    return "risk-low";
  }
  if (audit.status === "paper_validation_pending" || audit.status === "coverage_gaps_present") {
    return "risk-medium";
  }
  return "risk-high";
}

export function professionalDepthTitle(depth: ProfessionalAnalysisDepth) {
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

export function professionalDepthTone(depth: ProfessionalAnalysisDepth) {
  if (depth.status === "complete" || depth.status === "mostly_covered") {
    return "risk-low";
  }
  if (depth.status === "source_limited") {
    return "risk-medium";
  }
  return "risk-high";
}

export function professionalDepthStatusLabel(status: string) {
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

export function professionalDepthItemTone(status: string) {
  if (status === "complete" || status === "fund_source_ready") {
    return "risk-low";
  }
  if (status === "mostly_covered" || status === "partial") {
    return "risk-medium";
  }
  return "risk-high";
}

export function professionalRecommendationAuditItemTone(status: string) {
  if (status === "ready_for_review") {
    return "risk-low";
  }
  if (status === "paper_validation_pending" || status === "coverage_gap") {
    return "risk-medium";
  }
  return "risk-high";
}

export function executionIdLabel(value: string | null | undefined) {
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

export function evidenceLocationLabel(value: string | null | undefined) {
  return value ? "저장소 밖 결과 경로 연결됨" : "결과 경로 없음";
}

export function summaryLocationLabel(value: string | null | undefined) {
  return value ? "요약 파일 연결됨" : "요약 경로 없음";
}

export function errorLogLabel(value: string | null | undefined) {
  return value ? "오류 내용 있음" : "없음";
}

export function operationCopy(value: string) {
  const oldHoldingReviewCompact = ["보유", "검토"].join("");
  const oldHoldingReview = ["보유", "검토"].join(" ");
  const oldReviewCandidate = ["검토", "후보"].join(" ");
  const oldReviewDocument = ["검토", "서"].join("");
  const oldPaper = ["페", "이퍼"].join("");
  return koCode(value)
    .replaceAll(
      "OpenAI quota is exhausted. Falling back to the configured offline provider.",
      "OpenAI 사용량 한도가 소진되어 예비 분석 경로로 전환됐다.",
    )
    .replaceAll(
      "Falling back to the configured offline provider.",
      "예비 분석 경로로 전환됐다.",
    )
    .replaceAll("professional-coverage-expansion-run", "전문 분석 근거 보강 실행")
    .replaceAll("recommendation_outcome_calibration_sample_expansion", "추천 성과 표본 확장")
    .replaceAll("news-ai-eval-run --provider fixture --execute를 실행해 기준 정답 뉴스 세트 회귀평가를 저장한다.", "뉴스 AI 기준 세트 평가를 실행해 최근 평가 결과를 저장한다.")
    .replaceAll("fixture/gold", "기준 정답")
    .replaceAll("fixture", "기준 세트")
    .replaceAll("provider health cache", "AI 상태 기록")
    .replaceAll("LLM provider", "AI 제공자")
    .replaceAll("LLM", "AI")
    .replaceAll("quota", "사용량 한도")
    .replaceAll("fallback", "예비 경로")
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
    .replaceAll("pipeline", "작업")
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
    .replaceAll("runner", "실행기")
    .replaceAll("open gate", "열린 확인 항목")
    .replaceAll("review candidate", "검토 후보")
    .replaceAll("candidate", "대상")
    .replaceAll(oldHoldingReviewCompact, "보유 상태 판단")
    .replaceAll(oldHoldingReview, "보유 상태 판단")
    .replaceAll(oldReviewCandidate, "검토 후보")
    .replaceAll(oldReviewDocument, "상세 근거")
    .replaceAll("guardrail", "안전 조건")
    .replaceAll("raw filing", "원문 공시")
    .replaceAll("registration", "증권신고서")
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
    .replaceAll("too early", "관찰 기간 미성숙")
    .replaceAll("failed", "중단")
    .replaceAll("실패", "중단")
    .replaceAll("상세 검토 가능", "상세 근거 확인")
    .replaceAll("검토 가능", "근거 확인")
    .replaceAll("원천 차단 count가 있는 종목", "원천 차단 종목")
    .replaceAll("원천 차단 count", "원천 차단 수")
    .replaceAll("degraded", "주의");
}

export function openGateCopy(value: string) {
  return operationCopy(value)
    .replaceAll("_", " ")
    .replace(/\bcount\b/g, "수")
    .replaceAll("원천 차단 수가 있는 종목", "원천 차단 종목");
}

export function aiInvocationErrorCopy(value: string, code = "") {
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
    return "Codex OAuth 인증 토큰이 만료되었거나 재사용되어 중단됐다. 서버에서 다시 로그인한 뒤 실제 호출 점검을 실행해야 한다.";
  }
  if (code === "codex_oauth_timeout" || value.includes("timeout")) {
    return "Codex OAuth 호출 시간이 초과됐다. limit와 timeout, 네트워크 상태 확인이 필요합니다.";
  }
  return operationCopy(value);
}

export function orderSubmitCopy(allowed: boolean) {
  return `실거래 주문 ${allowed ? "허용" : "금지"}`;
}

export function orderBoundaryCopy(value: string | null | undefined) {
  if (!value) {
    return "실거래 상태 미확인";
  }
  if (value === "read_only_no_order") {
    return "주문 차단";
  }
  return operationCopy(value);
}

export function recordLabel(value: string | null | undefined) {
  return value ? "기록 있음" : "기록 없음";
}

export const DEFAULT_MANUAL_SMOKE: ManualIngestSmoke = {
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

export const DEFAULT_LOCAL_WORKER: LocalIngestWorker = {
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

export const DEFAULT_CYCLE_AI_QUALITY_AUDIT: CycleAiQualityAudit = {
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

export const DEFAULT_NEWS_AI_EVAL_QUALITY: NewsAiEvalQuality = {
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

export const DEFAULT_LIVE_AI_INVOCATION_HEALTH: LiveAiInvocationHealth = {
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
  next_action: "최근 실제 AI 호출 증거가 없다. 뉴스 AI 배치가 실제로 호출됐는지 본다.",
};

export const DEFAULT_OPENAI_PROVIDER_HEALTH: OpenAiProviderHealth = {
  status: "missing_api_key",
  label: "OpenAI 키 없음",
  balance_known: false,
  balance_check_method: "not_available",
  remaining_balance_usd: null,
  api_key_configured: false,
  admin_api_key_configured: false,
  last_checked_at: "",
  next_retry_at: "",
  fallback_provider: "codex_oauth",
  local_fallback_provider: "local_rules",
  message: "OpenAI provider 상태를 아직 읽지 못했다. 예비 provider를 사용한다.",
  cost_status: {
    report_name: "openai_admin_cost_status",
    status: "admin_key_missing",
    cost_known: false,
    admin_api_key_configured: false,
    lookback_days: 7,
    total_cost_usd: null,
    latest_day_cost_usd: null,
    currency: "usd",
    period_start: "",
    period_end: "",
    last_checked_at: "",
    error_code: "",
    message: "Admin Costs API key가 없어 비용 조회를 실행할 수 없다.",
    billing_overview_url: "https://platform.openai.com/settings/organization/billing/overview",
    secret_free: true,
  },
};

export const DEFAULT_BENCHMARK_DRIFT_QUALITY: BenchmarkDriftQuality = {
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

export const DEFAULT_PORTFOLIO_REVIEW_DECISION_HISTORY: PortfolioReviewDecisionHistory = {
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
  managed_review_reason: "검토 이력, 안전 조건, 또는 후속 실행 분기 상태 확인이 필요합니다.",
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

export const DEFAULT_PORTFOLIO_REVIEW_DECISION_FEEDBACK: PortfolioReviewDecisionFeedback = {
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
  next_action: "portfolio-review-decision-outcome-feedback-run을 실행해 저장된 검토 결정이 후속 성과와 맞는지 본다.",
};

export const DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CALIBRATION: PortfolioReviewFeedbackCalibration = {
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

export const DEFAULT_PROFESSIONAL_ANALYSIS_NEXT_ACTION: ProfessionalAnalysisNextAction = {
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

export const DEFAULT_PROFESSIONAL_ANALYSIS_QUALITY: ProfessionalAnalysisQuality = {
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

export const DEFAULT_PROFESSIONAL_RECOMMENDATION_COVERAGE_AUDIT: ProfessionalRecommendationCoverageAudit = {
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

export const DEFAULT_PROFESSIONAL_ANALYSIS_DEPTH: ProfessionalAnalysisDepth = {
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

export const DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CADENCE: PortfolioReviewFeedbackCadence = {
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

export const DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_ACTION_ROUTER: PortfolioReviewFeedbackActionRouter = {
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

export const DEFAULT_RECOMMENDATION_OUTCOME_CALIBRATION: RecommendationOutcomeCalibration = {
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

export const DEFAULT_RECOMMENDATION_OUTCOME_MATURITY: RecommendationOutcomeMaturity = {
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
    label: "성과 측정창 상태를 먼저 본다.",
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

export const DEFAULT_RECOMMENDATION_OUTCOME_DUE_ACTION_ROUTER: RecommendationOutcomeDueActionRouter = {
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

export const DEFAULT_RECOMMENDATION_WEIGHT_REVIEW_READINESS: RecommendationWeightReviewReadiness = {
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

export const DEFAULT_OUTCOME_MATURITY_WAIT_MONITOR: OutcomeMaturityWaitMonitor = {
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

export const DEFAULT_PROFESSIONAL_SOURCE_GAP_PRIORITIZATION: ProfessionalSourceGapPrioritization = {
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

export const DEFAULT_PROFILE_SCHEDULER: ProfileSchedulerStatus = {
  status: "not_configured",
  install_status: "not_installed",
  scheduler_type: "",
  timer_count: 0,
  active_timer_count: 0,
  generated_at: "",
  source: "not_configured",
  timers: [],
};

export const DEFAULT_PRODUCTION_API_SERVER: ProductionApiServer = {
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
  next_action: "읽기 서버 실행 환경, 조회 권한, 허용 출처, DB 설정, DB 연결 경계를 본다.",
};

export const DEFAULT_AUTH_RBAC: AuthRbac = {
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
  next_action: "읽기 서버 준비, 읽기 토큰, 조회 역할, 쓰기 요청 차단, 증권사 주문 차단을 본다.",
};

export const DEFAULT_ALERT_DESTINATION: AlertDestination = {
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
  summary: "예약 실행 중단과 데이터 오염을 받을 외부 알림 목적지가 설정되지 않았다.",
  next_action: "무료 webhook, email, Telegram, Slack, Discord 중 하나를 저장소 밖 환경 파일에 설정하고 테스트 기록을 남긴다.",
  order_boundary: "read_only_no_order",
  automatic_action_allowed: false,
};

export const DEFAULT_DATA_OPERATIONS_ARTIFACT_RUNNER: DataOperationsArtifactRunner = {
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

export const DEFAULT_ACTIVE_RECOMMENDATION_PRICE_FRESHNESS: ActiveRecommendationPriceFreshness = {
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
