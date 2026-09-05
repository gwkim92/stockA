"use client";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { WorkspaceIcon } from "@/components/shell/WorkspaceIcon";
import { scopesFor, type DiscoveryKind } from "@/lib/discovery-model";
import styles from "./DiscoveryWorkspace.module.css";

export function useDiscoveryQuery(kind: DiscoveryKind) {
  const params = useSearchParams(), pathname = usePathname();
  const scopes = scopesFor(kind);
  const scope = scopes.some(item => item.key === params.get("scope")) ? params.get("scope")! : "all";
  const query = (params.get("q") ?? "").slice(0, 100);
  const group = params.get("group") ?? "";
  const window = ["1d", "5d", "20d", "60d"].includes(params.get("window") ?? "") ? params.get("window")! : "20d";
  function update(values: Record<string, string>, push = false) {
    const next = new URLSearchParams(globalThis.window.location.search);
    for (const [key, value] of Object.entries(values)) {
      if (!value || (key === "scope" && value === "all") || (key === "window" && value === "20d")) next.delete(key); else next.set(key, value);
    }
    const search = next.toString();
    globalThis.window.history[push ? "pushState" : "replaceState"](null, "", `${pathname}${search ? `?${search}` : ""}${globalThis.window.location.hash}`);
  }
  return { query, scope, group, window, scopes, update, reset: () => update({ q: "", scope: "all", group: "", window: "20d" }) };
}

export function DiscoveryToolbar({ kind, control, counts, total, shown, children }: {
  kind: DiscoveryKind; control: ReturnType<typeof useDiscoveryQuery>; counts: Record<string, number>; total: number; shown: number; children?: React.ReactNode;
}) {
  const name = kind === "stocks" ? "종목" : kind === "cycles" ? "테마" : "시장 지표";
  return <>
    <div className={styles.toolbar}>
      <div className={styles.filters} role="group" aria-label={`${name} 조건`}>
        {control.scopes.map(item => <button key={item.key} type="button" aria-pressed={control.scope === item.key} onClick={() => control.update({ scope: item.key }, true)}>{item.name}<span>{counts[item.key] ?? 0}</span></button>)}
      </div>
      <label className={styles.search}><WorkspaceIcon name="search" /><input aria-label={`${name} 검색`} placeholder={kind === "stocks" ? "기업명, 코드, 시장" : kind === "cycles" ? "테마 또는 관련 종목" : "지표명 또는 코드"} value={control.query} maxLength={100} onChange={e => control.update({ q: e.target.value })} /></label>
    </div>
    {children && <div className={styles.secondaryControls}>{children}</div>}
    <p className={styles.resultCount} role="status">수신 {total}개 · 표시 {shown}개 <button type="button" onClick={control.reset}>필터 초기화</button></p>
  </>;
}
export function EmptyDiscovery({ hasRows, reset }: { hasRows: boolean; reset: () => void }) {
  return <div className={styles.empty}><WorkspaceIcon name="search" /><h2>{hasRows ? "조건에 맞는 결과가 없습니다" : "수신된 목록이 비어 있습니다"}</h2><p>{hasRows ? "검색어나 필터를 바꿔보세요. 조건은 주소에 저장됩니다." : "조회 성공과 데이터 준비는 다릅니다. 분석·수집 상태를 확인하세요."}</p>{hasRows ? <button type="button" onClick={reset}>조건 초기화</button> : <Link href="/data-health">데이터 상태 확인</Link>}</div>;
}
