import { ValuationTargetRangeCard } from "@/components/valuation-target-range-card";
import { koCode, koReason } from "@/lib/korean-labels";
import { conditionLabel, count, currencyValue, fullValuation, nextReview, object, route, rows, shortDate, strings, text, thesisAttention, type Row, type ThesisReaderData } from "@/lib/research-reader-model";
import { ReaderFacts, ReaderFrame, ReaderLink, ReaderSection, StoredList } from "./ReaderFrame";
import styles from "./ResearchReader.module.css";
const counted = (v: unknown) => count(v) === null ? "미확인" : `${count(v)}개`;
const scalar = (v: unknown): string => typeof v === "string" ? v : typeof v === "number" && Number.isFinite(v) ? String(v) : typeof v === "boolean" ? v ? "예" : "아니오" : "미제공";
function GateRecords({ value }: { value: unknown }) {
  const gates = rows(value);
  if (!gates?.length) return <p className={styles.empty}>{gates === null ? "검토 항목 미제공" : "기록된 검토 항목이 없습니다."}</p>;
  return <div>{gates.map((gate, i) => {
    const facts = rows(gate.facts);
    return <article className={styles.evidence} key={i}>
      <span className={styles.tag}>{koCode(text(gate.status))}</span>
      <h3>{text(gate.title, text(gate.label, text(gate.gate_key, `검토 항목 ${i + 1}`)))}</h3>
      {text(gate.decision, "") && <p className={styles.prose}>{text(gate.decision)}</p>}
      <p className={styles.prose}>{text(gate.detail, text(gate.message, text(gate.reason, "설명 미제공")))}</p>
      {text(gate.next_step, "") && <p className={styles.caption}>다음 확인: {text(gate.next_step)}</p>}
      {facts && <ReaderFacts items={facts.map(fact => [text(fact.label), scalar(fact.value)] as const)} />}
    </article>;
  })}</div>;
}
function ValuationRecords({ value }: { value: Row }) {
  const methods = rows(value.methods), complete = fullValuation(value);
  return <><ReaderFacts items={[["원천 판정", koCode(text(value.status))], ["가치평가 기준일", shortDate(value.valuation_as_of_date ?? value.as_of_date, "미기록")], ["기준 가격", currencyValue(value.current_price ?? value.base_price, value.currency_code)], ["하방 추정 가치", currencyValue(value.target_low, value.currency_code)], ["중앙 추정 가치", currencyValue(value.target_base, value.currency_code)], ["상방 추정 가치", currencyValue(value.target_high, value.currency_code)]]} />
    {methods?.map((method, i) => <details className={styles.details} key={i}><summary>{koCode(text(method.method, `평가 방법 ${i + 1}`))} · {shortDate(method.as_of_date, "기준일 미확인")}</summary><ReaderFacts items={[["하방", currencyValue(method.fair_value_low, value.currency_code)], ["중앙", currencyValue(method.fair_value_base, value.currency_code)], ["상방", currencyValue(method.fair_value_high, value.currency_code)]]} />
      <h3 className={styles.subheading}>저장된 평가 가정</h3><ReaderFacts items={Object.entries(object(method.assumptions)).filter(([, v]) => typeof v === "string" || typeof v === "number").map(([key, v]) => [koCode(key), scalar(v)] as const)} /></details>)}
    {complete && <details className={styles.details}><summary>기존 전문 가치평가·사업부 모델 전체 보기</summary><ValuationTargetRangeCard valuation={complete} /></details>}
    <p className={styles.caption}>서로 다른 기준일의 추정 가치를 현재 가격이나 수익률로 대체하지 않습니다. 세부 재무·사업부 모델은 기업 분석에서 확인하세요.</p></>;
}
export function ThesisReader({ data, today }: { data: ThesisReaderData; today: string }) {
  const triggered = data.conditions?.filter(row => row.state === "triggered").length;
  const unknown = data.conditions?.filter(row => row.state === "unknown").length;
  const hasReview = !!data.review.id && !!data.review.date;
  const reviewFuture = !!data.review.date && data.review.date.slice(0, 10) > today;
  return <ReaderFrame eyebrow={`INVESTMENT THESIS · ${data.version}`} title={`${data.symbol} 투자 논리`}
    subtitle={`${koCode(data.status)} · ${thesisAttention(data)} · 다음 확인 ${nextReview(data.review.next, today)}`}
    chapters={[["thesis-claims", "핵심 주장"], ["thesis-conditions", "촉매·무효화"], ["thesis-review", "최근 검토"], ["thesis-evidence", "연결 근거"], ["thesis-valuation", "가치평가"], ["thesis-checks", "검토 기록"]]}
    aside={<>
      <section className={styles.contextCard}><h2>다음 판단을 위한 맥락</h2><ReaderFacts items={[["최근 검토일", shortDate(data.review.date, "미기록")], ["기록된 조치", hasReview ? koCode(data.review.action) : "미확인"], ["기록된 위험도", hasReview ? koCode(data.review.risk) : "미확인"], ["다음 확인일", nextReview(data.review.next, today)]]} />{reviewFuture && <p className={styles.warning}>검토 기록이 현재보다 미래입니다. 기준일을 확인하세요.</p>}<ReaderLink href={route("stocks", data.symbol)}>기업 분석 →</ReaderLink><ReaderLink href={data.recommendationHref}>연결 추천 판단서 →</ReaderLink><ReaderLink href="/portfolio/coverage">보유 검토 →</ReaderLink></section>
      <section className={styles.contextCard}><h2>문서 식별</h2><ReaderFacts items={[["투자 논리 ID", data.id], ["조회 해석", data.resolution === "exact" ? "요청 ID와 일치" : "기존 API 별칭 해석"]]} /><p className={styles.caption}>저장된 판단을 읽는 화면입니다. 주문·비중 변경을 실행하지 않습니다.</p></section>
    </>}>
    <ReaderSection id="thesis-claims" title="무엇을 근거로 보는 기업인가" kicker="THE INVESTMENT CASE">
      <p className={styles.prose}>{data.summary}</p><StoredList items={data.claims} missing="핵심 주장 목록 미제공" />
      {data.researchSummary && data.researchSummary !== data.summary && <details className={styles.details}><summary>연결 리서치 요약 · {koCode(data.researchSource)}</summary><p className={styles.prose}>{data.researchSummary}</p></details>}
    </ReaderSection>
    <ReaderSection id="thesis-conditions" title="성립 조건과 판단을 바꿀 조건">
      <div className={styles.twoColumns}><div><h3>촉매·성립 조건</h3><StoredList items={data.catalysts} missing="촉매 자료 미제공" /></div><div><h3>반대 근거·위험</h3><StoredList items={data.risks} missing="위험 자료 미제공" /></div></div>
      <div className={styles.conditionSummary}><span>발동 기록 <strong>{triggered === undefined ? "미확인" : `${triggered}개`}</strong></span><span>판정 미확인 <strong>{unknown === undefined ? "미확인" : `${unknown}개`}</strong></span></div>
      <p className={styles.caption}>저장된 상태를 구분해 표시합니다. 미발동 기록은 현재도 안전하다는 보장이 아니며, 미확인을 발동으로 세지 않습니다.</p>
      {data.conditions?.map((condition, i) => <article className={styles.condition} key={i}><span className={styles.tag} data-state={condition.state}>{conditionLabel(condition.state)}</span><p>{koReason(condition.text)}</p></article>)}
      {!data.conditions?.length && <p className={styles.empty}>{data.conditions === null ? "무효화 조건 자료 미제공" : "기록된 무효화 조건이 없습니다."}</p>}
    </ReaderSection>
    <ReaderSection id="thesis-review" title="최근에 기록된 검토">
      {!hasReview ? <p className={styles.empty}>식별자와 검토일이 확인된 기록이 없습니다. 유지·축소 판단을 추정하지 않습니다.</p> : <><span className={styles.tag}>{koCode(data.review.action)} · {shortDate(data.review.date)}</span><p className={styles.prose}>{data.review.summary ?? "검토 요약 미제공"}</p>{data.review.notes && <details className={styles.details}><summary>저장된 변화 사유 원문</summary><p className={styles.original}>{data.review.notes}</p></details>}</>}
      <p className={styles.caption}>최신 검토 기록 한 건입니다. 서로 다른 시점의 문서를 비교해 새로 생성한 변경 이력은 아닙니다.</p>
    </ReaderSection>
    <ReaderSection id="thesis-evidence" title="주장을 뒷받침한 근거">
      {data.evidence?.map((item, i) => <article className={styles.evidence} key={`${item.id}-${i}`}><span className={styles.tag}>{koCode(item.type || "미분류")}</span><h3>{item.title}</h3><p className={styles.caption}>관측일 {shortDate(item.observedAt, "미기록")}</p><ReaderLink href={item.href}>{item.action} →</ReaderLink>{!item.href && <p className={styles.caption}>상세 경로 미제공 · 식별자 {item.id || "미기록"}</p>}</article>)}
      {!data.evidence?.length && <p className={styles.empty}>{data.evidence === null ? "근거 목록 미제공" : "연결 근거가 없습니다."}</p>}
    </ReaderSection>
    <ReaderSection id="thesis-valuation" title="가치평가와 가정"><ValuationRecords value={data.valuation} />
      <details className={styles.details}><summary>투자 논리에 연결된 시나리오</summary><ReaderFacts items={[["기준 시나리오", scalar(data.valuationView.base_case)], ["상방 조건", scalar(data.valuationView.upside_case)], ["하방 조건", scalar(data.valuationView.downside_case)], ["안전마진 관점", scalar(data.valuationView.margin_of_safety_view)]]} /></details>
    </ReaderSection>
    <ReaderSection id="thesis-checks" title="원천이 보고한 검토 상태">
      <ReaderFacts items={[["전문 검토 판정", koCode(text(data.professional.status))], ["확인 항목", counted(data.professional.gate_count)], ["통과 항목", counted(data.professional.pass_count)], ["차단 항목", counted(data.professional.blocked_count)], ["생애주기 원천 판정", koCode(text(data.readiness.status))]]} />
      <p className={styles.caption}>누락된 건수를 0으로 채우거나 문서의 존재를 검토 통과로 바꾸지 않습니다.</p>
      <details className={styles.details}><summary>전문 검토 세부 항목</summary><GateRecords value={data.professional.gates} /><StoredList items={strings(data.readiness.missing_items)} missing="보강 항목 미제공" /></details>
      <details className={styles.details}><summary>근거 품질 세부 항목</summary><p>원천 판정 {koCode(text(data.quality.quality_status))}</p><GateRecords value={data.quality.gates} /></details>
    </ReaderSection>
  </ReaderFrame>;
}
