import Link from "next/link";
import type { Route } from "next";
import { koCode } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";
import { buildRecommendationMemo, NO_LINKED_THESIS, type MemoThesisResult } from "@/lib/recommendation-memo-model";
import styles from "./recommendation-executive-brief.module.css";

function Points({ values, empty }: { values: readonly string[]; empty: string }) {
  return values.length ? <ul>{values.map((value, i) => <li key={`${i}-${value}`}>{value}</li>)}</ul> : <p className={styles.missing}>{empty}</p>;
}

export function RecommendationExecutiveBrief({ data, thesis = NO_LINKED_THESIS }: {
  data: RecommendationDetailData;
  thesis?: MemoThesisResult;
}) {
  const memo = buildRecommendationMemo(data, thesis);
  return (
    <section className={styles.brief} id="recommendation-investment-memo" aria-labelledby="recommendation-executive-brief-title" data-testid="investment-memo">
      <header className={styles.header}>
        <span>{memo.isFund ? "ETF·펀드 투자 판단" : "기업 투자 판단"} · 분석 기준 {memo.analysisDate ?? "미확인"}</span>
        <h2 id="recommendation-executive-brief-title">투자 논리와 판단 조건</h2>
        <p>요약과 원천을 함께 읽고, 어떤 조건에서 판단을 바꿀지 확인하세요. 실거래 주문과 자동 비중 변경은 실행하지 않습니다.</p>
      </header>
      <nav className={styles.readingNav} aria-label="투자 판단서 목차">
        {[["memo-claim","투자 논리"],["memo-catalysts","촉매"],["memo-risks","위험"],["memo-conditions","무효화"],["memo-review","다음 검토"],["memo-value",memo.isFund ? "상품 구조" : "가치평가"],["memo-sources","원문"]].map(([id,label]) => <a key={id} href={`#${id}`}>{label}</a>)}
      </nav>
      <div className={styles.overview}>
        <div><span>보유 상태</span><strong>{memo.positionLabel}</strong><p>{memo.positionSummary}</p></div>
        <div data-tone={memo.evidence.tone}><span>근거 연결 상태</span><strong>{memo.evidence.label}</strong><p>{memo.evidence.detail}</p></div>
      </div>
      <p className={styles.notice} role="status">{memo.notice}</p>
      <article className={styles.claim} id="memo-claim">
        <h3>왜 투자 후보인가</h3><small>{memo.claimSource}</small>
        <p>{memo.summary}</p>
        <Points values={memo.claims} empty="뒷받침하는 핵심 주장이 기록되지 않았습니다." />
      </article>
      <div className={styles.grid}>
        <article id="memo-catalysts"><h3>어떤 변화가 촉매인가</h3><small>{memo.catalystSource}</small><Points values={memo.catalysts} empty="확인할 촉매가 기록되지 않았습니다." /></article>
        <article id="memo-risks"><h3>반대 근거와 주요 위험</h3><small>{memo.riskSource}</small><Points values={memo.risks} empty="반대 근거와 위험이 기록되지 않았습니다. 위험이 없다는 뜻은 아닙니다." /></article>
        <article id="memo-conditions"><h3>언제 판단을 철회하나</h3><small>{memo.conditionSource}</small>
          {memo.conditions.length ? <ul>{memo.conditions.map((item, i) => <li key={i}>{item.condition}<small className={styles.conditionStatus}>기록 상태: {koCode(item.status)}</small></li>)}</ul>
            : <p className={styles.missing}>무효화 조건이 기록되지 않았습니다.</p>}
        </article>
        <article id="memo-review"><h3>다음 검토에서 무엇을 확인하나</h3>
          <dl><div><dt>최근 검토</dt><dd>{memo.reviewedAt ?? "미기록"}</dd></div><div><dt>기록된 다음 검토일</dt><dd>{memo.nextReview ?? "미지정"}</dd></div></dl>
          <p>{memo.reviewSummary}</p><small>저장된 검토 일정이며, 이 화면에서 새 실행 일정을 만들지 않습니다.</small>
          {memo.thesisHref && <Link href={memo.thesisHref as Route}>전체 투자 논리와 검토 이력</Link>}
        </article>
      </div>
      {memo.isFund ? <article className={styles.valuation} id="memo-value">
        <h3>ETF 구성과 비용을 어떻게 볼 것인가</h3>
        <small>보유 구성 기준 {memo.fund.date ?? "미확인"} · 비용 기준 {memo.fund.expenseDate ?? "미확인"}</small>
        <dl><div><dt>보유 구성</dt><dd>{memo.fund.count === null ? "미확인" : `${memo.fund.count}개`}</dd></div>
          <div><dt>구성 커버리지</dt><dd>{memo.fund.coverage}</dd></div><div><dt>비용률</dt><dd>{memo.fund.expense}</dd></div><div><dt>벤치마크</dt><dd>{memo.fund.benchmark}</dd></div></dl>
        <p>ETF에는 개별 기업의 목표 가치를 대신 적용하지 않습니다. NAV 괴리와 추적 품질은 원천 자료에서 함께 확인하세요.</p>
        <Link href="#recommendation-fund-analysis">ETF 구성·비용·추적 근거</Link>
      </article> : <article className={styles.valuation} id="memo-value">
        <h3>가격과 추정 가치는 어떻게 다른가</h3>
        <small>가치평가 기준 {memo.valuation.date ?? "미확인"} · 기준 주가는 추정 가치가 아닙니다.</small>
        <dl><div><dt>분석 기준 주가</dt><dd>{memo.valuation.referencePrice}</dd></div><div><dt>모형 추정 가치</dt><dd>{memo.valuation.target}</dd></div>
          <div><dt>추정 범위 하단</dt><dd>{memo.valuation.low}</dd></div><div><dt>추정 범위 상단</dt><dd>{memo.valuation.high}</dd></div></dl>
        <details><summary>모형별 핵심 가정</summary>{memo.valuation.methods.length ? memo.valuation.methods.map((method, i) => <div key={i} className={styles.method}>
          <strong>{method.name}</strong><small>기준 {method.date ?? "미확인"}</small>
          {method.assumptions.length ? <ul>{method.assumptions.map((item, j) => <li key={j}>{item.label}: {item.value}{item.interpretation ? ` · ${item.interpretation}` : ""}</li>)}</ul> : <p>가정이 기록되지 않았습니다.</p>}
        </div>) : <p>연결된 가치평가 모형이 없습니다.</p>}</details>
        <Link href="#recommendation-valuation">가치평가 전체 근거</Link>
      </article>}
      <footer className={styles.sources} id="memo-sources">
        <h3>원문과 상세 근거</h3>
        <small>{memo.isFund ? "상품 원천은 ETF 상세 근거에서 확인하세요." : `기업 리서치 기준 ${memo.researchDate ?? "미확인"}. 아래는 리서치에 연결된 원문 목록이며, 모든 주장에 대한 개별 검증을 뜻하지 않습니다.`}</small>
        <div>{memo.sources.map((source, i) => <Link key={source.id} href={source.href as Route}>연결 원문 {i + 1}</Link>)}
          <Link href={`/stocks/${encodeURIComponent(data.symbol)}` as Route}>종목 리서치</Link>
          <Link href="#recommendation-evidence-review">뉴스·점수 출처 대조</Link>
        </div>
        {!memo.isFund && memo.sources.length === 0 && <p className={styles.missing}>연결된 기업 리서치 원문이 없습니다.</p>}
      </footer>
    </section>
  );
}
