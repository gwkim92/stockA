import { describe, expect, it } from "vitest";

import { displayStatus, statusFromDataCondition } from "./status";

describe("displayStatus", () => {
  it("returns Korean investor language for every supported status", () => {
    const labels = [
      displayStatus("ready").label,
      displayStatus("watch").label,
      displayStatus("stale").label,
      displayStatus("source_limited").label,
      displayStatus("blocked").label,
      displayStatus("not_applicable").label,
      displayStatus("empty").label,
      displayStatus("error").label,
    ];

    expect(labels).toEqual([
      "정상",
      "관찰",
      "오래됨",
      "원천 제한",
      "안전 차단",
      "해당 없음",
      "데이터 없음",
      "오류",
    ]);
  });
});

describe("statusFromDataCondition", () => {
  it("keeps safety blocks separate from system errors", () => {
    expect(statusFromDataCondition({ blocked: true })).toBe("blocked");
    expect(statusFromDataCondition({ failed: true })).toBe("error");
  });

  it("prioritizes source limitations over empty data", () => {
    expect(statusFromDataCondition({ empty: true, sourceLimited: true })).toBe("source_limited");
  });
});
