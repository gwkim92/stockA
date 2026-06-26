import Link from "next/link";

import { koCode } from "@/lib/korean-labels";
import type { AiEvidenceNeighborhoodData } from "@/lib/types";

import { evidenceChunkPreview, stockEventSourceDocumentHref } from "./stock-evidence-format";

type StockEvidenceSourceSectionProps = {
  readonly neighborhood: AiEvidenceNeighborhoodData;
};

export function StockEvidenceSourceSection({ neighborhood }: StockEvidenceSourceSectionProps) {
  return (
    <section className="stock-evidence-section" aria-label={`${neighborhood.symbol} 저장된 원문 근거`}>
      <div className="stock-evidence-section-head">
        <div>
          <span>원천 대조</span>
          <h3>투자 근거가 참조한 원문</h3>
        </div>
        <p>본문 추출 여부와 출처를 먼저 보여준다. 영어 원문은 필요할 때만 연다.</p>
      </div>
      <div className="stock-source-card-grid">
        {neighborhood.evidence_chunks.slice(0, 4).map((chunk) => {
          const document = stockEventSourceDocumentHref(chunk.source_document_id);
          const sourceKind =
            chunk.source_text_kind === "raw_html_text"
              ? "원문 본문 추출"
              : chunk.used_metadata_fallback
                ? "본문 부족, 문서 정보 대체"
                : "추출 상태 미확인";
          return (
            <article className="stock-source-card" key={chunk.chunk_id}>
              <span>{chunk.used_metadata_fallback ? "요약 정보 기반" : "원문 본문 기반"}</span>
              <strong>{evidenceChunkPreview(chunk.text_preview)}</strong>
              <p>{chunk.source_url_host || "출처 없음"} · {sourceKind} · 근거 저장 상태 {koCode(chunk.embedding_status)}</p>
              {document ? <Link href={document}>원천 문서 열기</Link> : null}
            </article>
          );
        })}
        {neighborhood.evidence_chunks.length === 0 ? (
          <p className="stock-evidence-empty">아직 이 종목에 연결된 원문 근거가 없다.</p>
        ) : null}
      </div>
    </section>
  );
}
