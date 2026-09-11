import { RecommendationOutcomes } from '@/components/review/RecommendationOutcomes';
import { loadRecommendationOutcomes } from '@/lib/recommendation-outcomes';
export const dynamic='force-dynamic';
export const metadata={title:'전체 추천 성과'};
export default async function Page({searchParams}:{searchParams:Promise<Record<string,string|string[]|undefined>>}) {
 return <RecommendationOutcomes result={await loadRecommendationOutcomes(await searchParams)}/>;
}
