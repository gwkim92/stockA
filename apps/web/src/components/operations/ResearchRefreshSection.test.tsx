import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ResearchRefreshSection } from "./ResearchRefreshSection";
import type { ResearchRefreshStatus } from "@/lib/research-refresh";

const data: ResearchRefreshStatus = {
  status: "attention_required", observed_at: "2026-09-11T15:00:00Z", as_of_date: "2026-09-11",
  budget_resets_at: "2026-09-12T00:00:00Z", model_name: "fixture-model", daily_used: 5,
  daily_limit: 5, daily_remaining: 0, total_count: 3, attention_count: 1,
  counts: { due: 1, reconcile: 1, waiting_for_source: 1 },
  rows: ["AAPL", "MSFT", "EROK"].map((symbol, i) => ({ symbol,
    state: ["due", "reconcile", "waiting_for_source"][i], source_run_id: null,
    source_collected_at: null, claim_id: null, retry_after: null, failure_code: null })),
};

describe("research refresh operations", () => {
  it("shows exhausted budget, unknown-result boundary, and filters actual companies", () => {
    render(<ResearchRefreshSection data={data} />);
    expect(screen.getByText(/오늘 한도 소진/)).toBeVisible();
    expect(screen.getByText(/중복 호출을 막고 저장 기록/)).toBeVisible();
    fireEvent.change(screen.getByLabelText("상태"), { target: { value: "waiting_for_source" } });
    expect(screen.getByRole("link", { name: "EROK" })).toHaveAttribute("href", "/stocks/EROK");
    expect(screen.queryByRole("link", { name: "AAPL" })).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("기업 찾기"), { target: { value: "MSFT" } });
    expect(screen.getByText("조건에 맞는 기업이 없습니다.")).toBeVisible();
  });
  it("keeps unavailable distinct from an empty successful read", () => {
    const { rerender } = render(<ResearchRefreshSection />);
    expect(screen.getByRole("status")).toHaveTextContent("확인되지 않았습니다");
    expect(screen.queryByText("오늘 생성 한도 사용")).not.toBeInTheDocument();
    rerender(<ResearchRefreshSection data={{...data, status: "loaded", rows: [], total_count: 0, counts: {}, attention_count: 0}} />);
    fireEvent.click(screen.getByText(/기업별 상태와 처리 이유/));
    expect(screen.getByText("현재 자동 갱신 대상 기업이 없습니다.")).toBeVisible();
  });
});
