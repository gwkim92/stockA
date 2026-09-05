import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, within, cleanup } from "@testing-library/react";
import fixture from "../../tests/e2e/recommendation-memo-fixture.json";
import type { RecommendationDetailData, ThesisDetailData, ApiResponse } from "./types";
import { buildRecommendationMemo, memoEvidenceAssessment, memoCurrency, memoPercent, memoDate, memoPositionLabel, thesisMatchesRecommendation } from "./recommendation-memo-model";
import { loadRecommendationThesis } from "./recommendation-memo-data";
import { RecommendationExecutiveBrief } from "../components/recommendation-executive-brief";
import { RecommendationPositionReality } from "../components/recommendation-position-reality";
import { recommendationProductKind, buildRecommendationViewModel } from "./presentation/recommendation";

vi.mock("./frontend-api", () => ({ getThesisDetail: vi.fn() }));
const recommendation = () => structuredClone(fixture.recommendation) as unknown as RecommendationDetailData;
const thesis = () => structuredClone(fixture.thesis) as unknown as ThesisDetailData;
const envelope = (data: ThesisDetailData) => ({ data, contract_version: "frontend-api-v0.1", generated_at: "2026-09-05T12:00:00Z", links: {} }) as ApiResponse<ThesisDetailData>;
afterEach(() => { cleanup(); vi.useRealTimers(); vi.restoreAllMocks(); });

describe("investment memo", () => {
  it("does not interpret zero expected evidence as complete", () => {
    const audit = { ...recommendation().professional_evidence_audit, available_layer_count: 0, expected_layer_count: 0 };
    expect(memoEvidenceAssessment(audit).label).toBe("근거 상태 미확인");
    expect(memoEvidenceAssessment(audit).tone).toBe("watch");
  });
  it.each([undefined, null, -1, NaN, Infinity, "4"])("rejects an invalid expected count: %s", value => {
    expect(memoEvidenceAssessment({ ...recommendation().professional_evidence_audit, expected_layer_count: value }).tone).toBe("watch");
  });
  it("source limitation wins over a paper-input flag", () => {
    const data = recommendation(); data.professional_evidence_audit.source_blocker.blocked = true;
    expect(buildRecommendationMemo(data).evidence.tone).toBe("blocked");
    expect(buildRecommendationViewModel(data).statusLabel).toBe("원천 근거 제한");
  });
  it("preserves confirmed non-holdings but not unknown positions", () => {
    expect(memoPositionLabel("not_held")).toBe("미보유"); expect(memoPositionLabel("unknown")).toBe("보유 상태 미확인");
    const data = recommendation(); data.position_context.status = "unknown";
    expect(buildRecommendationViewModel(data).summary).toContain("보유 상태 미확인");
  });
  it("does not replace a missing target with the reference price", () => {
    const data = recommendation(); data.valuation_target_range.target_base = null;
    const memo = buildRecommendationMemo(data);
    expect(memo.valuation.referencePrice).toContain("180"); expect(memo.valuation.target).toBe("미측정");
  });
  it("does not present unavailable valuation payloads as a valid target", () => {
    const data = recommendation(); data.valuation_target_range.status = "unavailable";
    expect(buildRecommendationMemo(data).valuation.target).toBe("미측정");
  });
  it.each([NaN, Infinity, undefined, "12"])("keeps nonnumeric values unknown: %s", value => {
    expect(memoPercent(value)).toBe("미확인"); expect(memoCurrency(value, "USD")).toBe("미측정");
  });
  it("guards currency format and keeps measured zero", () => {
    expect(memoCurrency(10, "invalid currency")).toBe("통화 미확인"); expect(memoPercent(0)).toBe("0%");
  });
  it.each(["2026-02-30", "bad-date", "2026-02-30T12:00:00Z"])("rejects invalid source/review dates: %s", value => expect(memoDate(value)).toBeNull());
  it("preserves linked thesis claims and separate source dates", () => {
    const memo = buildRecommendationMemo(recommendation(), { status: "available", data: thesis() });
    expect(memo.summary).toBe(fixture.thesis.summary); expect(memo.claimSource).toContain("2026-09-04");
    expect(memo.researchDate).toBe("2026-09-02"); expect(memo.valuation.date).toBe("2026-09-03"); expect(memo.nextReview).toBe("2026-10-30");
  });
  it.each(["thesis_id", "symbol", "instrument_id"] as const)("rejects a mismatched %s before displaying thesis text", key => {
    const invalid = thesis(); invalid[key] = "other-id"; invalid.summary = "ALIEN-CLAIM";
    expect(thesisMatchesRecommendation(recommendation(), invalid)).toBe(false);
    expect(JSON.stringify(buildRecommendationMemo(recommendation(), { status: "available", data: invalid }))).not.toContain("ALIEN-CLAIM");
  });
  it("does not manufacture a missing review date", () => {
    const value = thesis(); value.latest_review.next_review_date = "";
    expect(buildRecommendationMemo(recommendation(), { status: "available", data: value }).nextReview).toBeNull();
  });
  it("separates ETF analysis even when fund data is absent", () => {
    const data = recommendation(); data.professional_evidence_audit.product_type = "fund_or_etf";
    expect(recommendationProductKind(data)).toBe("fund_or_etf");
    const memo = buildRecommendationMemo(data);
    expect(memo.isFund).toBe(true); expect(memo.sources).toEqual([]); expect(memo.summary).not.toContain("서비스 매출");
  });
  it("does not mutate caller data or generate unsafe source paths", () => {
    const data = recommendation(); data.equity_research!.source_document_ids.push("../private", "javascript:alert(1)");
    const before = JSON.stringify(data); const memo = buildRecommendationMemo(data);
    expect(memo.sources).toHaveLength(1); expect(JSON.stringify(data)).toBe(before);
  });
  it("renders the actual claim, invalidation, assumptions and primary-document link", () => {
    render(<RecommendationExecutiveBrief data={recommendation()} thesis={{ status: "available", data: thesis() }} />);
    const memo = screen.getByTestId("investment-memo");
    expect(within(memo).getByText(fixture.thesis.summary)).toBeInTheDocument();
    expect(within(memo).getByText(/연속 두 분기/)).toBeInTheDocument();
    expect(within(memo).getByText("2026-10-30")).toBeInTheDocument();
    expect(within(memo).getByRole("link", { name: "연결 원문 1" })).toHaveAttribute("href", "/source-documents/source-document-1");
    expect(within(memo).getByRole("link", { name: "전체 투자 논리와 검토 이력" })).toHaveAttribute("href", "/theses/thesis-1");
    expect(within(memo).getByText(/매출 성장률: 5%/)).toBeInTheDocument();
  });
  it("does not label unknown account data as a confirmed empty position", () => {
    const data = recommendation();
    for (const position of [data.position_context, data.position_context.broker_reference]) {
      position.status = "unknown"; position.quantity = null; position.average_cost = null; position.cost_basis_native = null;
    }
    render(<RecommendationPositionReality data={data} />);
    expect(screen.getAllByText(/보유 상태 미확인/).length).toBeGreaterThan(0);
    expect(screen.queryByText("미보유라 계산하지 않음")).not.toBeInTheDocument();
    expect(screen.queryByText("미보유 계좌")).not.toBeInTheDocument();
  });
});

describe("optional exact-linked thesis read", () => {
  it("does not query an unlinked recommendation", async () => {
    const data = recommendation(); data.linked_thesis_id = "";
    const read = vi.fn(); expect(await loadRecommendationThesis(data, { read })).toEqual({ status: "not_linked", data: null }); expect(read).not.toHaveBeenCalled();
  });
  it("loads only the expected linked thesis", async () => {
    const read = vi.fn(async () => envelope(thesis()));
    expect((await loadRecommendationThesis(recommendation(), { read })).status).toBe("available");
    expect(read).toHaveBeenCalledWith("thesis-1", expect.objectContaining({ signal: expect.any(AbortSignal) }));
  });
  it("does not include raw provider errors", async () => {
    const read = vi.fn(async () => { throw Error("secret-dsn-password"); });
    const result = await loadRecommendationThesis(recommendation(), { read });
    expect(result.status).toBe("unavailable"); expect(JSON.stringify(result)).not.toContain("secret");
  });
  it("mismatched instrument never enters the memo", async () => {
    const value = thesis(); value.instrument_id = "instrument-other";
    expect((await loadRecommendationThesis(recommendation(), { read: async () => envelope(value) })).status).toBe("mismatch");
  });
  it("bounds an optional stalled read and aborts it", async () => {
    vi.useFakeTimers(); let signal: AbortSignal | undefined;
    const pending = loadRecommendationThesis(recommendation(), { timeoutMs: 20, read: (_id, options) => { signal = options.signal; return new Promise(() => {}); } });
    await vi.advanceTimersByTimeAsync(21);
    expect((await pending).status).toBe("timeout"); expect(signal?.aborted).toBe(true); expect(vi.getTimerCount()).toBe(0);
  });
});
