'use client';
import { useEffect, useRef, useState } from 'react';
import { CHECKS, draftKey, emptyDraft, exportReview, parseDraft, type Draft, type ReviewModel } from '@/lib/company-review-model';
import { dateOnly } from '@/lib/research-reader-model';
import styles from './ReviewNotebook.module.css';
type StorageState = 'loading' | 'ready' | 'unavailable' | 'corrupt' | 'conflict';
function download(text: string, filename: string) {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
  const a = document.createElement('a'); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function ReviewDraft({ model, snapshot }: { model: ReviewModel; snapshot: string }) {
  const key = draftKey(model), raw = useRef<string | null>(null);
  const [draft, setDraft] = useState(() => emptyDraft(model, snapshot));
  const [storage, setStorage] = useState<StorageState>('loading');
  const [dirty, setDirty] = useState(false), [message, setMessage] = useState('초안 저장소를 확인하는 중입니다.');
  const [deleting, setDeleting] = useState(false);
  const stale = draft.snapshot !== snapshot;
  const storageWarning = storage === 'conflict'
    ? '다른 탭에서 초안이 변경됐습니다. 현재 메모를 내보낸 뒤 저장된 초안을 다시 읽으세요.'
    : storage === 'corrupt'
      ? '저장된 초안을 읽을 수 없습니다. 원본을 보관하거나 삭제하기 전에는 덮어쓰지 않습니다.'
      : '브라우저 저장소를 사용할 수 없습니다. 작성 중인 메모는 화면에만 있으며 파일로 내보낼 수 있습니다.';
  const load = () => {
    try {
      raw.current = window.localStorage.getItem(key);
      const stored = raw.current === null ? null : parseDraft(raw.current, model);
      if (raw.current !== null && !stored) { setStorage('corrupt'); setMessage('저장된 초안을 읽을 수 없습니다. 원본을 보관하거나 삭제하기 전에는 덮어쓰지 않습니다.'); return; }
      setDraft(stored ?? emptyDraft(model, snapshot)); setDirty(false); setStorage('ready'); setDeleting(false);
      setMessage(stored ? '이 브라우저의 저장된 초안을 불러왔습니다.' : '아직 저장하지 않은 개인 초안입니다.');
    } catch { setStorage('unavailable'); setMessage('브라우저 저장소에 접근할 수 없습니다. 작성은 가능하며 파일 내보내기를 이용하세요.'); }
  };
  useEffect(() => { load(); /* Snapshot changes are handled explicitly, never by reattaching old checks. */ }, [key]);
  useEffect(() => {
    const changed = (event: StorageEvent) => {
      if ((event.key === key || event.key === null) && event.newValue !== raw.current) {
        setStorage('conflict'); setMessage('다른 탭에서 초안이 변경됐습니다. 현재 메모를 내보낸 뒤 저장된 초안을 다시 읽으세요.');
      }
    };
    window.addEventListener('storage', changed); return () => window.removeEventListener('storage', changed);
  }, [key]);
  useEffect(() => {
    if (!dirty) return;
    const leaving = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    const navigate = (event: MouseEvent) => {
      const link = event.target instanceof Element ? event.target.closest('a') : null;
      if (!link || link.hasAttribute('download') || link.target === '_blank' || event.metaKey || event.ctrlKey) return;
      const destination = new URL(link.href, window.location.href);
      if ((destination.origin !== window.location.origin || destination.pathname !== window.location.pathname)
        && !window.confirm('아직 저장하지 않은 메모가 있습니다. 저장하지 않고 이동할까요?')) {
        event.preventDefault(); event.stopPropagation();
      }
    };
    window.addEventListener('beforeunload', leaving); document.addEventListener('click', navigate, true);
    return () => { window.removeEventListener('beforeunload', leaving); document.removeEventListener('click', navigate, true); };
  }, [dirty]);
  const edit = (values: Partial<Draft>) => { setDraft(d => ({ ...d, ...values })); setDirty(true); setMessage('수정 내용이 아직 저장되지 않았습니다.'); };
  const save = () => {
    if (storage !== 'ready' || stale) return;
    const next = { ...draft, savedAt: new Date().toISOString() }, encoded = JSON.stringify(next);
    if (!parseDraft(encoded, model)) { setMessage('메모 길이 또는 날짜 형식을 확인하세요. 저장하지 않았습니다.'); return; }
    try {
      if (window.localStorage.getItem(key) !== raw.current) { setStorage('conflict'); setMessage('다른 탭에서 초안이 변경돼 덮어쓰지 않았습니다.'); return; }
      window.localStorage.setItem(key, encoded); raw.current = encoded; setDraft(next); setDirty(false);
      setMessage('이 브라우저에 저장했습니다. 서버·계정·다른 기기에는 동기화되지 않습니다.');
    } catch { setStorage('unavailable'); setMessage('저장에 실패했습니다. 현재 메모는 화면에 남아 있습니다. 파일로 내보내세요.'); }
  };
  const remove = () => {
    try {
      if (window.localStorage.getItem(key) !== raw.current) { setStorage('conflict'); setMessage('저장된 초안이 바뀌어 삭제하지 않았습니다. 다시 읽어 확인하세요.'); setDeleting(false); return; }
      window.localStorage.removeItem(key); raw.current = null; setDraft(emptyDraft(model, snapshot)); setStorage('ready'); setDirty(false); setDeleting(false);
      setMessage('이 기업의 브라우저 초안을 삭제했습니다.');
    } catch { setStorage('unavailable'); setMessage('초안 삭제에 실패했습니다.'); }
  };
  const editable = storage !== 'loading' && storage !== 'corrupt' && !stale;
  return <section id="review-note" className={styles.notePanel} aria-labelledby="review-note-title" data-testid="review-draft">
    <div className={styles.sectionHead}><div><span className={styles.kicker}>03 · MY REVIEW</span><h2 id="review-note-title">내 검토와 다음 확인</h2></div><span className={styles.localBadge}>개인 초안 · 브라우저 저장</span></div>
    <p className={styles.caption}>공용 기기에서는 저장하지 마세요. 계정별 보관·암호화·서버 동기화가 없으며 브라우저 데이터 삭제 시 사라집니다.</p>
    {stale && <div className={styles.warning} role="status"><strong>분석 묶음이 바뀌었습니다.</strong><p>이전 초안 기준: {draft.asOf ?? '미확인'}. 현재 주장에 예전 체크 표시를 적용하지 않았습니다.</p>
      <button type="button" onClick={() => { setDraft(d => ({ ...d, snapshot, asOf: model.asOf, checks: [], savedAt: '' })); setDirty(true); setMessage('기존 메모를 가져오고 체크 표시를 초기화했습니다. 저장 전까지 이전 초안은 그대로 보관됩니다.'); }}>메모만 가져와 새 기준으로 검토</button></div>}
    {(storage === 'conflict' || storage === 'corrupt' || storage === 'unavailable') && <div className={styles.warning}>
      <p>{storageWarning}</p><button type="button" onClick={() => { if (!dirty || window.confirm('현재 미저장 메모 대신 저장된 초안을 불러올까요?')) load(); }}>저장된 초안 다시 읽기</button>
      {storage === 'corrupt' && raw.current !== null && <button type="button" onClick={() => download(raw.current!, `${model.symbol}-review-stored.txt`)}>읽지 못한 초안 원본 내보내기</button>}
    </div>}
    <div className={styles.noteGrid}>
      <div className={styles.noteFields}>
        <div className={styles.field}><label htmlFor="review-note-text">내 판단과 근거</label><textarea id="review-note-text" rows={4} maxLength={4000} value={draft.note} disabled={!editable} placeholder="어떤 주장을 받아들이거나 보류하는가? 원천 문서·구간과 함께 적으세요." onChange={e => edit({ note: e.target.value })} /></div>
        <div className={styles.field}><label htmlFor="review-opposition">반대 근거와 남은 의문</label><textarea id="review-opposition" rows={3} maxLength={3000} value={draft.opposition} disabled={!editable} placeholder="주장에 맞지 않는 자료, 다른 설명, 확인하지 못한 부분" onChange={e => edit({ opposition: e.target.value })} /></div>
      </div>
      <div className={styles.nextFields}>
        <fieldset disabled={!editable}><legend>내가 확인한 항목</legend>{CHECKS.map(([item,label]) => <label key={item}><input type="checkbox" checked={draft.checks.includes(item)} onChange={e => edit({ checks: e.target.checked ? [...draft.checks, item] : draft.checks.filter(key => key !== item) })} />{label}</label>)}<p className={styles.caption}>직접 남기는 표시입니다. 시스템의 근거 검증·추천 승인과는 무관합니다.</p></fieldset>
        <div className={styles.field}><label htmlFor="review-next-action">다음에 확인할 사항</label><textarea id="review-next-action" rows={2} maxLength={2000} disabled={!editable} value={draft.nextAction} placeholder="예: 다음 실적에서 서비스 매출과 현금흐름을 대조" onChange={e => edit({ nextAction: e.target.value })} /></div>
        <div className={styles.field}><label htmlFor="review-next-date">직접 정한 확인 날짜</label><input id="review-next-date" type="date" value={draft.nextDate} disabled={!editable} onChange={e => edit({ nextDate: e.target.value })} /></div><p className={styles.caption}>날짜 메모만 저장합니다. 캘린더 등록·자동 알림은 없습니다.</p>
      </div>
    </div>
    <div className={styles.saveBar}><div className={styles.actions}>
      <button type="button" className={styles.primary} disabled={storage !== 'ready' || stale || (!!draft.nextDate && !dateOnly(draft.nextDate))} onClick={save}>이 브라우저에 저장</button>
      <button type="button" disabled={storage === 'loading' || storage === 'corrupt'} onClick={() => download(exportReview({ ...draft, savedAt: dirty ? '' : draft.savedAt }, model, snapshot), `${model.symbol}-review.md`)}>검토 노트 내보내기</button>
      <button type="button" disabled={storage === 'loading' || storage === 'unavailable'} onClick={() => setDeleting(true)}>초안 삭제</button>
    </div><p role="status" className={styles.saveStatus}>{message}{dirty ? ' 페이지를 떠나기 전 저장하거나 내보내세요.' : ''}</p></div>
    {deleting && <div className={styles.warning}><p>이 기업의 저장된 초안과 현재 작성 내용을 삭제할까요? 다른 기업의 초안은 유지합니다.</p><button type="button" onClick={remove}>삭제 확인</button><button type="button" onClick={() => setDeleting(false)}>취소</button></div>}
  </section>;
}
