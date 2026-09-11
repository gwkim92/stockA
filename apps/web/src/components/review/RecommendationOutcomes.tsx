import Link from 'next/link';
import type { Route } from 'next';
import { koCode } from '@/lib/korean-labels';
import { evaluationHref, FILTER_KEYS, OUTCOMES_PATH, outcomeHref, percent, type OutcomeResult } from '@/lib/recommendation-outcomes';
import styles from './RecommendationOutcomes.module.css';
export function RecommendationOutcomes({result}:{result:OutcomeResult}) {
 const {report,query}=result;
 const first=Object.fromEntries(FILTER_KEYS.map(k=>[k,query[k]]));
 const rows=report?.rows??[];
 const filtered=FILTER_KEYS.some(key=>Boolean(query[key]));
 const scopeLabel=[query.symbol||'전체 종목',query.horizon?(query.horizon==='other'?'그 외 기간':query.horizon+'일 구간'):'모든 관찰 기간',query.benchmark==='_missing'?'벤치마크 미기록':query.benchmark].filter(Boolean).join(' · ');
 return <div className={styles.page} data-testid="recommendation-outcomes">
  <header className={styles.header}><span>DECISION OUTCOMES</span><h1>전체 추천 성과</h1><p>추천을 기록한 뒤 가격은 어떻게 움직였는지, 같은 기간의 벤치마크와 대조합니다.</p></header>
  <nav className={styles.tabs} aria-label="성과 조회 종류"><Link href={OUTCOMES_PATH} aria-current="page">전체 추천 성과</Link><Link href="/performance" prefetch={false}>보유 성과귀속</Link><Link href="/performance/evaluations" prefetch={false}>평가 이력</Link></nav>
  <details className={styles.filterPanel} open={filtered}><summary><strong>조회 조건</strong><span>{scopeLabel}</span><small>종목·추천일·기간·벤치마크 선택</small></summary>
  <form className={styles.filters} action={OUTCOMES_PATH} method="get" aria-label="추천 성과 조회 조건">
   <label>종목 코드<input name="symbol" aria-label="종목 코드" defaultValue={query.symbol} placeholder="예: AAPL" maxLength={20} autoCapitalize="characters" /></label>
   <label>추천일 시작<input type="date" name="from_date" defaultValue={query.from_date}/></label>
   <label>추천일 종료<input type="date" name="to_date" defaultValue={query.to_date}/></label>
   <label>관찰 구간<select aria-label="관찰 구간" name="horizon" defaultValue={query.horizon}><option value="">모든 관찰 기간</option><option value="30">30일 구간</option><option value="90">90일 구간</option><option value="180">180일 구간</option><option value="365">365일 구간</option><option value="other">그 외 관찰 기간</option></select></label>
   <label>벤치마크<select aria-label="벤치마크" name="benchmark" defaultValue={query.benchmark}><option value="">모든 벤치마크</option>{[...new Set([...(report?.benchmarks.filter((v):v is string=>v!==null)??[]),...(query.benchmark&&query.benchmark!=='_missing'?[query.benchmark]:[])])].map(code=><option key={code} value={code}>{code}</option>)}<option value="_missing">벤치마크 미기록</option></select></label>
   <label>초과수익<select aria-label="초과수익" name="alpha" defaultValue={query.alpha}><option value="">모든 결과</option><option value="positive">벤치마크 상회 (&gt; 0)</option><option value="negative">벤치마크 하회 (&lt; 0)</option><option value="zero">동일 (0)</option><option value="missing">초과수익 미측정</option></select></label>
   <div className={styles.formActions}><button type="submit">결과 조회</button><a href={OUTCOMES_PATH}>조건 초기화</a></div>
  </form></details>
  {!report ? <section className={styles.empty} role="status"><h2>{result.issue==='invalid'?'조회 조건을 확인해 주세요':'성과 자료를 불러오지 못했습니다'}</h2><p>{result.issue==='invalid'?'종목 코드, 날짜 순서와 조회 주소를 확인하세요.':'응답 실패를 성과 0건이나 수익률 0으로 표시하지 않습니다.'}</p><a href={outcomeHref(first)}>다시 조회</a></section> : <>
   <section className={styles.summary} aria-label="조회 범위 요약">
    <div><span>저장된 측정</span><strong>{report.summary.measurement_count.toLocaleString('ko-KR')}<small>건</small></strong></div>
    <div><span>추천 기록</span><strong>{report.summary.recommendation_count.toLocaleString('ko-KR')}<small>개</small></strong></div>
    <div><span>종목</span><strong>{report.summary.symbol_count.toLocaleString('ko-KR')}<small>개</small></strong></div>
    <div><span>초과수익 미측정</span><strong>{report.summary.missing_alpha_count.toLocaleString('ko-KR')}<small>건</small></strong></div>
   </section>
   <div className={styles.scope}><p>조회 조건 전체의 집계 · 추천일 {report.summary.first_recommendation_date??'해당 없음'}{report.summary.last_recommendation_date&&` ~ ${report.summary.last_recommendation_date}`}</p><p>한 추천에 여러 관찰 기간의 측정이 있을 수 있습니다. 기간·벤치마크가 다른 수익률은 합산하지 않습니다.</p></div>
   <details className={styles.guide}><summary>기간과 기록을 읽는 기준</summary><p>30·90·180·365일 구간은 기존 평가 기준의 ±7일 범위를 따릅니다. 각 행에는 실제 관찰일과 측정 시작·종료일을 그대로 표시합니다. 당일 측정과 이 범위 밖의 기록은 ‘그 외 관찰 기간’에 포함됩니다.</p><p>추천 점수와 연결 투자 논리는 현재 저장된 기록입니다. ‘평가 보존본’은 해당 성과를 사용한 평가 실행 시점의 기록이며, 추천 생성 당시의 불변 사본을 뜻하지 않습니다. 성과 목록은 실계좌 수익률이나 거래 실행 결과가 아닙니다.</p></details>
   <section className={styles.results} aria-labelledby="measurements-heading"><header className={styles.resultsHeading}><h2 id="measurements-heading">추천별 측정 결과</h2><span>측정 종료일 최신순 · 이번 페이지 {rows.length}건</span></header>
    <ol className={styles.list}>{rows.map(row=><li key={row.outcome_id}>
     <article className={styles.row} aria-label={`${row.symbol} ${row.recommendation_date} 추천 ${row.horizon_days}일 성과`}>
      <div className={styles.identity}><Link href={`/stocks/${encodeURIComponent(row.symbol)}` as Route} className={styles.symbol}>{row.symbol}</Link><span>{koCode(row.recommendation_action)} · 저장 점수 {row.recommendation_score.toLocaleString('ko-KR',{maximumFractionDigits:4})}</span><small>추천일 {row.recommendation_date}</small><small>#{row.recommendation_id} · {koCode(row.strategy_name)}</small></div>
      <div className={styles.period}><strong>{row.nominal_horizon===null?'그 외 관찰 기간':`${row.nominal_horizon}일 구간`}</strong><span>실제 {row.horizon_days}일 관찰</span><small>{row.measurement_start_date} → {row.measurement_end_date}</small></div>
      <dl className={styles.returns}><div><dt>절대수익률</dt><dd>{percent(row.absolute_return_pct)}</dd></div><div><dt>{row.benchmark_code??'벤치마크 미기록'}</dt><dd>{percent(row.benchmark_return_pct)}</dd></div><div data-tone={row.alpha_pct===null?'unknown':row.alpha_pct>0?'positive':row.alpha_pct<0?'negative':'neutral'}><dt>초과수익</dt><dd>{percent(row.alpha_pct,true)}</dd></div></dl>
      <div className={styles.rowFooter}><nav aria-label={`${row.symbol} 추천 ${row.recommendation_id} 대조`}><Link href={`/recommendations/recommendation-${row.recommendation_id}` as Route} prefetch={false}>추천 기록 →</Link>{row.thesis_id&&<Link href={`/theses/thesis-${row.thesis_id}` as Route} prefetch={false}>연결 투자 논리 →</Link>}{row.evaluation_snapshot?<Link href={evaluationHref(row.evaluation_snapshot) as Route} prefetch={false}>평가 보존본 · {row.evaluation_snapshot.as_of_date??'기준일 미기록'} →</Link>:<span>이 측정의 평가 보존본 없음</span>}</nav>
       <details><summary>측정 근거</summary><dl className={styles.evidence}><div><dt>기준 가격</dt><dd>{row.entry_price.toLocaleString('ko-KR',{maximumFractionDigits:6})} → {row.exit_price.toLocaleString('ko-KR',{maximumFractionDigits:6})} {row.currency_code}</dd></div><div><dt>관측 최대 낙폭</dt><dd>{percent(row.max_drawdown_pct)}</dd></div><div><dt>저장된 결과 분류</dt><dd>{koCode(row.outcome_label)}</dd></div><div><dt>측정 기록</dt><dd>#{row.outcome_id} · 실행 {row.source_run_id??'미기록'}</dd></div></dl></details>
      </div>
     </article>
    </li>)}</ol>
    {!rows.length&&<div className={styles.empty} role="status"><h3>{query.before?'이후 페이지에 표시할 결과가 없습니다':'조건에 맞는 저장 성과가 없습니다'}</h3><p>이 결과만으로 수익률 0이나 측정 실패라고 판단하지 않습니다. 관찰 기간의 만기와 자료 수집 상태를 확인하세요.</p><Link href="/data-health" prefetch={false}>성과 측정 상태 확인 →</Link></div>}
   </section>
   <nav className={styles.pager} aria-label="추천 성과 페이지"><a href={outcomeHref(first)}>{query.before?'처음 페이지 · 최신 기록':'최신 기록 다시 조회'}</a>{report.pagination.next_cursor&&<Link href={outcomeHref({...query,before:report.pagination.next_cursor,through:report.pagination.through}) as Route} prefetch={false}>이전 측정 더 보기 →</Link>}</nav>
   <p className={styles.footnote}>다음 페이지는 같은 저장 범위를 유지합니다. 새로 수집된 기록은 ‘최신 기록’에서 확인할 수 있습니다.</p>
  </>}
 </div>;
}
