import type { ReactNode } from "react";

import styles from "./RecommendationDetailDisclosure.module.css";

type DisclosureTone = "neutral" | "ready" | "watch" | "blocked";

type RecommendationDetailDisclosureProps = {
  readonly id: string;
  readonly eyebrow: string;
  readonly title: string;
  readonly summary: string;
  readonly badge: string;
  readonly tone?: DisclosureTone;
  readonly defaultOpen?: boolean;
  readonly children: ReactNode;
};

export function RecommendationDetailDisclosure({
  badge,
  children,
  defaultOpen = false,
  eyebrow,
  id,
  summary,
  title,
  tone = "neutral",
}: RecommendationDetailDisclosureProps) {
  const toneClass = tone === "neutral" ? "" : styles[tone];
  return (
    <details className={`bento-card reveal delay-1 ${styles.disclosure} ${toneClass}`} id={id} open={defaultOpen}>
      <summary className={styles.summary}>
        <span className={styles.copy}>
          <span className={styles.eyebrow}>{eyebrow}</span>
          <strong className={styles.title}>{title}</strong>
          <span className={styles.body}>{summary}</span>
        </span>
        <span className={styles.actions}>
          <span className={styles.badge}>{badge}</span>
          <span className={styles.toggle}>
            <span className={styles.toggleClosed}>펼치기</span>
            <span className={styles.toggleOpen}>접기</span>
          </span>
        </span>
      </summary>
      <div className={styles.content}>{children}</div>
    </details>
  );
}
