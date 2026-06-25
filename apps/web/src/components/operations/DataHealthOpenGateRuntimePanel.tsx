import type { DataHealthOpenGateRuntimePanel as DataHealthOpenGateRuntimePanelData } from "./DataHealthRuntimeDetailPanelTypes";

type DataHealthOpenGateRuntimePanelProps = {
  readonly panel: DataHealthOpenGateRuntimePanelData;
};

export function DataHealthOpenGateRuntimePanel({ panel }: DataHealthOpenGateRuntimePanelProps) {
  return (
    <article className="ledger-panel" id="runtime-boundary">
      <div className="section-heading stacked-heading">
        <span>조건과 최신성</span>
        <h2>조건과 데이터 최신성</h2>
      </div>
      {panel.gates.length > 0 ? (
        <div className="flow-steps data-health-summary-grid runtime-gate-list">
          {panel.gates.map((gate) => (
            <div className="flow-step" key={gate.id}>
              <span>{gate.typeLabel}</span>
              <strong>{gate.label}</strong>
              <p>{gate.summary}</p>
              <dl className="fact-list compact-facts">
                <div>
                  <dt>상태</dt>
                  <dd>
                    <span className={`risk-tag ${gate.statusTone}`}>{gate.statusLabel}</span>
                  </dd>
                </div>
                <div>
                  <dt>다음 행동</dt>
                  <dd>{gate.nextActionLabel}</dd>
                </div>
                <div>
                  <dt>실거래 상태</dt>
                  <dd>{gate.orderBoundaryLabel}</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      ) : null}
      <div className="tag-ledger">
        {panel.chips.map((gate) => (
          <span className={`risk-tag ${gate.tone}`} key={gate.key}>
            {gate.label}
          </span>
        ))}
      </div>
      <dl className="fact-list compact-facts">
        {panel.freshnessRows.map((item) => (
          <div key={item.datasetLabel}>
            <dt>{item.datasetLabel}</dt>
            <dd>{item.valueLabel}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}
