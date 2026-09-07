import { RESEARCH_FIELD_LABELS, type ResearchDisplayIssue } from '@/lib/research-display-contract';
import styles from './ResearchDataNotice.module.css';
export function ResearchDataNotice({ issue }: { issue: ResearchDisplayIssue | null | undefined }) {
  if (!issue) return null;
  return <div className={styles.notice} role="status" aria-atomic="true" aria-label="리서치 데이터 상태" data-testid="research-data-notice">
    <strong>{issue.metadataInvalid ? '리서치 데이터 상태를 확인할 수 없습니다' : issue.invalid.length ? '리서치 일부 필드의 형식 오류' : '리서치 일부 필드 미제공'}</strong>
    {issue.invalid.length > 0 && !issue.metadataInvalid && <p>형식 오류: {issue.invalid.map(field => RESEARCH_FIELD_LABELS[field]).join(' · ')}. 잘못된 값을 분석 문장이나 원천 링크로 바꾸지 않았습니다.</p>}
    {issue.unavailable.length > 0 && <p>미제공: {issue.unavailable.map(field => RESEARCH_FIELD_LABELS[field]).join(' · ')}. 빈 목록이나 위험이 없다는 의미가 아닙니다.</p>}
    <p>표시 가능한 기록만 읽습니다. 데이터 형식 확인은 분석의 사실성·투자 판단 검증과 별개입니다.</p>
  </div>;
}
