import Link from "next/link";
import type { Route } from "next";
import { koCode, koReason } from "@/lib/korean-labels";
import { count, list, number, percent, record, recordedReview, weight, words, type ReviewReport } from "@/lib/review-workspace-model";
import styles from "./ReviewWorkspace.module.css";
const countLabel = (v: unknown) => count(v) === null ? "미확인" : `${count(v)}개`;
export function RecordedPortfolioReview({ report }: { report: ReviewReport }) {
  const { history, decisions, feedback, feedbackLinked, items } = recordedReview(report);
  const risk = record(report.raw.risk_budget);
  return <div className={styles.supportGrid}>
    <section className={styles.panel} aria-label="저장된 검토 판단">
      <div className={styles.panelHeading}><span>기록된 판단</span><h2>최근 검토와 다음 확인 사항</h2><p>저장된 최신 검토 기록입니다. 이전·현재 판단을 비교해 새로 만든 변경 요약은 아닙니다.</p></div>
      {decisions === null ? <p className={styles.note}>연결 가능한 검토 기록이 없습니다. 판단을 임의로 만들지 않습니다.</p>
        : <><p className={styles.note}>검토 기준 {words(history.as_of_date)} · 기록 {words(history.eval_run_id)}</p>{decisions.slice(0, 6).map((row, i) => <article className={styles.evidenceItem} key={i}><h3>{words(row.symbol)} · {words(row.decision_label, koCode(words(row.decision_type)))}</h3><p>{words(row.rationale, "검토 사유 미제공")}</p><p>다음 확인: {koReason(words(row.next_review_action, "미지정"))}</p><div className={styles.links}>{words(row.related_thesis_id, "") && <Link href={`/theses/${encodeURIComponent(words(row.related_thesis_id))}` as Route}>연결 투자 논리 →</Link>}{words(row.related_recommendation_id, "") && <Link href={`/recommendations/${encodeURIComponent(words(row.related_recommendation_id))}` as Route}>당시 추천 →</Link>}</div></article>)}{decisions.length === 0 && <p className={styles.note}>이 검토 기록의 판단 목록이 비어 있습니다.</p>}{decisions.length > 6 && <p className={styles.note}>전체 {decisions.length}개 중 앞 6개 · 나머지는 위험예산·분석 상세에서 확인</p>}</>}
    </section>
    <section className={styles.panel} aria-label="위험과 사후 평가">
      <div className={styles.panelHeading}><span>후속 점검</span><h2>위험과 사후 평가</h2></div>
      <dl className={styles.factList}><div><dt>위험예산 원천 판정</dt><dd>{koCode(words(risk.status))}</dd></div><div><dt>단일 종목 한도 초과</dt><dd>{countLabel(risk.over_single_position_limit_count)}</dd></div><div><dt>집중도 한도 초과</dt><dd>{countLabel(record(risk.concentration).over_limit_count)}</dd></div></dl>
      {feedbackLinked && items !== null ? <div className={styles.evidenceItem}><h3>연결된 검토의 사후 평가</h3><p>{koCode(words(feedback.feedback_status))}</p><small>{words(feedback.as_of_date)} · 원본 검토 {words(feedback.source_history_eval_run_id)}</small><dl className={styles.factList}><div><dt>관찰 기간 대기</dt><dd>{countLabel(feedback.too_early_count)}</dd></div><div><dt>반대 결과 기록</dt><dd>{countLabel(feedback.contradicted_count)}</dd></div></dl></div>
        : <p className={styles.note}>동일한 검토 기록을 참조한 사후 평가가 확인되지 않았습니다. 다른 실행의 결과를 합쳐 보여주지 않습니다.</p>}
      <p className={styles.note}><Link href="/portfolio/coverage/details" prefetch={false}>위험예산·리밸런싱 후보·성과 대기 상세 →</Link></p>
    </section>
  </div>;
}
export function PerformanceEvidence({ report }: { report: ReviewReport }) {
  const quality = record(report.raw.quality_evaluation), checks = list(quality.checks), components = list(report.raw.attribution_components), exclusions = list(report.raw.coverage_exclusions), gates = list(report.raw.quality_gates);
  return <div className={styles.evidenceSections}>
    <section className={styles.panel} aria-label="성과 해석 범위">
      <div className={styles.panelHeading}><span>해석과 한계</span><h2>표본·원천 연결을 먼저 확인하세요</h2><p>표본 상태는 저장된 평가 결과를 표시합니다. 이 화면에서 평가 기준이나 추천 가중치를 바꾸지 않습니다.</p></div>
      <dl className={styles.factList}><div><dt>평가 상태</dt><dd>{koCode(words(quality.status))}</dd></div><div><dt>표본 판정</dt><dd>{koCode(words(quality.sample_size_status))}</dd></div><div><dt>보유 판단–성과 충돌</dt><dd>{countLabel(quality.review_outcome_mismatch_count)}</dd></div></dl>
      <details className={styles.disclosure}><summary>평가 항목·측정 방식 보기</summary><p>측정 방식: {words(report.raw.methodology)}</p>{checks?.map((row, i) => <article className={styles.evidenceItem} key={i}><h3>{words(row.label)} · {koCode(words(row.status))}</h3><p>{words(row.detail, "설명 미제공")}</p><p>{words(row.next_step, "다음 확인 항목 미제공")}</p></article>)}{checks === null && <p>평가 항목 자료 미제공</p>}{gates?.map((row, i) => <p key={i}>{koCode(words(row.gate))} · {koCode(words(row.status))} · {koReason(words(row.reason))}</p>)}</details>
    </section>
    <div className={styles.supportGrid}>
      <section className={styles.panel} aria-label="관점별 기여도"><div className={styles.panelHeading}><h2>관점별 기여도</h2><p>종목·테마는 같은 성과를 다른 관점에서 설명할 수 있습니다. 합산해 총수익률을 만들지 않습니다. 100bp = 1%p입니다.</p></div>
        {components?.map((row, i) => <article className={styles.evidenceItem} key={i}><div className={styles.between}><h3>{words(row.symbol, koCode(words(row.theme_key)))} · {koCode(words(row.component_type))}</h3><strong>{number(row.contribution_bps) === null ? "미측정" : `${number(row.contribution_bps)}bp`}</strong></div><p>{words(row.interpretation, "해석 미제공")}</p><small>비중 {weight(row.weight)} · 초과수익 {percent(row.alpha, true)}</small>{words(row.theme_key, "") && <div className={styles.links}><Link href={`/themes/${encodeURIComponent(words(row.theme_key))}` as Route}>테마 근거 →</Link></div>}</article>)}
        {!components?.length && <p className={styles.note}>{components === null ? "관점별 기여 자료 미제공" : "기록된 기여 항목이 없습니다."}</p>}
      </section>
      <section className={styles.panel} aria-label="측정 제외 항목"><div className={styles.panelHeading}><h2>측정에서 빠진 항목</h2><p>제외 비중과 이유를 함께 읽으세요. 측정되지 않은 결과는 성과가 0이라는 뜻이 아닙니다.</p></div>
        {exclusions?.map((row, i) => <article className={styles.evidenceItem} key={i}><h3>{words(row.symbol)} · 비중 {weight(row.weight)}</h3><p>{koReason(words(row.reason))}</p><p>다음 확인: {koReason(words(row.required_action))}</p></article>)}
        {!exclusions?.length && <p className={styles.note}>{exclusions === null ? "제외 항목 자료 미제공" : "제공된 제외 목록이 비어 있습니다."}</p>}
        <p className={styles.note}><Link href="/remediation">보완 작업 →</Link></p>
      </section>
    </div>
  </div>;
}
