import { loadDiscovery } from "@/lib/discovery-data";
import { object, count } from "@/lib/discovery-model";
import { DiscoveryFrame, DiscoveryMetrics } from "@/components/discovery/DiscoveryFrame";
import { StockExplorer } from "@/components/discovery/StockExplorer";
export const dynamic = "force-dynamic";
export const metadata = { title: "종목 탐색" };
export default async function StocksPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  const value = (key: string) => typeof params[key] === "string" ? params[key] as string : "";
  const search = { q: value("q").slice(0, 100), scope: value("scope"), cursor: value("cursor") };
  const result = await loadDiscovery("stocks", { search }), data = result.data;
  const summary = object(data?.raw.summary);
  const metric = (value: unknown) => count(value) === null ? "미확인" : `${count(value)}개`;
  return <DiscoveryFrame title="종목 탐색" eyebrow="COMPANY RESEARCH" description="기업을 찾고, 가격 기준일과 연결된 투자 논리를 비교하세요." result={result}>
    {data && <><DiscoveryMetrics items={[
      { name: "조회 대상 종목", value: metric(data.raw.stock_count), note: "API 조회 대상 전체 · 전체 시장 아님" },
      { name: "추천 연결", value: metric(summary.recommended_stock_count), note: "전체 조회 대상의 연결 수 · 근거 충족과는 별개" },
      { name: "보유 연결", value: metric(summary.held_stock_count), note: "전체 조회 대상의 포트폴리오 연결 수" },
      { name: "가격 확인", value: metric(summary.attention_stock_count), note: "가격 누락 또는 스냅샷과 관측일 다름" },
    ]} /><StockExplorer data={data} search={search} /></>}
  </DiscoveryFrame>;
}
