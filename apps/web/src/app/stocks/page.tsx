import { loadDiscovery } from "@/lib/discovery-data";
import { linked, priceAttention } from "@/lib/discovery-model";
import { DiscoveryFrame, DiscoveryMetrics } from "@/components/discovery/DiscoveryFrame";
import { StockExplorer } from "@/components/discovery/StockExplorer";
export const dynamic = "force-dynamic";
export const metadata = { title: "종목 탐색" };
export default async function StocksPage() {
  const result = await loadDiscovery("stocks"), data = result.data;
  return <DiscoveryFrame title="종목 탐색" eyebrow="COMPANY RESEARCH" description="기업을 찾고, 가격 기준일과 연결된 투자 논리를 비교하세요." result={result}>
    {data && <><DiscoveryMetrics items={[
      { name: "수신된 종목", value: `${data.rows.length}개`, note: "현재 목록의 종목 · 전체 시장 아님" },
      { name: "추천 연결", value: `${data.rows.filter(row => linked(row, "recommendation")).length}개`, note: "연결 존재 · 근거 충족과는 별개" },
      { name: "보유 연결", value: `${data.rows.filter(row => linked(row, "position")).length}개`, note: "반환된 포트폴리오 기록 기준" },
      { name: "가격 확인", value: `${data.rows.filter(row => priceAttention(row, data.asOfDate)).length}개`, note: "가격 누락 또는 스냅샷과 관측일 다름" },
    ]} /><StockExplorer data={data} /></>}
  </DiscoveryFrame>;
}
