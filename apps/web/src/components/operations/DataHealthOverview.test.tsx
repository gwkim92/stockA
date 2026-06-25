import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DataHealthOverview } from "./DataHealthOverview";

describe("DataHealthOverview", () => {
  it("renders the operator overview without exposing raw execution codes", () => {
    render(
      <DataHealthOverview
        asOfDate="2026-06-25"
        collectionCards={[
          {
            check: "최근 가격일 2026-06-24",
            finishedAt: "2026-06-25 07:30",
            index: "01",
            purpose: "종목 가격과 차트, 모멘텀 지표의 원천이다.",
            statusLabel: "성공",
            statusTone: "risk-low",
            title: "주식 캔들",
          },
        ]}
        commandCards={[
          {
            body: "즉시 조치할 장애는 없다.",
            cta: "실행 이력 보기",
            href: "#execution-log",
            label: "1. 지금 먼저",
            metric: "0개 열린 항목",
            title: "열린 항목 없음",
            tone: "ready",
          },
        ]}
        headline="수집·분석 상태 정상"
        metaItems={["자동 실행 활성", "보강 필요 항목 0개", "호출 예산 700/800", "실거래 상태 읽기 전용"]}
        triageBuckets={[
          {
            description: "성과 측정창이 끝날 때까지 기다린다.",
            gates: [
              {
                id: "outcome-wait",
                label: "성과 관찰 대기",
                nextAction: "다음 측정일까지 대기",
                statusLabel: "대기",
                statusTone: "risk-medium",
                summary: "추천 산식 변경을 막고 성과 표본을 더 쌓는다.",
              },
            ],
            href: "#outcome-maturity-wait-monitor",
            key: "managed-wait",
            label: "설계된 대기",
            title: "기다려야 하는 항목",
            tone: "risk-medium",
          },
        ]}
        triageStatus="즉시 조치할 장애는 없고 성과 대기만 남아 있다."
      />,
    );

    expect(screen.getByRole("heading", { name: "수집·분석 상태 정상" })).toBeInTheDocument();
    expect(screen.getByText("열린 항목 없음")).toBeInTheDocument();
    expect(screen.getByText("성과 관찰 대기")).toBeInTheDocument();
    expect(screen.getByText("수집·분석 커버리지")).toBeInTheDocument();
    expect(screen.getByText("종목·차트")).toBeInTheDocument();
    expect(screen.getAllByText("주식 캔들")).toHaveLength(2);
    expect(screen.queryByText(/pipeline|runner|artifact|managed-wait/i)).not.toBeInTheDocument();
  });
});
