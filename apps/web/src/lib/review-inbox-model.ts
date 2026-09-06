/** Read-only discovery of existing human drafts. No company API or new storage. */
import { CHECKS, draftKey, parseDraft, type Draft } from './company-review-model';
import { stockSymbol } from './company-evidence-model';
import { dateOnly, identifier } from './research-reader-model';

export const REVIEW_STORAGE_PREFIX = 'stocka:company-review:';
const V1_PREFIX = `${REVIEW_STORAGE_PREFIX}v1:`;
export type SavedReview = { key: string; draft: Draft };
export type StorageProblem = { key: string; reason: 'unsupported' | 'invalid' | 'unreadable' };
export type InboxRead = { state: 'ready' | 'partial' | 'unavailable'; notes: SavedReview[]; problems: StorageProblem[] };
export const unavailableInbox = (): InboxRead => ({ state: 'unavailable', notes: [], problems: [] });
export type ReviewStore = Pick<Storage, 'length' | 'key' | 'getItem'>;
export const INBOX_LIMITS = { keys: 2000, reviews: 200, characters: 1_000_000 } as const;

export function parseSavedReview(key: string, raw: string): SavedReview | null {
  if (!key.startsWith(V1_PREFIX) || key.length > 2400) return null;
  const parts = key.slice(V1_PREFIX.length).split(':');
  if (parts.length !== 2) return null;
  try {
    const symbol = decodeURIComponent(parts[0]), instrumentId = decodeURIComponent(parts[1]);
    if (stockSymbol(symbol) !== symbol || !identifier(instrumentId) || instrumentId === 'instrument-unknown') return null;
    const identity = { symbol, instrumentId };
    if (draftKey(identity) !== key) return null;
    const draft = parseDraft(raw, identity);
    return draft ? { key, draft } : null;
  } catch { return null; }
}

/** Caps apply before parsing. Unknown/partial reads never become a complete empty collection. */
export function readReviewInbox(store: ReviewStore): InboxRead {
  const result: InboxRead = { state: 'ready', notes: [], problems: [] };
  try {
    const length = store.length;
    if (length > INBOX_LIMITS.keys) result.state = 'partial';
    const keys = new Set<string>();
    for (let index = 0; index < Math.min(length, INBOX_LIMITS.keys); index++) {
      const key = store.key(index);
      if (key?.startsWith(REVIEW_STORAGE_PREFIX)) keys.add(key);
    }
    if (keys.size > INBOX_LIMITS.reviews || store.length !== length) result.state = 'partial';
    let characters = 0;
    for (const key of [...keys].sort().slice(0, INBOX_LIMITS.reviews)) {
      let raw: string | null;
      try { raw = store.getItem(key); }
      catch { result.state = 'partial'; result.problems.push({ key, reason: 'unreadable' }); continue; }
      if (raw === null) { result.state = 'partial'; continue; }
      characters += Math.min(raw.length, 24001);
      if (characters > INBOX_LIMITS.characters) { result.state = 'partial'; break; }
      const note = parseSavedReview(key, raw);
      if (note) result.notes.push(note);
      else result.problems.push({ key, reason: key.startsWith(V1_PREFIX) ? 'invalid' : 'unsupported' });
    }
    return result;
  } catch {
    return { ...result, state: result.notes.length || result.problems.length ? 'partial' : 'unavailable' };
  }
}

export type DueBucket = 'overdue' | 'today' | 'planned' | 'undated';
export type InboxFilter = 'all' | DueBucket;
export const INBOX_FILTERS = [
  ['all', '전체'], ['overdue', '날짜 지남'], ['today', '오늘 확인'], ['planned', '확인 예정'], ['undated', '날짜 미지정'],
] as const;
export function localReviewDay(now: Date): string {
  if (!Number.isFinite(now.getTime())) return '';
  return `${String(now.getFullYear()).padStart(4, '0')}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}
export function dueBucket(nextDate: string, today: string): DueBucket | null {
  if (!dateOnly(today)) return null;
  if (nextDate === '') return 'undated';
  if (!dateOnly(nextDate)) return null;
  return nextDate < today ? 'overdue' : nextDate === today ? 'today' : 'planned';
}
export function filterSavedReviews(notes: SavedReview[], filter: InboxFilter, query: string, today: string): SavedReview[] {
  const needle = query.trim().toLocaleLowerCase();
  return notes.filter(({ draft: d }) => (filter === 'all' || dueBucket(d.nextDate, today) === filter)
    && (!needle || [d.symbol, d.instrumentId, d.note, d.opposition, d.nextAction].join('\n').toLocaleLowerCase().includes(needle)))
    .sort((a, b) => (a.draft.nextDate || '9999-99-99').localeCompare(b.draft.nextDate || '9999-99-99')
      || Date.parse(b.draft.savedAt) - Date.parse(a.draft.savedAt) || a.key.localeCompare(b.key));
}

const literal = (text: string) => text.split(/\r?\n/).map(line => `    ${line}`).join('\n');
/** No invented current model or source inventory is appended to recovered notes. */
export function exportSavedReview(draft: Draft): string {
  return ['# stockA 저장된 개인 검토',
    '브라우저에 저장된 사람의 초안입니다. 최신 분석·원천은 포함하지 않으며 추천·검증 승인·일정 알림이 아닙니다.',
    literal(`종목: ${draft.symbol}\n기업 ID: ${draft.instrumentId}\n분석 기준: ${draft.asOf ?? '미확인'}\n저장 시각: ${draft.savedAt}\n분석 묶음 ID: ${draft.snapshot}`),
    '## 내 판단과 근거', literal(draft.note || '미작성'),
    '## 반대 근거와 남은 의문', literal(draft.opposition || '미작성'),
    '## 다음 확인 사항', literal(draft.nextAction || '미작성'), literal(`직접 정한 날짜: ${draft.nextDate || '미지정'} (알림 없음)`),
    '## 저장 당시 직접 남긴 체크', literal(CHECKS.map(([key, label]) => `${draft.checks.includes(key) ? '[x]' : '[ ]'} ${label}`).join('\n')),
  ].join('\n\n') + '\n';
}
export function exportInboxNotes(read: InboxRead): string {
  return JSON.stringify({ format: 'stocka-saved-review-notes-v1', scope: 'loaded-valid-notes-only',
    completeRead: read.state === 'ready', unreadableCount: read.problems.length,
    notice: '읽은 유효 초안만 포함합니다. 계정 보관·최신 원천·자동 복원 기능은 아닙니다.',
    notes: read.notes.map(note => note.draft) }, null, 2) + '\n';
}
