'use client';
import { filterNews, newsHref, NEWS_SCOPES, type NewsPage, type NewsQuery } from '@/lib/news-theme-model';
import { NewsRecord, SignalLink } from './SignalShared';
import { useSignalSearch } from './SignalControls';
import styles from './SignalWorkspace.module.css';

export function NewsInbox({ data, query }: { data: NewsPage; query: NewsQuery }) {
  const { params, update } = useSignalSearch();
  const q = (params.get('q') ?? '').slice(0, 100);
  const scope = NEWS_SCOPES.some(([key]) => key === params.get('scope')) ? params.get('scope')! : 'all';
  const filtered = filterNews(data.items, q, scope);
  return <section className={styles.panel} aria-label="뉴스 검토 목록" data-testid="news-inbox">
    <div className={styles.panelHead}><h2>검토할 뉴스와 공시</h2><p>원문을 읽고, 연결된 해석·기업·테마로 이어가세요.</p></div>
    <div className={styles.toolbar}>
      <div className={styles.scopes} role="group" aria-label="현재 페이지 선별">
        {NEWS_SCOPES.map(([key, label]) => <button type="button" key={key} aria-pressed={scope === key} onClick={() => update({ scope: key }, true)}>{label}<span>{filterNews(data.items, '', key).length}</span></button>)}
      </div>
      <label className={styles.search}>이 페이지에서 검색<input aria-label="뉴스 본문 검색" maxLength={100} placeholder="제목·내용·종목" value={q} onChange={e => update({ q: e.target.value })} /></label>
      <button className={styles.reset} type="button" onClick={() => update({ q: '', scope: 'all' })}>선별 초기화</button>
    </div>
    <p className={styles.resultCount} role="status">수신 {data.items.length}개 기록 중 {filtered.length}개 표시 · 검색·선별은 현재 페이지에만 적용</p>
    {filtered.map((item, index) => <NewsRecord key={`${item.id}-${index}`} item={item} date={query.date} />)}
    {!filtered.length && <div className={styles.empty}><h3>{data.items.length ? '이 페이지에서 조건에 맞는 기록이 없습니다' : '수신된 뉴스 목록이 비어 있습니다'}</h3><p>{data.items.length ? '검색·선별 조건을 바꾸거나 다음 페이지를 확인하세요.' : '빈 목록은 전체 시장에 뉴스가 없다는 뜻이 아닙니다.'}</p></div>}
    <nav className={styles.pagination} aria-label="뉴스 페이지 이동">
      {query.cursor && <SignalLink href={newsHref(query, { q, scope, cursor: '' })}>첫 페이지로</SignalLink>}
      {data.nextCursor && <SignalLink href={newsHref(query, { q, scope, cursor: data.nextCursor })}>다음 페이지 →</SignalLink>}
      <span>{data.pagingIssue ? '추가 페이지 정보 미확인' : data.hasMore ? '다음 기록이 있습니다' : '반환된 페이지의 끝'}</span>
    </nav>
    <p className={styles.footnote}>원천이 반환한 순서를 유지합니다. 동일 이벤트가 서로 다른 종목·원천 관계로 반복될 수 있으며, 수신 건수는 고유 기사 수와 다를 수 있습니다.</p>
  </section>;
}
