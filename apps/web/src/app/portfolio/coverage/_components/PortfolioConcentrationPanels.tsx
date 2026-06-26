import type { PortfolioCoverageData } from "@/lib/types";

import {
  concentrationStatusClass,
  concentrationStatusLabel,
  exposureStatusLabel,
  formatCoveragePercent,
  userFacingText,
} from "./portfolioCoverageFormat";

type ExposureRow = {
  exposure_key: string;
  exposure_name: string;
  exposure_weight: number;
  position_count: number;
  symbols: string[];
  limit: number;
  excess_weight: number;
  status: string;
};

function ExposureList({ empty, items }: { readonly empty: string; readonly items: readonly ExposureRow[] }) {
  if (items.length === 0) {
    return <p className="empty-state" style={{ margin: 0 }}>{empty}</p>;
  }

  return (
    <div className="bento-list" style={{ gap: "8px" }}>
      {items.map((item) => (
        <div className="bento-list-item" key={item.exposure_key}>
          <div>
            <span className={`risk-tag ${item.status === "over_limit" ? "risk-high" : "risk-low"}`}>
              {exposureStatusLabel(item.status)}
            </span>
            <strong>{userFacingText(item.exposure_name)}</strong>
            <span>
              {item.symbols.join(", ") || "심볼 없음"} · {item.position_count}개 포지션
            </span>
          </div>
          <div style={{ textAlign: "right", minWidth: "120px" }}>
            <strong>{formatCoveragePercent(item.exposure_weight)}</strong>
            <small style={{ display: "block", color: "var(--text-secondary)" }}>
              한도 {formatCoveragePercent(item.limit)}
            </small>
          </div>
        </div>
      ))}
    </div>
  );
}

type PortfolioConcentrationPanelsProps = {
  readonly concentration: PortfolioCoverageData["risk_budget"]["concentration"];
  readonly riskBudget: PortfolioCoverageData["risk_budget"];
};

export function PortfolioConcentrationPanels({ concentration, riskBudget }: PortfolioConcentrationPanelsProps) {
  return (
    <>
      <article
        className="bento-card span-4"
        style={{ borderColor: concentration.status === "needs_concentration_review" ? "var(--accent-red)" : "var(--border-light)" }}
      >
        <div className="section-heading">
          <div>
            <span className="metric-sub">섹터·테마 집중도</span>
            <h2>같은 흐름에 얼마나 몰렸는지 확인</h2>
          </div>
          <span className={`risk-tag ${concentrationStatusClass(concentration.status)}`}>
            {concentrationStatusLabel(concentration.status)}
          </span>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          같은 섹터나 테마에 여러 종목이 묶이면 종목 수가 분산되어 보여도 실제 위험은 한 방향으로 움직일 수 있습니다.
          이 표는 주문 지시가 아니라 확인 우선순위를 정하기 위한 노출도 지도입니다.
        </p>
        <div className="status-rail compact-rail" aria-label="집중도 정책 요약" style={{ marginBottom: "20px" }}>
          <article className="rail-cell">
            <span>섹터 한도</span>
            <strong>{formatCoveragePercent(concentration.max_sector_weight)}</strong>
            <small>초과 시 집중도 확인</small>
          </article>
          <article className="rail-cell">
            <span>테마 한도</span>
            <strong>{formatCoveragePercent(concentration.max_theme_weight)}</strong>
            <small>상위 흐름 노출</small>
          </article>
          <article className="rail-cell">
            <span>미분류 한도</span>
            <strong>{formatCoveragePercent(concentration.max_unclassified_weight)}</strong>
            <small>데이터 품질 공백</small>
          </article>
          <article className="rail-cell">
            <span>미분류 비중</span>
            <strong>{formatCoveragePercent(concentration.unclassified_weight)}</strong>
            <small>{concentration.unclassified_symbols.join(", ") || "없음"}</small>
          </article>
          <article className="rail-cell">
            <span>초과 그룹</span>
            <strong>{concentration.over_limit_count}</strong>
            <small>섹터/테마 합산</small>
          </article>
        </div>

        <div className="bento-grid">
          <article className="bento-card span-2">
            <span className="metric-sub">섹터 노출</span>
            <h3 style={{ fontSize: "1.15rem", margin: "6px 0 12px" }}>산업 방향으로 묶인 위험</h3>
            <ExposureList empty="섹터 분류가 아직 없습니다. 종목 분류 데이터를 보강해야 합니다." items={concentration.sector_exposures} />
          </article>
          <article className="bento-card span-2">
            <span className="metric-sub">테마 노출</span>
            <h3 style={{ fontSize: "1.15rem", margin: "6px 0 12px" }}>거시·테마 흐름으로 묶인 위험</h3>
            <ExposureList empty="테마 분류가 아직 없습니다. 뉴스/사이클 연결을 먼저 보강해야 합니다." items={concentration.theme_exposures} />
          </article>
        </div>
      </article>

      <article id="portfolio-position-map" className="bento-card span-4">
        <div className="section-heading">
          <div>
            <span className="metric-sub">리밸런싱 우선순위</span>
            <h2>바로 주문하지 않고 먼저 확인할 대상</h2>
          </div>
          <span className="risk-tag risk-medium">읽기 전용</span>
        </div>
        {riskBudget.rebalance_priorities.length === 0 ? (
          <p className="empty-state" style={{ margin: 0 }}>
            현재 정책 기준에서 우선 확인할 포지션이 없습니다.
          </p>
        ) : (
          <div className="bento-list">
            {riskBudget.rebalance_priorities.map((priority) => (
              <div className="bento-list-item" key={`${priority.symbol}-${priority.action}`}>
                <div>
                  <span className="metric-sub">우선순위 {priority.priority}</span>
                  <strong>{priority.symbol} · {formatCoveragePercent(priority.current_weight)}</strong>
                  <span>{userFacingText(priority.action)}</span>
                </div>
                <span style={{ color: "var(--text-secondary)", maxWidth: "520px" }}>
                  {userFacingText(priority.reason)}
                </span>
              </div>
            ))}
          </div>
        )}
      </article>
    </>
  );
}
