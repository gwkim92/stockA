import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { AiAgentRegistryData, CodexOauthOperatorStatus } from "@/lib/types";

const { getAiAgentRegistryMock } = vi.hoisted(() => ({
  getAiAgentRegistryMock: vi.fn(),
}));

vi.mock("@/lib/frontend-api", () => ({
  getAiAgentRegistry: getAiAgentRegistryMock,
}));

import AiAgentAdminPage from "./page";

const rawOperatorStatus: CodexOauthOperatorStatus = {
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

const registry = {
  status: "available",
  report_name: "test-ai-agent-registry",
  agent_count: 0,
  required_agent_count: 0,
  missing_required_agents: [],
  primary_providers: ["codex_oauth"],
  fallback_providers: ["local_rules"],
  local_fallback_providers: ["local_rules"],
  blocked_order_agent_count: 0,
  runtime_policy: {
    model_editing_enabled: false,
    live_request_invocation_enabled: false,
    batch_invocation_only: true,
    canonical_write_enabled: false,
    broker_submit_allowed: false,
    automatic_order_allowed: false,
    order_boundary: "read_only_no_order",
    primary_api_key_configured: false,
    primary_provider_status: "unknown",
    primary_provider_fallback_reason: "테스트 예비 경로",
    openai_billing_status: "unknown",
    openai_api_disabled: true,
    openai_provider_health: {
      status: "unknown",
      label: "미확인",
      balance_known: false,
      balance_check_method: "미조회",
      remaining_balance_usd: null,
      api_key_configured: false,
      admin_api_key_configured: false,
      last_checked_at: "",
      next_retry_at: "",
      fallback_provider: "codex_oauth",
      local_fallback_provider: "local_rules",
      message: "비용 상태 미조회",
      cost_status: {
        report_name: "test-cost-status",
        status: "unknown",
        cost_known: false,
        admin_api_key_configured: false,
        lookback_days: 7,
        total_cost_usd: null,
        latest_day_cost_usd: null,
        currency: "USD",
        period_start: "",
        period_end: "",
        last_checked_at: "",
        error_code: "",
        message: "비용 미조회",
        billing_overview_url: "https://platform.openai.com/settings/organization/billing/overview",
        secret_free: true,
      },
    },
    codex_oauth_status: "healthy",
    codex_oauth_operator: rawOperatorStatus,
    configuration_source: "test",
    next_action: "none",
  },
  agents: [],
} as AiAgentRegistryData;

describe("AiAgentAdminPage", () => {
  it("does not serialize raw OAuth operator details into the rendered page", async () => {
    getAiAgentRegistryMock.mockResolvedValue({ data: registry });

    const { container } = render(await AiAgentAdminPage());
    const html = container.innerHTML;

    expect(screen.getByRole("heading", { name: "예비 AI 연결 상태" })).toBeInTheDocument();
    expect(screen.getByText("서버 CLI/SSH 전용")).toBeInTheDocument();
    expect(container.querySelectorAll("button, form")).toHaveLength(0);
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
      expect(html).not.toContain(forbidden);
    }
  });
});
