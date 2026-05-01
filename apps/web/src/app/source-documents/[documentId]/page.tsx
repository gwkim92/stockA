import Link from "next/link";
import { getSourceDocumentDetail } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "Source Document" };

type SourceDocumentPageProps = {
  params: Promise<{ documentId: string }>;
};

export default async function SourceDocumentPage({ params }: SourceDocumentPageProps) {
  const { documentId } = await params;
  const response = await getSourceDocumentDetail(documentId);
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          DOC • {data.symbol} • {data.form_type} • {data.period_end}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>Source Document Dossier</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
              Source documents stay outside the browser bundle. This route exposes only the metadata and reviewed excerpts needed to audit a stored evidence object.
            </p>
          </div>
          
          <div style={{ 
            padding: "20px 32px", 
            background: data.access_policy.browser_download_enabled ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)", 
            border: `1px solid ${data.access_policy.browser_download_enabled ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)"}`,
            borderRadius: "var(--radius-md)",
            textAlign: "center"
          }}>
            <span className="metric-sub" style={{ color: data.access_policy.browser_download_enabled ? "var(--accent-green)" : "var(--accent-red)" }}>Raw Download</span>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0", textTransform: "uppercase" }}>
              {data.access_policy.browser_download_enabled ? "Enabled" : "Blocked"}
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: 500 }}>
              {data.source_type}
            </div>
          </div>
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card span-2" style={{ background: "var(--bg-card-hover)", borderColor: "var(--border-focus)" }}>
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Document</span>
            <h2 style={{ fontSize: "1.5rem" }}>{data.title}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div>
              <span className="metric-sub">Document ID</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500, fontFamily: "monospace" }}>{data.document_id}</div>
            </div>
            <div>
              <span className="metric-sub">Accession</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500, fontFamily: "monospace" }}>{data.accession_id}</div>
            </div>
            <div>
              <span className="metric-sub">Publisher</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>{data.publisher}</div>
            </div>
            <div>
              <span className="metric-sub">Filed At</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>{data.filed_at}</div>
            </div>
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Retrieval Provenance</span>
            <h2 style={{ fontSize: "1.5rem" }}>{data.retrieval.parser_version}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div>
              <span className="metric-sub">Source Run</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500, fontFamily: "monospace" }}>{data.retrieval.source_run_id}</div>
            </div>
            <div>
              <span className="metric-sub">Fetched At</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>{data.retrieval.fetched_at}</div>
            </div>
            <div style={{ gridColumn: "span 2" }}>
              <span className="metric-sub">Storage URI</span>
              <div style={{ fontSize: "0.85rem", fontWeight: 500, fontFamily: "monospace", color: "var(--text-secondary)", wordBreak: "break-all" }}>{data.storage_uri}</div>
            </div>
            <div style={{ gridColumn: "span 2" }}>
              <span className="metric-sub">Checksum</span>
              <div style={{ fontSize: "0.85rem", fontWeight: 500, fontFamily: "monospace", color: "var(--text-secondary)", wordBreak: "break-all" }}>{data.checksum}</div>
            </div>
          </div>
        </article>

        <article className="bento-card span-2 row-span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Reviewed Excerpts</span>
            <h2 style={{ fontSize: "1.5rem" }}>Chunk Ledger</h2>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", overflowY: "auto" }}>
            {data.excerpts.map((excerpt) => (
              <div key={excerpt.chunk_id} style={{
                padding: "16px",
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-light)",
                borderRadius: "var(--radius-sm)"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <strong style={{ fontSize: "1rem", color: "var(--text-primary)" }}>{excerpt.section}</strong>
                  <span className="bento-badge" style={{ margin: 0, padding: "2px 8px", fontSize: "0.65rem" }}>{excerpt.locator}</span>
                </div>
                <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: 1.5, margin: "0 0 12px 0" }}>{excerpt.summary}</p>
                <span style={{ fontSize: "0.7rem", color: "var(--text-tertiary)", fontFamily: "monospace" }}>ID: {excerpt.chunk_id}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Linked Evidence</span>
            <h2 style={{ fontSize: "1.5rem" }}>AI Extraction Path</h2>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "24px" }}>
            {data.linked_evidence.map((evidence) => (
              <div key={evidence.evidence_id} style={{
                padding: "16px",
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-light)",
                borderRadius: "var(--radius-sm)",
                display: "flex",
                flexDirection: "column",
                gap: "4px"
              }}>
                <span className="metric-sub">{evidence.evidence_type}</span>
                <strong style={{ fontSize: "1rem" }}>{evidence.title}</strong>
                <Link href={`/ai-evidence/${evidence.evidence_id}`} style={{
                  color: "var(--accent-blue)",
                  fontSize: "0.85rem",
                  textDecoration: "underline",
                  textUnderlineOffset: "3px",
                  marginTop: "4px",
                  width: "fit-content"
                }}>
                  {evidence.evidence_id}
                </Link>
              </div>
            ))}
          </div>
          <div style={{ padding: "12px 16px", background: "rgba(255,255,255,0.05)", borderRadius: "var(--radius-sm)", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
            <span className="metric-sub" style={{ display: "block", marginBottom: "4px" }}>Access Policy Note</span>
            {data.access_policy.reason}
          </div>
        </article>
      </section>
    </div>
  );
}
