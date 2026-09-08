import { EvaluationHistory } from '@/components/review/EvaluationHistory';
import { loadEvaluationHistory } from '@/lib/evaluation-history';
export const dynamic = 'force-dynamic';
export const metadata = { title: '추천 평가 이력' };
export default async function Page({ searchParams }: { searchParams: Promise<{ before?: string | string[] }> }) {
  return <EvaluationHistory result={await loadEvaluationHistory({ cursor: (await searchParams).before })} />;
}
