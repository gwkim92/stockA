import { object, type Row } from './research-reader-model';

export const RESEARCH_FIELD_LABELS = {
  title: '제목', korean_summary: '요약', key_points: '핵심 주장', catalysts: '촉매',
  risks: '반대 근거·위험', invalidation_conditions: '판단을 바꿀 조건', source_document_ids: '리서치 입력 문서',
} as const;
export type ResearchField = keyof typeof RESEARCH_FIELD_LABELS;
export type ResearchDisplayIssue = { invalid: ResearchField[]; unavailable: ResearchField[]; metadataInvalid: boolean };
const fields = Object.keys(RESEARCH_FIELD_LABELS) as ResearchField[];
function fieldList(value: unknown): value is ResearchField[] {
  return Array.isArray(value) && value.every(item => typeof item === 'string' && fields.includes(item as ResearchField))
    && new Set(value).size === value.length;
}
/** Quality is a typed producer contract, not an accuracy/confidence score. */
export function researchDisplayIssue(research: Row): ResearchDisplayIssue | null {
  if (!Object.hasOwn(research, 'data_quality')) return null; // Legacy payload: no validation claim.
  const quality = object(research.data_quality);
  const invalid = quality.invalid_fields, unavailable = quality.unavailable_fields;
  if (quality.policy !== 'equity_display_contract_v1' || !fieldList(invalid) || !fieldList(unavailable)
    || invalid.some(field => unavailable.includes(field))
    || quality.status !== (invalid.length ? 'invalid_fields' : unavailable.length ? 'partial' : 'complete')) {
    return { invalid: [...fields], unavailable: [], metadataInvalid: true };
  }
  return invalid.length || unavailable.length ? { invalid: [...invalid], unavailable: [...unavailable], metadataInvalid: false } : null;
}
/** Null means unknown to the existing readers. Only an actual valid [] means empty. */
export function projectResearchForReader(value: unknown): Row {
  const raw = object(value), issue = researchDisplayIssue(raw);
  if (!issue) return raw;
  const projected = { ...raw };
  for (const field of [...issue.invalid, ...issue.unavailable]) projected[field] = null;
  return projected;
}
