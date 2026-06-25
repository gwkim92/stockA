import type { Route } from "next";
import Link from "next/link";

import styles from "./OperationsConsoleHeader.module.css";

type OperationsConsoleHeaderProps = {
  readonly section: string;
  readonly title: string;
  readonly description: string;
  readonly currentPath: Route;
};

const operationsLinks = [
  { href: "/data-health" as Route, label: "데이터 상태" },
  { href: "/admin/ai-agents" as Route, label: "AI 운영" },
  { href: "/trading-readiness" as Route, label: "거래 안전" },
  { href: "/remediation" as Route, label: "보완 작업" },
] as const;

export function OperationsConsoleHeader({
  section,
  title,
  description,
  currentPath,
}: OperationsConsoleHeaderProps) {
  return (
    <section className={styles.header} aria-label={`${section} 운영 콘솔`}>
      <div className={styles.copy}>
        <span>운영 관리 · {section}</span>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
      <nav className={styles.navigation} aria-label="운영 관리 메뉴">
        {operationsLinks.map((item) => (
          <Link
            aria-current={item.href === currentPath ? "page" : undefined}
            className={item.href === currentPath ? styles.active : undefined}
            href={item.href}
            key={item.href}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </section>
  );
}
