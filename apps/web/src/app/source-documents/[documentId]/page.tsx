import Link from "next/link";
import { NewsTitleBlock } from "@/components/news-title-block";
import { getSourceDocumentDetail } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { SourceDocumentDetailData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "원천 문서" };

type SourceDocumentPageProps = {
  params: Promise<{ documentId: string }>;
};

type SourceExcerpt = SourceDocumentDetailData["excerpts"][number];

function isKnownCode(value: string | null | undefined) {
  return Boolean(value && value !== "UNKNOWN" && value !== "UNCLASSIFIED");
}

function hasHangul(value: string) {
  return /[가-힣]/.test(value);
}

function inferKoreanTopic(value: string) {
  const text = value.toLowerCase();
  if (/(quantum|qubit|rigetti|d-wave|ionq|qbts|qubt|ibm)/.test(text)) {
    return "양자컴퓨팅·정책 수혜";
  }
  if (/(fed|warsh|rate|rates|treasury|bond|yield|inflation|annuity)/.test(text)) {
    return "금리·연준";
  }
  if (/(oil|iran|hormuz|crude|energy|gas|xom|drilling)/.test(text)) {
    return "에너지·지정학";
  }
  if (/(nvidia|semiconductor|chip|qualcomm|skyworks|qorvo|tower semiconductor|tsem)/.test(text)) {
    return "AI 반도체 사이클";
  }
  if (/(s&p|nasdaq|dow|stock market|stocks|buffett indicator)/.test(text)) {
    return "미국 시장 참여도";
  }
  return "시장 뉴스 흐름";
}

function extractTitle(value: string) {
  return value.match(/Title:\s*(.*?)(?:\s+Summary:|$)/)?.[1]?.trim();
}

function extractSummary(value: string) {
  return value.match(/Summary:\s*(.*?)(?:\s+Published\/Event At:|$)/)?.[1]?.trim();
}

function sourceDocumentDigest(data: SourceDocumentDetailData) {
  if (data.korean_summary) {
    return data.korean_summary;
  }
  const target = isKnownCode(data.symbol) ? `${koCode(data.symbol)} 관련` : `${koCode(data.source_type)} 원천`;
  const topic = inferKoreanTopic(`${data.title} ${data.excerpts.map((excerpt) => excerpt.summary).join(" ")}`);
  return `${target} ${topic} 문서다. 영어 원문을 먼저 읽지 말고, 연결된 AI 근거와 발췌의 한국어 검토 요약으로 테마·종목·방향 해석이 맞는지 확인한다.`;
}

function sourceExcerptDigest(excerpt: SourceExcerpt, documentTitle: string) {
  const title = extractTitle(excerpt.summary) ?? documentTitle;
  const summary = extractSummary(excerpt.summary);
  const translated = koLabel(summary ?? title);
  if (hasHangul(translated) && translated !== summary && translated !== title) {
    return translated;
  }
  const topic = inferKoreanTopic(`${title} ${summary ?? ""}`);
  return `${topic} 관련 원천 발췌다. 제목과 세부 문장은 영어 원문에 보관되어 있고, 화면에서는 이 발췌가 어떤 테마 흐름으로 쓰였는지 먼저 확인한다.`;
}

export default async function SourceDocumentPage({ params }: SourceDocumentPageProps) {
  const { documentId } = await params;
  const response = await getSourceDocumentDetail(documentId);
  const data = response.data;
  const hasKoreanSummary = Boolean(data.korean_title || data.korean_summary);
  const firstEvidenceId = data.linked_evidence[0]?.evidence_id ?? null;
  const downloadStatus = data.access_policy.browser_download_enabled ? "원문 열람 가능" : "원문 열람 제한";

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          문서 • {data.symbol} • {data.form_type} • {data.period_end}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>원천 문서 검토서</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
              한국어 검토 요약을 먼저 보고, 필요할 때만 영어 원문 제목과 발췌를 펼쳐서 대조한다.
              이 화면은 뉴스가 어떤 AI 근거와 연결됐는지 확인하는 곳이다.
            </p>
          </div>
          
          <div style={{ 
            padding: "20px 32px", 
            background: data.access_policy.browser_download_enabled ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)", 
            border: `1px solid ${data.access_policy.browser_download_enabled ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)"}`,
            borderRadius: "var(--radius-md)",
            textAlign: "center"
          }}>
            <span className="metric-sub" style={{ color: data.access_policy.browser_download_enabled ? "var(--accent-green)" : "var(--accent-red)" }}>원문 다운로드</span>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0", textTransform: "uppercase" }}>
              {data.access_policy.browser_download_enabled ? "허용" : "차단"}
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: 500 }}>
              {koCode(data.source_type)}
            </div>
          </div>
        </div>
      </section>

      <section className="ai-evidence-command-panel reveal delay-1" aria-labelledby="source-command-title">
        <div className="ai-evidence-command-lead">
          <span>원천 문서 작업대</span>
          <h2 id="source-command-title">AI 해석의 출발점을 한국어로 먼저 대조한다.</h2>
          <p>
            이 문서는 추천을 승인하는 화면이 아니다. 원문 제목·요약, 발췌, 연결된 AI 근거를 확인해
            AI가 붙인 테마·종목·방향이 원천과 맞는지 검증하는 화면이다.
          </p>
        </div>
        <div className="ai-evidence-command-grid">
          <a className="ai-evidence-command-card ready" href="#source-document-summary">
            <span>01</span>
            <small>문서 요약</small>
            <strong>{koCode(data.source_type)}</strong>
            <em>{hasKoreanSummary ? "한국어 요약 있음" : "한국어 요약 추론"}</em>
            <p>영어 원문을 바로 읽기 전에 이 문서가 어떤 뉴스·테마 판단에 쓰였는지 먼저 확인한다.</p>
            <b>문서 요약 보기</b>
          </a>
          <a className="ai-evidence-command-card watch" href="#source-document-excerpts">
            <span>02</span>
            <small>검토 발췌</small>
            <strong>{data.excerpts.length}개 발췌</strong>
            <em>영어 원문은 펼쳐서 대조</em>
            <p>화면은 한국어 검토 요약을 먼저 보여주고, 필요한 경우에만 원문 발췌를 펼쳐 확인한다.</p>
            <b>발췌 보기</b>
          </a>
          <a className="ai-evidence-command-card ready" href="#linked-ai-evidence">
            <span>03</span>
            <small>AI 근거 연결</small>
            <strong>{data.linked_evidence.length}개 근거</strong>
            <em>{firstEvidenceId ? "상세 연결 가능" : "연결 근거 없음"}</em>
            <p>연결된 AI 근거 상세에서 원천, 번역, 구조화, 자동 검증, 추천 연결을 이어서 본다.</p>
            <b>AI 근거 보기</b>
          </a>
          <a
            className={data.access_policy.browser_download_enabled ? "ai-evidence-command-card ready" : "ai-evidence-command-card block"}
            href="#source-access-policy"
          >
            <span>04</span>
            <small>접근 정책</small>
            <strong>{downloadStatus}</strong>
            <em>{koCode(data.access_policy.reason)}</em>
            <p>다운로드 가능 여부는 원천 접근 정책일 뿐이다. 이 화면에서 추천 승인이나 주문 처리는 하지 않는다.</p>
            <b>접근 정책 보기</b>
          </a>
        </div>
      </section>

      <section className="source-review-panel reveal delay-1" aria-labelledby="source-review-title">
        <div>
          <span>한국어 검토 요약</span>
          <h2 id="source-review-title">영어 원문을 읽기 전에 이 문서가 무엇에 쓰였는지 먼저 확인한다</h2>
          <p>{sourceDocumentDigest(data)}</p>
        </div>
        <aside>
          <strong>{data.linked_evidence.length}</strong>
          <span>연결된 AI 근거</span>
          <p>근거 상세에서 종목·테마·방향 해석이 맞는지 이어서 확인한다.</p>
        </aside>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card span-2" id="source-document-summary" style={{ background: "var(--bg-card-hover)", borderColor: "var(--border-focus)" }}>
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">문서</span>
            <NewsTitleBlock
              title={data.title}
              summary={sourceDocumentDigest(data)}
              koreanTitle={data.korean_title}
              koreanSummary={data.korean_summary}
              translationConfidence={data.translation_confidence}
              symbol={data.symbol}
            />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div>
              <span className="metric-sub">문서 식별자</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500, fontFamily: "monospace" }}>{data.document_id}</div>
            </div>
            <div>
              <span className="metric-sub">접수번호</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500, fontFamily: "monospace" }}>{data.accession_id}</div>
            </div>
            <div>
              <span className="metric-sub">게시자</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>{data.publisher}</div>
            </div>
            <div>
              <span className="metric-sub">공시 시각</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>{data.filed_at}</div>
            </div>
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">수집 출처</span>
            <h2 style={{ fontSize: "1.5rem" }}>{data.retrieval.parser_version}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div>
              <span className="metric-sub">수집 실행</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500, fontFamily: "monospace" }}>{data.retrieval.source_run_id}</div>
            </div>
            <div>
              <span className="metric-sub">수집 시각</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>{data.retrieval.fetched_at}</div>
            </div>
            <div style={{ gridColumn: "span 2" }}>
              <span className="metric-sub">저장 경로</span>
              <div style={{ fontSize: "0.85rem", fontWeight: 500, fontFamily: "monospace", color: "var(--text-secondary)", wordBreak: "break-all" }}>{data.storage_uri}</div>
            </div>
            <div style={{ gridColumn: "span 2" }}>
              <span className="metric-sub">체크섬</span>
              <div style={{ fontSize: "0.85rem", fontWeight: 500, fontFamily: "monospace", color: "var(--text-secondary)", wordBreak: "break-all" }}>{data.checksum}</div>
            </div>
          </div>
        </article>

        <article className="bento-card span-2 row-span-2" id="source-document-excerpts">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">검토된 발췌</span>
            <h2 style={{ fontSize: "1.5rem" }}>검토 발췌 목록</h2>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", overflowY: "auto" }}>
            {data.excerpts.length === 0 ? (
              <p className="empty-state">이 문서에는 아직 화면에 노출할 검토 발췌가 없다.</p>
            ) : null}
            {data.excerpts.map((excerpt) => (
              <div key={excerpt.chunk_id} style={{
                padding: "16px",
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-light)",
                borderRadius: "var(--radius-sm)"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <strong style={{ fontSize: "1rem", color: "var(--text-primary)" }}>{koLabel(excerpt.section)}</strong>
                  <span className="bento-badge" style={{ margin: 0, padding: "2px 8px", fontSize: "0.65rem" }}>{excerpt.locator}</span>
                </div>
                <p className="source-korean-digest">{sourceExcerptDigest(excerpt, data.title)}</p>
                <details className="news-original-title source-original-detail">
                  <summary>영어 원문 발췌 보기</summary>
                  <p>{excerpt.summary}</p>
                </details>
                <span style={{ fontSize: "0.7rem", color: "var(--text-tertiary)", fontFamily: "monospace" }}>ID: {excerpt.chunk_id}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="bento-card span-2" id="linked-ai-evidence">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">연결된 증거</span>
            <h2 style={{ fontSize: "1.5rem" }}>AI 증거 연결</h2>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "24px" }}>
            {data.linked_evidence.length === 0 ? (
              <p className="empty-state">이 원천 문서에 연결된 AI 근거가 아직 없다.</p>
            ) : null}
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
                <span className="metric-sub">{koCode(evidence.evidence_type)}</span>
                <NewsTitleBlock
                  compact
                  title={evidence.title}
                  summary={`${koCode(evidence.evidence_type)}로 연결된 원천 근거다. 상세 화면에서 종목·테마·방향 해석을 확인한다.`}
                  symbol={data.symbol}
                />
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
          <div id="source-access-policy" style={{ padding: "12px 16px", background: "rgba(255,255,255,0.05)", borderRadius: "var(--radius-sm)", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
            <span className="metric-sub" style={{ display: "block", marginBottom: "4px" }}>접근 정책 메모</span>
            {koLabel(data.access_policy.reason)}
          </div>
        </article>
      </section>
    </div>
  );
}
