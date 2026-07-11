import type { Route } from "next";
import Link from "next/link";

import { koCode } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";

import styles from "./RecommendationCompatibilityReport.module.css";

type RecommendationCompatibilityReportProps = {
  readonly data: RecommendationDetailData;
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

export function RecommendationCompatibilityReport({ data }: RecommendationCompatibilityReportProps) {
  const measuredOutcome = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);

  return (
    <div className="pageStack">
      <section
        className={`decision-brief workspace-brief reveal ${styles.compatibilityBrief}`}
        aria-labelledby="recommendation-detail-title"
      >
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">
            추천 리포트 · 요약형 기록 · {koCode(data.horizon_type)} · {data.as_of_date}
          </span>
          <h1 className="decision-brief-title" id="recommendation-detail-title">
            {data.symbol} 추천 판단서
          </h1>
          <p className="decision-brief-copy">
            이 기록은 최신 전문 분석 항목이 붙기 전 생성된 추천이다. 점수와 성과는 참고할 수 있지만,
            재무, ETF 구성, 브로커 현실과 전문 감사가 필요한 판단은 최신 추천 리포트에서 다룬다.
          </p>
          <div className="decision-brief-meta" aria-label="추천 기본 상태">
            <span>추천 {koCode(data.recommendation)}</span>
            <span>점수 {formatPercent(data.score)}</span>
            <span>성과 {measuredOutcome ? koCode(data.outcome.label) : "미측정"}</span>
            <span>실거래 주문 차단</span>
          </div>
        </div>
        <div className="decision-brief-grid workspace-command-grid" aria-label="추천 기본 정보">
          <Link className="decision-card primary is-watch" href="/recommendations">
            <span>현재 상태</span>
            <strong>요약형 추천 기록</strong>
            <small>전문 판단서 입력이 없어 추천 점수와 성과만 제한적으로 제공된다.</small>
            <b>추천 목록</b>
          </Link>
          <Link className="decision-card" href={`/stocks/${data.symbol}` as Route}>
            <span>종목 분석</span>
            <strong>{data.symbol}</strong>
            <small>가격, 뉴스, 사이클, 보유 여부는 종목 리서치 화면으로 이어진다.</small>
            <b>종목 리서치</b>
          </Link>
          <Link className="decision-card is-watch" href="/paper-trading">
            <span>실행 상태</span>
            <strong>주문 제출 없음</strong>
            <small>이 요약형 기록만으로 가상 검증이나 실거래 후보를 만들지 않는다.</small>
            <b>가상 매매</b>
          </Link>
        </div>
      </section>
    </div>
  );
}
