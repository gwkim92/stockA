import type { DataHealthExecutionHistoryRow } from "@/components/operations/DataHealthExecutionHistoryPanel";
import { koCode } from "@/lib/korean-labels";

import {
  executionIdLabel,
  operationCopy,
  statusRiskClass,
} from "./dataHealthModel";
import type { DataHealthData } from "./dataHealthTypes";

export function buildDataHealthExecutionHistoryRows(
  data: DataHealthData,
): readonly DataHealthExecutionHistoryRow[] {
  return data.pipeline_runs.map((run) => ({
    cadenceLabel: koCode(run.cadence),
    domainLabel: koCode(run.domain),
    finishedAtLabel: run.finished_at,
    freshnessLabel: koCode(run.health_status),
    id: run.latest_run_id,
    latestRunLabel: executionIdLabel(run.latest_run_id),
    pipelineNameLabel: operationCopy(run.pipeline_name),
    statusLabel: koCode(run.latest_status),
    statusTone: statusRiskClass(run.latest_status),
  }));
}
