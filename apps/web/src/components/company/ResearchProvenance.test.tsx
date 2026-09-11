import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ResearchProvenance } from './ResearchProvenance';

vi.mock('@/components/research/SourcePeek', () => ({ SourcePeek: ({ label }: { label: string }) => <button>{label}</button> }));
afterEach(cleanup);

describe('report source review', () => {
  const research = { provider: 'codex_oauth', model_name: 'gpt-5.6-terra', generation: { mode: 'ai', structural_status: 'complete' } };
  it('keeps structural completeness separate from unreviewed content', () => {
    render(<ResearchProvenance research={research} />);
    expect(screen.getByText('AI 생성 보고서 · 내용 검토 미기록')).toBeTruthy();
    expect(screen.queryByRole('region', { name: '보고서 원천 검토 결과' })).toBeNull();
  });
  it('opens verified audit issues with source links and no approval claim', () => {
    render(<ResearchProvenance research={{ ...research, content_review: {
      status: 'needs_source_correction', summary: '재무 선택 오류', reviewed_at: '2026-09-11', reviewer: 'AI 보조 원문 대조',
      limitations: '투자 판단 승인이 아닙니다.', findings: [{ title: '원천 확인', detail: '주식 수 일자와 결산일이 다릅니다.', source_url: 'https://www.sec.gov/filing', source_label: '공시 원문' }],
    } }} />);
    expect(screen.getByText('원천 검토 · 보완 필요').closest('details')?.open).toBe(true);
    fireEvent.click(screen.getByText('검토 항목 1개와 원문'));
    expect(screen.getByRole('link', { name: '공시 원문 ↗' }).getAttribute('href')).toBe('https://www.sec.gov/filing');
    expect(screen.getByText('투자 판단 승인이 아닙니다.')).toBeTruthy();
  });
  it('rejects unsafe review URLs while retaining findings', () => {
    render(<ResearchProvenance research={{ ...research, content_review: { status: 'needs_source_correction', findings: [{ title: '문제', source_url: 'javascript:alert(1)' }] } }} />);
    expect(screen.getByText('문제')).toBeTruthy();
    expect(screen.queryByRole('link', { hidden: true })).toBeNull();
  });
  it('opens a changed-source warning without presenting the old report as current', () => {
    render(<ResearchProvenance research={{ ...research, financial_source_freshness: { status: 'source_changed' } }} />);
    expect(screen.getByRole('status').textContent).toContain('갱신 전 자료');
    expect(screen.getByRole('status').closest('details')?.open).toBe(true);
    expect(screen.queryByText('보고서의 재무 입력 버전이 현재 수집 자료와 일치합니다.', { exact: false })).toBeNull();
  });
  it('limits a version match to financial inputs and retains content review uncertainty', () => {
    render(<ResearchProvenance research={{ ...research, financial_source_freshness: { status: 'current' } }} />);
    expect(screen.getByText(/재무 입력 버전이 현재 수집 자료와 일치/).textContent).toContain('다른 자료의 최신성');
    expect(screen.getByText('AI 생성 보고서 · 내용 검토 미기록')).toBeTruthy();
  });
});
