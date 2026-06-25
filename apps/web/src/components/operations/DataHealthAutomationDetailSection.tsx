import {
  AutomationCardsPanel,
  ExecutionStructurePanel,
  LocalWorkerPanel,
  ManualSmokePanel,
  NewsAfterAnalysisPanel,
  ProfileSchedulerPanel,
  SchedulerDetailPanel,
} from "./DataHealthAutomationDetailPanels";
import type { DataHealthAutomationDetailSectionProps } from "./DataHealthAutomationDetailTypes";

export function DataHealthAutomationDetailSection({
  automationCards,
  automationStatusLabel,
  localWorker,
  manualSmoke,
  newsAfterAnalysisSteps,
  profileScheduler,
  schedulerDetail,
}: DataHealthAutomationDetailSectionProps) {
  return (
    <details className="operator-details-panel reveal delay-2">
      <summary>
        <span>상세 운영 기록</span>
        <strong>스케줄, 실행 요약, 수동 점검, 작업별 실행 구조를 필요할 때만 펼친다</strong>
      </summary>

      <section className="flow-panel details-inner" aria-labelledby="automation-summary-title">
        <div className="section-heading flow-heading">
          <span>자동 수집 / 분석 상태</span>
          <h2 id="automation-summary-title">최근 실행과 실제 반복 자동화를 분리해서 본다</h2>
        </div>
        <p className="page-lede">
          아래 작업은 최근 실행 이력과 반복 실행 상태를 같이 보여준다. 현재 반복 실행은 {automationStatusLabel} 상태이며,
          수집 성공과 추천 근거는 별도로 검토한다.
        </p>

        <SchedulerDetailPanel panel={schedulerDetail} />
        <ExecutionStructurePanel />
        <ProfileSchedulerPanel panel={profileScheduler} />
        <NewsAfterAnalysisPanel steps={newsAfterAnalysisSteps} />
        <LocalWorkerPanel panel={localWorker} />
        <ManualSmokePanel panel={manualSmoke} />
        <AutomationCardsPanel cards={automationCards} />
      </section>
    </details>
  );
}
