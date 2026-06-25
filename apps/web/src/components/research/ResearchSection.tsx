import type { ReactNode } from "react";

import styles from "./ResearchSection.module.css";

type ResearchSectionProps = {
  readonly eyebrow: string;
  readonly title: string;
  readonly description?: string;
  readonly children: ReactNode;
  readonly id?: string;
};

export function ResearchSection({ eyebrow, title, description, children, id }: ResearchSectionProps) {
  const headingId = id ? `${id}-title` : undefined;
  return (
    <section className={styles.section} id={id} aria-labelledby={headingId}>
      <header className={styles.header}>
        <span>{eyebrow}</span>
        <h2 id={headingId}>{title}</h2>
        {description ? <p>{description}</p> : null}
      </header>
      <div className={styles.content}>{children}</div>
    </section>
  );
}
