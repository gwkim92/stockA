import { EvaluationHistory } from '@/components/review/EvaluationHistory';
import { loadEvaluationHistory } from '@/lib/evaluation-history';
export const dynamic = 'force-dynamic';
export const metadata = { title: '평가 기록 비교' };
export default async function Page({ params, searchParams }: { params: Promise<{ runId: string }>; searchParams: Promise<{ after?: string | string[] }> }) {
  return <EvaluationHistory detail result={await loadEvaluationHistory({ runId: (await params).runId, cursor: (await searchParams).after })} />;
}
