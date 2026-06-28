import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DataHealthDataGapScorecards } from "./DataHealthDataGapScorecards";

describe("DataHealthDataGapScorecards", () => {
  it("states data gaps as policy limits instead of hidden failures", () => {
    render(
      <DataHealthDataGapScorecards
        cards={[
          {
            currentPolicy: "원천 확인 전 성과 보정과 추천 반영을 막는다.",
            impact: "종목 상세에는 한계로 표시한다.",
            label: "기업 이벤트",
            nextAction: "무료 공식 원천 우선",
            priority: "즉시 무료 가능",
            title: "분할·배당·상장 이벤트",
            tone: "watch",
          },
        ]}
      />,
    );

    expect(screen.getByRole("heading", { name: "없는 데이터를 추정하지 않고 판단 한계로 남깁니다" })).toBeInTheDocument();
    expect(screen.getByText("분할·배당·상장 이벤트")).toBeInTheDocument();
    expect(screen.getByText(/추천 반영을 막는다/)).toBeInTheDocument();
    expect(screen.queryByText(/missing|raw_|fallback|canonical|shadow/i)).not.toBeInTheDocument();
  });
});
