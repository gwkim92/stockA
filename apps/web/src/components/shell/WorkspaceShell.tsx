"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import {
  OPERATIONS_NAVIGATION,
  PORTFOLIO_NAVIGATION,
  PRIMARY_NAVIGATION,
  RESEARCH_NAVIGATION,
  routeIsActive,
} from "./navigation";
import styles from "./WorkspaceShell.module.css";

type WorkspaceShellProps = {
  readonly children: ReactNode;
};

type NavigationGroupProps = {
  readonly label: string;
  readonly items: readonly {
    readonly href: Route;
    readonly label: string;
    readonly description: string;
  }[];
};

function NavigationGroup({ label, items }: NavigationGroupProps) {
  return (
    <div className={styles.utilityGroup}>
      <span>{label}</span>
      {items.map((item) => (
        <Link className={styles.utilityLink} href={item.href} key={item.href}>
          <strong>{item.label}</strong>
          <small>{item.description}</small>
        </Link>
      ))}
    </div>
  );
}

export function WorkspaceShell({ children }: WorkspaceShellProps) {
  const pathname = usePathname();

  return (
    <div className={styles.frame}>
      <a className={styles.skipLink} href="#main-content">
        본문으로 바로가기
      </a>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <Link className={styles.brand} href="/" aria-label="Stockanalysis 오늘 화면">
            <span className={styles.brandMark} aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M3 17.5 8.2 12l4 3 8.8-9" stroke="currentColor" strokeWidth="1.8" />
                <path d="M3 21h18" stroke="currentColor" strokeWidth="1.2" opacity=".55" />
              </svg>
            </span>
            <span className={styles.brandCopy}>
              <strong>Stockanalysis</strong>
              <small>중장기 투자 리서치</small>
            </span>
          </Link>

          <nav className={styles.primaryNav} aria-label="투자 리서치 주요 메뉴">
            {PRIMARY_NAVIGATION.map((item) => (
              <Link
                aria-current={routeIsActive(pathname, item.href) ? "page" : undefined}
                className={styles.navLink}
                href={item.href}
                key={item.href}
                title={item.description}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <details className={styles.utility}>
            <summary>전체 메뉴</summary>
            <div className={styles.utilityMenu}>
              <NavigationGroup label="리서치 상세" items={RESEARCH_NAVIGATION} />
              <NavigationGroup label="포트폴리오" items={PORTFOLIO_NAVIGATION} />
              <NavigationGroup label="운영 관리" items={OPERATIONS_NAVIGATION} />
            </div>
          </details>
        </div>
      </header>
      <main className={styles.main} id="main-content">
        {children}
      </main>
    </div>
  );
}
