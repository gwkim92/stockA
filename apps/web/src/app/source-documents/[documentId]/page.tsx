import { notFound } from "next/navigation";
import { loadReader } from "@/lib/research-reader-data";
import { sourceRouteIdentifier } from "@/lib/research-reader-model";
import { SourceReader } from "@/components/readers/SourceReader";
import { ReaderUnavailable } from "@/components/readers/ReaderFrame";
export const dynamic = "force-dynamic";
export const metadata = { title: "원천 문서 읽기" };
export default async function SourceDocumentPage({ params }: { params: Promise<{ documentId: string }> }) {
  const { documentId } = await params;
  const id = sourceRouteIdentifier(documentId);
  if (!id) notFound();
  const result = await loadReader("source", id);
  if (result.issue === "not-found" || result.issue === "identifier") notFound();
  return result.data ? <SourceReader data={result.data} /> : <ReaderUnavailable issue={result.issue} />;
}
