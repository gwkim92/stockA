import { count, object, rows, strings, text } from '@/lib/company-evidence-model';
import { shortDate } from '@/lib/research-reader-model';
import { SourcePeek } from '@/components/research/SourcePeek';
import styles from './CompanyWorkspace.module.css';

export function ResearchProvenance({ research: rawResearch }: { research: unknown }) {
  const research = object(rawResearch);
  const generation = object(research.generation);
  const mode = text(generation.mode, 'unknown');
  const review = object(research.content_review);
  const needsCorrection = review.status === 'needs_source_correction';
  const source = object(research.financial_source_freshness);
  const sourceChanged = source.status === 'source_changed';
  const documents = strings(research.source_document_ids);
  return <details className={styles.disclosure} open={mode === 'fallback' || needsCorrection || sourceChanged}>
    <summary>
      {needsCorrection ? '원천 검토 · 보완 필요' : sourceChanged ? '재무 자료 변경 · 이전 자료로 생성한 보고서' : mode === 'fallback' ? '대체 보고서 · 실제 AI 생성 결과 아님' : mode === 'ai' ? 'AI 생성 보고서 · 내용 검토 미기록' : '생성 경로 미확인'}
    </summary>
    <p>리서치 기준 {shortDate(research.as_of_date, '미기록')} · 생성 모델 {text(research.model_name)} · 제공 경로 {text(research.provider)}</p>
    <p role={sourceChanged ? 'status' : undefined}>
      {sourceChanged ? '재무 자료가 변경되었습니다. 이 보고서는 갱신 전 자료를 사용했습니다.'
        : source.status === 'current' ? '보고서의 재무 입력 버전이 현재 수집 자료와 일치합니다.'
        : source.status === 'source_unavailable' ? '자동 수집한 재무 원천 버전이 없어 최신 여부를 대조하지 못했습니다.'
        : '보고서의 재무 입력 버전이 기록되지 않아 최신 여부를 대조하지 못했습니다.'}
      {' '}뉴스·밸류에이션 등 다른 자료의 최신성이나 내용 검증 결과는 별도로 확인해야 합니다.
    </p>
    <p>형식 확인: {generation.structural_status === 'complete' ? '필수 항목의 자료형 확인' : '누락·형식 확인 필요'}.
      {!needsCorrection && '기업 주장·촉매·무효화 조건에 대한 별도 내용 검토 기록은 없습니다.'}</p>
    {needsCorrection && <section aria-label="보고서 원천 검토 결과">
      <p>{text(review.summary)}</p>
      <p className={styles.caption}>{text(review.reviewer)} · {shortDate(review.reviewed_at, '검토일 미기록')}</p>
      <details>
      <summary>검토 항목 {rows(review.findings)?.length ?? 0}개와 원문</summary>
      <ul>{rows(review.findings)?.map((finding, index) => <li key={index}>
        <strong>{text(finding.title)}</strong><p>{text(finding.detail)}</p>
        {safeReviewUrl(finding.source_url) && <a href={safeReviewUrl(finding.source_url)!} target="_blank" rel="noopener noreferrer">{text(finding.source_label, '검토 원천 열기')} ↗</a>}
      </li>)}</ul>
      <p className={styles.caption}>{text(review.limitations)}</p>
      </details>
    </section>}
    <p>입력 문서 {count(generation.source_document_count) ?? '미확인'}개가 연결되어 있습니다. 각 주장이 해당 문서로 입증됐다는 판정은 아닙니다.</p>
    {!!documents?.length && <div className={styles.actions}>{documents.map((id, index) => <SourcePeek key={id} documentId={id} label={`입력 문서 ${index + 1}`} />)}</div>}
  </details>;
}

function safeReviewUrl(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password ? url.href : null; }
  catch { return null; }
}
