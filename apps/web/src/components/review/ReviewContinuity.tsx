'use client';
import { useEffect, useState, type ReactNode } from 'react';
import { ReaderLink } from '@/components/readers/ReaderFrame';
import type { ReviewModel } from '@/lib/company-review-model';
import { compareReviewBasis, readSelectedReview, selectSavedReview, REVIEW_BASIS_COPY, REVIEW_READ_COPY,
  type SavedReviewRead } from '@/lib/review-continuity-model';
import styles from './ReviewContinuity.module.css';

type ReadState = SavedReviewRead | { status: 'loading' };
/** Read-only selected-note context. It never writes or migrates a draft. */
export function ReviewContinuity({ model, snapshot, requested, children }: {
  model: ReviewModel; snapshot: string; requested: unknown; children: ReactNode;
}) {
  const selection = selectSavedReview(model.symbol, requested);
  const target = selection.status === 'selected' ? selection.key : selection.status;
  const [loaded, setLoaded] = useState<{ target: string; result: ReadState }>({ target: '', result: { status: 'loading' } });
  const [admittedKey, setAdmittedKey] = useState<string | null>(null);
  const [externallyChanged, setExternallyChanged] = useState(false);
  const refresh = () => {
    const result = readSelectedReview(selection, () => window.localStorage);
    setLoaded({ target, result });
    if (result.status === 'loaded' && result.draft.symbol === model.symbol && result.draft.instrumentId === model.instrumentId) setAdmittedKey(target);
    setExternallyChanged(false);
  };
  useEffect(() => {
    refresh();
    if (selection.status !== 'selected') return;
    const changed = (event: StorageEvent) => {
      if (event.key === null || event.key === selection.key) setExternallyChanged(true);
    };
    window.addEventListener('storage', changed);
    return () => window.removeEventListener('storage', changed);
    // Only the selected identity determines which saved record is loaded.
    // A new server snapshot must not remount or discard an unsaved editor.
  }, [target]);
  if (selection.status === 'direct') return <>{children}</>;
  const result = loaded.target === target ? loaded.result : { status: 'loading' as const };
  const saved = result.status === 'loaded' ? result.draft : null;
  const basis = saved ? compareReviewBasis(saved, model, snapshot) : null;
  const comparable = basis === 'same_basis' || basis === 'changed_basis';
  // After an initially verified handoff, a later failed comparison reload must
  // not unmount dirty editor state. Its existing compare-before-save/conflict
  // checks still govern writes. Initial unresolved/mismatched routes stay closed.
  const retainEditor = admittedKey === target && selection.status === 'selected' && selection.identity.instrumentId === model.instrumentId;
  const showEditor = comparable || retainEditor;
  const conditions = model.groups.find(group => group.key === (model.fund ? 'limits' : 'conditions'))?.items;
  const status = result.status;
  const readMessage = status === 'loaded' || status === 'direct' ? null : REVIEW_READ_COPY[status];
  return <>
    <section className={styles.panel} id="saved-review-comparison" aria-labelledby="saved-comparison-title" data-testid="saved-review-comparison">
      <header className={styles.header}><div><span className={styles.kicker}>SAVED JUDGMENT / CURRENT RESEARCH</span><h2 id="saved-comparison-title">저장한 판단과 현재 분석</h2></div><ReaderLink href="/research-notes">검토함으로 돌아가기 →</ReaderLink></header>
      {basis && <div className={styles.notice} role="status"><strong>{REVIEW_BASIS_COPY[basis].title}</strong><p>{REVIEW_BASIS_COPY[basis].explanation}</p></div>}
      {readMessage !== null && <p className={styles.notice} role="status">{readMessage}</p>}
      {retainEditor && !comparable && <p className={styles.notice} role="status">선택한 저장 메모를 다시 확인하지 못했지만, 이미 열어 작성 중인 편집기는 보존했습니다. 저장 충돌을 확인하고 필요한 메모부터 내보내세요.</p>}
      {externallyChanged && <p className={styles.notice} role="status">다른 탭에서 선택한 메모가 변경됐습니다. 비교 중인 내용은 자동으로 바꾸지 않았습니다. 편집기의 저장 충돌도 별도로 확인하세요.</p>}
      {saved && <div className={styles.columns}>
        <article><h3>저장 당시의 내 판단</h3><dl className={styles.meta}><div><dt>기업 ID</dt><dd>{saved.instrumentId}</dd></div><div><dt>분석 기준</dt><dd>{saved.asOf ?? '미확인'}</dd></div><div><dt>저장 시각</dt><dd>{saved.savedAt}</dd></div></dl>
          <h4>내 판단과 근거</h4><p className={styles.body}>{saved.note || '작성된 판단 메모가 없습니다.'}</p>
          <h4>반대 근거와 남은 의문</h4><p className={styles.body}>{saved.opposition || '작성된 의문이 없습니다.'}</p>
          <h4>다음 확인 사항</h4><p className={styles.body}>{saved.nextAction || '작성된 확인 사항이 없습니다.'}</p>
          <p className={styles.caption}>직접 정한 날짜 {saved.nextDate || '미지정'} · 알림 없음</p>
        </article>
        <article><h3>{comparable ? '현재 화면의 저장된 분석' : '현재 조회된 기업'}</h3><dl className={styles.meta}><div><dt>기업 ID</dt><dd>{model.instrumentId}</dd></div><div><dt>분석 기준</dt><dd>{model.asOf ?? '미확인'}</dd></div><div><dt>리서치 기록</dt><dd>{model.researchDate ?? '미확인'}</dd></div></dl>
          {comparable ? <><p className={styles.caption}>{model.origin}</p><p className={styles.body}>{model.summary}</p><h4>{model.fund ? '저장된 제한 사항' : '판단을 바꿀 조건'}</h4>
            {conditions?.length ? <ul>{conditions.slice(0, 3).map((item, index) => <li key={index}>{item}</li>)}</ul> : <p className={styles.body}>{conditions === null || conditions === undefined ? '조건 목록 미제공' : '반환된 조건 목록이 비어 있습니다.'}</p>}
            <a href="#review-claims">주장·위험·전체 조건으로 이동 →</a><p className={styles.caption}>왼쪽은 사람의 저장 메모, 오른쪽은 현재 제공된 분석입니다. 둘의 내용이 서로 입증됐다는 뜻은 아닙니다.</p></>
            : <p className={styles.body}>식별자가 다른 메모와 분석은 대조 결과로 묶지 않습니다. 현재 기업을 검토하려면 별도 검토 화면을 열어 주세요.</p>}
        </article>
      </div>}
      <div className={styles.actions}><button type="button" onClick={refresh}>선택한 저장 메모 다시 읽기</button>
        {!showEditor && result.status !== 'loading' && <ReaderLink href={`/stocks/${encodeURIComponent(model.symbol)}/review`}>현재 기업의 별도 검토 열기 →</ReaderLink>}
      </div><p className={styles.caption}>비교 메모는 이 화면을 열거나 다시 읽을 때 불러온 기록입니다. 아래 편집기에서 저장한 변경은 ‘다시 읽기’로 반영합니다. 이 화면은 메모를 복사·이전하거나 과거 분석 본문을 복원하지 않습니다.</p>
    </section>
    {showEditor ? children : <p className={styles.blocked} id="review-note" role="status">선택한 메모와 현재 기업의 연결이 확인되기 전에는 이 경로에서 편집하지 않습니다.</p>}
  </>;
}
