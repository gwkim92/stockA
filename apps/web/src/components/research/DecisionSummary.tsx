import type { Route } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import styles from "./DecisionSummary.module.css";

type DecisionAction = {
  readonly href: Route;
  readonly label: string;
};

type DecisionSummaryProps = {
  readonly eyebrow: string;
  readonly title: string;
  readonly description: string;
  readonly primaryAction: DecisionAction;
  readonly secondaryActions?: readonly DecisionAction[];
  readonly side: ReactNode;
};

const NO_SECONDARY_ACTIONS: readonly DecisionAction[] = [];

export function DecisionSummary({
  eyebrow,
  title,
  description,
  primaryAction,
  secondaryActions = NO_SECONDARY_ACTIONS,
  side,
}: DecisionSummaryProps) {
  return (
    <section className={styles.summary} aria-labelledby="decision-summary-title">
      <div className={styles.copy}>
        <span className={styles.eyebrow}>{eyebrow}</span>
        <h1 className={styles.title} id="decision-summary-title">
          {title}
        </h1>
        <p className={styles.description}>{description}</p>
        <div className={styles.actions}>
          <Link className={styles.primaryAction} href={primaryAction.href}>
            {primaryAction.label}
          </Link>
          {secondaryActions.map((action) => (
            <Link className={styles.secondaryAction} href={action.href} key={action.href}>
              {action.label}
            </Link>
          ))}
        </div>
      </div>
      <aside className={styles.side}>{side}</aside>
    </section>
  );
}
