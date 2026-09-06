'use client';
import { useRouter } from 'next/navigation';
import type { Route } from 'next';
import type { ReactNode } from 'react';
import { selectReviewSource, type ReviewModel } from '@/lib/company-review-model';
import { ReaderLink } from '@/components/readers/ReaderFrame';
import { ReviewDraft } from './ReviewDraft';
import styles from './ReviewNotebook.module.css';
export function ReviewNotebook({ model, snapshot, source, sourcePanel }: { model: ReviewModel; snapshot: string; source: unknown; sourcePanel: ReactNode }) {
  const router = useRouter(), selected = selectReviewSource(model, source);
  return <div className={styles.page} data-testid="company-review-notebook">
    <header className={styles.header}><div><span className={styles.kicker}>RESEARCH NOTEBOOK</span><h1>{model.symbol}<span>검토 노트</span></h1><p>{model.name} · 읽은 근거와 내 판단을 구분해 남깁니다.</p></div><ReaderLink href={`/stocks/${encodeURIComponent(model.symbol)}`}>← 기업 리서치</ReaderLink></header>
    <nav className={styles.steps} aria-label="검토 순서"><a href="#review-claims"><span>01</span>주장 확인</a><a href="#review-source"><span>02</span>원천 대조</a><a href="#review-note"><span>03</span>내 검토 작성</a></nav>
    <div className={styles.context}><span>기업 분석 {model.asOf ?? '미확인'}</span><span>리서치 기록 {model.researchDate ?? '미확인'}</span><strong>{model.origin}</strong></div>
    {model.blocked && <p className={styles.warning} role="status">원천 제한이 있는 분석입니다. 개인 체크 표시나 메모 작성으로 제한이 해제되지 않습니다.</p>}
    <div className={styles.compare}>
      <section id="review-claims" className={styles.analysisPanel} aria-labelledby="review-claims-title">
        <div className={styles.sectionHead}><div><span className={styles.kicker}>01 · STORED ANALYSIS</span><h2 id="review-claims-title">{model.fund ? '노출·비용·제한' : '투자 주장과 반대 근거'}</h2></div></div>
        <p className={styles.lead}>{model.summary}</p>
        {model.groups.map((group, index) => <section className={styles.claimGroup} key={group.key}><h3><span>{String(index+1).padStart(2,'0')}</span>{group.title}</h3>
          {group.items?.length ? <ul>{group.items.map((item,i) => <li key={i}>{item}</li>)}</ul> : <p className={styles.empty}>{group.items === null ? '목록 미제공' : '반환된 목록이 비어 있습니다.'} 근거가 충분하다는 뜻은 아닙니다.</p>}
        </section>)}
        <div className={styles.actions}><ReaderLink href={model.thesisHref}>연결 투자 논리 →</ReaderLink><ReaderLink href={model.recommendationHref}>추천 판단서 →</ReaderLink><ReaderLink href={`/stocks/${encodeURIComponent(model.symbol)}/details`}>수치·전문 분석 →</ReaderLink></div>
      </section>
      <section id="review-source" className={styles.sourcePanel} aria-labelledby="review-source-title">
        <div className={styles.sectionHead}><div><span className={styles.kicker}>02 · SOURCE COMPARISON</span><h2 id="review-source-title">연결 원천 대조</h2></div><span className={styles.localBadge}>{model.sources.length}개 연결 문서</span></div>
        <label className={styles.sourcePicker}>대조할 문서<select aria-label="대조할 문서" value={selected.id ?? ''} onChange={e => {
          const params = new URLSearchParams(window.location.search); params.set('source', e.target.value);
          router.push(`/stocks/${encodeURIComponent(model.symbol)}/review?${params}` as Route, { scroll: false });
        }}><option value="" disabled>{model.sources.length ? '연결 문서를 선택하세요' : '연결 문서 없음'}</option>{model.sources.map(s => <option key={s.id} value={s.id}>{s.title} · {s.context}</option>)}</select></label>
        {sourcePanel}
      </section>
    </div>
    <ReviewDraft model={model} snapshot={snapshot} />
    <p className={styles.footer}>화면의 분석 기준은 완전한 과거 시점 복원이 아닙니다. 문서 목록과 개인 체크 표시는 주장 검증·투자 추천·거래 승인이 아닙니다.</p>
  </div>;
}
