export type DataHealthTone = "ready" | "watch" | "block" | "risk-low" | "risk-medium" | "risk-high";

export type DataHealthCommandCard = {
  readonly body: string;
  readonly cta: string;
  readonly href: string;
  readonly label: string;
  readonly metric: string;
  readonly title: string;
  readonly tone: DataHealthTone;
};

export type DataHealthTriageGate = {
  readonly id: string;
  readonly label: string;
  readonly nextAction: string;
  readonly statusLabel: string;
  readonly statusTone: "risk-low" | "risk-medium" | "risk-high";
  readonly summary: string;
};

export type DataHealthTriageBucket = {
  readonly description: string;
  readonly gates: readonly DataHealthTriageGate[];
  readonly href: string;
  readonly key: string;
  readonly label: string;
  readonly title: string;
  readonly tone: "risk-low" | "risk-medium" | "risk-high";
};

export type DataHealthCollectionCard = {
  readonly check: string;
  readonly finishedAt: string;
  readonly index: string;
  readonly purpose: string;
  readonly statusLabel: string;
  readonly statusTone: string;
  readonly title: string;
};

type DataHealthOverviewProps = {
  readonly asOfDate: string;
  readonly collectionCards: readonly DataHealthCollectionCard[];
  readonly commandCards: readonly DataHealthCommandCard[];
  readonly headline: string;
  readonly metaItems: readonly string[];
  readonly triageBuckets: readonly DataHealthTriageBucket[];
  readonly triageStatus: string;
};

function assertNever(value: never): never {
  throw new Error(`Unhandled data health tone: ${value}`);
}

function commandToneClass(tone: DataHealthTone): string {
  switch (tone) {
    case "ready":
    case "risk-low":
      return "is-good";
    case "watch":
    case "risk-medium":
      return "is-watch";
    case "block":
    case "risk-high":
      return "is-block";
    default:
      return assertNever(tone);
  }
}

function coverageDestination(card: DataHealthCollectionCard): { readonly href: string; readonly label: string } {
  if (card.title.includes("주식 캔들")) {
    return { href: "/stocks", label: "종목·차트" };
  }
  if (card.title.includes("뉴스 원문")) {
    return { href: "/intelligence", label: "뉴스 흐름" };
  }
  if (card.title.includes("분류") || card.title.includes("AI")) {
    return { href: "/ai-evidence", label: "AI 근거" };
  }
  if (card.title.includes("추천")) {
    return { href: "/recommendations", label: "추천" };
  }
  if (card.title.includes("보유")) {
    return { href: "/portfolio/coverage", label: "포트폴리오" };
  }
  if (card.title.includes("토스")) {
    return { href: "/paper-trading", label: "브로커 현실" };
  }
  return { href: "/data-health", label: "상세 상태" };
}

export function DataHealthOverview({
  asOfDate,
  collectionCards,
  commandCards,
  headline,
  metaItems,
  triageBuckets,
  triageStatus,
}: DataHealthOverviewProps) {
  return (
    <>
      <section className="decision-brief workspace-brief data-health-brief reveal" aria-labelledby="data-health-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">데이터·자동화 · {asOfDate}</span>
          <h1 className="decision-brief-title" id="data-health-title">
            {headline}
          </h1>
          <p className="decision-brief-copy">
            최신성, 자동 실행, 무료 API 예산과 AI 품질을 기준으로 투자 화면의 신뢰도를 판단합니다.
          </p>
          <div className="decision-brief-meta" aria-label="데이터 상태 핵심 수치">
            {metaItems.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>
        <div className="decision-brief-grid workspace-command-grid data-health-command-grid" aria-label="데이터 상태 관제판">
          {commandCards.map((card, index) => (
            <a
              className={`decision-card data-health-command-card ${index === 0 ? "is-priority" : ""} ${commandToneClass(card.tone)}`}
              href={card.href}
              key={card.label}
            >
              <span>{card.label}</span>
              <strong>{card.title}</strong>
              <small>
                {card.metric} · {card.body}
              </small>
              <b>{card.cta}</b>
            </a>
          ))}
        </div>
      </section>

      <section className="feature-map-panel reveal delay-1" aria-labelledby="open-gate-triage-title">
        <div className="section-heading stacked-heading">
          <span>열린 확인 항목</span>
          <h2 id="open-gate-triage-title">장애, 대기, 원천 한계를 분리한다</h2>
          <p>{triageStatus}</p>
        </div>
        {triageBuckets.length > 0 ? (
          <div className="data-health-triage-grid">
            {triageBuckets.map((bucket) => (
              <article className="data-health-triage-card" key={bucket.key}>
                <div className="data-health-triage-head">
                  <span>{bucket.label}</span>
                  <strong className={`risk-tag ${bucket.tone}`}>{bucket.gates.length}개</strong>
                </div>
                <h3>{bucket.title}</h3>
                <p>{bucket.description}</p>
                <div className="data-health-triage-list">
                  {bucket.gates.map((gate) => (
                    <a href={bucket.href} key={gate.id}>
                      <span className={`risk-tag ${gate.statusTone}`}>{gate.statusLabel}</span>
                      <strong>{gate.label}</strong>
                      <small>{gate.summary}</small>
                      <small>다음 확인: {gate.nextAction}</small>
                    </a>
                  ))}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <strong>열린 확인 항목 없음</strong>
            <p>현재 상단 기준에서 즉시 조치할 장애, 관리되지 않은 대기, 원천 한계가 없다.</p>
          </div>
        )}
      </section>

      <section className="feature-map-panel reveal delay-1" aria-labelledby="collection-status-title">
        <div className="section-heading stacked-heading">
          <span>수집/분석별 상태</span>
          <h2 id="collection-status-title">무엇이 언제 실행됐고, 어디에 쓰이는지 본다</h2>
        </div>
        <p className="board-intro">
          주식 캔들, 뉴스 원문, 1차 분류, AI 분석, 추천 갱신, 보유 상태 판단이 각각 따로 돈다.
          문제가 있는 데이터가 있으면 해당 화면의 판단을 낮게 신뢰해야 한다.
        </p>
        <div className="data-health-coverage-matrix" aria-label="수집·분석 커버리지 매트릭스">
          <div className="data-health-coverage-head">
            <span>수집·분석 커버리지</span>
            <strong>원천 데이터가 어느 투자 화면에 쓰이는지</strong>
            <small>상태가 낮으면 연결된 화면의 판단 신뢰도도 낮춘다.</small>
          </div>
          <div className="data-health-coverage-rows">
            {collectionCards.map((card) => {
              const destination = coverageDestination(card);
              return (
                <a className="data-health-coverage-row" href={destination.href} key={card.index}>
                  <span>{card.index}</span>
                  <strong>{card.title}</strong>
                  <em className={`risk-tag ${card.statusTone}`}>{card.statusLabel}</em>
                  <small>{card.purpose}</small>
                  <small>{card.check}</small>
                  <b>{destination.label}</b>
                </a>
              );
            })}
          </div>
        </div>
        <div className="feature-map-grid collection-map-grid">
          {collectionCards.map((card) => (
            <article className="feature-map-card collection-map-card" key={card.index}>
              <span>{card.index}</span>
              <strong>{card.title}</strong>
              <em className={`risk-tag ${card.statusTone}`}>{card.statusLabel}</em>
              <small>{card.purpose}</small>
              <small>{card.check}</small>
              <small>최근 완료: {card.finishedAt}</small>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
