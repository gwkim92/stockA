'use client';
import { usePathname, useSearchParams } from 'next/navigation';
import { type NewsQuery } from '@/lib/news-theme-model';
import styles from './SignalWorkspace.module.css';

export function useSignalSearch() {
  const params = useSearchParams(), pathname = usePathname();
  const update = (values: Record<string, string>, push = false) => {
    const next = new URLSearchParams(window.location.search);
    for (const [key, value] of Object.entries(values)) {
      if (!value || value === 'all') next.delete(key); else next.set(key, value);
    }
    window.history[push ? 'pushState' : 'replaceState'](null, '', `${pathname}${next.size ? `?${next}` : ''}${window.location.hash}`);
  };
  return { params, update };
}
export function NewsRequestForm({ query, today }: { query: NewsQuery; today: string }) {
  const { params } = useSignalSearch();
  return <form method="get" action="/events" className={styles.requestForm} aria-label="뉴스 조회 범위" key={`${query.date}-${query.symbol}-${query.theme}`}>
    <label>기준일까지 조회<input type="date" name="date" defaultValue={query.date} max={today} required /></label>
    <button type="submit">조회 적용</button>
    <input type="hidden" name="q" value={(params.get('q') ?? '').slice(0, 100)} />
    <input type="hidden" name="scope" value={params.get('scope') ?? 'all'} />
    <details className={styles.serverFilters} open={!!query.symbol || !!query.theme}>
      <summary>종목·테마로 조회 범위 좁히기</summary>
      <div><label>조회 종목 코드<input name="symbol" aria-label="조회 종목 코드" defaultValue={query.symbol} placeholder="예: AAPL" maxLength={20} /></label>
        <label>조회 테마 코드<input name="theme" aria-label="조회 테마 코드" defaultValue={query.theme} placeholder="예: semiconductor" maxLength={240} /></label></div>
      <small>조회 적용 시 첫 페이지부터 다시 가져옵니다.</small>
    </details>
  </form>;
}
export function ThemeDateForm({ date, today }: { date: string; today: string }) {
  return <form method="get" className={styles.themeDate} aria-label="테마 조회 기준일"><label>조회 기준일<input type="date" name="date" defaultValue={date} max={today} required /></label><button type="submit">조회</button></form>;
}
