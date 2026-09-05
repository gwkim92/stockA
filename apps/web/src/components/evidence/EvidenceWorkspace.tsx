import { koCode } from '@/lib/korean-labels';
import { route, shortDate, type Row } from '@/lib/research-reader-model';
import { chunkTarget, count, decimal, measuredConfidence, object, rows, strings, text, type Interpretation } from '@/lib/company-evidence-model';
import { ReaderFacts, ReaderFrame, ReaderLink, ReaderSection, StoredList } from '@/components/readers/ReaderFrame';
import styles from './EvidenceWorkspace.module.css';

function ImpactList({ value, type }: { value: unknown; type: 'stocks' | 'themes' }) {
  const impacts = rows(value);
  if (!impacts?.length) return <p className={styles.empty}>{impacts === null ? '영향 분석 미제공' : '저장된 영향 대상이 없습니다.'}</p>;
  return <div className={styles.impactGrid}>{impacts.map((row, i) => <article key={i}><h3>{text(row.target)} · {koCode(text(row.impact_direction))}</h3><p>{text(row.rationale, '판단 사유 미제공')}</p><p className={styles.caption}>모델 신뢰도 {measuredConfidence(row.confidence)} · 영향 강도 {decimal(row.impact_strength)}</p>{text(row.evidence_summary, '') && <details className={styles.disclosure}><summary>모델이 기록한 근거 요약</summary><p>{text(row.evidence_summary)}</p></details>}<ReaderLink href={route(type, row.target)}>연결 대상 리서치 →</ReaderLink></article>)}</div>;
}
function ContextRecords({ data }: { data: Interpretation }) {
  const groups: [string, unknown][] = [['참고 테마', data.context.known_themes], ['참고 테마 관계', data.context.theme_edges], ['동시 관측 영향', data.context.current_event_impacts], ['유사 이벤트', data.context.recent_similar_events]];
  return <><p className={styles.caption}>검색 문맥 기준일 {shortDate(data.context.as_of_date, '미기록')} · 참고 자료의 존재가 이 해석의 정확성을 검증하지 않습니다.</p><div className={styles.contextGrid}>{groups.map(([label, value]) => <details key={label} className={styles.disclosure}><summary>{label} · {rows(value) === null ? '미확인' : `${rows(value)!.length}개`}</summary>{rows(value)?.map((row, i) => <div key={i} className={styles.contextItem}><ReaderFacts items={Object.entries(row).filter(([key, v]) => ['theme_key', 'theme_name', 'parent_theme_key', 'child_theme_key', 'relation_type', 'event_id', 'title', 'event_at', 'symbol', 'impact_direction', 'confidence'].includes(key) && ['string', 'number', 'boolean'].includes(typeof v)).map(([key, v]) => [koCode(key), String(v)] as const)} /></div>)}</details>)}</div></>;
}
export function EvidenceWorkspace({ data }: { data: Interpretation }) {
  const candidate = data.candidate, cluster = data.cluster;
  return <ReaderFrame title={data.title} eyebrow="EVIDENCE REVIEW · 해석과 원천 대조" subtitle={`${data.reviewLabel} · 사건 기록 ${shortDate(data.eventAt, '미기록')}`}
    chapters={[["evidence-interpretation", "저장된 해석"], ["evidence-fields", "추출값 대조"], ["evidence-sources", "근거 발췌"], ["evidence-context", "맥락·실행 기록"]]}
    aside={<>
      <section className={styles.card} aria-label="근거 사용 상태"><h2>{data.reviewLabel}</h2><p>{text(data.validator.decision_ko, '모델 실행 성공과 투자 근거 사용 승인은 서로 다릅니다.')}</p><StoredList items={strings(data.validator.reasons_ko)} missing="검증 사유 목록 미제공" /><ReaderFacts items={[["검토 판정", koCode(text(data.run.quality_gate))], ["실행 상태", koCode(text(data.run.status))]]} /></section>
      <section className={styles.card}><h2>원천과 연결 대상</h2>{data.sourceMismatch && <p className={styles.warning}>문서 식별자와 연결 경로가 일치하지 않아 원천 링크를 보류했습니다.</p>}{!data.sourceHref && !data.sourceMismatch && <p>직접 원천 문서 연결 미제공</p>}<ReaderLink href={route('stocks', data.symbol)}>연결 기업 리서치 →</ReaderLink><ReaderLink href={data.thesisHref}>연결 투자 논리 →</ReaderLink><ReaderLink href={data.recommendationHref}>연결 추천 판단서 →</ReaderLink><p className={styles.caption}>명시적으로 연결된 경로만 표시합니다. 시장 문맥의 첫 종목·추천을 이 근거의 판단으로 대체하지 않습니다.</p></section>
    </>}>
    <ReaderSection id="evidence-interpretation" title={cluster ? '왜 함께 묶인 기록인가' : '무엇을 해석한 기록인가'}>
      <div className={styles.state} data-blocked={data.blocked}><strong>{data.reviewLabel}</strong><p>{data.blocked ? '차단된 근거입니다. 원천과 분석 기록은 읽을 수 있지만 추천 입력 사용 가능으로 표시하지 않습니다.' : '아래 내용은 저장된 해석입니다. 실제 원천과 반대 근거를 함께 확인하세요.'}</p></div>
      <ReaderLink href={data.sourceHref}>원천 문서 열기</ReaderLink>
      {data.summary ? <p className={styles.prose}>{data.summary}</p> : <p className={styles.empty}>저장된 한국어 요약이 없습니다. 제목의 키워드로 해석을 만들지 않습니다.</p>}
      {data.originalTitle !== data.title && <details className={styles.disclosure}><summary>원문 제목</summary><p>{data.originalTitle}</p></details>}
      <div className={styles.quickFacts}><ReaderFacts items={[["분류된 테마", text(data.classification.theme_name, text(data.classification.theme_key))], ["기록된 방향", koCode(text(data.classification.impact_direction))], ["영향 점수", decimal(data.classification.impact_score)]]} /></div>
      <p className={styles.caption}>모델 점수·신뢰도는 실현 수익률이나 투자 성공 확률이 아닙니다.</p>
      {candidate && <><h3>뉴스 후보 분석</h3><p className={styles.prose}>{text(candidate.event_summary, '후보 요약 미제공')}</p><div className={styles.warning}><strong>불확실성과 반대 가능성</strong><p>{text(candidate.uncertainty_notes, '불확실성 설명 미제공 · 위험이 없다는 뜻이 아닙니다.')}</p></div><p className={styles.caption}>추천 관련성: {text(candidate.recommendation_relevance)}</p><h3>종목 영향 가설</h3><ImpactList value={candidate.instrument_impacts} type="stocks" /><h3>테마 영향 가설</h3><ImpactList value={candidate.theme_impacts} type="themes" /></>}
      {cluster && <><h3>{text(cluster.story_label, text(cluster.theme_name, '뉴스 묶음'))}</h3><p className={styles.caption}>기준 {shortDate(cluster.as_of_date, '미기록')} · 보고된 이벤트 {count(cluster.event_count) ?? '미확인'}개 · 수신된 상세 {data.clusterEvents?.length ?? '미확인'}개</p>{data.clusterEvents?.map((event, i) => <article className={styles.clusterEvent} key={i}><h3>{text(event.korean_title, text(event.title))}</h3><p>{shortDate(event.event_at, '사건일 미기록')} · {koCode(text(event.impact_direction))}</p><ReaderLink href={route('source-documents', event.source_document_id)}>해당 이벤트 원천 →</ReaderLink></article>)}</>}
    </ReaderSection>
    <ReaderSection id="evidence-fields" title="추출된 주장과 정확한 근거 위치">
      <div data-testid="evidence-fields">{data.fields?.map((field, i) => { const href = chunkTarget(data.chunks, field.source_chunk_id); return <article className={styles.field} key={i}><span>{koCode(text(field.field))}</span><p>{text(field.value, '추출값 미제공')}</p><small>모델 신뢰도 {measuredConfidence(field.confidence)}</small>{href ? <a href={href}>근거 발췌 확인 →</a> : <p className={styles.warning}>대응하는 발췌를 수신하지 못했습니다. 다른 발췌를 대신 연결하지 않습니다.</p>}</article>; })}{!data.fields?.length && <p className={styles.empty}>{data.fields === null ? '추출값 목록 미제공' : '기록된 추출값이 없습니다.'}</p>}</div>
    </ReaderSection>
    <ReaderSection id="evidence-sources" title="모델이 참조한 발췌·요약">
      <p className={styles.caption}>저장된 발췌·요약 필드를 그대로 표시합니다. 완전한 원문이나 검증된 직접 인용과는 다릅니다.</p>
      {data.chunks?.map((chunk, i) => <article className={styles.chunk} id={`evidence-chunk-${i}`} key={text(chunk.chunk_id)}><header><span>{text(chunk.locator, '위치 미표기')}</span><h3>{text(chunk.section, '구간 미표기')}</h3></header><p className={styles.original}>{text(chunk.summary, '발췌 내용 미제공')}</p><details className={styles.disclosure}><summary>발췌 연결 기록</summary><ReaderFacts items={[["발췌 ID", text(chunk.chunk_id)], ["저장된 관련성", text(chunk.relevance)]]} /></details></article>)}
      {!data.chunks?.length && <p className={styles.empty}>{data.chunks === null ? '발췌 자료 미제공' : '수신된 발췌 목록이 비어 있습니다.'}</p>}
    </ReaderSection>
    <ReaderSection id="evidence-context" title="해석 당시의 맥락과 실행 기록">
      <ContextRecords data={data} /><details className={styles.disclosure}><summary>실행·식별 정보</summary><ReaderFacts items={[["요청 ID", data.requested], ["반환 ID", data.id], ["조회 해석", data.alias ? '기존 API 별칭 해석' : '요청 ID와 일치'], ["실행 ID", text(data.run.run_id)], ["분석 제공자", text(data.run.provider)], ["모델", text(data.run.model_id)], ["실행 완료일", shortDate(data.run.finished_at, '미기록')]]} /></details><details className={styles.disclosure}><summary>저장된 주의사항</summary><StoredList items={data.notes} missing="주의사항 미제공" /></details>
    </ReaderSection>
  </ReaderFrame>;
}
