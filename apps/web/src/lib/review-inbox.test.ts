// @vitest-environment node
import { describe, expect, it, vi } from 'vitest';
import { draftKey, type Draft } from './company-review-model';
import { dueBucket, exportInboxNotes, exportSavedReview, filterSavedReviews, INBOX_LIMITS,
  localReviewDay, parseSavedReview, readReviewInbox, type ReviewStore, type SavedReview } from './review-inbox-model';
const draft = (patch: Partial<Draft> = {}): Draft => ({ version: 1, symbol: 'AAPL', instrumentId: 'instrument-aapl',
  snapshot: 'a'.repeat(64), asOf: '2026-09-05', savedAt: '2026-09-06T12:00:00Z',
  note: '내 판단', opposition: '반대 가능성', nextAction: '현금흐름 대조', nextDate: '2026-09-07', checks: [], ...patch });
const item = (patch: Partial<Draft> = {}): SavedReview => { const d = draft(patch); return {key: draftKey(d), draft: d}; };
function store(entries: [string, string][]): ReviewStore {
  const values = new Map(entries), keys = [...values.keys()];
  return { length: keys.length, key: vi.fn(index => keys[index] ?? null), getItem: vi.fn(key => values.get(key) ?? null) };
}
const entries = (items: SavedReview[]): [string, string][] => items.map(note => [note.key, JSON.stringify(note.draft)]);

describe('saved review identity and existing draft compatibility', () => {
  it('reads the unchanged v1 draft without needing a fabricated current analysis', () => {
    const note = item(); expect(parseSavedReview(note.key, JSON.stringify(note.draft))).toEqual(note);
  });
  it.each(['other:AAPL:instrument-aapl', 'stocka:company-review:v2:AAPL:instrument-aapl',
    'stocka:company-review:v1:aapl:instrument-aapl', 'stocka:company-review:v1:%41APL:instrument-aapl',
    'stocka:company-review:v1:AAPL:../private', 'stocka:company-review:v1:AAPL:%ZZ',
    'stocka:company-review:v1:AAPL:instrument-aapl:extra', 'stocka:company-review:v1:AAPL:instrument-unknown'])('rejects noncanonical/foreign key %s', key => {
    expect(parseSavedReview(key, JSON.stringify(draft()))).toBeNull();
  });
  it.each([{symbol:'MSFT'}, {instrumentId:'other'}, {version:2}, {snapshot:'bad'}, {nextDate:'2026-02-30'},
    {savedAt:''}, {checks:['approved']}, {unknown:true}])('never silently repairs incompatible stored data %s', patch => {
    expect(parseSavedReview(draftKey(draft()), JSON.stringify({...draft(), ...patch}))).toBeNull();
  });
  it('rejects malformed/oversized JSON', () => {
    expect(parseSavedReview(draftKey(draft()), '{')).toBeNull();
    expect(parseSavedReview(draftKey(draft()), 'x'.repeat(24001))).toBeNull();
  });
  it('keeps two instrument histories under one symbol separate', () => {
    const a = item(), b = item({instrumentId:'instrument-old'});
    expect(readReviewInbox(store(entries([a,b]))).notes).toHaveLength(2);
  });
});

describe('bounded read-only storage discovery', () => {
  it('never reads unrelated values or mutates storage', () => {
    const s = store([...entries([item()]), ['unrelated-secret', 'do not read']]);
    expect(readReviewInbox(s)).toMatchObject({state:'ready', notes:[item()], problems:[]});
    expect(s.getItem).toHaveBeenCalledTimes(1); expect(s.getItem).not.toHaveBeenCalledWith('unrelated-secret');
  });
  it('distinguishes complete empty storage from unavailable storage', () => {
    expect(readReviewInbox(store([]))).toEqual({state:'ready',notes:[],problems:[]});
    expect(readReviewInbox({get length(){throw Error('denied');}, key:()=>null, getItem:()=>null}).state).toBe('unavailable');
  });
  it('keeps valid notes beside corrupt and unsupported entries', () => {
    const s = store([...entries([item()]), ['stocka:company-review:v1:MSFT:instrument-msft','broken'], ['stocka:company-review:v2:SPY:instrument-spy','future']]);
    const result=readReviewInbox(s);expect(result.notes).toHaveLength(1);expect(result.problems.map(p=>p.reason)).toEqual(['invalid','unsupported']);
    expect(s.getItem('stocka:company-review:v1:MSFT:instrument-msft')).toBe('broken');
  });
  it('marks failed reads as partial rather than missing notes', () => {
    const s=store(entries([item(),item({symbol:'MSFT',instrumentId:'instrument-msft'})]));
    s.getItem=vi.fn(key=>{if(key.includes('MSFT'))throw Error('denied');return JSON.stringify(draft());});
    const result=readReviewInbox(s);expect(result.state).toBe('partial');expect(result.notes).toHaveLength(1);expect(result.problems[0].reason).toBe('unreadable');
  });
  it('detects a disappearing key during enumeration', () => {
    const s=store(entries([item()]));s.getItem=()=>null;expect(readReviewInbox(s).state).toBe('partial');
  });
  it('caps total key enumeration without probing unrelated values', () => {
    const s={length:3000,key:vi.fn(i=>`other-${i}`),getItem:vi.fn()};
    expect(readReviewInbox(s).state).toBe('partial');expect(s.key).toHaveBeenCalledTimes(INBOX_LIMITS.keys);expect(s.getItem).not.toHaveBeenCalled();
  });
  it('caps review count and labels exports as partial', () => {
    const notes=Array.from({length:201},(_,i)=>item({symbol:`S${i}`,instrumentId:`instrument-${i}`}));
    const result=readReviewInbox(store(entries(notes)));expect(result.notes).toHaveLength(200);expect(result.state).toBe('partial');
    expect(JSON.parse(exportInboxNotes(result)).completeRead).toBe(false);
  });
  it('caps cumulative parsed text independently of entry count', () => {
    const notes=Array.from({length:150},(_,i)=>item({symbol:`S${i}`,instrumentId:`instrument-${i}`,note:'a'.repeat(4000),opposition:'b'.repeat(3000),nextAction:'c'.repeat(2000)}));
    const result=readReviewInbox(store(entries(notes)));expect(result.state).toBe('partial');expect(result.notes.length).toBeLessThan(150);expect(result.notes.length).toBeGreaterThan(0);
  });
});

describe('user dates, literal search and notes-only export', () => {
  it.each([['2026-09-06','overdue'],['2026-09-07','today'],['2026-09-08','planned'],['','undated']])('classifies a directly chosen date %s', (date, expected) => {
    expect(dueBucket(date,'2026-09-07')).toBe(expected);
  });
  it('does not classify an unknown device date or invalid calendar date', () => {
    expect(dueBucket('2026-09-07','')).toBeNull();expect(dueBucket('2026-02-30','2026-09-07')).toBeNull();
    expect(localReviewDay(new Date(2026,8,7,0,10))).toBe('2026-09-07');expect(localReviewDay(new Date('bad'))).toBe('');
  });
  it('sorts dated notes before undated notes without mutating the source', () => {
    const notes=[item({symbol:'SPY',nextDate:''}),item({symbol:'MSFT',nextDate:'2026-09-09'}),item({symbol:'AAPL',nextDate:'2026-09-06'})];
    const before=JSON.stringify(notes);expect(filterSavedReviews(notes,'all','','2026-09-07').map(n=>n.draft.symbol)).toEqual(['AAPL','MSFT','SPY']);expect(JSON.stringify(notes)).toBe(before);
  });
  it('combines literal private search with date filters', () => {
    const notes=[item(),item({symbol:'MSFT',note:'literal [x]',nextDate:'2026-09-08'})];
    expect(filterSavedReviews(notes,'planned',' [x] ','2026-09-07').map(n=>n.draft.symbol)).toEqual(['MSFT']);
    expect(filterSavedReviews(notes,'today','[x]','2026-09-07')).toEqual([]);
    expect(filterSavedReviews(notes,'all','aapl','2026-09-07')).toHaveLength(1);
  });
  it('exports literal notes and saved IDs without inventing current company/source data', () => {
    const text=exportSavedReview(draft({note:'<script>bad()</script>\n# not a heading'}));
    expect(text).toContain('    <script>bad()</script>\n    # not a heading');expect(text).toContain('instrument-aapl');
    expect(text).toContain('최신 분석·원천은 포함하지');expect(text).not.toContain('Apple Inc.');expect(text).not.toContain('/source-documents/');
  });
  it('bulk export preserves original draft fields and excludes corrupt entries', () => {
    const result=readReviewInbox(store([...entries([item()]), ['stocka:company-review:v1:MSFT:instrument-msft','broken']]));
    const exported=JSON.parse(exportInboxNotes(result));expect(exported.notes).toEqual([draft()]);expect(exported.unreadableCount).toBe(1);expect(exported.scope).toBe('loaded-valid-notes-only');
  });
});
