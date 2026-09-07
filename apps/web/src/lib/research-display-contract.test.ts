// @vitest-environment node
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { parseCompany } from './company-evidence-model';
import { reviewModel } from './company-review-model';
import { reviewSnapshot } from './company-review-data';
import { projectResearchForReader, researchDisplayIssue } from './research-display-contract';

// Actual Python producer, with synthetic stored inputs and denied external IO.
// This is not a hand-written approximation of its JSON response.
const produced = JSON.parse(execFileSync('python3', ['tests/contracts/research-producer.py'], {
  encoding: 'utf8', timeout: 15000, maxBuffer: 1000000,
}));
const example = JSON.parse(readFileSync('../../docs/api/frontend/examples/stock-detail.json', 'utf8'));
function company(research: unknown) {
  return parseCompany({ ...example, data: { ...example.data, equity_research: research, recent_events: [], macro_flow_impacts: [] } }, 'AAPL');
}
describe('actual Python research payload to TypeScript reader', () => {
  it('preserves normal claims, exact source identifiers and zero sensitivity', () => {
    const result = company(produced.valid), view = reviewModel(result);
    expect(result.research.valuation_sensitivity).toEqual({ confidence: 0 });
    expect(view.groups[0].items).toEqual(['정상 주장']);
    expect(view.sources.map(item => item.id)).toEqual(['source-document-7001', 'source-document-7002']);
    expect(view.researchIssue).toBeUndefined();
  });
  it('does not reconstitute a rejected list as successful empty research', () => {
    const result = company(produced.malformed), view = reviewModel(result);
    expect(result.research.key_points).toBeNull();
    expect(view.groups[0].items).toBeNull();
    expect(view.sources).toEqual([]);
    expect(view.researchIssue?.invalid).toEqual(['key_points', 'source_document_ids']);
    expect(JSON.stringify(view)).not.toContain('synthetic-object');
    expect(JSON.stringify(view)).not.toContain('valid fragment');
    expect(JSON.stringify(view)).not.toContain('source-document-True');
  });
  it('keeps a genuinely empty list different from a missing list', () => {
    expect(reviewModel(company(produced.empty)).groups[0].items).toEqual([]);
    const partial = reviewModel(company(produced.partial));
    expect(partial.groups.find(group => group.key === 'risks')?.items).toBeNull();
    expect(partial.researchIssue?.unavailable).toEqual(['risks']);
  });
  it('adding complete producer metadata does not invalidate an otherwise unchanged saved draft', () => {
    const legacy = { ...produced.valid }; delete legacy.data_quality;
    expect(reviewSnapshot(reviewModel(company(legacy)))).toBe(reviewSnapshot(reviewModel(company(produced.valid))));
  });
  it('a change from malformed to valid records does change the displayed basis', () => {
    expect(reviewSnapshot(reviewModel(company(produced.malformed)))).not.toBe(reviewSnapshot(reviewModel(company(produced.valid))));
  });
});
describe('display-quality metadata validation', () => {
  it('does not invent a validation claim for legacy responses', () => {
    const raw = { key_points: ['legacy'] };
    expect(projectResearchForReader(raw)).toBe(raw);
    expect(researchDisplayIssue(raw)).toBeNull();
  });
  it.each([null, {}, { policy: 'other' },
    { policy: 'equity_display_contract_v1', status: 'complete', invalid_fields: ['key_points'], unavailable_fields: [] },
    { policy: 'equity_display_contract_v1', status: 'invalid_fields', invalid_fields: ['key_points'], unavailable_fields: ['key_points'] },
    { policy: 'equity_display_contract_v1', status: 'invalid_fields', invalid_fields: ['secret-source-body'], unavailable_fields: [] },
  ])('rejects malformed status metadata without echoing arbitrary field names', data_quality => {
    const raw = { key_points: ['not authorized by this status'], source_document_ids: ['source-document-1'], data_quality };
    const result = projectResearchForReader(raw);
    expect(result.key_points).toBeNull();
    expect(result.source_document_ids).toBeNull();
    expect(researchDisplayIssue(raw)?.metadataInvalid).toBe(true);
    expect(JSON.stringify(researchDisplayIssue(raw))).not.toContain('secret-source-body');
  });
  it('does not mutate the API response when projecting unavailable fields', () => {
    const before = JSON.stringify(produced.partial);
    projectResearchForReader(produced.partial);
    expect(JSON.stringify(produced.partial)).toBe(before);
  });
});
