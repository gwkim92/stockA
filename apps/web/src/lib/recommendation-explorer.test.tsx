import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { filterRecommendations, researchScore, sourceLimited, type ExplorerRow } from "./recommendation-explorer-model";
import { RecommendationExplorer } from "@/components/research/RecommendationExplorer";
import ErrorPage from "@/app/error";
import Loading from "@/app/loading";
const row = (symbol: string, rank: number, limited = false, linked = true) => ({
  symbol, name: symbol === "AAPL" ? "Apple" : symbol, recommendation_id: `recommendation-${rank}`, rank_position: rank, score: .8, linked_thesis_id: linked ? `thesis-${rank}` : null,
  evidence: { quality_status: "available" }, evidence_quality: { title: "저장된 기업 근거", missing_layer_labels: [], source_blocker: { blocked: limited } },
}) as unknown as ExplorerRow;
afterEach(cleanup);
describe("candidate explorer", () => {
  it("filters without changing backend order or source objects", () => {
    const input = [row("TSLA",3),row("AAPL",1),row("EROK",2,true)]; const original = JSON.stringify(input);
    expect(filterRecommendations(input,"","all")).toEqual(input);
    expect(filterRecommendations(input,"apple","all").map(item=>item.symbol)).toEqual(["AAPL"]);
    expect(filterRecommendations(input,"","limited").map(item=>item.symbol)).toEqual(["EROK"]);
    expect(filterRecommendations(input,"","linked").map(item=>item.symbol)).toEqual(["TSLA","AAPL"]);
    expect(JSON.stringify(input)).toBe(original);
  });
  it.each([null,undefined,NaN,Infinity,-1,2,"0.5"])("does not imply a score for %s", value => expect(researchScore(value)).toBe("미확인"));
  it("presents normalized model score, not a percentage probability",()=> expect(researchScore(.82)).toBe("0.82 / 1"));
  it("keeps source restrictions visible",()=>expect(sourceLimited(row("EROK",1,true))).toBe(true));
  it("search and filters are functional and can be reset", () => {
    render(<RecommendationExplorer rows={[row("AAPL",1),row("EROK",2,true)]} />);
    fireEvent.click(screen.getByRole("button",{ name: /원천 제한/ }));
    expect(screen.queryByRole("link",{ name: "AAPL" })).toBeNull();
    expect(screen.getByRole("link",{ name: "EROK" })).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox"), { target: { value:"none" } });
    expect(screen.getByText("조건에 맞는 후보가 없습니다")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button",{ name:"필터 초기화" }));
    expect(screen.getByRole("link",{ name:"AAPL" })).toBeInTheDocument();
  });
  it("empty data retains a real recovery path",()=>{
    render(<RecommendationExplorer rows={[]} />);
    expect(screen.getByRole("link",{ name:"데이터 상태 확인" })).toHaveAttribute("href","/data-health");
  });
});
describe("workspace states", () => {
  it("does not expose a raw service error and retry is functional", () => {
    const reset=vi.fn(); const {container}=render(<ErrorPage error={new Error("postgres://user:secret@host")} reset={reset} />);
    expect(container.textContent).not.toContain("secret");
    fireEvent.click(screen.getByRole("button",{name:"다시 시도"}));expect(reset).toHaveBeenCalledOnce();
  });
  it("supports the Next retry interface without guessing a server cause", () => {
    const retry=vi.fn();render(<ErrorPage error={new Error("private")} unstable_retry={retry}/>);
    fireEvent.click(screen.getByRole("button",{name:"다시 시도"}));expect(retry).toHaveBeenCalledOnce();
  });
  it("loading exposes status without invented data",()=>{
    const {container}=render(<Loading/>);expect(screen.getByRole("status")).toHaveTextContent("자료를 불러오고");
    expect(container.textContent).not.toMatch(/0%|정상|추천 0/);
  });
});
