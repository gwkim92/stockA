import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PageDecisionMap } from "./PageDecisionMap";

describe("PageDecisionMap", () => {
  it("renders a Korean review order without exposing internal execution terms", () => {
    render(
      <PageDecisionMap
        eyebrow="화면 읽는 순서"
        title="먼저 판단할 항목"
        description="긴 화면에서 투자 판단에 직접 필요한 영역부터 이동한다."
        steps={[
          {
            description: "수익률과 손익 방향을 먼저 본다.",
            href: "#portfolio-return-summary",
            label: "수익률",
            status: "먼저 확인",
            title: "평가손익",
            tone: "ready",
          },
          {
            description: "주문 전 안전장치를 확인한다.",
            href: "#portfolio-outcome-boundary",
            label: "경계",
            status: "차단 유지",
            title: "거래 경계",
            tone: "block",
          },
        ]}
      />,
    );

    const navigation = screen.getByRole("list", { name: "화면 확인 순서" });
    const links = within(navigation).getAllByRole("link");
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "#portfolio-return-summary",
      "#portfolio-outcome-boundary",
    ]);
    expect(screen.getByText("수익률")).toBeInTheDocument();
    expect(screen.getByText("경계")).toBeInTheDocument();
    expect(screen.getByText("평가손익")).toBeInTheDocument();
    expect(screen.getByText("거래 경계")).toBeInTheDocument();
    expect(screen.queryByText(/pipeline|runner|artifact/i)).not.toBeInTheDocument();
  });
});
