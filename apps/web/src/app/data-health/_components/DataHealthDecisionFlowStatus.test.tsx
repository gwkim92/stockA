import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DataHealthDecisionFlowStatus } from "./DataHealthDecisionFlowStatus";

describe("DataHealthDecisionFlowStatus", () => {
  it("renders the investment decision flow without exposing raw runner language", () => {
    render(
      <DataHealthDecisionFlowStatus
        cards={[
          {
            evidence: "RSS 원문, 한국어 번역, AI 구조화, 자동 검증을 거친 근거만 넘어간다.",
            href: "#live-ai-invocation-health",
            impact: "뉴스 근거 화면 확인",
            label: "01 뉴스·AI",
            statusLabel: "최근 실행 성공 · AI 호출 상태 확인",
            title: "뉴스 근거 사용 가능",
            tone: "ready",
          },
          {
            evidence: "성과와 포트폴리오 사후평가가 성숙하기 전까지 추천 반영 비중 변경은 금지된다.",
            href: "#outcome-calibration",
            impact: "반영 비중 변경 금지",
            label: "06 성과 피드백",
            statusLabel: "성과 표본 대기",
            title: "성과 표본 대기",
            tone: "watch",
          },
        ]}
      />,
    );

    expect(screen.getByRole("heading", { name: "수집부터 성과 피드백까지 어느 판단 단계가 신뢰 가능한지 판정합니다" })).toBeInTheDocument();
    expect(screen.getByText("뉴스 근거 사용 가능")).toBeInTheDocument();
    expect(screen.getAllByText("성과 표본 대기")).toHaveLength(2);
    expect(screen.queryByText(/pipeline|runner|artifact|fallback|canonical|shadow/i)).not.toBeInTheDocument();
  });
});
