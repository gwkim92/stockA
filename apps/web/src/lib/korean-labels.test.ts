import { describe, expect, it } from "vitest";

import { koCode } from "./korean-labels";

describe("koCode investor labels", () => {
  it("translates cycle and provider status codes", () => {
    expect(koCode("CHINA ADR COVERAGE")).toBe("중국 ADR 분석 범위");
    expect(koCode("missing_api_key")).toBe("API 키 없음");
    expect(koCode("admin_key_missing")).toBe("관리자 비용 조회 키 없음");
  });
});
