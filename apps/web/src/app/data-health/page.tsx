import { getDataHealth } from "@/lib/frontend-api";

import { DataHealthPageContent } from "./_components/DataHealthPageContent";
import { buildDataHealthPageModel } from "./_components/dataHealthPageModel";
export const dynamic = "force-dynamic";
export const metadata = { title: "데이터·자동화 상태" };

export default async function DataHealthPage() {
  const response = await getDataHealth();
  return <DataHealthPageContent model={buildDataHealthPageModel(response.data)} />;
}
