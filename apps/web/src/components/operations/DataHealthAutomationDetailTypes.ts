export type DataHealthFactRow = {
  readonly label: string;
  readonly value: string;
};

export type DataHealthSchedulerDetailPanel = {
  readonly description: string;
  readonly factRows: readonly DataHealthFactRow[];
  readonly title: string;
};

export type DataHealthSchedulerTimer = {
  readonly activeStateLabel: string;
  readonly lastResultLabel: string;
  readonly nextElapseLabel: string;
  readonly profileLabel: string;
  readonly scheduleLabel: string;
};

export type DataHealthProfileSchedulerPanel = {
  readonly activeTimerSummaryLabel: string;
  readonly timers: readonly DataHealthSchedulerTimer[];
};

export type DataHealthOperatingFlowStep = {
  readonly finishedAtLabel: string;
  readonly index: string;
  readonly next: string;
  readonly output: string;
  readonly ownerLabel: string;
  readonly statusLabel: string;
  readonly title: string;
  readonly warningLabel: string;
};

export type DataHealthLocalWorkerCycleRow = {
  readonly artifactRunCountLabel: string;
  readonly jobCountLabel: string;
  readonly smokeStatusLabel: string;
  readonly startedAtLabel: string;
  readonly title: string;
};

export type DataHealthLocalWorkerPanel = {
  readonly cycleRows: readonly DataHealthLocalWorkerCycleRow[];
  readonly description: string;
  readonly eyebrow: string;
  readonly factRows: readonly DataHealthFactRow[];
  readonly title: string;
};

export type DataHealthManualSmokeRunRow = {
  readonly errorLabel: string;
  readonly exitCodeLabel: string;
  readonly jobLabel: string;
  readonly pipelineLabel: string;
  readonly statusLabel: string;
};

export type DataHealthManualSmokePanel = {
  readonly artifactRows: readonly DataHealthManualSmokeRunRow[];
  readonly description: string;
  readonly eyebrow: string;
  readonly factRows: readonly DataHealthFactRow[];
  readonly title: string;
};

export type DataHealthAutomationCard = {
  readonly cadenceLabel: string;
  readonly description: string;
  readonly detail: string;
  readonly finishedAtLabel: string;
  readonly stateLabel: string;
  readonly title: string;
};

export type DataHealthAutomationDetailSectionProps = {
  readonly automationCards: readonly DataHealthAutomationCard[];
  readonly automationStatusLabel: string;
  readonly localWorker: DataHealthLocalWorkerPanel;
  readonly manualSmoke: DataHealthManualSmokePanel;
  readonly newsAfterAnalysisSteps: readonly DataHealthOperatingFlowStep[];
  readonly profileScheduler: DataHealthProfileSchedulerPanel;
  readonly schedulerDetail: DataHealthSchedulerDetailPanel;
};
