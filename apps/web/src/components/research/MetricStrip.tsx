import type { CSSProperties } from "react";

import styles from "./MetricStrip.module.css";

export type MetricItem = {
  readonly label: string;
  readonly value: string;
  readonly context: string;
};

type MetricStripProps = {
  readonly items: readonly MetricItem[];
  readonly label: string;
};

export function MetricStrip({ items, label }: MetricStripProps) {
  const style = { "--metric-count": Math.min(items.length, 5) } as CSSProperties;
  return (
    <section className={styles.strip} style={style} aria-label={label}>
      {items.map((item) => (
        <article className={styles.metric} key={item.label}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
          <small>{item.context}</small>
        </article>
      ))}
    </section>
  );
}
