import { loadReviewSource } from '@/lib/company-review-data';
import type { ReviewModel } from '@/lib/company-review-model';
import { reviewSourcePresentation } from '@/lib/review-data-presentation';
import { shortDate } from '@/lib/research-reader-model';
import { ReaderLink } from '@/components/readers/ReaderFrame';
import styles from './ReviewNotebook.module.css';
export async function ReviewSource({ model, requested }: { model: ReviewModel; requested: unknown }) {
  const result = await loadReviewSource(model, requested);
  if (result.invalid) return <p role="status" className={styles.warning}>이 기업에 명시적으로 연결되지 않은 문서입니다. 다른 자료로 대체하지 않았습니다. 아래 문서 선택에서 연결 자료를 골라 주세요.</p>;
  if (!result.id) return <p className={styles.empty}>{reviewSourcePresentation(model).empty} 주장별 근거가 없다고 단정하지 않고 추가 자료를 확인하세요.</p>;
  if (!result.data) return <div role="status" className={styles.warning}><p>선택한 원천을 불러오지 못했습니다. 분석 내용과 작성 중인 메모는 유지됩니다.</p><a href="" className={styles.link}>현재 문서 다시 조회</a></div>;
  const source = result.data;
  return <div data-testid="review-source-content">
    <div className={styles.sourceMeta}><span>{source.publisher} · {source.form || source.type}</span><span>공개일 {shortDate(source.filedAt, '미기록')}</span></div>
    <h3 className={styles.sourceTitle}>{source.koreanTitle ?? source.title}</h3>
    <p className={styles.caption}>API가 제공한 발췌·요약입니다. 완전한 원문이나 직접 인용으로 보장하지 않습니다.</p>
    {model.asOf && source.filedAt && source.filedAt.slice(0,10) > model.asOf && <p className={styles.warning}>문서 공개일이 기업 분석 기준일 이후입니다. 당시 알려진 근거로 취급하지 마세요.</p>}
    {source.excerpts?.map(chunk => <article className={styles.excerpt} key={chunk.id}><span>{chunk.locator}</span><h4>{chunk.section}</h4><p>{chunk.summary}</p></article>)}
    {!source.excerpts?.length && <p className={styles.empty}>{source.excerpts === null ? '발췌 자료 미제공' : '반환된 발췌가 없습니다.'}</p>}
    {source.koreanSummary && <details className={styles.details}><summary>저장된 한국어 요약</summary><p>{source.koreanSummary}</p></details>}
    <details className={styles.details}><summary>원제·문서 기준·식별 정보</summary><p>{source.title}</p><dl><dt>대상 기간</dt><dd>{source.periodEnd ?? '미기록'}</dd><dt>수집 시각</dt><dd>{source.fetchedAt ?? '미기록'}</dd><dt>요청 ID</dt><dd>{result.id}</dd><dt>반환 ID</dt><dd>{source.id}</dd><dt>ID 해석</dt><dd>{source.resolution === 'exact' ? '일치' : '기존 API의 별칭 해석'}</dd></dl></details>
    <ReaderLink href={`/source-documents/${encodeURIComponent(result.id)}`}>원천 문서 상세 →</ReaderLink>
    <p className={styles.caption}>이 목록은 연결 자료입니다. 특정 주장에 대한 증명이나 원문 다운로드 권한을 뜻하지 않습니다.</p>
  </div>;
}
