import type { ReactNode } from "react";

import styles from "./StockEvidenceDisclosure.module.css";

type StockEvidenceDisclosureProps = {
  readonly eyebrow: string;
  readonly title: string;
  readonly summary: string;
  readonly children: ReactNode;
  readonly defaultOpen?: boolean;
};

export function StockEvidenceDisclosure({
  eyebrow,
  title,
  summary,
  children,
  defaultOpen = false,
}: StockEvidenceDisclosureProps) {
  return (
    <details className={styles.disclosure} open={defaultOpen}>
      <summary className={styles.summary}>
        <span>{eyebrow}</span>
        <strong>{title}</strong>
        <small>{summary}</small>
      </summary>
      <div className={styles.body}>{children}</div>
    </details>
  );
}
