"use client";
import { usePathname, useSearchParams } from "next/navigation";
import type { ReactNode } from "react";
import styles from "./ReviewWorkspace.module.css";
export const HOLDING_FILTERS = [["all", "전체 보유"], ["thesis", "투자 논리 확인"], ["outcome", "성과 확인"], ["valuation", "평가자료 확인"]] as const;
export const OUTCOME_FILTERS = [["all", "전체 결과"], ["positive", "초과수익 양수"], ["negative", "초과수익 음수"], ["unknown", "미측정"]] as const;
export function useReviewFilters() {
  const params = useSearchParams(), path = usePathname();
  function update(values: Record<string, string>, push = false) {
    const next = new URLSearchParams(window.location.search);
    for (const [key, value] of Object.entries(values)) { if (!value || value === "all") next.delete(key); else next.set(key, value); }
    window.history[push ? "pushState" : "replaceState"](null, "", `${path}${next.size ? `?${next}` : ""}`);
  }
  return { query: (params.get("q") ?? "").slice(0, 100), scope: params.get("scope") ?? "all", horizon: params.get("horizon") ?? "", update,
    reset: () => update({ q: "", scope: "all", horizon: "" }) };
}
export function ReviewFilters({ controls, filters, shown, total, children }: { controls: ReturnType<typeof useReviewFilters>; filters: readonly (readonly [string, string])[]; shown: number; total: number; children?: ReactNode }) {
  const active = filters.some(([key]) => key === controls.scope) ? controls.scope : "all";
  return <div className={styles.controls}>
    <div className={styles.filterRow} role="group" aria-label="목록 필터">{filters.map(([key, label]) => <button key={key} type="button" aria-pressed={active === key} onClick={() => controls.update({ scope: key }, true)}>{label}</button>)}</div>
    <div className={styles.searchRow}><label className={styles.search}>종목 검색<input aria-label="종목 검색" placeholder="종목 코드 입력" maxLength={100} value={controls.query} onChange={e => controls.update({ q: e.target.value })} /></label>{children}<button type="button" onClick={controls.reset}>필터 초기화</button><span role="status">{total}개 중 {shown}개 표시</span></div>
  </div>;
}
