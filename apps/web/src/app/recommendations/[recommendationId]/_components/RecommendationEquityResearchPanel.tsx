import type { Route } from "next";
import Link from "next/link";

import { koCode } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";

import { RecommendationResearchList } from "./RecommendationResearchList";
import { userFacingRecommendationText } from "./recommendation-panel-format";
import styles from "./RecommendationEquityResearchPanel.module.css";

type ValuationSensitivityItem = {
  readonly key: string;
  readonly value: string;
};

type RecommendationEquityResearchPanelProps = {
  readonly symbol: string;
  readonly equityResearch: RecommendationDetailData["equity_research"];
  readonly valuationItems: readonly ValuationSensitivityItem[];
};

function stockHref(symbol: string) {
  return `/stocks/${encodeURIComponent(symbol)}` as Route;
}

function sourceDocumentHref(documentId: string) {
  return `/source-documents/${documentId}` as Route;
}

function providerLabel(provider: string) {
  if (provider === "codex_oauth") {
    return "AI 분석";
  }
  if (provider === "fixture") {
    return "검증용 샘플 분석";
  }
  return koCode(provider);
}

export function RecommendationEquityResearchPanel({
  equityResearch,
  symbol,
  valuationItems,
}: RecommendationEquityResearchPanelProps) {
  return (
    <section className={styles.panel} aria-label="기업 리서치 연결">
      <div className={styles.head}>
        <div>
          <span>기업 리서치 연결</span>
          <h2>{equityResearch ? userFacingRecommendationText(equityResearch.title) : `${symbol} 기업 리서치가 아직 연결되지 않았다`}</h2>
          <p>
            추천을 뉴스 신호만으로 보지 않기 위해 기업 분석 결과를 같이 보여준다. 이 리포트는 추천 점수와 주문을 직접 바꾸지 않고,
            재무·밸류에이션 점수 항목을 해석하는 읽기 전용 근거다.
          </p>
        </div>
        {equityResearch ? (
          <strong className={styles.badge}>
            {providerLabel(equityResearch.provider)} · {equityResearch.as_of_date}
          </strong>
        ) : null}
      </div>

      {equityResearch ? (
        <>
          <p className={styles.summary}>{userFacingRecommendationText(equityResearch.korean_summary)}</p>

          <div className={styles.metricGrid} aria-label="기업 리서치 구성">
            <div className={styles.metric}>
              <span>핵심 변화</span>
              <strong>{equityResearch.key_points.length}</strong>
              <small>사업·재무 포인트</small>
            </div>
            <div className={styles.metric}>
              <span>촉매</span>
              <strong>{equityResearch.catalysts.length}</strong>
              <small>좋아질 조건</small>
            </div>
            <div className={styles.metric}>
              <span>리스크</span>
              <strong>{equityResearch.risks.length}</strong>
              <small>틀릴 수 있는 이유</small>
            </div>
            <div className={styles.metric}>
              <span>무효화 조건</span>
              <strong>{equityResearch.invalidation_conditions.length}</strong>
              <small>투자 논리 재판단 기준</small>
            </div>
          </div>

          <div className={styles.researchGrid}>
            <RecommendationResearchList emptyText="핵심 변화가 아직 구조화되지 않았다." items={equityResearch.key_points} title="핵심 포인트" />
            <RecommendationResearchList emptyText="상승 촉매가 아직 구조화되지 않았다." items={equityResearch.catalysts} title="촉매" />
            <RecommendationResearchList emptyText="리스크가 아직 구조화되지 않았다." items={equityResearch.risks} title="리스크" />
            <RecommendationResearchList
              emptyText="투자 논리 무효화 조건이 아직 구조화되지 않았다."
              items={equityResearch.invalidation_conditions}
              title="무효화 조건"
            />
          </div>

          {valuationItems.length > 0 ? (
            <div className={styles.valuationGrid}>
              {valuationItems.map((item) => (
                <div key={item.key}>
                  <span>{userFacingRecommendationText(item.key)}</span>
                  <strong>{userFacingRecommendationText(item.value)}</strong>
                </div>
              ))}
            </div>
          ) : null}

          <div className={styles.actions}>
            <Link className="btn btn-primary" href={stockHref(symbol)}>
              종목 리서치 전체 보기
            </Link>
            {equityResearch.source_document_ids.slice(0, 3).map((documentId, index) => (
              <Link className="btn btn-secondary" href={sourceDocumentHref(documentId)} key={documentId}>
                원천 문서 {index + 1}
              </Link>
            ))}
          </div>
        </>
      ) : (
        <div className={styles.empty}>
          아직 이 종목의 기업 리서치 결과가 없다. 기업 리서치 배치가 실행되면 사업 설명, 재무 변화, 촉매, 리스크, 무효화 조건이 이곳에
          연결된다.
        </div>
      )}
    </section>
  );
}
