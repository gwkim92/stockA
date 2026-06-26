import type { LiveAiInvocationHealth, NewsAiEvalQuality, OpenAiProviderHealth } from "./dataHealthTypes";

import { koCode } from "@/lib/korean-labels";

import { statusRiskClass } from "./dataHealthCopyModel";

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
