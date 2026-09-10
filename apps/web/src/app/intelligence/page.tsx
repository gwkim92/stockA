import Link from "next/link";
import { getAiNewsClusters, getEvents } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import { knownSymbol, route, shortDate } from "@/lib/research-reader-model";
import { measuredConfidence } from "@/lib/company-evidence-model";
import { NewsWorkspace, type NewsItem } from "@/components/research/NewsWorkspace";
import styles from "@/components/research/NewsWorkspace.module.css";
export const dynamic = "force-dynamic";
export const metadata = { title: "뉴스 리서치" };
export default async function IntelligencePage() {
  const [eventResult, clusterResult] = await Promise.allSettled([getEvents({ limit: 24 }), getAiNewsClusters({ limit: 8 })]);
  const events = eventResult.status === "fulfilled" ? eventResult.value.data : null;
  const clusters = clusterResult.status === "fulfilled" ? clusterResult.value.data : null;
  const items: NewsItem[] = [
    ...(clusters?.clusters ?? []).map(cluster => ({
      id: `cluster-${cluster.evidence_id}`, kind: "cluster" as const,
      title: koLabel(cluster.story_label || cluster.title), original: cluster.title,
      summary: null, date: shortDate(cluster.as_of_date, "미기록"), subject: koCode(cluster.theme_key),
      symbols: cluster.symbols.filter(symbol => knownSymbol(symbol) !== null),
      direction: Object.entries(cluster.direction_counts).filter(([, value]) => value > 0).map(([key, value]) => `${koCode(key)} ${value}`).join(" · ") || "방향 미분류",
      risk: (cluster.direction_counts.risk_review ?? 0) > 0 || (cluster.direction_counts.negative ?? 0) > 0,
      evidenceHref: route("ai-evidence", cluster.evidence_id),
      sources: cluster.source_documents.filter(source => route("source-documents", source.source_document_id)).map(source => ({ id: source.source_document_id, title: source.korean_title || source.title })),
      reasons: cluster.relation_reasons.map(koLabel), notes: cluster.audit_notes,
      provider: koCode(cluster.extraction_run.provider), model: cluster.extraction_run.model_id || "실행 기록 미제공",
      confidence: measuredConfidence(cluster.confidence), quality: koCode(cluster.extraction_run.status), count: `뉴스 ${cluster.event_count}개`, headlines: cluster.events.map(event => ({ title: event.korean_title || event.title, date: shortDate(event.event_at, "미기록"), direction: koCode(event.impact_direction) })),
    })),
    ...(events?.events ?? []).map(event => ({
      id: `event-${event.event_id}`, kind: "event" as const, title: event.korean_title || event.title, original: event.title,
      summary: event.korean_summary || null, date: shortDate(event.event_at, "미기록"), subject: koCode(event.theme_key),
      symbols: knownSymbol(event.symbol) ? [event.symbol] : [], direction: koCode(event.impact_direction),
      risk: ["risk_review", "negative"].includes(event.impact_direction), evidenceHref: route("ai-evidence", event.ai_evidence_id),
      sources: event.source_document_id && route("source-documents", event.source_document_id) ? [{ id: event.source_document_id, title: event.korean_title || event.title }] : [],
      reasons: [...new Set(event.related_events.map(related => related.reason).filter(Boolean))], notes: [],
      provider: event.ai_evidence_provider ? koCode(event.ai_evidence_provider) : "분석 기록 미제공", model: "이 목록의 실행 모델 미제공",
      confidence: measuredConfidence(event.ai_evidence_confidence), quality: event.ai_evidence_type === "news_event_candidate_rejected" || event.quality_gate === "validator_blocked" ? "추천 입력 차단·보류" : koCode(event.quality_gate), count: "개별 뉴스", headlines: [],
    })),
  ];
  return <div className={styles.page}>
    <header className={styles.heading}><div><span className={styles.kicker}>NEWS & EVIDENCE</span><h1>뉴스 리서치</h1><p>사건을 읽고, 저장된 해석을 원천과 대조합니다.</p></div><nav aria-label="뉴스 관련 화면"><Link href="/events">전체 원천 뉴스 →</Link><Link href="/ai-evidence">전체 분석 근거 →</Link></nav></header>
    <div className={styles.status}><span>뉴스 조회 기준 <strong>{events?.as_of_date ?? "미확인"}</strong></span><span>뉴스 묶음 기준 <strong>{clusters?.as_of_date ?? "미확인"}</strong></span><span>수신 <strong>묶음 {clusters ? clusters.clusters.length : "미조회"}개 · 개별 {events ? events.events.length : "미조회"}개</strong></span></div>
    {(!events || !clusters) && <p className={styles.notice} role="status">{!events ? "개별 뉴스" : "뉴스 묶음"}{!events && !clusters ? "와 뉴스 묶음" : ""} 자료를 불러오지 못했습니다. 수신한 자료는 계속 표시합니다.</p>}
    <NewsWorkspace items={[...items.filter(item => item.kind === "event"), ...items.filter(item => item.kind === "cluster")]} />
    <p className={styles.status}>검색·분류는 수신된 묶음 최대 8개와 개별 뉴스 최대 24개에 적용됩니다. 과거 자료와 다음 페이지는 전체 원천 뉴스·분석 근거에서 확인하세요.</p>
  </div>;
}
