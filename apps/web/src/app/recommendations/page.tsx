import Link from "next/link";
import { MetricStrip } from "@/components/research/MetricStrip";
import { RecommendationExplorer } from "@/components/research/RecommendationExplorer";
import { WorkspaceIcon } from "@/components/shell/WorkspaceIcon";
import { getRecommendations } from "@/lib/frontend-api";
import { sourceLimited } from "@/lib/recommendation-explorer-model";
import { isoDate } from "@/lib/research-home-model";
import styles from "./RecommendationsPage.module.css";
export const dynamic = "force-dynamic";
export const metadata = { title: "투자 후보" };
export default async function RecommendationsPage() {
  const { data } = await getRecommendations();
  const rows = data.recommendations;
  const limited = rows.filter(sourceLimited).length;
  const linked = rows.filter(row => row.linked_thesis_id && !sourceLimited(row)).length;
  return <div className={styles.page}>
    <header className={styles.heading}><div><span>INVESTMENT RESEARCH</span><h1>기업의 숫자 너머, 투자 논리까지</h1><p>연결된 근거와 반대 신호를 비교하며 검토할 기업을 좁혀보세요.</p></div><Link href="/stocks">기업 탐색 <WorkspaceIcon name="arrow" /></Link></header>
    <MetricStrip label="추천 현황" items={[
      { label: "수신된 후보", value: `${rows.length}개`, context: "현재 응답에 포함된 기업·상품" },
      { label: "논리 연결", value: `${linked}개`, context: "투자 논리 연결 · 원천 제한 제외" },
      { label: "원천 제한", value: `${limited}개`, context: "자료 한계를 먼저 확인할 후보" },
      { label: "분석 기준일", value: isoDate(data.as_of_date) ?? "미확인", context: "응답 시각과 원천 관측일은 별개" },
    ]} />
    <RecommendationExplorer rows={rows} />
    <aside className={styles.boundaryNote}><WorkspaceIcon name="shield" /><p>리서치용 후보 목록입니다. 모델 점수는 수익 확률이 아니며, 이 화면에서 주문이나 비중 변경은 실행하지 않습니다.</p><Link href="/trading-readiness">거래 안전 상태</Link></aside>
  </div>;
}
