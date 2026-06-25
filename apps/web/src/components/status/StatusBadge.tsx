import { displayStatus } from "@/lib/presentation";
import type { DisplayStatusKind } from "@/lib/presentation";

import styles from "./StatusBadge.module.css";

type StatusBadgeProps = {
  readonly kind: DisplayStatusKind;
  readonly label?: string;
};

export function StatusBadge({ kind, label }: StatusBadgeProps) {
  const status = displayStatus(kind);
  return (
    <span className={`${styles.badge} ${styles[kind]}`} title={status.description}>
      {label ?? status.label}
    </span>
  );
}
