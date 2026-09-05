import { notFound } from 'next/navigation';
import { loadInterpretation } from '@/lib/company-evidence-data';
import { ReaderUnavailable } from '@/components/readers/ReaderFrame';
import { EvidenceWorkspace } from '@/components/evidence/EvidenceWorkspace';
export const dynamic = 'force-dynamic';
export const metadata = { title: '근거 해석 대조' };
export default async function EvidencePage({ params }: { params: Promise<{ evidenceId: string }> }) {
  const { evidenceId } = await params;
  const result = await loadInterpretation(evidenceId);
  if (result.issue === 'identifier' || result.issue === 'not-found') notFound();
  return result.data ? <EvidenceWorkspace data={result.data} /> : <ReaderUnavailable issue={result.issue} />;
}
