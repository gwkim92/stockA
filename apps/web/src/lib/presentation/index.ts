export { investorCopy } from "./copy";
export { formatCount, formatDate, formatPercent } from "./format";
export { evidenceCopy, portfolioCopy, recommendationCopy, stockCopy } from "./investment-copy";
export {
  calculatePortfolioReturnSummary,
  calculatePositionReturn,
  formatSignedPercent,
  movementMagnitudePercent,
  movementTone,
  summarizeMovementBuckets,
} from "./returns";
export type {
  MovementBucketSummary,
  MovementTone,
  PortfolioReturnSummary,
  PositionReturn,
  SignedPercentLabel,
  SignedPercentOptions,
} from "./returns";
export {
  DISPLAY_STATUS_KINDS,
  displayStatus,
  statusFromDataCondition,
} from "./status";
export type { DisplayStatus, DisplayStatusKind } from "./status";
