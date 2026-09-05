import { loadNews } from '@/lib/news-theme-data';
import type { SearchInput } from '@/lib/news-theme-model';
import { NewsInbox } from '@/components/signals/NewsInbox';
import { NewsRequestForm } from '@/components/signals/SignalControls';
import { SignalError, SignalLink } from '@/components/signals/SignalShared';
import styles from '@/components/signals/SignalWorkspace.module.css';
export const dynamic = 'force-dynamic';
export const metadata = { title: '뉴스 선별' };
export default async function EventsPage({ searchParams }: { searchParams: Promise<SearchInput> }) {
  const result = await loadNews(await searchParams);
  const query = result.query ?? { date: result.today, symbol: '', theme: '', cursor: '' };
  return <div className={styles.page} data-testid="news-workspace">
    <header className={styles.header}><div><span className={styles.eyebrow}>NEWS INBOX</span><h1>뉴스 선별</h1><p>확인할 뉴스와 공시를 좁히고, 다음 투자 검토로 이어가세요.</p></div></header>
    <NewsRequestForm query={query} today={result.today} />
    {result.data && result.query ? <><p className={styles.context}>요청 기준일 {result.requestedDate} · API 반환 기준 {result.data.asOf ?? '미확인'}</p><NewsInbox data={result.data} query={result.query} /></> : <SignalError issue={result.issue} home="/events" />}
    <p className={styles.note}>기준일까지의 기록이며 모두 당일 뉴스라는 뜻은 아닙니다. 기본 조회 날짜는 API 기준인 UTC를 사용합니다.</p>
    <footer className={styles.footer}><SignalLink href="/cycles">테마 사이클 →</SignalLink><SignalLink href="/events/classification">기존 분류 상세</SignalLink><SignalLink href="/ai-evidence">전체 분석 근거</SignalLink><SignalLink href="/ai-evidence/blocked">보류된 근거</SignalLink></footer>
  </div>;
}
