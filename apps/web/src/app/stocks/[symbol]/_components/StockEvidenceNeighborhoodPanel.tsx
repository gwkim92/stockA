import Link from "next/link";

import { koCode, koLabel } from "@/lib/korean-labels";
import type { AiEvidenceNeighborhoodData } from "@/lib/types";

import { StockEvidenceDisclosure } from "./StockEvidenceDisclosure";
import { StockEvidenceSourceSection } from "./StockEvidenceSourceSection";
import { StockStoryGroupSection } from "./StockStoryGroupSection";
import styles from "./StockEvidenceNeighborhoodPanel.module.css";
import {
  stockEventsHref,
  stockEvidenceGuardrails,
  stockEvidenceHref,
  stockEvidenceProviderLabel,
  stockRecommendationHref,
  stockThesisHref,
} from "./stock-evidence-format";
import { formatPercent, stockText } from "./stock-detail-panel-format";

type StockEvidenceNeighborhoodPanelProps = {
  readonly neighborhood: AiEvidenceNeighborhoodData;
};

export function StockEvidenceNeighborhoodPanel({ neighborhood }: StockEvidenceNeighborhoodPanelProps) {
  const firstTheme = neighborhood.themes[0];
  const firstArtifact = neighborhood.ai_artifacts[0];
  const firstThesis = neighborhood.theses[0];
  const firstRecommendation = neighborhood.recommendations[0];
  const storyGroups = neighborhood.story_groups ?? [];
  const ragContext = neighborhood.internal_rag_context;
  const ragPassedGateCount = ragContext.quality_gates.filter((gate) => gate.status === "passed").length;
  const investmentLinkCount = neighborhood.summary.thesis_count + neighborhood.summary.recommendation_count;
  const firstEvidenceHref = firstArtifact ? stockEvidenceHref(firstArtifact.evidence_id) : null;
  const readinessLabel = ragContext.status === "ready" ? "판단 근거 준비됨" : "근거 보강 필요";
  const readinessCopy =
    ragContext.status === "ready"
      ? "뉴스, 번역, 원문 근거, 기존 추천·투자 논리가 함께 조회된다. 저장된 근거만 보여준다."
      : "연결된 자료가 부족합니다. 원문과 번역 상태가 확보되기 전에는 추천이나 보유 판단에 사용하지 않습니다.";

  return (
    <section className="stock-evidence-panel reveal delay-4" aria-label="이 종목이 뉴스와 엮인 이유">
      <div className="stock-evidence-head">
        <div>
          <span className="metric-sub">뉴스·투자 근거 연결</span>
          <h2>
            {neighborhood.symbol}에 영향을 <span className="keep-phrase">줄 수 있는</span> 뉴스가 어디서 왔고,
            어떻게 연결됐는지 본다
          </h2>
          <p>
            수집 뉴스, 한국어 요약, 종목·테마 영향, 원문 근거, 추천·투자 논리 연결을 한 흐름으로 정리했다.
            저장된 분석만 읽고 새 추천이나 주문은 만들지 않는다.
          </p>
        </div>
        <aside>
          <span>현재 상태</span>
          <strong>{readinessLabel}</strong>
          <small>
            검사 {ragPassedGateCount}/{ragContext.quality_gates.length}개 통과 · 투자 연결 {investmentLinkCount.toLocaleString("ko-KR")}개
          </small>
        </aside>
      </div>

      <div className="stock-evidence-summary" aria-label="뉴스와 종목 연결 요약">
        <div>
          <span>수집 이벤트</span>
          <strong>{neighborhood.summary.event_count.toLocaleString("ko-KR")}개</strong>
          <small>뉴스·공시가 이 종목에 연결된 수</small>
        </div>
        <div>
          <span>뉴스 묶음</span>
          <strong>{(neighborhood.summary.story_group_count ?? storyGroups.length).toLocaleString("ko-KR")}개</strong>
          <small>같은 이슈로 묶인 후보</small>
        </div>
        <div>
          <span>심화 근거</span>
          <strong>{neighborhood.summary.ai_artifact_count.toLocaleString("ko-KR")}개</strong>
          <small>저장된 투자 근거</small>
        </div>
        <div>
          <span>원문 근거</span>
          <strong>{neighborhood.summary.evidence_chunk_count.toLocaleString("ko-KR")}개</strong>
          <small>뉴스·공시 본문 연결</small>
        </div>
      </div>

      <div className={styles.focusStrip} aria-label={`${neighborhood.symbol} 핵심 근거 경로`}>
        <article className={styles.focusCard}>
          <span>추천 입력 전 확인</span>
          <strong>{readinessLabel}</strong>
          <p>{readinessCopy}</p>
        </article>

        <div className="stock-evidence-chain" aria-label={`${neighborhood.symbol} 뉴스 근거 관계 흐름`}>
          <article className="stock-evidence-chain-card">
            <span>1. 수집된 사건</span>
            <strong>이벤트 {neighborhood.summary.event_count.toLocaleString("ko-KR")}개</strong>
            <p>
              {neighborhood.events[0]
                ? koLabel(neighborhood.events[0].title)
                : "아직 이 종목에 연결된 이벤트가 없다."}
            </p>
            <Link href={stockEventsHref(neighborhood.symbol)}>수집 뉴스 보기</Link>
          </article>
          <article className="stock-evidence-chain-card">
            <span>2. 테마·노출</span>
            <strong>{firstTheme ? koCode(firstTheme.theme_key) : "테마 없음"}</strong>
            <p>
              {firstTheme
                ? `멤버십 ${koCode(firstTheme.membership_type)} · 신뢰도 ${formatPercent(firstTheme.confidence)}`
                : "테마 연결이 쌓이면 이 위치에 표시된다."}
            </p>
          </article>
          <article className="stock-evidence-chain-card">
            <span>3. 투자 영향</span>
            <strong>{firstArtifact ? koCode(firstArtifact.evidence_type) : "심화 근거 없음"}</strong>
            <p>
              {firstArtifact
                ? `${stockEvidenceProviderLabel(firstArtifact.provider)} · 신뢰도 ${formatPercent(firstArtifact.confidence)}`
                : "아직 저장된 투자 근거가 없다."}
            </p>
            {firstEvidenceHref ? <Link href={firstEvidenceHref}>근거 상세 열기</Link> : <small>근거 대기</small>}
          </article>
          <article className="stock-evidence-chain-card final">
            <span>4. 투자 판단 연결</span>
            <strong>{firstRecommendation ? koCode(firstRecommendation.action) : firstThesis ? "투자 논리만 있음" : "판단 대기"}</strong>
            <p>
              {firstRecommendation
                ? `점수 ${formatPercent(firstRecommendation.total_score)} · 목표 비중 ${formatPercent(firstRecommendation.recommended_weight)}`
                : firstThesis
                  ? `${stockText(firstThesis.title)} · 확신 ${formatPercent(firstThesis.conviction_score)}`
                  : "추천이나 보유 판단으로 연결되기 전 단계다."}
            </p>
            <div className="mini-link-stack">
              {firstRecommendation ? <Link href={stockRecommendationHref(firstRecommendation.recommendation_id)}>추천 상세</Link> : null}
              {firstThesis ? <Link href={stockThesisHref(firstThesis.thesis_id)}>투자 논리</Link> : null}
            </div>
          </article>
        </div>
      </div>

      <div className={styles.detailStack}>
        <StockEvidenceDisclosure
          eyebrow="자동 검증"
          title="추천 입력 전 통과해야 하는 근거 조건"
          summary="원문, 번역, 종목 연결, 추천 연결 상태를 자동 검증한 결과다. 통과하지 않은 항목은 투자 판단 입력에서 낮게 본다."
        >
          <div className="stock-evidence-gate-grid">
            {ragContext.quality_gates.map((gate) => (
              <article className="stock-evidence-gate-card" data-status={gate.status} key={gate.gate}>
                <span>{gate.status === "passed" ? "통과" : gate.status === "watch" ? "관찰" : "보강 필요"}</span>
                <strong>{stockText(koCode(gate.gate))}</strong>
                <p>{stockText(gate.message_ko)}</p>
              </article>
            ))}
          </div>
        </StockEvidenceDisclosure>

        <StockEvidenceDisclosure
          eyebrow="뉴스 묶음"
          title="같은 이슈로 묶인 뉴스와 대표 이벤트"
          summary="같은 테마나 원천 문서에서 나온 뉴스를 묶어 시장 흐름으로 본다. 자세한 대표 뉴스는 펼쳐서 확인합니다."
        >
          <StockStoryGroupSection neighborhood={neighborhood} storyGroups={storyGroups} />
        </StockEvidenceDisclosure>

        <StockEvidenceDisclosure
          eyebrow="원천 문서"
          title="투자 근거가 참조한 원문 대조"
          summary="영어 원문 전체를 바로 노출하지 않고, 출처와 본문 추출 상태만 먼저 보여준다."
        >
          <StockEvidenceSourceSection neighborhood={neighborhood} />
        </StockEvidenceDisclosure>

        <StockEvidenceDisclosure
          eyebrow="사용 경계"
          title="이 화면이 바꾸지 않는 것"
          summary="이 섹션은 근거 확인 화면이다. 추천 점수, 보유 수량, 실제 주문 상태는 여기서 바뀌지 않는다."
        >
          <div className="stock-guardrail-list" aria-label="종목 근거 화면 사용 경계">
            {stockEvidenceGuardrails().map((guardrail) => (
              <article key={guardrail}>
                <span>사용 경계</span>
                <p>{koLabel(guardrail)}</p>
              </article>
            ))}
          </div>
        </StockEvidenceDisclosure>
      </div>
    </section>
  );
}
