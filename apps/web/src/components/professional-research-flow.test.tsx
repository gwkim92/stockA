import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProfessionalResearchFlow } from "./professional-research-flow";

describe("ProfessionalResearchFlow", () => {
  it("labels an empty analysis track instead of rendering an unexplained canvas", () => {
    render(
      <ProfessionalResearchFlow
        eyebrow="전문 분석 흐름"
        title="AAPL 추천을 분석서처럼 읽는다"
        summary="전문 판단 흐름 데이터가 아직 충분히 연결되지 않았다."
        steps={[]}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("연결된 전문 분석 단계가 아직 없습니다");
    expect(screen.getByRole("status")).toHaveTextContent("이 화면에서는 주문을 만들지 않습니다");
  });
});
