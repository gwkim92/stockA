export type CodexOauthStatusTone = "ready" | "waiting" | "blocked";

export type CodexOauthStatusView = {
  readonly accessBoundary: "상태 조회 전용";
  readonly executionBoundary: string;
  readonly executionTone: "ready" | "blocked";
  readonly lastCheckedIso: string;
  readonly lastCheckedLabel: string;
  readonly lastSmokeLabel: string;
  readonly loginProbeLabel: string;
  readonly nextAction: string;
  readonly operationChannel: "서버 CLI/SSH 전용";
  readonly statusLabel: string;
  readonly statusSummary: string;
  readonly tone: CodexOauthStatusTone;
};

type StatusDescriptor = Pick<CodexOauthStatusView, "nextAction" | "statusLabel" | "statusSummary" | "tone">;

function statusDescriptor(status: string): StatusDescriptor {
  if (status === "healthy") {
    return {
      nextAction: "웹에서는 상태만 확인합니다. 재로그인과 실제 호출 점검은 서버 CLI/SSH에서 실행합니다.",
      statusLabel: "연결 정상",
      statusSummary: "예비 AI 연결과 최근 운영 점검이 정상 상태로 기록되어 있습니다.",
      tone: "ready",
    };
  }
  if (status === "authenticated_smoke_required") {
    return {
      nextAction: "서버 CLI/SSH에서 실제 AI 호출 점검을 실행한 뒤 상태를 다시 확인합니다.",
      statusLabel: "로그인 확인 · 점검 필요",
      statusSummary: "서버 로그인이 감지됐지만 실제 AI 호출 점검은 아직 완료되지 않았습니다.",
      tone: "waiting",
    };
  }
  if (status === "news_smoke_running") {
    return {
      nextAction: "서버 작업이 끝난 뒤 이 페이지를 새로고침해 결과를 확인합니다.",
      statusLabel: "운영 점검 진행 중",
      statusSummary: "서버 운영 경계에서 뉴스 AI 호출 점검이 진행 중입니다.",
      tone: "waiting",
    };
  }
  if (status === "device_auth_pending") {
    return {
      nextAction: "인증 코드와 URL은 웹에 공개하지 않습니다. 서버 CLI/SSH에서 로그인 절차를 계속합니다.",
      statusLabel: "서버 로그인 진행 필요",
      statusSummary: "예비 AI 로그인이 대기 중이며 웹 화면은 인증 정보를 표시하거나 제출하지 않습니다.",
      tone: "blocked",
    };
  }
  if (status === "device_code_expired") {
    return {
      nextAction: "서버 CLI/SSH에서 만료된 로그인 절차를 정리하고 새 로그인을 시작합니다.",
      statusLabel: "서버 로그인 만료",
      statusSummary: "이전 로그인 절차가 만료되어 서버 운영자 조치가 필요합니다.",
      tone: "blocked",
    };
  }
  if (status === "relogin_required") {
    return {
      nextAction: "서버 CLI/SSH에서 재로그인한 뒤 실제 AI 호출 점검을 실행합니다.",
      statusLabel: "서버 재로그인 필요",
      statusSummary: "예비 AI 인증이 유효하지 않아 서버 운영자 조치가 필요합니다.",
      tone: "blocked",
    };
  }
  return {
    nextAction: "서버 CLI/SSH에서 인증과 최근 점검 상태를 확인합니다.",
    statusLabel: "상태 확인 필요",
    statusSummary: "예비 AI 연결 상태를 안전하게 분류하지 못해 운영 확인 전까지 보수적으로 차단합니다.",
    tone: "blocked",
  };
}

function normalizedIso(value: string): string {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:\d{2})$/.test(value)) {
    return "";
  }
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? new Date(timestamp).toISOString() : "";
}

function checkedAtLabels(value: string) {
  const iso = normalizedIso(value);
  return {
    lastCheckedIso: iso,
    lastCheckedLabel: iso ? `${iso.slice(0, 16).replace("T", " ")} UTC` : "기록 없음",
  };
}

function smokeLabel(status: string) {
  if (["healthy", "passed", "succeeded", "success"].includes(status)) {
    return "통과";
  }
  if (["pending", "queued", "running", "news_smoke_running"].includes(status)) {
    return "진행 중";
  }
  if (["blocked", "error", "failed", "failure"].includes(status)) {
    return "중단";
  }
  if (!status || status === "not_checked" || status === "unknown") {
    return "기록 없음";
  }
  return "확인 필요";
}

function loginProbeLabel(status: string) {
  if (["authenticated", "healthy", "ready", "succeeded"].includes(status)) {
    return "로그인 감지됨";
  }
  if (["checking", "pending", "running"].includes(status)) {
    return "확인 중";
  }
  if (["auth_invalid", "invalid", "relogin_required", "unauthenticated"].includes(status)) {
    return "재로그인 필요";
  }
  if (!status || status === "not_checked" || status === "unknown") {
    return "기록 없음";
  }
  return "확인 필요";
}

function recordValue(raw: unknown): Record<string, unknown> {
  return raw !== null && typeof raw === "object" && !Array.isArray(raw)
    ? (raw as Record<string, unknown>)
    : {};
}

function stringValue(raw: Record<string, unknown>, key: string): string {
  return typeof raw[key] === "string" ? raw[key] : "";
}

export function buildCodexOauthStatusView(input: unknown): CodexOauthStatusView {
  const raw = recordValue(input);
  const descriptor = statusDescriptor(stringValue(raw, "status"));
  const checkedAt = checkedAtLabels(stringValue(raw, "last_checked_at"));
  const executionBoundarySafe =
    raw.read_only === true
    && raw.broker_submit_allowed === false
    && raw.automatic_order_allowed === false
    && raw.order_boundary === "read_only_no_order";

  return {
    accessBoundary: "상태 조회 전용",
    executionBoundary: executionBoundarySafe
      ? "읽기 전용 · 실거래 주문 차단"
      : "경계 불일치 · 운영 검토 필요",
    executionTone: executionBoundarySafe ? "ready" : "blocked",
    ...checkedAt,
    lastSmokeLabel: smokeLabel(stringValue(raw, "last_smoke_status")),
    loginProbeLabel: loginProbeLabel(stringValue(raw, "login_probe_status")),
    nextAction: descriptor.nextAction,
    operationChannel: "서버 CLI/SSH 전용",
    statusLabel: executionBoundarySafe ? descriptor.statusLabel : "운영 경계 확인 필요",
    statusSummary: executionBoundarySafe
      ? descriptor.statusSummary
      : "읽기 전용 주문 경계가 예상과 달라 웹 조작을 허용하지 않고 운영 확인을 요구합니다.",
    tone: executionBoundarySafe ? descriptor.tone : "blocked",
  };
}
