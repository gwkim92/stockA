import type { DataHealthActiveRecommendationPriceFreshnessPanel } from "./DataHealthRuntimeDetailPanelTypes";

type DataHealthRecommendationPricePanelProps = {
  readonly panel: DataHealthActiveRecommendationPriceFreshnessPanel;
};

export function DataHealthRecommendationPricePanel({ panel }: DataHealthRecommendationPricePanelProps) {
  return (
    <article className="ledger-panel" id="active-recommendation-price-freshness">
      <div className="section-heading stacked-heading">
        <span>추천 종목 가격</span>
        <h2>추천에 쓰는 가격이 최신인지 확인</h2>
        <p>추천, 성과 측정, 가상 매매 검증은 종목별 가격을 읽는다. 오래된 종목이 보이면 가격 보강이 먼저다.</p>
      </div>
      <dl className="fact-list">
        <div>
          <dt>상태</dt>
          <dd>
            <span className={`risk-tag ${panel.statusTone}`}>{panel.statusLabel}</span>
          </dd>
        </div>
        <div>
          <dt>추천 종목</dt>
          <dd>{panel.symbolCoverageLabel}</dd>
        </div>
        <div>
          <dt>최신 가격일</dt>
          <dd>{panel.latestTradeDateLabel}</dd>
        </div>
        <div>
          <dt>뒤처진 종목</dt>
          <dd>{panel.staleSummaryLabel}</dd>
        </div>
        <div>
          <dt>거래 경계</dt>
          <dd>{panel.orderBoundaryLabel}</dd>
        </div>
      </dl>
      <p className="panel-copy">{panel.nextActionLabel}</p>
      {panel.staleSymbols.length > 0 ? (
        <div className="flow-steps data-health-summary-grid">
          {panel.staleSymbols.map((item) => (
            <a className="flow-step" href={item.href} key={item.symbol}>
              <span>{item.statusLabel}</span>
              <strong>{item.symbol}</strong>
              <p>
                {item.latestTradeDateLabel} · {item.daysBehindLabel} · {item.activeRecommendationCountLabel}
              </p>
            </a>
          ))}
        </div>
      ) : null}
    </article>
  );
}
