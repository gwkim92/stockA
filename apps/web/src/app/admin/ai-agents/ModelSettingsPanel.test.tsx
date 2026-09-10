import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ModelSettingsPanel from "./ModelSettingsPanel";
import type { ModelSettings } from "@/lib/model-settings-types";

afterEach(() => vi.unstubAllGlobals());
const initial = (): ModelSettings => ({ enabled: true, authorized: true, session_expires_at: 1900000000, revision: 0,
  default_model: "gpt-5.6-terra", overrides: {}, catalog: [{ id: "gpt-5.6-terra", label: "Terra" }, { id: "gpt-5.6-luna", label: "Luna" }], catalog_checked_at: 1800000000,
  workloads: [{ task: "news-rss-korean-translation", label: "뉴스 한국어 번역", purpose: "한국어 번역", source: "ingest/news/translation.py", execution: "뉴스 배치", effective_model: "gpt-5.6-terra", latest: null, last_success: null }], audit: [] });

describe("model settings panel", () => {
  it("saves an override and shows durable readback without claiming execution", async () => {
    let stored = initial();
    const fetcher = vi.fn(async (_url, init) => {
      if (init?.method === "PATCH") {
        const payload = JSON.parse(init.body);
        stored = { ...stored, ...payload, revision: 1, workloads: stored.workloads.map(w => ({ ...w, effective_model: payload.overrides[w.task] || payload.default_model })) };
      }
      return { ok: true, json: async () => stored };
    });
    vi.stubGlobal("fetch", fetcher);
    render(<ModelSettingsPanel />);
    const select = await screen.findByLabelText("작업별 모델");
    fireEvent.change(select, { target: { value: "gpt-5.6-luna" } });
    fireEvent.click(screen.getByRole("button", { name: "모델 설정 저장" }));
    await screen.findByText("설정 #1 저장 완료. 다음 Codex AI 호출부터 적용됩니다.");
    expect(select).toHaveValue("gpt-5.6-luna");
    expect(screen.getByText("아직 확인된 실행 없음")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "모델 설정 저장" })).toBeDisabled();
    expect(stored.overrides).toEqual({ "news-rss-korean-translation": "gpt-5.6-luna" });
  });
  it("keeps viewer controls locked and preserves draft after conflict", async () => {
    let authorized = false;
    vi.stubGlobal("fetch", vi.fn(async (_url, init) => {
      if (init?.method === "PATCH") return { ok: false, json: async () => ({ error: "다른 변경이 저장됐습니다." }) };
      return { ok: true, json: async () => ({ ...initial(), authorized }) };
    }));
    render(<ModelSettingsPanel />);
    expect(await screen.findByLabelText("공통 기본 모델")).toBeDisabled();
    authorized = true;
    fireEvent.click(screen.getByRole("button", { name: "새로고침" }));
    await waitFor(() => expect(screen.getByLabelText("공통 기본 모델")).toBeEnabled());
    fireEvent.change(screen.getByLabelText("공통 기본 모델"), { target: { value: "gpt-5.6-luna" } });
    fireEvent.click(screen.getByRole("button", { name: "모델 설정 저장" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("다른 변경이 저장됐습니다.");
    expect(screen.getByLabelText("공통 기본 모델")).toHaveValue("gpt-5.6-luna");
  });
});
