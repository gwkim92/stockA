import type { SVGProps } from "react";
export type WorkspaceIconName = "home" | "market" | "cycle" | "news" | "company" | "memo" | "portfolio" | "performance" | "search" | "menu" | "close" | "arrow" | "health" | "settings" | "source" | "shield";
const paths: Record<WorkspaceIconName, string> = {
  home: "M3 10 12 3l9 7v10a1 1 0 0 1-1 1h-6v-7h-4v7H4a1 1 0 0 1-1-1Z",
  market: "M3 20h18M5 16V9m7 7V4m7 12v-5", cycle: "M20 7a9 9 0 0 0-15-2L2 8m0-5v5h5m-3 9a9 9 0 0 0 15 2l3-3m0 5v-5h-5",
  news: "M4 3h13v17a1 1 0 0 0 2 0V8h3v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm2 5h7M6 12h7m-7 4h7",
  company: "M4 21V5l10-2v18M14 9h6v12M8 8h2m-2 5h2m-2 5h2M2 21h20", memo: "M5 3h10l4 4v14H5V3Zm10 0v5h4M8 12h8m-8 4h6",
  portfolio: "M9 7V3h6v4M3 7h18v14H3V7Zm0 6h18m-11 0v3h4v-3", performance: "M3 3v18h18M6 15l4-5 4 3 6-7m-5 0h5v5",
  search: "M16 16l5 5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z", menu: "M4 6h16M4 12h16M4 18h16", close: "m6 6 12 12M18 6 6 18",
  arrow: "M4 12h16m-6-6 6 6-6 6", health: "M2 12h5l3-8 4 16 3-8h5", settings: "M4 7h16M4 17h16M8 4v6m8 4v6",
  source: "m10 13 4-4M8 15l-2 2a3 3 0 0 1-4-4l5-5a3 3 0 0 1 4 0m2 1 2-2a3 3 0 0 1 4 4l-5 5a3 3 0 0 1-4 0", shield: "m12 3 9 4v5c0 5-9 9-9 9s-9-4-9-9V7l9-4Zm-4 9 3 3 5-6",
};
export function WorkspaceIcon({ name, ...props }: SVGProps<SVGSVGElement> & { name: WorkspaceIconName }) {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false" {...props}><path d={paths[name]} /></svg>;
}
