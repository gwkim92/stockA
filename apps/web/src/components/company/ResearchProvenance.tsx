import { count, object, strings, text } from '@/lib/company-evidence-model';
import { shortDate } from '@/lib/research-reader-model';
import { SourcePeek } from '@/components/research/SourcePeek';
import styles from './CompanyWorkspace.module.css';

export function ResearchProvenance({ research: rawResearch }: { research: unknown }) {
  const research = object(rawResearch);
  const generation = object(research.generation);
  const mode = text(generation.mode, 'unknown');
  const documents = strings(research.source_document_ids);
  return <details className={styles.disclosure} open={mode === 'fallback'}>
    <summary>
      {mode === 'fallback' ? '대체 보고서 · 실제 AI 생성 결과 아님' : mode === 'ai' ? 'AI 생성 보고서 · 내용 검토 미기록' : '생성 경로 미확인'}
    </summary>
    <p>리서치 기준 {shortDate(research.as_of_date, '미기록')} · 생성 모델 {text(research.model_name)} · 제공 경로 {text(research.provider)}</p>
    <p>형식 확인: {generation.structural_status === 'complete' ? '필수 항목의 자료형 확인' : '누락·형식 확인 필요'}.
      기업 주장·촉매·무효화 조건에 대한 별도 내용 검토 기록은 없습니다.</p>
    <p>입력 문서 {count(generation.source_document_count) ?? '미확인'}개가 연결되어 있습니다. 각 주장이 해당 문서로 입증됐다는 판정은 아닙니다.</p>
    {!!documents?.length && <div className={styles.actions}>{documents.map((id, index) => <SourcePeek key={id} documentId={id} label={`입력 문서 ${index + 1}`} />)}</div>}
  </details>;
}
