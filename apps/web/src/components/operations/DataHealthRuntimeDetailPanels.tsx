import { DataHealthOpenGateRuntimePanel } from "./DataHealthOpenGateRuntimePanel";
import { DataHealthProviderBudgetPanel } from "./DataHealthProviderBudgetPanel";
import { DataHealthRecommendationPricePanel } from "./DataHealthRecommendationPricePanel";
import { DataHealthRuntimeBoundaryPanel } from "./DataHealthRuntimeBoundaryPanel";
import type { DataHealthRuntimeDetailPanelsProps } from "./DataHealthRuntimeDetailPanelTypes";

export type {
  DataHealthRuntimeChip,
  DataHealthRuntimeDetailPanelsProps,
} from "./DataHealthRuntimeDetailPanelTypes";

export function DataHealthRuntimeDetailPanels({
  activeRecommendationPriceFreshness,
  openGates,
  providerBudget,
  runtimeBoundary,
}: DataHealthRuntimeDetailPanelsProps) {
  return (
    <aside className="side-ledger">
      <DataHealthProviderBudgetPanel panel={providerBudget} />
      <DataHealthRecommendationPricePanel panel={activeRecommendationPriceFreshness} />
      <DataHealthOpenGateRuntimePanel panel={openGates} />
      <DataHealthRuntimeBoundaryPanel panel={runtimeBoundary} />
    </aside>
  );
}
