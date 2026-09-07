/** Carry a saved review identity, never its text, into current research. */
import { draftKey, type Draft, type ReviewModel } from './company-review-model';
import { parseSavedReview } from './review-inbox-model';
import { stockSymbol } from './company-evidence-model';
import { identifier } from './research-reader-model';

type Identity = Pick<ReviewModel, 'symbol' | 'instrumentId'>;
export type ReviewSelection = { status: 'direct' | 'invalid' } | { status: 'selected'; key: string; identity: Identity };
export type SavedReviewRead = { status: 'direct' | 'invalid' | 'missing' | 'corrupt' | 'unavailable' }
  | { status: 'loaded'; draft: Draft };
export type ReviewBasis = 'same_basis' | 'changed_basis' | 'different_instrument';

export function selectSavedReview(symbol: string, requested: unknown): ReviewSelection {
  if (requested === undefined) return { status: 'direct' };
  const instrumentId = identifier(requested);
  if (stockSymbol(symbol) !== symbol || !instrumentId || instrumentId === 'instrument-unknown') return { status: 'invalid' };
  try {
    const identity = { symbol, instrumentId };
    return { status: 'selected', key: draftKey(identity), identity };
  } catch { return { status: 'invalid' }; }
}

/** Only a canonical identity is serialized; no text, snapshot or arbitrary key. */
export function savedReviewHref(identity: Identity): string | null {
  const selection = selectSavedReview(identity.symbol, identity.instrumentId);
  return selection.status === 'selected'
    ? `/stocks/${encodeURIComponent(identity.symbol)}/review?savedInstrument=${encodeURIComponent(identity.instrumentId)}`
    : null;
}

/** The storage factory is intentionally lazy: invalid selectors cause no lookup. */
export function readSelectedReview(selection: ReviewSelection, getStore: () => Pick<Storage, 'getItem'>): SavedReviewRead {
  if (selection.status !== 'selected') return { status: selection.status };
  let raw: string | null;
  try { raw = getStore().getItem(selection.key); }
  catch { return { status: 'unavailable' }; }
  if (raw === null) return { status: 'missing' };
  const saved = parseSavedReview(selection.key, raw);
  return saved ? { status: 'loaded', draft: saved.draft } : { status: 'corrupt' };
}

/** A bundle hash comparison is not an old-report diff or source verification. */
export function compareReviewBasis(draft: Draft, current: Identity, snapshot: string): ReviewBasis {
  if (draft.symbol !== current.symbol || draft.instrumentId !== current.instrumentId) return 'different_instrument';
  return draft.snapshot === snapshot ? 'same_basis' : 'changed_basis';
}

export const REVIEW_BASIS_COPY: Record<ReviewBasis, { title: string; explanation: string }> = {
  same_basis: {
    title: '저장 당시와 같은 분석 묶음',
    explanation: '기업 식별자와 화면 분석 묶음 ID가 같습니다. 원천 본문·분석 정확도·투자 판단의 검증을 뜻하지 않습니다.',
  },
  changed_basis: {
    title: '저장 당시와 다른 분석 묶음',
    explanation: '저장된 내 판단을 현재 요약·위험·무효화 조건과 다시 대조하세요. 이전 분석 본문은 저장하지 않았으므로 자동 변경 내역을 만들지 않습니다.',
  },
  different_instrument: {
    title: '종목 코드는 같지만 기업 식별자가 다릅니다',
    explanation: '선택한 메모를 현재 기업의 판단으로 가져오지 않았습니다. 아래 메모는 읽기 전용이며 다른 기업의 편집기에 자동으로 연결하지 않습니다.',
  },
};
export const REVIEW_READ_COPY = {
  loading: '선택한 저장 메모를 확인하는 중입니다.',
  invalid: '검토함에서 전달된 메모 식별자가 올바르지 않습니다. 다른 메모로 대체하지 않았습니다.',
  missing: '선택한 메모가 이 브라우저에 없습니다. 삭제됐거나 다른 기기에서 연 링크일 수 있습니다.',
  corrupt: '선택한 메모의 형식이나 기업 식별 정보를 확인할 수 없습니다. 저장된 원본은 변경하지 않았습니다.',
  unavailable: '브라우저 저장소를 읽을 수 없습니다. 메모가 없다고 판단하지 않습니다.',
} as const;
