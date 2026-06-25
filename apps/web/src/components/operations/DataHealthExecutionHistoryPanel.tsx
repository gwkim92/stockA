import type { DataHealthRiskTone } from "./DataHealthRuntimeDetailPanelTypes";

export type DataHealthExecutionHistoryRow = {
  readonly cadenceLabel: string;
  readonly domainLabel: string;
  readonly finishedAtLabel: string;
  readonly freshnessLabel: string;
  readonly id: string;
  readonly latestRunLabel: string;
  readonly pipelineNameLabel: string;
  readonly statusLabel: string;
  readonly statusTone: DataHealthRiskTone;
};

type DataHealthExecutionHistoryPanelProps = {
  readonly rows: readonly DataHealthExecutionHistoryRow[];
};

export function DataHealthExecutionHistoryPanel({ rows }: DataHealthExecutionHistoryPanelProps) {
  return (
    <article className="ledger-panel queue-panel">
      <div className="section-heading">
        <span>실행 이력</span>
        <h2>작업 실행 이력</h2>
      </div>
      <div className="ledger-table-wrap">
        <table className="ledger-table data-health-table">
          <thead>
            <tr>
              <th scope="col">작업</th>
              <th scope="col">도메인</th>
              <th scope="col">상태</th>
              <th scope="col">최신성</th>
              <th scope="col">최근 실행</th>
              <th scope="col">완료 시각</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>
                  <strong>{row.pipelineNameLabel}</strong>
                  <small>{row.cadenceLabel}</small>
                </td>
                <td>{row.domainLabel}</td>
                <td>
                  <span className={`risk-tag ${row.statusTone}`}>{row.statusLabel}</span>
                </td>
                <td>{row.freshnessLabel}</td>
                <td>{row.latestRunLabel}</td>
                <td>{row.finishedAtLabel}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
