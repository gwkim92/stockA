import { notFound } from 'next/navigation';
import { loadTheme } from '@/lib/news-theme-data';
import type { SearchInput } from '@/lib/news-theme-model';
import { ThemeWorkspace } from '@/components/signals/ThemeWorkspace';
import { SignalError } from '@/components/signals/SignalShared';
export const dynamic = 'force-dynamic';
export const metadata = { title: '테마 검토' };
export default async function ThemePage({ params, searchParams }: { params: Promise<{ themeKey: string }>; searchParams: Promise<SearchInput> }) {
  const { themeKey } = await params;
  const result = await loadTheme(themeKey, await searchParams);
  if (result.issue === 'identifier' || result.issue === 'not-found') notFound();
  return result.data ? <ThemeWorkspace data={result.data} date={result.requestedDate} today={result.today} />
    : <div><h1>테마 검토</h1><SignalError issue={result.issue} home={`/themes/${encodeURIComponent(themeKey)}`} /></div>;
}
