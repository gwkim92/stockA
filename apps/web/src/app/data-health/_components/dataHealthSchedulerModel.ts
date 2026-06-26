import type {
  ProfileTimer,
  SchedulerActivation,
  SchedulerCadenceGroup,
  SchedulerStatus,
  TimerGroupDefinition,
} from "./dataHealthTypes";

import { koCode } from "@/lib/korean-labels";

import { statusRiskClass } from "./dataHealthCopyModel";

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
