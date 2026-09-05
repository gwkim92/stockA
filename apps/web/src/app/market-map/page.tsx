import { loadDiscovery } from "@/lib/discovery-data";
import { flattenMarket, marketAttention, objectRows } from "@/lib/discovery-model";
import { DiscoveryFrame, DiscoveryMetrics } from "@/components/discovery/DiscoveryFrame";
import { MarketExplorer, MarketEvidence } from "@/components/discovery/MarketExplorer";
export const dynamic = "force-dynamic";
export const metadata = { title: "시장 배경" };
export default async function MarketMapPage() {
  const result = await loadDiscovery("market"), data = result.data, indicators = flattenMarket(data?.rows ?? []);
  return <DiscoveryFrame title="시장 배경" eyebrow="CROSS-ASSET CONTEXT" description="금리·달러·원자재의 관측값과 기간별 움직임을 비교하세요. 시장 배경을 종목의 직접 투자 근거와 구분합니다." result={result}>
    {data && <><DiscoveryMetrics items={[
      { name: "수신된 지표", value: `${indicators.length}개`, note: `${data.rows.length}개 시장 영역 · 원래 목록 순서` },
      { name: "원천 확인", value: `${indicators.filter(row => marketAttention(row, result.requestedDate)).length}개`, note: "누락·지연·미확인 원천 또는 미래 관측일" },
      { name: "모델 체제 기록", value: data.raw.regimes == null ? "미확인" : `${objectRows(data.raw.regimes).length}개`, note: "원시 지표와 구분한 모델 해석" },
      { name: "상관관계 기록", value: data.raw.correlations == null ? "미확인" : `${objectRows(data.raw.correlations).length}쌍`, note: "상관관계는 인과관계가 아님" },
    ]} /><MarketExplorer data={data} requestedDate={result.requestedDate} /><MarketEvidence data={data} /></>}
  </DiscoveryFrame>;
}
