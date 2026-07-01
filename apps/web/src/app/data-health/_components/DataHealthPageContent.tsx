import type { Route } from "next";

import {
  DataHealthAutomationDetailSection,
} from "@/components/operations/DataHealthAutomationDetailSection";
import { DataHealthOverview } from "@/components/operations/DataHealthOverview";
import { DataHealthTossBrokerSection } from "@/components/operations/DataHealthTossBrokerSection";
import { OperationsConsoleHeader } from "@/components/operations/OperationsConsoleHeader";
import { PageDecisionMap } from "@/components/research/PageDecisionMap";

import { DataHealthAiFallbackWarning } from "./DataHealthAiFallbackWarning";
import { DataHealthDataGapScorecards } from "./DataHealthDataGapScorecards";
import { DataHealthDecisionFlowStatus } from "./DataHealthDecisionFlowStatus";
import { DataHealthDetailDecisionCardsSection } from "./DataHealthDetailDecisionCardsSection";
import { DataHealthExecutionLogDetails } from "./DataHealthExecutionLogDetails";
import { DataHealthInvestmentQualityDetails } from "./DataHealthInvestmentQualityDetails";
import { DataHealthLiveAiInvocationSection } from "./DataHealthLiveAiInvocationSection";
import { DataHealthNewsAiEvalQualitySection } from "./DataHealthNewsAiEvalQualitySection";
import { DataHealthOpenAiProviderSection } from "./DataHealthOpenAiProviderSection";
import { DataHealthQualityAuditSection } from "./DataHealthQualityAuditSection";
import { DataHealthSchedulerCadenceSection } from "./DataHealthSchedulerCadenceSection";
import type { DataHealthPageModel } from "./dataHealthPageModel";

type DataHealthPageContentProps = {
  readonly model: DataHealthPageModel;
};

export function DataHealthPageContent({ model }: DataHealthPageContentProps) {
  return (
    <div className="terminal-page decision-page">
      <OperationsConsoleHeader
        section="데이터 상태"
        title={model.headerTitle}
        description={model.headerDescription}
        currentPath={"/data-health" as Route}
      />
      <PageDecisionMap {...model.decisionMap} />
      <DataHealthDecisionFlowStatus cards={model.decisionFlowCards} />
      <DataHealthDataGapScorecards cards={model.dataGapCards} />
      <DataHealthOverview
        asOfDate={model.data.as_of_date}
        collectionCards={model.overviewCollectionCards}
        commandCards={model.commandCenterCards}
        headline={model.dataHealthHeadline}
        metaItems={model.dataHealthMetaItems}
        triageBuckets={model.triageOverviewBuckets}
        triageStatus={model.gateTriageStatus}
      />

      <DataHealthTossBrokerSection {...model.tossBrokerSection} />

      <DataHealthQualityAuditSection
        qualityAudit={model.qualityAudit}
        qualityAuditSamples={model.qualityAuditSamples}
      />

      <DataHealthLiveAiInvocationSection liveAiInvocationHealth={model.liveAiInvocationHealth} />

      <DataHealthOpenAiProviderSection openAiProviderHealth={model.openAiProviderHealth} />

      <DataHealthNewsAiEvalQualitySection newsAiEvalQuality={model.newsAiEvalQuality} />

      <DataHealthDetailDecisionCardsSection cards={model.detailDecisionCards} />

      <DataHealthInvestmentQualityDetails data={model.data} />

      <DataHealthSchedulerCadenceSection
        ec2SchedulerInstalled={model.ec2SchedulerInstalled}
        groups={model.schedulerCadenceGroups}
      />

      <DataHealthAiFallbackWarning run={model.runs.aiRun} />

      <DataHealthAutomationDetailSection {...model.automationDetailSection} />

      <DataHealthExecutionLogDetails
        executionHistoryRows={model.executionHistoryRows}
        runtimeDetailPanels={model.runtimeDetailPanels}
      />
    </div>
  );
}
