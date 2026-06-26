import { koCode, koReason } from "@/lib/korean-labels";

import type { AuditSampleRecord } from "./dataHealthTypes";

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
    .replaceAll("확인한다.", "확인합니다.")
    .replaceAll("확인한다", "확인합니다")
    .replaceAll("봐야 한다.", "판단합니다.")
    .replaceAll("봐야 한다", "판단합니다")
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
