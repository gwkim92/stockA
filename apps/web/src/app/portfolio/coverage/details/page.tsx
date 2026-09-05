import Link from "next/link";
import LegacyPortfolioPage from "../LegacyPortfolioPage";
export const dynamic = "force-dynamic";
export const metadata = { title: "최신 위험예산·분석 상세" };
export default function PortfolioPolicyDetailsPage() {
  return <><p><Link href="/portfolio/coverage">← 보유 검토로 돌아가기</Link></p><p>최신 정책·운영 상세입니다. 보유 검토 화면에서 선택한 과거 기준일과는 별도로 조회합니다.</p><LegacyPortfolioPage /></>;
}
