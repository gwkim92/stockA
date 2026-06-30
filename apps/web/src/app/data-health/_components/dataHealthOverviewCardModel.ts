import type { DataHealthCommandCard } from "@/components/operations/DataHealthOverview";
import { koCode } from "@/lib/korean-labels";

import { liveAiInvocationQualityMetric } from "./dataHealthAiProviderModel";
import { formatPercent } from "./dataHealthCopyModel";
import { automationStateLabel } from "./dataHealthRunModel";
import type {
  CycleAiQualityAudit,
  DataHealthData,
  LiveAiInvocationHealth,
  NewsAiEvalQuality,
  OutcomeMaturityWaitMonitor,
  ProfessionalAnalysisQuality,
  ProfessionalSourceGapPrioritization,
  ProfileSchedulerStatus,
  SchedulerActivation,
} from "./dataHealthTypes";

type BuildDataHealthHeadlineInput = {
  readonly failedPipelines: number;
  readonly openGateCount: number;
};

type BuildDataHealthMetaItemsInput = {
  readonly openGateCount: number;
  readonly outcomeWaitMonitor: OutcomeMaturityWaitMonitor;
  readonly providerBudget: DataHealthData["provider_budget"];
  readonly schedulerActivation: SchedulerActivation;
};

type BuildDataHealthCommandCardsInput = {
  readonly allTimersActive: boolean;
  readonly dataQualityReady: boolean;
  readonly dueNowGateCount: number;
  readonly failedPipelines: number;
  readonly fixNowGateCount: number;
  readonly investmentReviewGateCount: number;
  readonly liveAiInvocationHealth: LiveAiInvocationHealth;
  readonly managedWaitGateCount: number;
  readonly newsAiEvalQuality: NewsAiEvalQuality;
  readonly openGateCount: number;
  readonly outcomeWaitMonitor: OutcomeMaturityWaitMonitor;
  readonly professionalQuality: ProfessionalAnalysisQuality;
  readonly professionalSourceGaps: ProfessionalSourceGapPrioritization;
  readonly profileScheduler: ProfileSchedulerStatus;
  readonly qualityAudit: CycleAiQualityAudit;
  readonly safeInvestmentBoundary: boolean;
  readonly sourceLimitGateCount: number;
};

export function buildDataHealthHeadline({
  failedPipelines,
  openGateCount,
}: BuildDataHealthHeadlineInput) {
  if (failedPipelines > 0) {
    return `즉시 조치가 필요한 작업 ${failedPipelines.toLocaleString("ko-KR")}개`;
  }
  if (openGateCount > 0) {
    return `자동화와 원천 제한 ${openGateCount.toLocaleString("ko-KR")}개 관리 중`;
  }
  return "수집·분석 상태 정상";
}

export function buildDataHealthMetaItems({
  openGateCount,
  outcomeWaitMonitor,
  providerBudget,
  schedulerActivation,
}: BuildDataHealthMetaItemsInput) {
  return [
    `자동 실행 ${automationStateLabel(schedulerActivation)}`,
    `보강 필요 항목 ${openGateCount.toLocaleString("ko-KR")}개`,
    `호출 예산 ${providerBudget.remaining_request_count}/${providerBudget.daily_budget}`,
    `실거래 상태 ${koCode(outcomeWaitMonitor.order_boundary)}`,
  ];
}

function firstActionHref(input: BuildDataHealthCommandCardsInput) {
  if (input.fixNowGateCount > 0) {
    return "#open-gate-triage-title";
  }
  if (input.dueNowGateCount > 0) {
    return "#outcome-maturity-wait-monitor";
  }
  if (input.sourceLimitGateCount > 0) {
    return "#professional-source-gaps";
  }
  if (input.managedWaitGateCount > 0) {
    return "#outcome-maturity-wait-monitor";
  }
  return "#execution-log";
}

function firstActionTitle(input: BuildDataHealthCommandCardsInput) {
  if (input.fixNowGateCount > 0) {
    return `즉시 조치 ${input.fixNowGateCount}개`;
  }
  if (input.dueNowGateCount > 0) {
    return `성과 실행 ${input.dueNowGateCount}개`;
  }
  if (input.sourceLimitGateCount > 0) {
    return `원천 한계 ${input.sourceLimitGateCount}개 관리`;
  }
  if (input.managedWaitGateCount > 0) {
    return `성과 대기 ${input.managedWaitGateCount}개`;
  }
  if (input.openGateCount > 0) {
    return `점검 항목 ${input.openGateCount}개`;
  }
  return "열린 항목 없음";
}

function firstActionBody(input: BuildDataHealthCommandCardsInput) {
  if (input.fixNowGateCount > 0) {
    return "수집·AI·접근 장애가 있으면 추천 화면보다 먼저 복구해야 한다.";
  }
  if (input.dueNowGateCount > 0) {
    return "성과 측정창이 열렸거나 사후평가 실행 조건이 됐다. 주문 없이 검증 작업만 실행한다.";
  }
  if (input.sourceLimitGateCount > 0) {
    return "원천 한계는 오류를 숨기는 것이 아니라 합성 데이터를 만들지 않고 판단 입력에서 제외한 상태다.";
  }
  if (input.managedWaitGateCount > 0) {
    return "성과 측정창이 끝날 때까지 기다리는 설계된 대기다. 추천 산식 변경은 계속 막는다.";
  }
  return "즉시 조치할 장애는 없다. 최신 실행과 품질 샘플만 아래에서 보면 된다.";
}

function firstActionCta(input: BuildDataHealthCommandCardsInput) {
  if (input.fixNowGateCount > 0) {
    return "즉시 조치 보기";
  }
  if (input.dueNowGateCount > 0) {
    return "성과 실행 보기";
  }
  if (input.sourceLimitGateCount > 0) {
    return "원천 한계 보기";
  }
  if (input.managedWaitGateCount > 0) {
    return "성과 대기 보기";
  }
  return "실행 이력 보기";
}

export function buildDataHealthCommandCards(input: BuildDataHealthCommandCardsInput): DataHealthCommandCard[] {
  return [
    {
      label: "1. 지금 먼저",
      title: firstActionTitle(input),
      body: firstActionBody(input),
      metric: `${input.openGateCount.toLocaleString("ko-KR")}개 열린 항목`,
      href: firstActionHref(input),
      cta: firstActionCta(input),
      tone: input.fixNowGateCount > 0
        ? "block"
        : input.dueNowGateCount > 0 || input.sourceLimitGateCount > 0 || input.managedWaitGateCount > 0
          ? "watch"
          : "ready",
    },
    {
      label: "2. 자동 수집",
      title: input.allTimersActive && input.failedPipelines === 0 ? "자동 수집 작동 중" : "자동 수집 증거 부족",
      body: input.allTimersActive
        ? "뉴스, 가격, 추천, 성과 측정 작업이 각각의 서버 예약 실행기로 분리되어 돈다."
        : "예약 실행기 일부가 꺼졌거나 실행 증거가 부족하다. 멈춘 작업 묶음을 먼저 찾는다.",
      metric: `${input.profileScheduler.active_timer_count}/${input.profileScheduler.timer_count}개 활성 · 문제 실행 ${input.failedPipelines}개`,
      href: "#scheduler-detail",
      cta: "자동화 보기",
      tone: input.allTimersActive && input.failedPipelines === 0 ? "ready" : "watch",
    },
    {
      label: "3. 뉴스·AI 품질",
      title: input.dataQualityReady
        ? "품질 기준 통과"
        : input.liveAiInvocationHealth.attention_required
          ? "실제 AI 호출 증거 부족"
          : input.qualityAudit.issue_count > 0 || input.newsAiEvalQuality.failed_case_count > 0
            ? "오염 의심 항목 있음"
            : "품질 근거 보강 중",
      body: input.dataQualityReady
        ? "뉴스 오염 감사, AI 기준 평가, 실제 Codex OAuth 호출이 모두 통과했다. 벤치마크 괴리 품질과 세부 샘플은 아래에서 본다."
        : input.liveAiInvocationHealth.attention_required
          ? "기준 세트 평가가 통과해도 실제 AI 호출이 중단되면 뉴스 번역과 AI 구조화는 규칙 기반 대체 결과일 수 있다. 실제 호출 상태를 먼저 본다."
          : input.qualityAudit.issue_count > 0 || input.newsAiEvalQuality.failed_case_count > 0
            ? "중복 뉴스, 오분류, AI 기준 평가 중단, 벤치마크 괴리 품질 중 확인할 항목이 있다. 추천 입력 전에 품질 근거를 본다."
            : "큰 오염은 없지만 번역, 전파, 사이클 스냅샷, 가상 매매 검증 근거가 아직 부족하다. 벤치마크 괴리 품질도 함께 본다.",
      metric: liveAiInvocationQualityMetric(input.liveAiInvocationHealth, input.newsAiEvalQuality),
      href: "#quality-audit",
      cta: "품질 감사 보기",
      tone: input.dataQualityReady ? "ready" : "watch",
    },
    {
      label: "4. 투자 안전",
      title: input.safeInvestmentBoundary ? "추천 산식·실거래 차단" : "투자 경계 불일치",
      body: input.safeInvestmentBoundary
        ? "성과 표본이 성숙하기 전까지 추천 산식 반영 비중 변경과 실거래 주문 제출은 막혀 있다."
        : "추천 산식 검토나 실거래 상태 조건이 예상과 다르다. 추천 산식/거래 안전 상태를 먼저 본다.",
      metric: input.outcomeWaitMonitor.weight_review_blocked ? "반영 비중 변경 금지 · 주문 차단" : "투자 경계 불일치",
      href: "#outcome-maturity-wait-monitor",
      cta: "투자 경계 보기",
      tone: input.safeInvestmentBoundary ? "ready" : "block",
    },
    {
      label: "5. 원천·전문분석",
      title: input.professionalSourceGaps.source_blocker_count > 0
        ? `원천 차단 ${input.professionalSourceGaps.source_blocker_count}개`
        : input.professionalQuality.status === "managed_source_limited"
          ? "원천 한계 관리 중"
          : "전문 분석 연결 상태",
      body: input.professionalSourceGaps.source_blocker_count > 0
        ? "표준 재무 원천이 부족한 종목은 전문 판단과 가상 매매 입력에서 제외한다."
        : "재무·피어·밸류에이션·산업·AI 리서치 근거가 추천별로 얼마나 채워졌는지 본다.",
      metric: `평균 연결률 ${formatPercent(input.professionalQuality.average_coverage_ratio)} · 투자 검토 ${input.investmentReviewGateCount}개`,
      href: "#professional-analysis-quality",
      cta: "전문 분석 보기",
      tone: input.professionalSourceGaps.source_blocker_count > 0 || input.professionalQuality.status === "managed_source_limited" ? "watch" : "ready",
    },
  ];
}
