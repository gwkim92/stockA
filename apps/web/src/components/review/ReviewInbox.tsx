'use client';
import { useEffect, useRef, useState } from 'react';
import { ReaderLink } from '@/components/readers/ReaderFrame';
import { CHECKS } from '@/lib/company-review-model';
import { REVIEW_STORAGE_PREFIX, INBOX_FILTERS, dueBucket, exportInboxNotes, exportSavedReview,
  filterSavedReviews, localReviewDay, readReviewInbox, unavailableInbox, type InboxFilter, type InboxRead } from '@/lib/review-inbox-model';
import styles from './ReviewInbox.module.css';

function download(text: string, filename: string) {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename;
  document.body.appendChild(anchor); anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const bucketLabel = (date: string, today: string) => INBOX_FILTERS.find(([key]) => key === dueBucket(date, today))?.[1] ?? '날짜 미확인';

export function ReviewInbox() {
  const [read, setRead] = useState<InboxRead | null>(null);
  const [today, setToday] = useState(''), [zone, setZone] = useState('');
  const [query, setQuery] = useState(''), [filter, setFilter] = useState<InboxFilter>('all');
  const [selected, setSelected] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const title = useRef<HTMLHeadingElement>(null);
  const refresh = (notice = '') => {
    try { setRead(readReviewInbox(window.localStorage)); }
    catch { setRead(unavailableInbox()); }
    setToday(localReviewDay(new Date()));
    setZone(Intl.DateTimeFormat().resolvedOptions().timeZone);
    setMessage(notice);
  };
  useEffect(() => {
    refresh();
    const storageChanged = (event: StorageEvent) => {
      if (event.key === null || event.key.startsWith(REVIEW_STORAGE_PREFIX)) refresh('다른 탭의 저장 변경을 반영했습니다.');
    };
    const visible = () => { if (document.visibilityState === 'visible') refresh(); };
    const timer = window.setInterval(() => setToday(localReviewDay(new Date())), 60_000);
    window.addEventListener('storage', storageChanged); document.addEventListener('visibilitychange', visible);
    return () => { window.clearInterval(timer); window.removeEventListener('storage', storageChanged); document.removeEventListener('visibilitychange', visible); };
  }, []);
  const notes = read?.notes ?? [], visible = filterSavedReviews(notes, filter, query, today);
  const active = notes.find(note => note.key === selected);
  const counts = Object.fromEntries(INBOX_FILTERS.map(([key]) => [key, key === 'all' ? notes.length : notes.filter(note => dueBucket(note.draft.nextDate, today) === key).length]));
  const open = (key: string) => {
    setSelected(key);
    requestAnimationFrame(() => title.current?.focus());
  };
  const exportRaw = (key: string) => {
    try {
      const raw = window.localStorage.getItem(key);
      if (raw === null) { refresh('해당 초안이 더 이상 저장소에 없습니다.'); return; }
      download(raw, 'stockA-unreadable-review.txt');
    } catch { setMessage('초안 원본을 읽지 못해 내보내지 않았습니다.'); }
  };
  return <div className={styles.page} data-testid="review-inbox">
    <header className={styles.header}><div><span className={styles.kicker}>PERSONAL RESEARCH</span><h1>내 검토함</h1><p>다시 확인할 기업과 남겨둔 질문을 한곳에서.</p></div><ReaderLink href="/stocks">기업 찾아 검토하기 →</ReaderLink></header>
    <p className={styles.scope}>이 브라우저에 직접 저장한 개인 초안입니다. 서버·계정·다른 기기와 동기화되지 않습니다.</p>
    <div className={styles.toolbar}><div className={styles.search}><label htmlFor="review-inbox-search">종목·메모에서 찾기</label><input id="review-inbox-search" type="search" maxLength={120} value={query} onChange={event => setQuery(event.target.value)} placeholder="종목 코드 또는 남겨둔 질문" /></div>
      <button type="button" onClick={() => refresh('브라우저 저장소 조회를 다시 시도했습니다.')}>목록 새로고침</button>
      <button type="button" disabled={!notes.length} onClick={() => download(exportInboxNotes(read!), 'stockA-saved-reviews.json')}>읽은 초안 묶음 내보내기</button>
    </div>
    <div className={styles.filters} role="group" aria-label="직접 정한 확인 날짜로 필터">{INBOX_FILTERS.map(([key, label]) => <button type="button" key={key} aria-pressed={filter === key} onClick={() => setFilter(key)}>{label}<span>{read && read.state !== 'unavailable' ? counts[key] : '—'}</span></button>)}</div>
    <p className={styles.caption}>{today ? `기기 날짜 ${today} · ${zone}` : '기기 날짜 확인 중'} · 날짜는 직접 적은 메모이며 자동 알림은 없습니다. 읽은 초안 안에서만 검색·집계합니다.</p>
    <p role="status" className={styles.status}>{message}</p>
    {!read && <p role="status">브라우저에 저장된 초안을 불러오는 중입니다.</p>}
    {read?.state === 'unavailable' && <section className={styles.warning} role="alert"><h2>브라우저 저장소를 읽을 수 없습니다</h2><p>저장된 메모가 없다는 뜻은 아닙니다. 저장소 접근이 허용된 상태에서 목록을 다시 읽어 주세요.</p></section>}
    {read?.state === 'partial' && <p className={styles.warning} role="alert">일부 항목만 읽었습니다. 읽기 제한·저장소 변경·접근 실패로 빠진 초안이 있을 수 있습니다. 아래 개수와 내보내기는 전체 보관함을 보장하지 않습니다.</p>}
    {!!read?.problems.length && <details className={styles.problems}><summary>읽지 못한 초안 {read.problems.length}개 · 원본은 보존됩니다</summary><p>다른 버전·잘못된 형식·식별 정보 불일치 또는 접근 실패가 있는 항목입니다. 정상 초안으로 바꾸거나 삭제하지 않았습니다.</p>{read.problems.map(problem => <div key={problem.key}><code>{problem.key}</code><button type="button" onClick={() => exportRaw(problem.key)}>현재 저장된 원본 내보내기</button></div>)}</details>}
    {read && read.state !== 'unavailable' && <div className={styles.workspace}>
      <section className={styles.listPanel} aria-labelledby="review-list-title"><div className={styles.sectionHead}><h2 id="review-list-title">저장된 검토</h2><span>{visible.length}개 표시</span></div>
        {visible.length ? <ul className={styles.list}>{visible.map(({key, draft}) => <li key={key}><button type="button" aria-pressed={selected === key} aria-label={`${draft.symbol} 저장된 메모 열기`} onClick={() => open(key)}><div className={styles.rowHead}><strong>{draft.symbol}</strong><span data-bucket={dueBucket(draft.nextDate, today)}>{bucketLabel(draft.nextDate, today)}</span></div><p className={styles.preview}>{draft.nextAction || draft.note || '작성된 질문이나 판단 메모가 없습니다.'}</p><div className={styles.rowMeta}><span>확인 {draft.nextDate || '날짜 미지정'}</span><span>분석 {draft.asOf ?? '미확인'}</span></div></button></li>)}</ul>
        : <div className={styles.empty}><h3>{notes.length ? '조건에 맞는 메모가 없습니다' : read.problems.length || read.state === 'partial' ? '읽을 수 있는 초안이 없습니다' : '아직 저장한 검토가 없습니다'}</h3><p>{notes.length ? '검색어나 날짜 필터를 바꿔 확인하세요.' : '기업 검토 화면에서 메모를 작성하고 “이 브라우저에 저장”을 누르면 여기에 나타납니다.'}</p>{notes.length > 0 && <button type="button" onClick={() => { setFilter('all'); setQuery(''); }}>검색·필터 초기화</button>}<ReaderLink href="/stocks">기업 탐색 →</ReaderLink></div>}
      </section>
      <section className={styles.reader} aria-labelledby="saved-review-title" data-testid="saved-review-reader"><h2 id="saved-review-title" tabIndex={-1} ref={title}>{active ? `${active.draft.symbol} · 저장된 내 검토` : '메모를 선택해 이어서 읽으세요'}</h2>
        {active ? <>
          <p className={styles.readerNotice}>저장 당시의 개인 메모입니다. 최신 분석과의 일치 여부는 확인하지 않았습니다. 체크 표시도 현재 분석의 검증 결과가 아닙니다.</p>
          <dl className={styles.meta}><div><dt>분석 기준</dt><dd>{active.draft.asOf ?? '미확인'}</dd></div><div><dt>내가 정한 확인 날짜</dt><dd>{active.draft.nextDate || '미지정'} · {bucketLabel(active.draft.nextDate, today)}</dd></div></dl>
          <section className={styles.next}><h3>다음 확인 사항</h3><p>{active.draft.nextAction || '아직 적지 않았습니다.'}</p></section>
          <section className={styles.note}><h3>내 판단과 근거</h3><p>{active.draft.note || '아직 적지 않았습니다.'}</p></section>
          <section className={styles.note}><h3>반대 근거와 남은 의문</h3><p>{active.draft.opposition || '아직 적지 않았습니다.'}</p></section>
          <details className={styles.details}><summary>저장 당시 체크와 식별 정보</summary><ul>{CHECKS.map(([key, label]) => <li key={key}>{active.draft.checks.includes(key) ? '표시함' : '미표시'} · {label}</li>)}</ul><dl><dt>기업 ID</dt><dd>{active.draft.instrumentId}</dd><dt>저장 시각</dt><dd>{active.draft.savedAt}</dd><dt>분석 묶음 ID</dt><dd>{active.draft.snapshot}</dd></dl></details>
          <div className={styles.readerActions}><ReaderLink href={`/stocks/${encodeURIComponent(active.draft.symbol)}/review`}>현재 분석과 다시 검토 →</ReaderLink><button type="button" onClick={() => download(exportSavedReview(active.draft), `${active.draft.symbol}-saved-review.md`)}>이 메모 내보내기</button></div>
        </> : <p className={styles.empty}>{selected ? '선택했던 초안이 현재 읽은 목록에 없습니다. 다른 탭에서 삭제·변경됐거나 읽을 수 없게 되었을 수 있습니다.' : '목록에서 기업을 고르면 판단·반대 근거·다음 질문을 읽을 수 있습니다. 기업 API를 조회하지 않습니다.'}</p>}
      </section>
    </div>}
    <details className={styles.storageBoundary}><summary>저장과 내보내기 범위</summary><p>공용 기기에서는 저장하지 마세요. 초안은 암호화·계정 분리되지 않으며 브라우저 데이터 삭제 시 사라질 수 있습니다. 이 화면은 읽기 전용이고, 메모 수정은 기업 검토 화면에서 합니다.</p><p>묶음 내보내기는 현재 읽은 정상 초안만 포함합니다. 손상된 항목은 별도로 원본을 보관하세요. 파일을 자동 복원하는 기능은 없습니다. 회사명·현재 분석·원천 본문은 저장된 초안에 없으므로 만들어 넣지 않습니다.</p><p>기업 API 장애와 별개로 메모를 읽을 수 있지만 앱 서버에는 접속할 수 있어야 합니다. 이 화면이 오프라인 앱이나 동시 변경의 원자적 기록을 보장하지는 않습니다.</p></details>
  </div>;
}
