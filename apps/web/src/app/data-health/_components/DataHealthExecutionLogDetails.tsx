import {
  DataHealthExecutionHistoryPanel,
  type DataHealthExecutionHistoryRow,
} from "@/components/operations/DataHealthExecutionHistoryPanel";
import {
  DataHealthRuntimeDetailPanels,
  type DataHealthRuntimeDetailPanelsProps,
} from "@/components/operations/DataHealthRuntimeDetailPanels";

type DataHealthExecutionLogDetailsProps = {
  readonly executionHistoryRows: readonly DataHealthExecutionHistoryRow[];
  readonly runtimeDetailPanels: DataHealthRuntimeDetailPanelsProps;
};

export function DataHealthExecutionLogDetails({
  executionHistoryRows,
  runtimeDetailPanels,
}: DataHealthExecutionLogDetailsProps) {
  return (
    <details className="operator-details-panel reveal delay-2" id="execution-log">
      <summary>
        <span>실행 로그와 예산 상세</span>
        <strong>작업 이력, 무료 API 예산, 조건/최신성</strong>
      </summary>

      <section className="split-ledger details-inner">
        <DataHealthExecutionHistoryPanel rows={executionHistoryRows} />
        <DataHealthRuntimeDetailPanels {...runtimeDetailPanels} />
      </section>
    </details>
  );
}
