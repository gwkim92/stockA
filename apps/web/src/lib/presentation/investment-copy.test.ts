import { describe, expect, it } from "vitest";

import { evidenceCopy, portfolioCopy, recommendationCopy, stockCopy } from "./investment-copy";

describe("investment presentation copy", () => {
  it("translates recommendation internals into investor language", () => {
    expect(recommendationCopy("source_data_blocked · read_only_no_order")).toBe(
      "원천 근거 부족으로 차단 · 읽기 전용, 실거래 주문 차단",
    );
  });

  it("normalizes stock research terminology", () => {
    expect(stockCopy("AI 기업 리서치와 paper validation gate")).toBe(
      "기업 리서치와 가상 매매 검증",
    );
  });

  it("removes evidence pipeline terminology", () => {
    expect(evidenceCopy("fixture에는 validator 상세 이유가 없다.")).toBe(
      "품질 차단 상세 사유가 아직 저장되지 않았습니다.",
    );
  });

  it("translates portfolio action codes without page-local replacements", () => {
    expect(portfolioCopy("no_op_wait_for_outcome_window")).toBe("성과 관찰 기간 대기");
  });
});
