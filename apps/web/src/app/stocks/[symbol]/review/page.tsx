import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { loadCompany } from '@/lib/company-evidence-data';
import { reviewModel } from '@/lib/company-review-model';
import { reviewSnapshot } from '@/lib/company-review-data';
import { ReaderUnavailable } from '@/components/readers/ReaderFrame';
import { ReviewNotebook } from '@/components/review/ReviewNotebook';
import { ReviewSource } from '@/components/review/ReviewSource';
export const dynamic = 'force-dynamic';
export const metadata = { title: '기업 검토 노트' };
export default async function ReviewPage({ params, searchParams }: {
  params: Promise<{ symbol: string }>; searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [{ symbol }, query] = await Promise.all([params, searchParams]);
  const result = await loadCompany(symbol);
  if (result.issue === 'identifier' || result.issue === 'not-found') notFound();
  if (!result.data) return <ReaderUnavailable issue={result.issue} />;
  const model = reviewModel(result.data), snapshot = reviewSnapshot(model);
  return <ReviewNotebook key={`${model.instrumentId}:${model.symbol}`} model={model} snapshot={snapshot} source={query.source}
    sourcePanel={<Suspense key={JSON.stringify(query.source ?? null)} fallback={<p role="status">선택한 원천을 불러오는 중입니다. 메모는 계속 작성할 수 있습니다.</p>}>
      <ReviewSource model={model} requested={query.source} />
    </Suspense>} />;
}
