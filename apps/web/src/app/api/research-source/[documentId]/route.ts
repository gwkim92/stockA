import { loadReader } from "@/lib/research-reader-data";
import { sourceRouteIdentifier } from "@/lib/research-reader-model";
export const dynamic = "force-dynamic";
/** Same validated read projection as the existing source page; never forward internal storage or tokens. */
export async function GET(_request: Request, context: { params: Promise<{ documentId: string }> }) {
  const id = sourceRouteIdentifier((await context.params).documentId);
  const headers = { "Cache-Control": "private, no-store" };
  if (!id) return Response.json({ error: "invalid_identifier" }, { status: 400, headers });
  const result = await loadReader("source", id);
  if (!result.data) return Response.json({ error: "source_unavailable" }, { status: result.issue === "not-found" ? 404 : 502, headers });
  return Response.json({ data: result.data }, { headers });
}
