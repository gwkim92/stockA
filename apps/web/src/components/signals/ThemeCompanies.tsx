'use client';
import { filterCompanies, ratioText, recordHref, type ThemeCompany } from '@/lib/news-theme-model';
import { SignalLink } from './SignalShared';
import { useSignalSearch } from './SignalControls';
import styles from './SignalWorkspace.module.css';

export function ThemeCompanies({ companies }: { companies: ThemeCompany[] | null }) {
  const { params, update } = useSignalSearch();
  const q = (params.get('company') ?? '').slice(0, 100), missingOnly = params.get('companyScope') === 'missing';
  if (companies === null) return <p className={styles.empty}>연결 기업 자료 미제공</p>;
  const filtered = filterCompanies(companies, q, missingOnly);
  return <div data-testid="theme-companies">
    <div className={styles.companyControls}>
      <label className={styles.search}>연결 종목 검색<input aria-label="연결 종목 검색" value={q} maxLength={100} placeholder="종목 코드" onChange={e => update({ company: e.target.value })} /></label>
      <button type="button" aria-pressed={missingOnly} onClick={() => update({ companyScope: missingOnly ? '' : 'missing' }, true)}>투자 논리 미연결</button>
      <button type="button" onClick={() => update({ company: '', companyScope: '' })}>종목 조건 초기화</button>
    </div>
    <p className={styles.note} role="status">수신 {companies.length}개 중 {filtered.length}개 표시 · 원래 연결 순서 유지</p>
    {filtered.map((company, index) => <article className={styles.companyRow} key={`${company.id}-${index}`}>
      <div><h3>{company.symbol ?? '종목 코드 미확인'}</h3><p>테마 연결 강도 {ratioText(company.strength)}</p></div>
      <div className={styles.actions}>
        <SignalLink href={recordHref('stocks', company.symbol)}>기업 분석 →</SignalLink>
        <SignalLink href={recordHref('theses', company.thesis)}>투자 논리 →</SignalLink>
        <SignalLink href={recordHref('recommendations', company.recommendation)}>추천 판단서 →</SignalLink>
        {!company.thesis && <span className={styles.note}>투자 논리 연결 미제공</span>}
      </div>
    </article>)}
    {!filtered.length && <p className={styles.empty}>{companies.length ? '조건에 맞는 연결 종목이 없습니다.' : '수신된 연결 종목 목록이 비어 있습니다.'}</p>}
  </div>;
}
