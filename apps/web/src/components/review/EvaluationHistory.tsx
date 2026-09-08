import Link from 'next/link';
import { displayValue, displayPercent, record, stateLabel, type EvaluationResult } from '@/lib/evaluation-history';
import styles from './EvaluationHistory.module.css';

const labels: Record<string, string> = { 'recommendation.action': '추천 판단', 'recommendation.total_score': '추천 점수', 'recommendation.status': '추천 상태', 'recommendation.recommended_weight': '제안 비중', 'recommendation.thesis_id': '연결된 투자 논리', 'thesis.title': '투자 논리 제목', 'thesis.summary': '투자 논리 요약', 'thesis.status': '투자 논리 상태', 'thesis.conviction_score': '확신도', 'thesis.invalidation_conditions': '무효화 조건' };
const action = (v: unknown) => ({ buy: '매수 검토', watch: '관찰', hold: '보유 검토', sell: '매도 검토', active: '활성', closed: '종료' }[String(v)] ?? displayValue(v));

export function EvaluationHistory({ result, detail = false }: { result: EvaluationResult; detail?: boolean }) {
  const h = result.history, run = h?.run;
  const base = detail && run ? `/performance/evaluations/${run.eval_run_id}` : '/performance/evaluations';
  return <div className={styles.page}>
    <span className={styles.eyebrow}>DECISION RECORD</span>
    <h1>{detail ? '평가 기록 비교' : '추천 평가 이력'}</h1>
    <p>{detail ? '평가 당시 저장한 판단과 지금의 자료를 나란히 확인합니다.' : '평가별로 저장된 추천 근거와 이후 확인된 성과를 살펴봅니다.'}</p>
    <nav className={styles.nav} aria-label="평가 이력 탐색"><Link href="/performance">판단 성과</Link><Link href="/performance/evaluations" aria-current={!detail ? 'page' : undefined}>평가 이력</Link></nav>
    {!h ? <section role="status"><h2>{result.issue === 'invalid' ? '조회 주소를 확인해 주세요' : result.issue === 'not_found' ? '요청한 평가 기록이 없습니다' : '평가 기록을 불러오지 못했습니다'}</h2><p>다른 평가나 빈 결과로 대신 표시하지 않습니다.</p><Link href="/performance/evaluations">평가 목록 다시 조회</Link></section> : <>
      <div className={styles.note}><p>이 기록은 추천 생성 당시가 아닌 <strong>평가 실행 당시</strong> 저장한 자료입니다. 현재 자료와의 비교는 기록을 수정하지 않습니다.</p></div>
      {!detail ? <>
        <h2>저장된 평가</h2>
        {h.runs?.length ? <ol className={styles.runs}>{h.runs.map(r => <li className={styles.run} key={r.eval_run_id}><div><Link href={`/performance/evaluations/${r.eval_run_id}`} prefetch={false}>{displayValue(r.as_of_date)} 평가</Link><small>평가 #{r.eval_run_id} · 관찰 기간 {displayValue(r.horizon_days)}일 · 기록 {r.snapshot_count}개</small><small>실행 시각 {displayValue(r.created_at)}</small></div><span className={styles.state}>{stateLabel(r.snapshot_state)}</span></li>)}</ol> : <p role="status">저장된 평가가 아직 없습니다.</p>}
      </> : run && <>
        <h2>{displayValue(run.as_of_date)} 기준 · 평가 #{run.eval_run_id}</h2>
        <p>실행 시각 {displayValue(run.created_at)} · {stateLabel(run.snapshot_state)}</p>
        <p>현재 자료 조회 시각 {displayValue(result.comparedAt)}</p>
        {run.snapshot_state === 'count_mismatch' && <p role="status" className={styles.risk}>전체 기록 수가 맞지 않습니다. 표시된 일부 기록만으로 평가 전체를 판단하지 마세요.</p>}
        {!h.snapshots?.length && <p role="status">{run.snapshot_state === 'legacy_unavailable' ? '이 과거 평가에는 상세 추천 기록이 저장되지 않았습니다.' : run.snapshot_state === 'recorded_empty' ? '평가 시점에 기록할 추천 대상이 없었습니다.' : '이 페이지에 표시할 추천 기록이 없습니다.'}</p>}
        {h.snapshots?.map((s, index) => {
          const comparison = result.comparisons[index], raw = s.snapshot_json, thesis = record(raw.thesis), oldOutcome = record(raw.selected_outcome), later = comparison?.later_outcome;
          const verified = comparison?.integrity === 'verified';
          return <article className={styles.snapshot} key={s.snapshot_id}>
            <header><h2>{s.primary_symbol}</h2><span className={verified ? styles.state : styles.risk}>{stateLabel(comparison?.integrity ?? 'unverifiable')}</span></header>
            <dl className={styles.facts}><div><dt>기록된 판단</dt><dd>{action(s.recommendation_action)}</dd></div><div><dt>기록된 점수</dt><dd>{displayValue(s.recommendation_total_score)}</dd></div><div><dt>현재와 비교</dt><dd>{stateLabel(comparison?.status ?? 'unavailable')}</dd></div></dl>
            {!verified && <p className={styles.risk}>저장 내용이 일치하는지 확인되지 않아 현재 자료와의 비교를 보류했습니다.</p>}
            <div className={styles.comparison}>
              <section><h3>평가 당시 근거</h3><p>{displayValue(thesis.summary)}</p><p>무효화 조건: {displayValue(thesis.invalidation_conditions)}</p><p>당시 초과수익 {displayPercent(oldOutcome.alpha_pct)} · 관찰 기간 {displayValue(oldOutcome.horizon_days)}일</p><p>측정 종료일 {displayValue(oldOutcome.measurement_end_date)}</p></section>
              <section><h3>현재 달라진 내용</h3>
                {comparison?.changes.length ? <ul className={styles.changes}>{comparison.changes.map(c => <li key={c.field}><strong>{labels[c.field] ?? c.field}</strong><p>기록: {action(c.recorded)}</p><p>현재: {action(c.current)}</p></li>)}</ul> : <p>{comparison?.status === 'unchanged' ? '비교한 추천·투자 논리 항목이 같습니다.' : stateLabel(comparison?.status ?? 'unavailable')}</p>}
                <h3>기준일 이후 측정 성과</h3>
                {later ? <><p>초과수익 <strong>{displayPercent(later.alpha_pct)}</strong> · {displayValue(later.benchmark_code)} 대비</p><p>{displayValue(later.measurement_start_date)} ~ {displayValue(later.measurement_end_date)} · {displayValue(later.horizon_days)}일</p></> : <p>{['changed', 'unchanged'].includes(comparison?.status ?? '') ? '동일한 관찰 기간의 후속 측정 결과가 없습니다.' : '현재 자료를 대조할 수 없어 후속 성과도 확인하지 못했습니다.'}</p>}
                <p>평가 기준일 이후 종료된 동일 기간의 최신 측정값입니다. 두 시점 사이에 새로 발생한 수익률을 뜻하지 않습니다.</p>
              </section>
            </div>
            <details><summary>기록 범위와 원문 확인</summary><p>추천 점수·판단·상태·제안 비중·연결된 투자 논리와 그 제목·요약·상태·확신도·무효화 조건을 비교합니다. 저장 내용 검증은 이 페이지에서 받은 기록에만 적용됩니다.</p><Link href={`/recommendations/recommendation-${s.source_recommendation_id}`} prefetch={false}>현재 추천 상세 보기</Link></details>
          </article>;
        })}
      </>}
      <nav className={styles.pager} aria-label="평가 기록 페이지"><Link href={{ pathname: base }} prefetch={false}>처음 페이지</Link>{h.pagination.has_more && <Link href={{ pathname: base, query: { [detail ? 'after' : 'before']: h.pagination.next_cursor } }} prefetch={false}>{detail ? '다음 추천 기록' : '이전 평가 더 보기'}</Link>}</nav>
    </>}
  </div>;
}
