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
  const [externallyChanged, setExternallyChanged] = useState(false);
  const refresh = () => {
    setLoaded({ target, result: readSelectedReview(selection, () => window.localStorage) });
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
  const editable = basis === 'same_basis' || basis === 'changed_basis';
  const conditions = model.groups.find(group => group.key === (model.fund ? 'limits' : 'conditions'))?.items;
  const status = result.status;
  const readMessage = status === 'loaded' || status === 'direct' ? null : REVIEW_READ_COPY[status];
  return <>
    <section className={styles.panel} id="saved-review-comparison" aria-labelledby="saved-comparison-title" data-testid="saved-review-comparison">
      <header className={styles.header}><div><span className={styles.kicker}>SAVED JUDGMENT / CURRENT RESEARCH</span><h2 id="saved-comparison-title">저장한 판단과 현재 분석</h2></div><ReaderLink href="/research-notes">검토함으로 돌아가기 →</ReaderLink></header>
      {basis && <div className={styles.notice} role="status"><strong>{REVIEW_BASIS_COPY[basis].title}</strong><p>{REVIEW_BASIS_COPY[basis].explanation}</p></div>}
      {readMessage !== null && <p className={styles.notice} role="status">{readMessage}</p>}
      {externallyChanged && <p className={styles.notice} role="status">다른 탭에서 선택한 메모가 변경됐습니다. 비교 중인 내용은 자동으로 바꾸지 않았습니다. 편집기의 저장 충돌도 별도로 확인하세요.</p>}
      {saved && <div className={styles.columns}>
        <article><h3>저장 당시의 내 판단</h3><dl className={styles.meta}><div><dt>기업 ID</dt><dd>{saved.instrumentId}</dd></div><div><dt>분석 기준</dt><dd>{saved.asOf ?? '미확인'}</dd></div><div><dt>저장 시각</dt><dd>{saved.savedAt}</dd></div></dl>
          <h4>내 판단과 근거</h4><p className={styles.body}>{saved.note || '작성된 판단 메모가 없습니다.'}</p>
          <h4>반대 근거와 남은 의문</h4><p className={styles.body}>{saved.opposition || '작성된 의문이 없습니다.'}</p>
          <h4>다음 확인 사항</h4><p className={styles.body}>{saved.nextAction || '작성된 확인 사항이 없습니다.'}</p>
          <p className={styles.caption}>직접 정한 날짜 {saved.nextDate || '미지정'} · 알림 없음</p>
        </article>
        <article><h3>{editable ? '현재 화면의 저장된 분석' : '현재 조회된 기업'}</h3><dl className={styles.meta}><div><dt>기업 ID</dt><dd>{model.instrumentId}</dd></div><div><dt>분석 기준</dt><dd>{model.asOf ?? '미확인'}</dd></div><div><dt>리서치 기록</dt><dd>{model.researchDate ?? '미확인'}</dd></div></dl>
          {editable ? <><p className={styles.caption}>{model.origin}</p><p className={styles.body}>{model.summary}</p><h4>{model.fund ? '저장된 제한 사항' : '판단을 바꿀 조건'}</h4>
            {conditions?.length ? <ul>{conditions.slice(0, 3).map((item, index) => <li key={index}>{item}</li>)}</ul> : <p className={styles.body}>{conditions === null || conditions === undefined ? '조건 목록 미제공' : '반환된 조건 목록이 비어 있습니다.'}</p>}
            <a href="#review-claims">주장·위험·전체 조건으로 이동 →</a><p className={styles.caption}>왼쪽은 사람의 저장 메모, 오른쪽은 현재 제공된 분석입니다. 둘의 내용이 서로 입증됐다는 뜻은 아닙니다.</p></>
            : <p className={styles.body}>식별자가 다른 메모와 분석은 대조 결과로 묶지 않습니다. 현재 기업을 검토하려면 별도 검토 화면을 열어 주세요.</p>}
        </article>
      </div>}
      <div className={styles.actions}><button type="button" onClick={refresh}>선택한 저장 메모 다시 읽기</button>
        {!editable && result.status !== 'loading' && <ReaderLink href={`/stocks/${encodeURIComponent(model.symbol)}/review`}>현재 기업의 별도 검토 열기 →</ReaderLink>}
      </div><p className={styles.caption}>이 비교 화면은 메모를 수정·복사·이전하지 않습니다. 현재 브라우저에서 읽은 기록이며 영구 이력이나 과거 분석 본문을 복원한 것이 아닙니다.</p>
    </section>
    {editable ? children : <p className={styles.blocked} id="review-note" role="status">선택한 메모와 현재 기업의 연결이 확인되기 전에는 이 경로에서 편집하지 않습니다.</p>}
  </>;
}
