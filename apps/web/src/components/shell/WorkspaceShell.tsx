"use client";
import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { PRIMARY_NAVIGATION, PORTFOLIO_NAVIGATION, RESEARCH_NAVIGATION, OPERATIONS_NAVIGATION, navigationContext, navigationResults, symbolDestination, type NavigationItem } from "./navigation";
import { WorkspaceIcon } from "./WorkspaceIcon";
import styles from "./WorkspaceShell.module.css";

function Brand() {
  return <Link className={styles.brand} href="/" aria-label="stockA 리서치 홈"><span className={styles.brandMark} aria-hidden="true">s<span>·</span></span><strong>stockA<span>RESEARCH</span></strong></Link>;
}
function NavGroup({ label, items, active, onNavigate }: { label: string; items: readonly NavigationItem[]; active: string; onNavigate?: () => void }) {
  return <div className={styles.group}><p>{label}</p>{items.map((item) => <Link key={item.href} href={item.href} className={styles.navLink} aria-current={active === item.href ? "page" : undefined} onClick={onNavigate}><WorkspaceIcon name={item.icon} /><span>{item.label}</span></Link>)}</div>;
}

export function WorkspaceShell({ children }: { readonly children: ReactNode }) {
  const pathname = usePathname();
  const active = navigationContext(pathname);
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const open = () => { setQuery(""); if (!dialog.current?.open) dialog.current?.showModal(); input.current?.focus(); };
  const close = () => dialog.current?.close();
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k" && !event.isComposing) {
        event.preventDefault(); if (dialog.current?.open) dialog.current.close(); else open();
      }
    };
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, []);
  useEffect(() => { dialog.current?.close(); }, [pathname]);
  const results = navigationResults(query);
  const symbol = symbolDestination(query);
  const inOperations = OPERATIONS_NAVIGATION.some((item) => item.href === active.href);
  return <div className={styles.frame} data-testid="workspace-shell">
    <a className={styles.skipLink} href="#main-content">본문으로 바로가기</a>
    <aside className={styles.sidebar} aria-label="리서치 사이드바">
      <Brand />
      <button className={styles.searchButton} onClick={open} type="button"><WorkspaceIcon name="search" /><span>빠른 이동</span><kbd>⌘ K</kbd></button>
      <nav aria-label="투자 리서치 주요 메뉴">
        <NavGroup label="탐색과 판단" items={PRIMARY_NAVIGATION} active={active.href} />
        <NavGroup label="검토와 성과" items={PORTFOLIO_NAVIGATION} active={active.href} />
      </nav>
      <details className={styles.secondaryNav} open={inOperations || RESEARCH_NAVIGATION.some((item) => item.href === active.href) ? true : undefined}>
        <summary>근거·운영 도구</summary>
        <nav aria-label="근거와 운영 도구"><NavGroup label="근거 자료" items={RESEARCH_NAVIGATION} active={active.href} /><NavGroup label="운영" items={OPERATIONS_NAVIGATION} active={active.href} /></nav>
      </details>
      <div className={styles.sidebarFooter}><WorkspaceIcon name="shield" /><div><strong>리서치 전용</strong><small>실거래 주문 비활성</small></div></div>
    </aside>
    <div className={styles.workspace}>
      <header className={styles.topbar}>
        <div className={styles.mobileBrand}><Brand /></div>
        <div className={styles.breadcrumb}><span>워크스페이스</span><span aria-hidden="true">/</span><strong>{active.label}</strong></div>
        <div className={styles.topActions}><span className={styles.mode}>중장기 리서치</span><button type="button" className={styles.iconButton} onClick={open} aria-label="화면 및 종목 코드 찾기"><WorkspaceIcon name="search" /></button><button type="button" className={styles.mobileMenu} onClick={open} aria-label="전체 메뉴 열기"><WorkspaceIcon name="menu" /></button></div>
      </header>
      <main className={styles.main} id="main-content" tabIndex={-1}>{children}</main>
      <footer className={styles.pageFooter}><span>stockA · 근거를 읽고, 판단을 기록합니다.</span><Link href="/data-health">데이터 상태</Link></footer>
    </div>
    <nav className={styles.mobileDock} aria-label="모바일 주요 메뉴">
      {[PRIMARY_NAVIGATION[0], PRIMARY_NAVIGATION[2], PRIMARY_NAVIGATION[5], PORTFOLIO_NAVIGATION[0]].map((item) => <Link key={item.href} href={item.href} aria-current={active.href === item.href ? "page" : undefined}><WorkspaceIcon name={item.icon} /><span>{item.label}</span></Link>)}
      <button type="button" onClick={open}><WorkspaceIcon name="menu" /><span>전체 메뉴</span></button>
    </nav>
    <dialog className={styles.commandDialog} ref={dialog} aria-labelledby="workspace-search-title" onClick={(event) => { if (event.target === dialog.current) close(); }}>
      <div className={styles.dialogBody}>
        <header><div><h2 id="workspace-search-title">어디를 살펴볼까요?</h2><p>화면을 찾거나 종목 코드로 바로 이동하세요.</p></div><button className={styles.iconButton} type="button" onClick={close} aria-label="빠른 이동 닫기"><WorkspaceIcon name="close" /></button></header>
        <label className={styles.searchField}><WorkspaceIcon name="search" /><input ref={input} autoComplete="off" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="예: 사이클, 성과, AAPL" aria-label="화면 이름 또는 종목 코드" /></label>
        <p className={styles.resultCount} role="status">{results.length}개 화면{symbol ? " · 종목 바로가기 가능" : ""}</p>
        <nav aria-label="빠른 이동 검색 결과" className={styles.results}>
          {symbol && <Link href={symbol as Route} onClick={close}><WorkspaceIcon name="company" /><span><strong>{query.trim().toUpperCase()} 종목 리서치</strong><small>종목 코드 직접 이동 · 데이터 존재 여부는 상세에서 확인</small></span><WorkspaceIcon name="arrow" /></Link>}
          {results.map((item) => <Link href={item.href} key={item.href} onClick={close}><WorkspaceIcon name={item.icon} /><span><strong>{item.label}</strong><small>{item.description}</small></span></Link>)}
          {!results.length && !symbol && <p className={styles.noResults}>일치하는 화면이 없습니다. 화면 이름이나 종목 코드를 확인해 주세요.</p>}
        </nav>
        <footer>Tab으로 이동 · Enter로 열기 · Esc로 닫기</footer>
      </div>
    </dialog>
  </div>;
}
