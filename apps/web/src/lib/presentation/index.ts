export { investorCopy } from "./copy";
export { brokerDataUseLabel, brokerOrderBoundaryLabel, formatBasisPointDiff } from "./broker";
export type { BrokerDataUseInput } from "./broker";
export { formatCount, formatDate, formatPercent } from "./format";
export { evidenceCopy, portfolioCopy, recommendationCopy, stockCopy } from "./investment-copy";
export {
  buildOperationsViewModel,
} from "./operations";
export {
  buildPaperTradingViewModel,
  paperTradingState,
  paperTradingStateLabel,
} from "./paper";
export type { PaperTradingState } from "./paper";
export { buildPortfolioCoverageViewModel } from "./portfolio";
export {
  buildRecommendationViewModel,
  recommendationExecutionStatus,
  recommendationProductKind,
  recommendationProductLabel,
} from "./recommendation";
export type { RecommendationProductKind } from "./recommendation";
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
export {
  buildStockViewModel,
  latestDailyChangePct,
  stockProductKind,
  stockProductLabel,
} from "./stock";
export type { StockProductKind } from "./stock";
export type { InvestmentViewModel, PresentationMetric } from "./view-model";
export { missingMetric } from "./view-model";
