import type { DisplayStatusKind } from "./status";

export type PresentationMetric = {
  readonly label: string;
  readonly value: string;
  readonly context: string;
};

export type InvestmentViewModel = {
  readonly title: string;
  readonly summary: string;
  readonly statusLabel: string;
  readonly statusTone: DisplayStatusKind;
  readonly investmentImpact: string;
  readonly nextAction: string;
  readonly sourceLimitReason: string;
  readonly metrics: readonly PresentationMetric[];
};

export function missingMetric(label: string, context: string): PresentationMetric {
  return {
    label,
    value: "해당 없음",
    context,
  };
}
