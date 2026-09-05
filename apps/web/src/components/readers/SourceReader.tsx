import { koCode } from "@/lib/korean-labels";
import { shortDate, route, type SourceReaderData } from "@/lib/research-reader-model";
import { ReaderFacts, ReaderFrame, ReaderLink, ReaderSection } from "./ReaderFrame";
import { SourceExcerpts } from "./SourceExcerpts";
import styles from "./ResearchReader.module.css";
export function SourceReader({ data }: { data: SourceReaderData }) {
  const policy = data.download === "restricted" ? "원문 다운로드 제한" : data.download === "unavailable" ? "원문 전달 경로 미제공" : "원문 접근 정책 미확인";
  return <ReaderFrame eyebrow="SOURCE READER · 원천 대조" title={data.koreanTitle ?? data.title}
    subtitle={`${data.publisher} · ${data.form || koCode(data.type)} · 공개일 ${shortDate(data.filedAt, "미기록")}`}
    chapters={[["source-excerpts", "발췌 읽기"], ["source-summary", "요약·원제"], ["source-connections", "근거 연결"], ["source-record", "수집 기록"]]}
    aside={<>
      <section className={styles.contextCard}><h2>문서 맥락</h2><ReaderFacts items={[["연결 종목", data.symbol ?? "미확인"], ["원천 유형", koCode(data.type)], ["기록된 대상일", data.periodEnd ?? "미기록"], ["게시·접수일", shortDate(data.filedAt, "미기록")], ["수집일", shortDate(data.fetchedAt, "미기록")]]} /><p className={styles.caption}>수집일은 원문 작성일·최신성을 뜻하지 않습니다.</p><ReaderLink href={route("stocks", data.symbol)}>연결 기업 리서치 →</ReaderLink><ReaderLink href={data.thesisHref}>연결 투자 논리 →</ReaderLink></section>
      <section className={styles.contextCard} aria-label="원문 접근 상태"><h2>{policy}</h2><p className={styles.caption}>여기서는 API가 제공한 발췌·요약만 읽습니다. 내부 저장 위치를 원문 링크로 사용하지 않습니다.</p></section>
    </>}>
    <ReaderSection id="source-excerpts" title="원천의 내용을 직접 대조하세요" kicker="READ THE EVIDENCE"><SourceExcerpts excerpts={data.excerpts} /></ReaderSection>
    <ReaderSection id="source-summary" title="저장된 요약과 원제">
      {data.koreanSummary ? <><span className={styles.tag}>저장된 한국어 요약</span><p className={styles.prose}>{data.koreanSummary}</p></> : <p className={styles.empty}>저장된 한국어 요약이 없습니다. 제목의 단어만으로 투자 주제나 방향을 추정하지 않습니다.</p>}
      <h3 className={styles.subheading}>원문 제목</h3><p className={styles.original}>{data.title}</p>
    </ReaderSection>
    <ReaderSection id="source-connections" title="이 자료에 연결된 해석">
      <p className={styles.caption}>원문과 해석은 별개입니다. 연결된 분석의 주장과 이 문서 내용을 비교하세요.</p>
      {data.evidence?.map((item, i) => <article className={styles.evidence} key={`${item.id}-${i}`}><span className={styles.tag}>{koCode(item.type || "미분류")}</span><h3>{item.title}</h3><ReaderLink href={item.href}>연결 해석 보기 →</ReaderLink></article>)}
      {!data.evidence?.length && <p className={styles.empty}>{data.evidence === null ? "연결 근거 목록 미제공" : "연결된 근거가 없습니다."}</p>}
    </ReaderSection>
    <ReaderSection id="source-record" title="수집·식별 기록">
      <ReaderFacts items={[["반환된 문서 ID", data.id], ["ID 해석", data.resolution === "exact" ? "요청 ID와 일치" : "기존 API 별칭 해석"], ["접수 식별자", data.accession], ["파서", data.parser], ["수집 시각", data.fetchedAt ?? "미기록"], ["기록된 체크섬", data.checksum]]} />
      <p className={styles.caption}>식별자와 체크섬의 존재만으로 원문 정확성이나 무결성 검증 완료를 뜻하지 않습니다.</p>
    </ReaderSection>
  </ReaderFrame>;
}
