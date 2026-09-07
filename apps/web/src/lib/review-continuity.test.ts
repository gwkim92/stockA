// @vitest-environment node
import { describe, expect, it, vi } from 'vitest';
import { draftKey, type Draft } from './company-review-model';
import { compareReviewBasis, readSelectedReview, savedReviewHref, selectSavedReview } from './review-continuity-model';
const identity = { symbol: 'AAPL', instrumentId: 'instrument-aapl' };
const snapshot = 'a'.repeat(64);
const draft = (changes: Partial<Draft> = {}): Draft => ({ version: 1, ...identity, snapshot, asOf: '2026-09-05',
  savedAt: '2026-09-07T02:00:00Z', note: 'private-note-body', opposition: 'private-opposition',
  nextAction: 'private-next-question', nextDate: '2026-10-01', checks: ['numbers'], ...changes });

describe('identity-preserving inbox handoff', () => {
  it('serializes only the selected identity, not private notes, search or checklist data', () => {
    const value = draft();
    const href = savedReviewHref(value)!;
    expect(href).toBe('/stocks/AAPL/review?savedInstrument=instrument-aapl');
    expect(href).not.toContain(value.note); expect(href).not.toContain(value.snapshot); expect(href).not.toContain('numbers');
    const url = new URL(href, 'http://fixture');
    expect([...url.searchParams.keys()]).toEqual(['savedInstrument']);
  });
  it('separates two saved instruments even under the same symbol', () => {
    expect(savedReviewHref(identity)).not.toBe(savedReviewHref({ ...identity, instrumentId: 'instrument-old' }));
  });
  it.each([null, '', [], ['instrument-aapl'], ['instrument-aapl', 'instrument-old'], '../private',
    'instrument-unknown', 'bad?query', 'bad%2Fvalue', 'with space', 'x'.repeat(241), true, 12, '\ud800'])('rejects unsafe or ambiguous selector %s before storage access', requested => {
    const factory = vi.fn();
    const selection = selectSavedReview('AAPL', requested);
    expect(selection.status).toBe('invalid');
    expect(readSelectedReview(selection, factory)).toEqual({ status: 'invalid' });
    expect(factory).not.toHaveBeenCalled();
  });
  it('direct review navigation does not read a selected-note context', () => {
    const factory = vi.fn();
    expect(readSelectedReview(selectSavedReview('AAPL', undefined), factory)).toEqual({ status: 'direct' });
    expect(factory).not.toHaveBeenCalled();
  });
  it('rejects noncanonical symbol links', () => {
    for (const symbol of ['aapl', '../AAPL', '', 'AAPL?x']) expect(savedReviewHref({ ...identity, symbol })).toBeNull();
  });
  it('uses an encoded identifier and the exact canonical storage key', () => {
    const value = draft({ instrumentId: 'issuer:old' });
    const selection = selectSavedReview('AAPL', value.instrumentId);
    const getItem = vi.fn(() => JSON.stringify(value));
    expect(readSelectedReview(selection, () => ({ getItem }))).toEqual({ status: 'loaded', draft: value });
    expect(getItem).toHaveBeenCalledExactlyOnceWith(draftKey(value));
    expect(savedReviewHref(value)).toContain('issuer%3Aold');
  });
});

describe('selected draft recovery and comparison boundaries', () => {
  it('does not substitute the current draft when the selected old draft is missing', () => {
    const selected = selectSavedReview('AAPL', 'instrument-old');
    const getItem = vi.fn((key: string) => key === draftKey(identity) ? JSON.stringify(draft()) : null);
    expect(readSelectedReview(selected, () => ({ getItem }))).toEqual({ status: 'missing' });
    expect(getItem).toHaveBeenCalledTimes(1); expect(getItem).not.toHaveBeenCalledWith(draftKey(identity));
  });
  it.each(['broken-json', JSON.stringify(draft({ symbol: 'MSFT' })), JSON.stringify(draft({ instrumentId: 'instrument-old' })),
    JSON.stringify({ ...draft(), source_body: 'untrusted-extra' })])('does not repair or expose a corrupted selected payload', raw => {
    expect(readSelectedReview(selectSavedReview('AAPL', identity.instrumentId), () => ({ getItem: () => raw }))).toEqual({ status: 'corrupt' });
  });
  it('separates inaccessible storage from absent notes and redacts the exception', () => {
    const factory = vi.fn(() => { throw new Error('private storage details'); });
    expect(readSelectedReview(selectSavedReview('AAPL', identity.instrumentId), factory)).toEqual({ status: 'unavailable' });
    expect(factory).toHaveBeenCalledTimes(1);
  });
  it('separates a getItem failure from an absent note', () => {
    expect(readSelectedReview(selectSavedReview('AAPL', identity.instrumentId), () => ({ getItem: () => { throw Error('denied'); } }))).toEqual({ status: 'unavailable' });
  });
  it('same displayed basis is distinct from a changed displayed basis', () => {
    expect(compareReviewBasis(draft(), identity, snapshot)).toBe('same_basis');
    expect(compareReviewBasis(draft(), identity, 'b'.repeat(64))).toBe('changed_basis');
  });
  it('instrument and symbol identity take precedence over an identical hash', () => {
    expect(compareReviewBasis(draft({ instrumentId: 'instrument-old' }), identity, snapshot)).toBe('different_instrument');
    expect(compareReviewBasis(draft({ symbol: 'MSFT' }), identity, snapshot)).toBe('different_instrument');
  });
  it('does not migrate or modify saved notes and manual checks during comparison', () => {
    const value = draft(), before = JSON.stringify(value);
    compareReviewBasis(value, identity, 'b'.repeat(64));
    expect(JSON.stringify(value)).toBe(before);
    const getItem = vi.fn(() => before), setItem = vi.fn(), removeItem = vi.fn();
    readSelectedReview(selectSavedReview('AAPL', identity.instrumentId), () => ({ getItem, setItem, removeItem }));
    expect(setItem).not.toHaveBeenCalled(); expect(removeItem).not.toHaveBeenCalled();
  });
});
