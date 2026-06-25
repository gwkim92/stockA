import type { DataHealthProviderBudgetPanel as DataHealthProviderBudgetPanelData } from "./DataHealthRuntimeDetailPanelTypes";

type DataHealthProviderBudgetPanelProps = {
  readonly panel: DataHealthProviderBudgetPanelData;
};

export function DataHealthProviderBudgetPanel({ panel }: DataHealthProviderBudgetPanelProps) {
  const budgetUsagePercent = Math.min(100, Math.max(0, panel.usagePercent));

  return (
    <article className="ledger-panel" id="provider-budget">
      <div className="section-heading stacked-heading">
        <span>무료 API 예산</span>
        <h2>데이터 제공자 호출 예산</h2>
      </div>
      <div className="budget-meter" aria-label={`호출 예산 사용률 ${budgetUsagePercent}%`}>
        <div style={{ width: `${budgetUsagePercent}%` }} />
      </div>
      <dl className="fact-list">
        <div>
          <dt>상태</dt>
          <dd>{panel.statusLabel}</dd>
        </div>
        <div>
          <dt>사용</dt>
          <dd>{panel.usedRequestCountLabel}</dd>
        </div>
        <div>
          <dt>기준일</dt>
          <dd>{panel.budgetDateLabel}</dd>
        </div>
        <div>
          <dt>최근 실행</dt>
          <dd>{panel.latestRunLabel}</dd>
        </div>
      </dl>
    </article>
  );
}
