"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import styles from "./ResearchWorkspace.module.css";

/** URL state keeps the selected chapter when opening an evidence page and returning. */
export function ResearchTabs({ tabs, children }: { tabs: readonly (readonly [string, string])[]; children: ReactNode[] }) {
  const params = useSearchParams(), path = usePathname();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const active = tabs.some(([id]) => id === params.get("view")) ? params.get("view")! : tabs[0][0];
  function select(id: string, replace = false) {
    const next = new URLSearchParams(window.location.search);
    next.set("view", id);
    window.history[replace ? "replaceState" : "pushState"](null, "", `${path}?${next}`);
  }
  useEffect(() => {
    const legacy = () => {
      const id = window.location.hash.slice(1);
      if (tabs.some(([key]) => key === id)) select(id, true);
    };
    legacy(); window.addEventListener("hashchange", legacy);
    return () => window.removeEventListener("hashchange", legacy);
    // Resolve legacy chapter links once per route; query state belongs to Next.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path]);
  return <>
    <div className={styles.tabs} role="tablist" aria-label="기업 리서치 목차">{tabs.map(([id, label], i) => <button key={id} type="button" role="tab" id={`tab-${id}`} aria-controls={`panel-${id}`} aria-selected={active === id} tabIndex={active === id ? 0 : -1} ref={node => { refs.current[i] = node; }} onClick={() => select(id)} onKeyDown={event => {
      const index = event.key === "ArrowRight" ? (i + 1) % tabs.length : event.key === "ArrowLeft" ? (i + tabs.length - 1) % tabs.length : event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : null;
      if (index !== null) { event.preventDefault(); select(tabs[index][0]); refs.current[index]?.focus(); }
    }}>{label}</button>)}</div>
    {tabs.map(([id], i) => <div key={id} role="tabpanel" id={`panel-${id}`} aria-labelledby={`tab-${id}`} hidden={id !== active} tabIndex={0} className={styles.tabPanel}>{children[i]}</div>)}
  </>;
}
