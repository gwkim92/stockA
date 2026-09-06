import { createHash } from 'node:crypto';
import { loadReader } from './research-reader-data';
import { selectReviewSource, type ReviewModel } from './company-review-model';
import type { ReadOptions } from './company-evidence-data';
/** Identifies this rendered analysis bundle, not immutable source versions or historical knowledge. */
export const reviewSnapshot = (model: ReviewModel) => createHash('sha256').update(JSON.stringify(model)).digest('hex');
export async function loadReviewSource(model: ReviewModel, requested: unknown, options?: ReadOptions) {
  const selection = selectReviewSource(model, requested);
  if (!selection.id) return { ...selection, data: null, issue: null };
  const result = await loadReader('source', selection.id, options);
  return { ...selection, data: result.data, issue: result.issue };
}
