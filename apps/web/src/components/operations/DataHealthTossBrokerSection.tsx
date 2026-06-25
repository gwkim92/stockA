type DataHealthTossBrokerSectionProps = {
  readonly cadenceCountLabel: string;
  readonly candleCountLabel: string;
  readonly comparisonLookbackLabel: string;
  readonly comparisonStatusLabel: string;
  readonly orderBoundaryLabel: string;
  readonly orderSubmitLabel: string;
  readonly requestedSymbolCountLabel: string;
  readonly syncStatusLabel: string;
  readonly syncStatusTone: "risk-low" | "risk-medium" | "risk-high";
  readonly title: string;
};

export function DataHealthTossBrokerSection({
  cadenceCountLabel,
  candleCountLabel,
  comparisonLookbackLabel,
  comparisonStatusLabel,
  orderBoundaryLabel,
  orderSubmitLabel,
  requestedSymbolCountLabel,
  syncStatusLabel,
  syncStatusTone,
  title,
}: DataHealthTossBrokerSectionProps) {
  return (
    <section className="feature-map-panel reveal delay-1" id="toss-market-data" aria-labelledby="toss-market-data-title">
      <div className="section-heading stacked-heading">
        <span>토스증권 브로커 데이터</span>
        <h2 id="toss-market-data-title">{title}</h2>
        <p>
          토스증권 데이터는 실제 계좌와 주문 가능성을 확인하는 브로커 현실 데이터다. 추천·사이클 계산은 계속
          분석 기준 가격을 사용하고, 토스 가격은 가격 기준 차이와 최신 일봉 미완성 여부를 검증한 뒤 참고한다.
        </p>
      </div>
      <div className="status-rail compact-rail">
        <article className="rail-cell">
          <span>수집 상태</span>
          <strong className={`risk-tag ${syncStatusTone}`}>{syncStatusLabel}</strong>
          <small>
            요청 종목 {requestedSymbolCountLabel} · 캔들 {candleCountLabel}
          </small>
        </article>
        <article className="rail-cell">
          <span>가격 기준 검증</span>
          <strong className="risk-tag risk-medium">{comparisonStatusLabel}</strong>
          <small>{comparisonLookbackLabel}</small>
        </article>
        <article className="rail-cell">
          <span>수집 주기</span>
          <strong>{cadenceCountLabel}</strong>
          <small>한국/미국 기준정보, 일봉, 관심 종목 호가·체결, 계좌 읽기 전용</small>
        </article>
        <article className="rail-cell">
          <span>실주문 상태</span>
          <strong className="risk-tag risk-low">{orderBoundaryLabel}</strong>
          <small>{orderSubmitLabel}</small>
        </article>
      </div>
    </section>
  );
}
