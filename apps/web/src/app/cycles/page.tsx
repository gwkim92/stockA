import { loadDiscovery } from "@/lib/discovery-data";
import { cycleSummary, label } from "@/lib/discovery-model";
import { koCode } from "@/lib/korean-labels";
import { DiscoveryFrame, DiscoveryMetrics } from "@/components/discovery/DiscoveryFrame";
import { CycleExplorer } from "@/components/discovery/CycleExplorer";
export const dynamic = "force-dynamic";
export const metadata = { title: "테마 사이클" };
export default async function CyclesPage() {
  const result = await loadDiscovery("cycles"), data = result.data, summary = cycleSummary(data?.rows ?? []);
  return <DiscoveryFrame title="테마 사이클" eyebrow="THEME OBSERVATORY" description="상태 전환과 뉴스·가격·기업 품질 특징을 나란히 확인하고, 관련 기업의 근거로 이어가세요." result={result}>
    {data && <><DiscoveryMetrics items={[
      { name: "관측 테마", value: `${data.rows.length}개`, note: `${koCode(label(data.raw.horizon_type))} · ${koCode(label(data.raw.strategy_name))}` },
      { name: "전환 관측", value: `${summary.changed}개`, note: `이전·현재 상태 미확인 ${summary.historyUnknown}개 별도` },
      { name: "특징 미측정", value: `${summary.gaps}개`, note: "하나 이상의 특징이 없거나 유효하지 않음" },
      { name: "테마–종목 연결 수", value: summary.memberships === null ? "미확인" : `${summary.memberships}건`, note: "중복 포함 · 고유 종목 수가 아님" },
    ]} /><CycleExplorer data={data} /></>}
  </DiscoveryFrame>;
}
