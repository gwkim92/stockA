import { Suspense } from 'react';
import { koCode } from '@/lib/korean-labels';
import { currencyValue, route, shortDate } from '@/lib/research-reader-model';
import { count, decimal, measuredConfidence, object, percentage, rows, strings, text, type CompanyData } from '@/lib/company-evidence-model';
import { loadCompanyNeighborhood } from '@/lib/company-evidence-data';
import { ReaderFacts, ReaderLink, StoredList } from '@/components/readers/ReaderFrame';
import { CompanyPriceChart } from './CompanyPriceChart';
import styles from './CompanyWorkspace.module.css';

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return <section id={id} className={styles.panel} aria-labelledby={`${id}-title`}><h2 id={`${id}-title`}>{title}</h2>{children}</section>;
}
async function RelatedContext({ data }: { data: CompanyData }) {
  const result = await loadCompanyNeighborhood(data.symbol, data.id);
  if (!result.data) return <p className={styles.empty}>추가 시장 문맥을 불러오지 못했습니다. 기업·가격·직접 근거는 계속 확인할 수 있습니다.</p>;
  return <><p className={styles.caption}>문맥 기준일 {shortDate(result.data.asOf, '미기록')} · 이 연결만으로 투자 논리를 채택하지 않습니다.</p>
    <div className={styles.related}>{result.data.themes?.map((theme, i) => <article key={i}><h3>{text(theme.theme_name, text(theme.theme_key))}</h3><p>{koCode(text(theme.membership_type))} · 모델 신뢰도 {measuredConfidence(theme.confidence)}</p><ReaderLink href={route('themes', theme.theme_key)}>테마 근거 →</ReaderLink></article>)}</div>
    {!result.data.themes?.length && <p className={styles.empty}>{result.data.themes === null ? '테마 목록 미제공' : '반환된 테마 연결이 없습니다.'}</p>}
  </>;
}
export function CompanyWorkspace({ data }: { data: CompanyData }) {
  const recommendation = data.recommendation, research = data.research, fund = data.fund;
  const sourceKnown = typeof data.guard.blocked === 'boolean';
  const chapters = [['company-case', '투자 논리'], ['company-prices', '가격 기록'], ['company-analysis', data.fundKind ? '구성과 비용' : '재무·가치'], ['company-evidence', '뉴스 근거'], ['company-context', '시장 문맥']];
  return <div data-testid="company-workspace" className={styles.page}>
    <header className={styles.header}><div><span className={styles.eyebrow}>{data.fundKind ? 'FUND RESEARCH' : 'COMPANY RESEARCH'} · {data.market}</span><h1>{data.symbol} <span>{data.name}</span></h1><p>분석 기준 {data.asOf ?? '미확인'} · 저장된 분석과 근거를 함께 읽습니다.</p></div><ReaderLink href={`/stocks/${encodeURIComponent(data.symbol)}/details`}>전문 분석 전체 보기 →</ReaderLink></header>
    <nav className={styles.chapters} aria-label="기업 리서치 목차">{chapters.map(([id, label]) => <a key={id} href={`#${id}`}>{label}</a>)}</nav>
    <div className={styles.signal} data-blocked={data.blocked} role="status"><strong>{data.blocked ? '원천 제한 · 투자 근거 보완 필요' : sourceKnown ? '원천 판정과 투자 논리를 함께 확인하세요' : '전문 원천 판정 미확인'}</strong><p>{text(data.guard.summary, '자료가 연결되었다는 것만으로 검토 통과나 주문 가능 상태를 뜻하지 않습니다.')}</p>{text(data.guard.blocker_label, '') && <p>{text(data.guard.blocker_label)}</p>}</div>
    <dl className={styles.metrics}>
      <div><dt>기록된 종가</dt><dd>{currencyValue(data.price, data.currency)}<small>관측일 {data.priceDate ?? '미확인'}</small></dd></div>
      <div><dt>보고된 1일 변화</dt><dd>{percentage(data.daily)}<small>누락된 변화율을 보간하지 않음</small></dd></div>
      <div><dt>보유 기록</dt><dd>{data.positionState === 'held' ? '보유 연결' : data.positionState === 'none' ? '보유 수량 없음' : '미확인'}<small>{data.position ? `${text(data.position.portfolio_name)} · ${shortDate(data.position.snapshot_date, '기준일 미확인')}` : '반환된 기록 기준'}</small></dd></div>
      <div><dt>추천 기록</dt><dd>{data.recommendationState === 'linked' ? '판단서 연결' : data.recommendationState === 'none' ? '연결 없음' : '미확인'}<small>{recommendation ? `모델 점수 ${decimal(recommendation.score)} · 수익률 아님` : '없음과 미확인을 구분'}</small></dd></div>
    </dl>
    <div className={styles.workbench}><div className={styles.main}>
      <Section id="company-case" title={data.fundKind ? '어떤 노출을 위한 상품인가' : '왜 이 기업을 검토하는가'}>
        <p className={styles.lead}>{data.fundKind ? text(fund?.summary, '펀드 분석 요약 미제공') : text(research.korean_summary, '저장된 기업 리서치 요약이 없습니다. 추천 연결과 실제 분석 근거를 구분해서 확인하세요.')}</p>
        {!data.fundKind && <><p className={styles.caption}>리서치 기준 {shortDate(research.as_of_date, '미기록')}</p><StoredList items={strings(research.key_points)} missing="핵심 주장 목록 미제공" /><div className={styles.twoColumns}><div><h3>성립 조건·촉매</h3><StoredList items={strings(research.catalysts)} missing="촉매 미제공" /></div><div><h3>반대 근거·위험</h3><StoredList items={strings(research.risks)} missing="위험 미제공" /></div></div></>}
        <div className={styles.actions}><ReaderLink href={data.thesisHref}>투자 논리 열기</ReaderLink><ReaderLink href={route('recommendations', recommendation?.recommendation_id)}>추천 판단서 열기</ReaderLink></div>
      </Section>
      <Section id="company-prices" title="기록된 가격 흐름"><CompanyPriceChart points={data.points} currency={data.currency} excluded={data.excludedPrices} /></Section>
      <Section id="company-analysis" title={data.fundKind ? '보유 구성과 비용' : '재무와 추정 가치'}>
        {data.fundKind ? <>
          <ReaderFacts items={[["벤치마크", text(fund?.benchmark_code)], ["구성 기준일", shortDate(fund?.source_as_of_date, '미기록')], ["보고된 구성 수", count(fund?.holding_count) === null ? '미확인' : `${count(fund?.holding_count)}개`], ["비용률", percentage(object(fund?.expense_ratio).value)]]} />
          <p className={styles.caption}>비용률 원천 {text(object(fund?.expense_ratio).source_name)} · {shortDate(object(fund?.expense_ratio).source_as_of_date, '기준일 미기록')}</p>
          <div className={styles.related}>{rows(fund?.top_holdings)?.map((item, i) => <article key={i}><h3>{text(item.symbol)} · {text(item.name)}</h3><p>기록된 구성 비중 {measuredConfidence(item.target_weight)}</p><ReaderLink href={route('stocks', item.symbol)}>구성 기업 →</ReaderLink></article>)}</div>
          <p className={styles.caption}>펀드에 개별 기업의 목표 가치나 재무제표 판단을 적용하지 않습니다.</p>
        </> : <>
          <p className={styles.caption}>재무 기간 {shortDate(data.financial.latest_period_end, '미확인')} · 원천 판정 {koCode(text(data.financial.status))}</p>
          <div className={styles.financialMetrics}>{rows(data.financial.metrics)?.slice(0, 8).map((metric, i) => <article key={i}><span>{text(metric.label, text(metric.metric_code))}</span><strong>{metric.metric_unit === 'ratio' ? percentage(metric.metric_value) : decimal(metric.metric_value)}</strong><small>{shortDate(metric.period_end, '기간 미확인')} · {koCode(text(metric.metric_status))}</small></article>)}</div>
          {!rows(data.financial.metrics)?.length && <p className={styles.empty}>계산된 재무 지표 목록 미제공 또는 비어 있음</p>}
          <details className={styles.disclosure}><summary>저장된 가치평가 범위</summary><ReaderFacts items={[["가치평가 기준일", shortDate(data.valuation.valuation_as_of_date ?? data.valuation.as_of_date, '미기록')], ["하방", currencyValue(data.valuation.target_low, data.valuation.currency_code)], ["중앙", currencyValue(data.valuation.target_base, data.valuation.currency_code)], ["상방", currencyValue(data.valuation.target_high, data.valuation.currency_code)]]} /><p>가격과 추정 가치는 별개이며, 가정·방법별 상세는 전문 분석에 보존되어 있습니다.</p></details>
        </>}
        <ReaderLink href={`/stocks/${encodeURIComponent(data.symbol)}/details`}>전체 재무·가치평가·산업 분석 →</ReaderLink>
      </Section>
      <Section id="company-evidence" title="직접 뉴스와 시장 배경 근거">
        {[['기업 직접 연결', data.events], ['상위 시장·테마 영향', data.macro]].map(([label, items]) => <div key={label as string}><h3>{label as string}</h3>{(items as CompanyData['events'])?.map((event, i) => <article className={styles.news} key={i}><span>{shortDate(event.event_at, '관측일 미기록')} · {koCode(text(event.impact_direction))}</span><h4>{text(event.korean_title, text(event.title))}</h4>{text(event.korean_summary, '') && <p>{text(event.korean_summary)}</p>}<div className={styles.actions}><ReaderLink href={route('ai-evidence', event.ai_evidence_id ?? event.event_id)}>근거 해석 열기 →</ReaderLink><ReaderLink href={route('source-documents', event.source_document_id)}>원천 문서 열기 →</ReaderLink></div></article>)}{!(items as CompanyData['events'])?.length && <p className={styles.empty}>{items === null ? '근거 목록 미제공' : '반환된 근거가 없습니다.'}</p>}</div>)}
      </Section>
      <Section id="company-context" title="연결된 시장 문맥"><Suspense fallback={<p className={styles.empty}>추가 시장 문맥을 불러오는 중입니다.</p>}><RelatedContext data={data} /></Suspense></Section>
    </div><aside className={styles.side} aria-label="기업 검토 맥락">
      <section className={styles.panel}><h2>판단을 바꿀 조건</h2><StoredList items={data.fundKind ? strings(fund?.limitations) : strings(research.invalidation_conditions)} missing="무효화 조건·제한 사항 미제공" /><ReaderLink href={data.thesisHref}>투자 논리와 조건 →</ReaderLink></section>
      <section className={styles.panel}><h2>가격 원천</h2><ReaderFacts items={[["분석 원천", koCode(text(data.provider.provider))], ["원천 최신성 판정", koCode(text(data.provider.freshness_status))], ["분석 사용 기록", typeof data.provider.used_for_scoring === 'boolean' ? data.provider.used_for_scoring ? '분석 입력에 사용' : '미사용 기록' : '미확인'], ["브로커 자료 판정", koCode(text(data.broker.status))]]} /><p className={styles.caption}>원천 자료의 존재를 계좌 상태나 실거래 가능 여부로 해석하지 않습니다.</p></section>
    </aside></div>
  </div>;
}
