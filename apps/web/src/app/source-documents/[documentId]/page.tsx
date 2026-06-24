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

function sourceTypeLabel(data: SourceDocumentDetailData) {
  return koCode(data.form_type || data.source_type || "news_rss_item");
}

function sourceDocumentKicker(data: SourceDocumentDetailData) {
  const subject = isKnownCode(data.symbol) ? `${koCode(data.symbol)} 원천` : "시장 뉴스 문서";
  return [subject, sourceTypeLabel(data), data.period_end].filter(Boolean).join(" · ");
}

function sourceDocumentDigest(data: SourceDocumentDetailData) {
  if (data.korean_summary) {
    return data.korean_summary;
  }
  const target = isKnownCode(data.symbol) ? `${koCode(data.symbol)} 관련` : sourceTypeLabel(data);
  const topic = inferKoreanTopic(`${data.title} ${data.excerpts.map((excerpt) => excerpt.summary).join(" ")}`);
  return `${target} ${topic} 문서다. 영어 원문을 먼저 읽기 전에 연결된 투자 근거와 발췌 요약으로 테마·종목·방향 해석이 맞는지 확인한다.`;
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

function recordStatus(value: string | null | undefined, presentLabel: string) {
  return value ? presentLabel : "기록 없음";
}

function retrievalSourceLabel(parserVersion: string | null | undefined, sourceType: string | null | undefined) {
  const text = `${parserVersion ?? ""} ${sourceType ?? ""}`.toLowerCase();
  if (text.includes("sec")) {
    return "SEC 공시 원문 수집";
  }
  if (text.includes("rss") || text.includes("news")) {
    return "뉴스 원문 수집";
  }
  return "원천 문서 수집";
}

function chunkLabel(chunkId: string, index: number) {
  const text = chunkId.toLowerCase();
  if (text.includes("business")) {
    return "사업 개요 근거";
  }
  if (text.includes("mdna")) {
    return "경영진 논의 근거";
  }
  if (text.includes("risk")) {
    return "위험 요인 근거";
  }
  if (text.includes("financial")) {
    return "재무 근거";
  }
  return `근거 발췌 ${index + 1}`;
}

function accessPolicyReasonLabel(value: string | null | undefined) {
  const text = `${value ?? ""}`.toLowerCase();
  if (text.includes("auth") || text.includes("rbac") || text.includes("access")) {
    return "현재는 원문 원격 다운로드를 열지 않고, 저장된 제목·요약·발췌만 화면에서 확인한다.";
  }
  return koLabel(value ?? "");
}

export default async function SourceDocumentPage({ params }: SourceDocumentPageProps) {
  const { documentId } = await params;
  const response = await getSourceDocumentDetail(documentId);
  const data = response.data;
  const hasKoreanSummary = Boolean(data.korean_title || data.korean_summary);
  const firstEvidenceId = data.linked_evidence[0]?.evidence_id ?? null;
  const downloadStatus = data.access_policy.browser_download_enabled ? "원문 열람 가능" : "원문 열람 제한";
  const retrievalLabel = retrievalSourceLabel(data.retrieval.parser_version, data.source_type);

  return (
    <div className="pageStack decision-page">
      <section className="decision-brief reveal" aria-labelledby="source-command-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">
            {sourceDocumentKicker(data)}
          </span>
          <h1 className="decision-brief-title" id="source-command-title">
            이 원천이 어떤 투자 근거가 됐는지 먼저 확인한다.
          </h1>
          <p className="decision-brief-copy">
            원문 제목·요약, 발췌, 연결된 투자 근거를 대조해 테마·종목·방향 해석이 원천과 맞는지 확인한다.
          </p>
          <div className="decision-brief-meta" aria-label="원천 문서 핵심 상태">
            <span>원문 열람 {data.access_policy.browser_download_enabled ? "허용" : "차단"}</span>
            <span>발췌 {data.excerpts.length.toLocaleString("ko-KR")}개</span>
            <span>투자 근거 {data.linked_evidence.length.toLocaleString("ko-KR")}개</span>
            <span>{sourceTypeLabel(data)}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <a className="decision-card is-good" href="#source-document-summary">
            <span>문서 요약</span>
            <strong>{sourceTypeLabel(data)}</strong>
            <small>{hasKoreanSummary ? "한국어 요약 있음" : "한국어 요약 추론"} · 어떤 뉴스·테마 판단에 쓰였는지 먼저 확인한다.</small>
            <b>문서 요약 보기</b>
          </a>
          <a className="decision-card is-watch" href="#source-document-excerpts">
            <span>근거 발췌</span>
            <strong>{data.excerpts.length.toLocaleString("ko-KR")}개 발췌</strong>
            <small>필요한 경우에만 영어 원문 발췌를 펼쳐 대조한다.</small>
            <b>발췌 보기</b>
          </a>
          <a className="decision-card is-good" href="#linked-ai-evidence">
            <span>투자 근거 연결</span>
            <strong>{data.linked_evidence.length.toLocaleString("ko-KR")}개 근거</strong>
            <small>{firstEvidenceId ? "상세 연결 가능" : "연결 근거 없음"} · 원천, 번역, 구조화, 검증을 이어서 본다.</small>
            <b>투자 근거 보기</b>
          </a>
          <a
            className={data.access_policy.browser_download_enabled ? "decision-card is-good" : "decision-card is-block"}
            href="#source-access-policy"
          >
            <span>접근 정책</span>
            <strong>{downloadStatus}</strong>
            <small>{accessPolicyReasonLabel(data.access_policy.reason)} · 추천 채택이나 주문 처리는 하지 않는다.</small>
            <b>접근 정책 보기</b>
          </a>
        </div>
      </section>

      <section className="source-review-panel reveal delay-1" aria-labelledby="source-review-title">
        <div>
          <span>한국어 근거 요약</span>
          <h2 id="source-review-title">영어 원문을 읽기 전에 이 문서가 무엇에 쓰였는지 먼저 확인한다</h2>
          <p>{sourceDocumentDigest(data)}</p>
        </div>
        <aside>
          <strong>{data.linked_evidence.length}</strong>
          <span>연결된 투자 근거</span>
          <p>근거 상세에서 종목·테마·방향 해석이 맞는지 이어서 확인한다.</p>
        </aside>
      </section>

      <section className="source-document-workbench reveal delay-1">
        <article className="source-document-summary-card" id="source-document-summary">
          <div className="source-document-card-head">
            <span>문서 요약</span>
            <h2>이 원천이 어떤 판단에 쓰였는지 확인한다</h2>
          </div>
          <div className="source-document-title-card">
            <NewsTitleBlock
              title={data.title}
              summary={sourceDocumentDigest(data)}
              koreanTitle={data.korean_title}
              koreanSummary={data.korean_summary}
              translationConfidence={data.translation_confidence}
              symbol={data.symbol}
            />
          </div>
          <div className="source-document-fact-grid">
            <article>
              <span>문서 기록</span>
              <strong>{recordStatus(data.document_id, "기록 있음")}</strong>
              <p>추적 가능한 원천 문서로 저장되어 있다.</p>
            </article>
            <article>
              <span>접수 기록</span>
              <strong>{recordStatus(data.accession_id, "접수 기록 있음")}</strong>
              <p>공시 문서는 접수번호, 뉴스 문서는 원천 식별자로 추적한다.</p>
            </article>
            <article>
              <span>게시자</span>
              <strong>{koLabel(data.publisher)}</strong>
              <p>{data.filed_at || "게시 시각 미기록"}</p>
            </article>
            <article>
              <span>분석 연결</span>
              <strong>{data.linked_evidence.length.toLocaleString("ko-KR")}개 투자 근거</strong>
              <p>연결된 투자 근거에서 테마·종목·방향 해석을 다시 대조한다.</p>
            </article>
          </div>
          <details className="secondary-details source-document-technical-detail">
            <summary>
              <span>기술 식별자 보기</span>
              <strong>감사용 식별자는 접어서 보관한다</strong>
            </summary>
            <div className="details-inner">
              <p>문서 ID: {data.document_id}</p>
              <p>접수번호: {data.accession_id || "없음"}</p>
            </div>
          </details>
        </article>

        <article className="source-document-summary-card">
          <div className="source-document-card-head">
            <span>수집 상태</span>
            <h2>{retrievalLabel}</h2>
          </div>
          <div className="source-document-fact-grid compact">
            <article>
              <span>수집 상태</span>
              <strong>{recordStatus(data.retrieval.source_run_id, "수집 기록 있음")}</strong>
              <p>수집 실행이 남아 있어 문제가 생기면 역추적할 수 있다.</p>
            </article>
            <article>
              <span>수집 시각</span>
              <strong>{data.retrieval.fetched_at || "미기록"}</strong>
              <p>이 시점의 원천 내용으로 투자 근거가 만들어졌다.</p>
            </article>
            <article>
              <span>원문 저장</span>
              <strong>{recordStatus(data.storage_uri, "원문 저장됨")}</strong>
              <p>화면은 원문 전문 대신 필요한 요약과 발췌를 먼저 보여준다.</p>
            </article>
            <article>
              <span>무결성</span>
              <strong>{recordStatus(data.checksum, "검증 기록 있음")}</strong>
              <p>원천 파일 변경 여부를 감사할 수 있는 기록이다.</p>
            </article>
          </div>
          <details className="secondary-details source-document-technical-detail">
            <summary>
              <span>수집 기술 정보 보기</span>
              <strong>수집기·저장 위치·검증값</strong>
            </summary>
            <div className="details-inner">
              <p>수집기: {data.retrieval.parser_version || "없음"}</p>
              <p>수집 실행: {data.retrieval.source_run_id || "없음"}</p>
              <p>저장 위치: {data.storage_uri || "없음"}</p>
              <p>체크섬: {data.checksum || "없음"}</p>
            </div>
          </details>
        </article>
      </section>

      <section className="source-document-section reveal delay-2" id="source-document-excerpts" aria-labelledby="source-document-excerpts-title">
        <div className="source-document-section-head">
          <span>근거 발췌</span>
          <h2 id="source-document-excerpts-title">판단에 쓰인 원문 조각을 한국어 흐름으로 확인한다</h2>
          <p>영어 전문은 필요할 때만 펼친다. 기본 표시는 이 발췌가 어떤 투자 흐름 판단에 쓰였는지 보여준다.</p>
        </div>
        <div className="source-excerpt-card-grid">
          {data.excerpts.length === 0 ? (
            <p className="empty-state">이 문서에는 아직 화면에 노출할 근거 발췌가 없다.</p>
          ) : null}
          {data.excerpts.map((excerpt, index) => {
            const label = chunkLabel(excerpt.chunk_id, index);
            return (
              <article className="source-excerpt-card" key={excerpt.chunk_id}>
                <div className="source-excerpt-card-head">
                  <span>{label}</span>
                  <strong>{koLabel(excerpt.section)}</strong>
                  <small>{koLabel(excerpt.locator)}</small>
                </div>
                <p>{sourceExcerptDigest(excerpt, data.title)}</p>
                <details className="secondary-details source-document-technical-detail">
                  <summary>
                    <span>{label} 영어 원문 보기</span>
                    <strong>원문 문장 대조</strong>
                  </summary>
                  <div className="details-inner">
                    <p>{excerpt.summary}</p>
                  </div>
                </details>
              </article>
            );
          })}
        </div>
      </section>

      <section className="source-document-section reveal delay-3" id="linked-ai-evidence" aria-labelledby="linked-ai-evidence-title">
        <div className="source-document-section-head">
          <span>투자 근거 연결</span>
          <h2 id="linked-ai-evidence-title">이 원천이 어떤 투자 근거로 쓰였는지 본다</h2>
          <p>원천이 맞는지 본 뒤, 연결된 근거에서 테마·종목·방향·품질 결과를 확인한다.</p>
        </div>
        <div className="source-linked-evidence-grid">
          {data.linked_evidence.length === 0 ? (
            <p className="empty-state">이 원천 문서에 연결된 투자 근거가 아직 없다.</p>
          ) : null}
          {data.linked_evidence.map((evidence) => (
            <article className="source-linked-evidence-card" key={evidence.evidence_id}>
              <span>{koCode(evidence.evidence_type)}</span>
              <NewsTitleBlock
                compact
                title={evidence.title}
                summary={`${koCode(evidence.evidence_type)}로 연결된 원천 근거다. 상세 화면에서 종목·테마·방향 해석을 확인한다.`}
                symbol={data.symbol}
              />
              <Link href={`/ai-evidence/${evidence.evidence_id}`}>
                투자 근거 상세 열기
              </Link>
            </article>
          ))}
        </div>
        <article className="source-access-policy-card" id="source-access-policy">
          <span>접근 정책 메모</span>
          <strong>{downloadStatus}</strong>
          <p>{accessPolicyReasonLabel(data.access_policy.reason)}</p>
        </article>
      </section>
    </div>
  );
}
