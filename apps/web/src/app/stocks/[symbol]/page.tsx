import { notFound } from 'next/navigation';
import { loadCompany } from '@/lib/company-evidence-data';
import { ReaderUnavailable } from '@/components/readers/ReaderFrame';
import { CompanyWorkspace } from '@/components/company/CompanyWorkspace';
export const dynamic = 'force-dynamic';
export const metadata = { title: '기업 리서치' };
export default async function StockPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const result = await loadCompany(symbol);
  if (result.issue === 'identifier' || result.issue === 'not-found') notFound();
  return result.data ? <CompanyWorkspace data={result.data} /> : <ReaderUnavailable issue={result.issue} />;
}
