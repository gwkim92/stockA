import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import CodexOauthOperatorPanel from "./CodexOauthOperatorPanel";
import type { CodexOauthStatusView } from "./codex-oauth-status-view";

const view: CodexOauthStatusView = {
  accessBoundary: "상태 조회 전용",
  executionBoundary: "읽기 전용 · 실거래 주문 차단",
  executionTone: "ready",
  lastCheckedIso: "2026-07-11T12:00:00.000Z",
  lastCheckedLabel: "2026-07-11 12:00 UTC",
  lastSmokeLabel: "통과",
  loginProbeLabel: "로그인 감지됨",
  nextAction: "재로그인과 실제 AI 호출 점검은 서버 CLI/SSH에서 실행합니다.",
  operationChannel: "서버 CLI/SSH 전용",
  statusLabel: "연결 정상",
  statusSummary: "예비 AI 연결의 최근 상태를 읽기 전용으로 확인합니다.",
  tone: "ready",
};

describe("CodexOauthOperatorPanel", () => {
  it("renders only the sanitized status and CLI boundary", () => {
    const { container } = render(<CodexOauthOperatorPanel status={view} />);

    expect(screen.getByRole("region", { name: "예비 AI 연결 상태" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "예비 AI 연결 상태" })).toBeInTheDocument();
    expect(screen.getByText("상태 조회 전용")).toBeInTheDocument();
    expect(screen.getByText("서버 CLI/SSH 전용")).toBeInTheDocument();
    expect(screen.getByText("읽기 전용 · 실거래 주문 차단")).toBeInTheDocument();
    expect(container.querySelectorAll("button, form")).toHaveLength(0);
    expect(container.querySelector('a[href^="http"]')).toBeNull();
    expect(container.textContent).not.toMatch(/device|auth_url|user_code|PID|\/opt\/|token=/i);
  });
});
