import type { DataHealthCollectionCard } from "@/components/operations/DataHealthOverview";
import { koCode } from "@/lib/korean-labels";

import {
  findPipelineRun,
  finishedAtLabel,
  runStateLabel,
  statusRiskClass,
} from "./dataHealthModel";
import type { DataHealthData, PipelineRun, TossInvestMarketData } from "./dataHealthTypes";

type DataHealthCollectionRuns = {
  readonly aiRun: PipelineRun | null;
  readonly decisionRun: PipelineRun | null;
  readonly marketPriceRun: PipelineRun | null;
  readonly newsEnrichmentRun: PipelineRun | null;
  readonly newsRun: PipelineRun | null;
  readonly remediationRun: PipelineRun | null;
};

type DataHealthCollectionStatusInput = {
  readonly data: DataHealthData;
  readonly runs: DataHealthCollectionRuns;
  readonly tossMarketData: TossInvestMarketData;
};

type DataHealthCollectionStatusSource = {
  readonly check: string;
  readonly index: string;
  readonly purpose: string;
  readonly run: PipelineRun | null;
  readonly title: string;
};

function buildCollectionStatusSources({
  data,
  runs,
  tossMarketData,
}: DataHealthCollectionStatusInput): readonly DataHealthCollectionStatusSource[] {
  return [
    {
      check: `최근 가격일 ${
        data.freshness.find((item) => item.dataset === "market.daily_price_bar")?.latest_observation_date
        ?? "미확인"
      }`,
      index: "01",
      purpose: "종목 가격과 차트, 모멘텀 지표의 원천이다.",
      run: runs.marketPriceRun,
      title: "주식 캔들",
    },
    {
      check: "수집 뉴스는 뉴스 화면에서 시간순으로 본다.",
      index: "02",
      purpose: "수집된 뉴스와 원문 화면의 원천이다.",
      run: runs.newsRun,
      title: "뉴스 원문",
    },
    {
      check: "AI 전 단계이므로 틀릴 수 있고, 이후 AI 분석과 검증이 보강한다.",
      index: "03",
      purpose: "뉴스를 종목, 테마, 방향 태그로 1차 정리한다.",
      run: runs.newsEnrichmentRun,
      title: "1차 분류 태깅",
    },
    {
      check: "화면을 열 때마다 AI를 새로 호출하지 않고 저장된 결과만 읽는다.",
      index: "04",
      purpose: "중요 뉴스를 구조화해 근거 항목을 만든다.",
      run: runs.aiRun,
      title: "AI 배치 분석",
    },
    {
      check: "차단 항목은 AI 차단 항목 화면에서 본다.",
      index: "05",
      purpose: "낮은 신뢰도, 알 수 없는 종목/테마, 저신호 뉴스를 차단한다.",
      run: runs.aiRun,
      title: "AI 결과 검증",
    },
    {
      check: "추천은 주문이 아니라 읽어야 할 상세 근거다.",
      index: "06",
      purpose: "가격, 뉴스, 사이클, 상위 흐름을 추천 점수로 합친다.",
      run: runs.decisionRun,
      title: "추천 신호",
    },
    {
      check: "보유 상태와 가상 매매 검증으로 이어진다.",
      index: "07",
      purpose: "투자 논리 공백, 성과 미측정, 보유 충돌을 운영 큐로 만든다.",
      run: runs.remediationRun,
      title: "보유 상태",
    },
    {
      check: `${koCode(tossMarketData.sync.status)} · ${tossMarketData.sync.requested_symbol_count.toLocaleString("ko-KR")}개 요청`,
      index: "08",
      purpose: "실제 증권사 화면에서 볼 가격·호가·체결·주의사항을 본다.",
      run: findPipelineRun(data, "toss-candles-us-shadow-daily", "tossinvest_market_data_sync"),
      title: "토스증권 브로커 데이터",
    },
  ];
}

export function buildDataHealthOverviewCollectionCards(
  input: DataHealthCollectionStatusInput,
): readonly DataHealthCollectionCard[] {
  return buildCollectionStatusSources(input).map((card) => ({
    check: card.check,
    finishedAt: finishedAtLabel(card.run),
    index: card.index,
    purpose: card.purpose,
    statusLabel: runStateLabel(card.run),
    statusTone: statusRiskClass(card.run?.health_status ?? "missing"),
    title: card.title,
  }));
}
