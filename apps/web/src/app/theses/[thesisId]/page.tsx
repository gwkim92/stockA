import { notFound } from "next/navigation";
import { loadReader } from "@/lib/research-reader-data";
import { ThesisReader } from "@/components/readers/ThesisReader";
import { ReaderUnavailable } from "@/components/readers/ReaderFrame";
export const dynamic = "force-dynamic";
export const metadata = { title: "투자 논리" };
export default async function ThesisPage({ params }: { params: Promise<{ thesisId: string }> }) {
  const { thesisId } = await params;
  const result = await loadReader("thesis", thesisId);
  if (result.issue === "not-found" || result.issue === "identifier") notFound();
  return result.data ? <ThesisReader data={result.data} today={result.today} /> : <ReaderUnavailable issue={result.issue} />;
}
