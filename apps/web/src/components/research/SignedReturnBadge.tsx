import { formatSignedPercent } from "@/lib/presentation";
import type { MovementTone, SignedPercentOptions } from "@/lib/presentation";

import styles from "./SignedReturnBadge.module.css";

const toneClassName: Record<MovementTone, string> = {
  up: styles.up,
  down: styles.down,
  flat: styles.flat,
  unknown: styles.unknown,
};

export type SignedReturnBadgeProps = {
  readonly value: number | null | undefined;
  readonly label?: string;
  readonly options?: SignedPercentOptions;
};

export function SignedReturnBadge({ value, label = "전일 대비", options }: SignedReturnBadgeProps) {
  const formatted = formatSignedPercent(value, options);

  return (
    <span className={`${styles.badge} ${toneClassName[formatted.tone]}`} aria-label={formatted.a11yLabel}>
      <strong>{formatted.label}</strong>
      <small>{label}</small>
    </span>
  );
}
