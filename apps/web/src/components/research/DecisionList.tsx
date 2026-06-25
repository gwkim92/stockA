import type { Route } from "next";
import Link from "next/link";

import type { DisplayStatusKind } from "@/lib/presentation";
import { StatusBadge } from "@/components/status/StatusBadge";

import styles from "./DecisionList.module.css";

export type DecisionListItem = {
  readonly key: string;
  readonly label: string;
  readonly subject: string;
  readonly title: string;
  readonly description: string;
  readonly status: DisplayStatusKind;
  readonly href: Route;
  readonly actionLabel: string;
};

type DecisionListProps = {
  readonly items: readonly DecisionListItem[];
  readonly emptyText: string;
};

export function DecisionList({ items, emptyText }: DecisionListProps) {
  if (items.length === 0) {
    return <p>{emptyText}</p>;
  }

  return (
    <div className={styles.list}>
      {items.map((item) => (
        <article className={styles.item} key={item.key}>
          <div className={styles.identity}>
            <span>{item.label}</span>
            <strong>{item.subject}</strong>
            <StatusBadge kind={item.status} />
          </div>
          <div className={styles.copy}>
            <strong>{item.title}</strong>
            <p>{item.description}</p>
          </div>
          <Link className={styles.action} href={item.href}>
            {item.actionLabel}
          </Link>
        </article>
      ))}
    </div>
  );
}
