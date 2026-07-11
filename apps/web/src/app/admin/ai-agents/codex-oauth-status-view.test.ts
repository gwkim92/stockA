import { describe, expect, it } from "vitest";

import type { CodexOauthOperatorStatus } from "@/lib/types";

import { buildCodexOauthStatusView } from "./codex-oauth-status-view";

const rawStatus: CodexOauthOperatorStatus = {
  status: "healthy",
  label: "RAW_LABEL_SENTINEL",
  summary: "RAW_SUMMARY_SENTINEL",
  auth_url: "https://auth.example.invalid/SECRET_AUTH_URL",
  user_code: "SECRET-DEVICE-CODE",
  expires_at: "2026-07-11T12:30:00Z",
  device_auth_pid: 424242,
  last_checked_at: "2026-07-11T12:00:00Z",
  last_event_type: "RAW_EVENT_SENTINEL",
  last_smoke_status: "succeeded",
  last_smoke_at: "2026-07-11T11:59:00Z",
  last_error_code: "SECRET_ERROR_CODE",
  last_error_summary: "token=SECRET_TOKEN /opt/stockanalysis/private/status.json",
  next_action: "RAW_NEXT_ACTION_SENTINEL",
  login_probe_status: "authenticated",
  login_probe_message: "SECRET_LOGIN_PROBE_MESSAGE",
  status_path: "/opt/stockanalysis/private/status.json",
  admin_action_required: false,
  read_only: true,
  broker_submit_allowed: false,
  automatic_order_allowed: false,
  order_boundary: "read_only_no_order",
};

describe("buildCodexOauthStatusView", () => {
  it("projects raw operator state through an explicit safe allowlist", () => {
    const view = buildCodexOauthStatusView(rawStatus);
    const serialized = JSON.stringify(view);

    expect(Object.keys(view).sort()).toEqual([
      "accessBoundary",
      "executionBoundary",
      "executionTone",
      "lastCheckedIso",
      "lastCheckedLabel",
      "lastSmokeLabel",
      "loginProbeLabel",
      "nextAction",
      "operationChannel",
      "statusLabel",
      "statusSummary",
      "tone",
    ]);
    expect(view).toMatchObject({
      accessBoundary: "상태 조회 전용",
      executionBoundary: "읽기 전용 · 실거래 주문 차단",
      lastCheckedIso: "2026-07-11T12:00:00.000Z",
      lastSmokeLabel: "통과",
      loginProbeLabel: "로그인 감지됨",
      operationChannel: "서버 CLI/SSH 전용",
      statusLabel: "연결 정상",
      tone: "ready",
    });
    for (const forbidden of [
      "SECRET_AUTH_URL",
      "SECRET-DEVICE-CODE",
      "424242",
      "SECRET_ERROR_CODE",
      "SECRET_TOKEN",
      "/opt/stockanalysis",
      "RAW_LABEL_SENTINEL",
      "RAW_SUMMARY_SENTINEL",
      "RAW_NEXT_ACTION_SENTINEL",
      "SECRET_LOGIN_PROBE_MESSAGE",
    ]) {
      expect(serialized).not.toContain(forbidden);
    }
  });

  it("fails closed when the execution boundary is inconsistent", () => {
    const view = buildCodexOauthStatusView({
      ...rawStatus,
      automatic_order_allowed: true,
      broker_submit_allowed: true,
      order_boundary: "submit_allowed",
      read_only: false,
    });

    expect(view.executionTone).toBe("blocked");
    expect(view.executionBoundary).toBe("경계 불일치 · 운영 검토 필요");
  });

  it("does not echo unknown status, probe, smoke, or invalid timestamp values", () => {
    const view = buildCodexOauthStatusView({
      ...rawStatus,
      status: "SECRET_UNKNOWN_STATUS",
      last_checked_at: "SECRET_INVALID_DATE",
      last_smoke_status: "SECRET_SMOKE_STATUS",
      login_probe_status: "SECRET_PROBE_STATUS",
    });

    expect(view.statusLabel).toBe("상태 확인 필요");
    expect(view.lastCheckedIso).toBe("");
    expect(view.lastCheckedLabel).toBe("기록 없음");
    expect(view.lastSmokeLabel).toBe("확인 필요");
    expect(view.loginProbeLabel).toBe("확인 필요");
    expect(JSON.stringify(view)).not.toMatch(/SECRET_/);
  });

  it.each([null, undefined, [], "SECRET_MALFORMED_STATUS"])(
    "fails closed for a missing or malformed operator status: %p",
    (input) => {
      const view = buildCodexOauthStatusView(input);

      expect(view).toMatchObject({
        executionBoundary: "경계 불일치 · 운영 검토 필요",
        executionTone: "blocked",
        lastCheckedLabel: "기록 없음",
        statusLabel: "운영 경계 확인 필요",
        tone: "blocked",
      });
      expect(JSON.stringify(view)).not.toContain("SECRET_MALFORMED_STATUS");
    },
  );
});
