import { Fragment } from "react";
import Link from "next/link";
import type { Route } from "next";

import { ValuationTargetRangeCard } from "@/components/valuation-target-range-card";
import { koCode } from "@/lib/korean-labels";
import { stockCopy } from "@/lib/presentation";
import type { StockDetailData } from "@/lib/types";

type ValuationItem = {
  readonly key: string;
  readonly value: string;
};

type StockValuationResearchPanelProps = {
  readonly data: StockDetailData;
  readonly valuationItems: readonly ValuationItem[];
};

function userFacingStockText(value: string | null | undefined) {
  return stockCopy(value);
}

function providerLabel(provider: string) {
  if (provider === "codex_oauth") {
    return "심화 근거 분석";
  }
  if (provider === "fixture") {
    return "검증용 샘플 분석";
  }
  return koCode(provider);
}

function valuationSensitivityLabel(key: string) {
  const labels: Record<string, string> = {
    "base case": "기준 시나리오",
    base_case: "기준 시나리오",
    confidence: "신뢰도",
    "upside case": "상승 시나리오",
    upside_case: "상승 시나리오",
    downside_case: "하락 시나리오",
  };
  return labels[key] ?? labels[key.toLowerCase()] ?? userFacingStockText(koCode(key));
}

function sourceDocumentHref(documentId: string | null) {
  return documentId ? (`/source-documents/${documentId}` as Route) : null;
}

function ResearchList({ title, items, emptyText }: { readonly title: string; readonly items: readonly string[]; readonly emptyText: string }) {
  return (
    <article className="bento-card">
      <span className="metric-sub">{title}</span>
      <div className="bento-list compact-list">
        {items.length > 0 ? (
          items.map((item) => <div className="bento-list-item" key={item}>{userFacingStockText(item)}</div>)
        ) : (
          <div className="empty-state">{emptyText}</div>
        )}
      </div>
    </article>
  );
}

export function StockValuationResearchPanel({ data, valuationItems }: StockValuationResearchPanelProps) {
  const equityResearch = data.equity_research;

  return (
    <>
      <div id="stock-valuation">
        <ValuationTargetRangeCard
          valuation={data.valuation_target_range}
          eyebrow="전문 밸류에이션"
          title={`${data.symbol} 목표가 범위`}
        />
      </div>

      <section className="bento-card span-4 reveal delay-3" id="stock-equity-research" aria-label="기업 리서치 리포트">
        <div className="section-heading">
          <div>
            <span className="metric-sub">기업 리서치 리포트</span>
            <h2>{equityResearch ? userFacingStockText(equityResearch.title) : `${data.symbol} 기업 리서치가 아직 생성되지 않았다`}</h2>
          </div>
          {equityResearch ? (
            <span className="bento-badge" style={{ margin: 0 }}>
              {providerLabel(equityResearch.provider)} • {equityResearch.as_of_date}
            </span>
          ) : null}
        </div>
        {equityResearch ? (
          <>
            <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
              {userFacingStockText(equityResearch.korean_summary)}
            </p>
            <div className="status-rail compact-rail" aria-label="기업 리서치 범위">
              <div className="rail-cell">
                <span>핵심 변화</span>
                <strong>{equityResearch.key_points.length}</strong>
                <small>사업·재무 포인트</small>
              </div>
              <div className="rail-cell">
                <span>촉매</span>
                <strong>{equityResearch.catalysts.length}</strong>
                <small>좋아질 조건</small>
              </div>
              <div className="rail-cell">
                <span>리스크</span>
                <strong>{equityResearch.risks.length}</strong>
                <small>틀릴 수 있는 이유</small>
              </div>
              <div className="rail-cell">
                <span>무효화 조건</span>
                <strong>{equityResearch.invalidation_conditions.length}</strong>
                <small>투자 논리 재검토 기준</small>
              </div>
            </div>
            <div className="bento-grid" style={{ marginTop: "18px" }}>
              <ResearchList
                title="핵심 포인트"
                items={equityResearch.key_points}
                emptyText="핵심 변화가 아직 구조화되지 않았다."
              />
              <ResearchList
                title="촉매"
                items={equityResearch.catalysts}
                emptyText="상승 촉매가 아직 구조화되지 않았다."
              />
              <ResearchList title="리스크" items={equityResearch.risks} emptyText="리스크가 아직 구조화되지 않았다." />
              <ResearchList
                title="무효화 조건"
                items={equityResearch.invalidation_conditions}
                emptyText="투자 논리 무효화 조건이 아직 구조화되지 않았다."
              />
            </div>
            {valuationItems.length > 0 ? (
              <div className="stock-meta-grid" style={{ marginTop: "18px" }}>
                {valuationItems.map((item) => (
                  <Fragment key={item.key}>
                    <span>{valuationSensitivityLabel(item.key)}</span>
                    <strong>{userFacingStockText(item.value)}</strong>
                  </Fragment>
                ))}
              </div>
            ) : null}
            {equityResearch.source_document_ids.length > 0 ? (
              <div className="btn-row">
                {equityResearch.source_document_ids.slice(0, 3).map((documentId, index) => (
                  <Link className="btn btn-secondary" href={sourceDocumentHref(documentId) ?? "/data-health"} key={documentId}>
                    원천 문서 {index + 1}
                  </Link>
                ))}
              </div>
            ) : null}
            <p style={{ color: "var(--text-muted)", marginBottom: 0 }}>
              이 리포트는 저장된 읽기 전용 분석이다. 추천 점수와 주문은 직접 변경하지 않으며,
              추천 상세의 재무·밸류에이션 근거와 성과 평가는 별도로 본다.
            </p>
          </>
        ) : (
          <div className="empty-state">
            아직 이 종목의 기업 리서치 결과가 없다. 자동 분석이 완료되면 사업 설명, 핵심 재무 변화,
            촉매, 리스크, 무효화 조건, 밸류에이션 민감도가 이곳에 표시된다.
          </div>
        )}
      </section>
    </>
  );
}

