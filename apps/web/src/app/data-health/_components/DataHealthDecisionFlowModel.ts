import type { DataHealthDataGapCard } from "./DataHealthDataGapScorecards";
import type { DataHealthDecisionFlowCard } from "./DataHealthDecisionFlowStatus";

export type DataHealthDecisionFlowModelInput = {
  readonly dataQualityReady: boolean;
  readonly newsRunLabel: string;
  readonly aiInvocationLabel: string;
  readonly aiAttentionRequired: boolean;
  readonly priceAttentionRequired: boolean;
  readonly marketPriceRunLabel: string;
  readonly latestPriceDateLabel: string;
  readonly crossAssetIndicatorRunLabel: string;
  readonly crossAssetRunLabel: string;
  readonly crossAssetHealthOk: boolean;
  readonly tossSyncLabel: string;
  readonly tossComparisonLabel: string;
  readonly tossAttentionRequired: boolean;
  readonly tossBrokerSubmitAllowed: boolean;
  readonly safeInvestmentBoundary: boolean;
  readonly decisionRunLabel: string;
  readonly remediationRunLabel: string;
  readonly outcomeWeightReviewBlocked: boolean;
  readonly recommendationOutcomeRunLabel: string;
  readonly nextRecommendationDueDateLabel: string;
  readonly manualWeightReviewAllowed: boolean;
};

export type DataHealthDataGapModelInput = {
  readonly crossAssetHealthOk: boolean;
  readonly fundSourceGapCount: number;
  readonly tossAttentionRequired: boolean;
};

export function buildDataHealthDecisionFlowCards(input: DataHealthDecisionFlowModelInput): DataHealthDecisionFlowCard[] {
  return [
    {
      label: "01 뉴스·AI",
      title: input.dataQualityReady ? "뉴스 근거 사용 가능" : "뉴스 근거 품질 확인",
      statusLabel: `${input.newsRunLabel} · AI ${input.aiInvocationLabel}`,
      evidence: "RSS 원문, 한국어 번역, AI 구조화, 자동 검증을 거친 근거만 추천·보유 화면으로 넘어간다.",
      impact: input.aiAttentionRequired ? "AI 호출 상태 먼저 확인" : "뉴스 근거 화면 확인",
      href: "#live-ai-invocation-health",
      tone: input.dataQualityReady ? "ready" : input.aiAttentionRequired ? "block" : "watch",
    },
    {
      label: "02 시장 가격",
      title: input.priceAttentionRequired ? "가격 보강 필요" : "분석 가격 최신",
      statusLabel: `${input.marketPriceRunLabel} · 최신 가격일 ${input.latestPriceDateLabel}`,
      evidence: "분석 기준 가격은 차트, 사이클, 성과, 추천 점수의 기준 데이터다.",
      impact: input.priceAttentionRequired ? "가격 보강 후 판단" : "종목·추천 화면 신뢰 가능",
      href: "#active-recommendation-price-freshness",
      tone: input.priceAttentionRequired ? "block" : "ready",
    },
    {
      label: "03 크로스에셋",
      title: input.crossAssetHealthOk ? "시장 체제 갱신됨" : "시장 체제 확인 필요",
      statusLabel: `${input.crossAssetIndicatorRunLabel} · ${input.crossAssetRunLabel}`,
      evidence: "금리, 달러, 원자재, 변동성, 신용 흐름을 시장 지도와 사이클 근거로 연결한다.",
      impact: "시장 지도와 사이클 지도 확인",
      href: "#collection-status-title",
      tone: input.crossAssetHealthOk ? "ready" : "watch",
    },
    {
      label: "04 토스 브로커 현실",
      title: input.tossSyncLabel === "성공" || input.tossSyncLabel === "succeeded" ? "브로커 데이터 수집됨" : "브로커 데이터 확인 필요",
      statusLabel: `${input.tossSyncLabel} · ${input.tossComparisonLabel}`,
      evidence: "토스증권 데이터는 실제 계좌, 주문 가능성, 가격 기준 차이, 최신 일봉 미완성 여부를 확인하는 보조 현실 데이터다.",
      impact: input.tossBrokerSubmitAllowed ? "주문 경계 재확인" : "실주문 차단 유지",
      href: "#toss-market-data",
      tone: input.tossAttentionRequired ? "watch" : "ready",
    },
    {
      label: "05 추천·보유",
      title: input.safeInvestmentBoundary ? "읽기 전용 판단 유지" : "투자 경계 점검",
      statusLabel: `${input.decisionRunLabel} · ${input.remediationRunLabel}`,
      evidence: "추천, thesis, 보유 위험, 가상 매매 검증은 결정 로직이 만들며 AI는 근거 설명만 보조한다.",
      impact: input.safeInvestmentBoundary ? "추천 산식·실거래 차단" : "경계 조건 확인",
      href: "#outcome-maturity-wait-monitor",
      tone: input.safeInvestmentBoundary ? "ready" : "block",
    },
    {
      label: "06 성과 피드백",
      title: input.outcomeWeightReviewBlocked ? "성과 표본 대기" : "성과 검토 가능",
      statusLabel: `${input.recommendationOutcomeRunLabel} · 다음 추천 측정일 ${input.nextRecommendationDueDateLabel}`,
      evidence: "성과와 포트폴리오 사후평가가 성숙하기 전까지 추천 반영 비중 변경은 금지된다.",
      impact: input.manualWeightReviewAllowed ? "수동 검토 가능" : "반영 비중 변경 금지",
      href: "#outcome-calibration",
      tone: input.outcomeWeightReviewBlocked ? "watch" : "ready",
    },
  ];
}

export function buildDataHealthDataGapCards(input: DataHealthDataGapModelInput): DataHealthDataGapCard[] {
  return [
    {
      label: "기업 이벤트",
      title: "분할·배당·상장 이벤트",
      priority: "즉시 무료 가능",
      currentPolicy: "공식 원천 확인 전에는 성과 보정과 추천 반영을 막고, 종목 상세에는 데이터 한계로 표시한다.",
      impact: "가격·성과·밸류에이션 해석의 왜곡을 막는다.",
      nextAction: "SEC/거래소/제공자 원천 우선",
      tone: "watch",
    },
    {
      label: "실적 일정·가이던스",
      title: "실적 발표와 회사 전망",
      priority: "무료이나 품질 제한",
      currentPolicy: "저장된 공시와 원문 링크가 있을 때만 AI 리서치 맥락으로 쓰고, 직접 점수 반영은 보류한다.",
      impact: "catalyst와 invalidation 조건은 보강하되 점수는 안정적으로 유지한다.",
      nextAction: "공식 IR/SEC 원천부터 연결",
      tone: "watch",
    },
    {
      label: "소유·내부자",
      title: "13F·기관 보유·내부자 거래",
      priority: "무료이나 느린 주기",
      currentPolicy: "파서와 회귀평가 전까지는 전문 분석 참고 근거 또는 반영 비중 0인 항목으로만 둔다.",
      impact: "수급 해석을 보강하지만 추천 순위를 즉시 바꾸지 않는다.",
      nextAction: "SEC 구조화 filing parser 후보",
      tone: "watch",
    },
    {
      label: "섹터 폭·신용·유동성",
      title: "시장 내부 체력과 자금 압박",
      priority: "즉시 무료 가능",
      currentPolicy: "FRED, ETF 구성, 시장 가격으로 크로스에셋과 사이클 근거를 만들되 새 score component는 반영 비중 0이다.",
      impact: "시장 지도와 사이클 지도의 신뢰도를 높인다.",
      nextAction: "cross-asset daily와 연결 유지",
      tone: input.crossAssetHealthOk ? "ready" : "watch",
    },
    {
      label: "ETF·펀드 원천",
      title: "구성종목·비용·NAV·추적 품질",
      priority: input.fundSourceGapCount > 0 ? "보강 필요" : "관리 중",
      currentPolicy: "공식 fund 원천이 없거나 오래되면 ETF 추천 상세에서 원천 한계로 표시한다.",
      impact: "ETF와 개별 회사 주식 분석을 분리한다.",
      nextAction: input.fundSourceGapCount > 0 ? "공식 provider importer 보강" : "현재 importer 유지",
      tone: input.fundSourceGapCount > 0 ? "block" : "ready",
    },
    {
      label: "토스 계좌·체결",
      title: "실제 계좌와 브로커 현실",
      priority: "무료 브로커 연동",
      currentPolicy: "계좌·호가·체결·주의 종목은 페이퍼와 보유 현실 확인에 쓰고 실거래 제출은 계속 차단한다.",
      impact: "화면에서 실행 가능성과 안전 차단을 분리한다.",
      nextAction: input.tossAttentionRequired ? "브로커 수집 상태 확인" : "read-only 검증 유지",
      tone: input.tossAttentionRequired ? "watch" : "ready",
    },
  ];
}
