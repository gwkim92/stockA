import type { Route } from "next";
import type { WorkspaceIconName } from "./WorkspaceIcon";
export type NavigationItem = { readonly href: Route; readonly label: string; readonly description: string; readonly icon: WorkspaceIconName };
export const PRIMARY_NAVIGATION = [
  { href: "/", label: "리서치 홈", description: "시장 변화와 검토할 기업", icon: "home" },
  { href: "/market-map", label: "시장 현황", description: "금리·달러·원자재·거시 지표", icon: "market" },
  { href: "/cycle-map", label: "테마 사이클", description: "거시에서 기업으로 이어지는 흐름", icon: "cycle" },
  { href: "/intelligence", label: "뉴스 리서치", description: "시장 뉴스와 해석 근거", icon: "news" },
  { href: "/stocks", label: "기업 탐색", description: "기업·ETF의 재무와 가격 흐름", icon: "company" },
  { href: "/recommendations", label: "투자 후보", description: "판단서·핵심 근거·무효화 조건", icon: "memo" },
] as const satisfies readonly NavigationItem[];
export const RESEARCH_NAVIGATION = [
  { href: "/cycles", label: "사이클 목록", description: "테마별 상태를 목록으로 비교", icon: "cycle" },
  { href: "/events", label: "원천 뉴스", description: "수집된 뉴스와 공시", icon: "news" },
  { href: "/ai-evidence", label: "분석 근거", description: "구조화된 근거와 원문 대조", icon: "source" },
  { href: "/ai-evidence/results", label: "분석 결과", description: "완료된 근거 분석 결과", icon: "memo" },
  { href: "/ai-evidence/blocked", label: "보류된 근거", description: "근거 사용 제한 사유", icon: "shield" },
  { href: "/events/classification", label: "이벤트 분류", description: "원천 이벤트의 분류 상태", icon: "settings" },
] as const satisfies readonly NavigationItem[];
export const PORTFOLIO_NAVIGATION = [
  { href: "/portfolio/coverage", label: "보유 검토", description: "보유 논리·위험·분석 공백", icon: "portfolio" },
  { href: "/performance", label: "판단 성과", description: "수익률과 벤치마크 비교", icon: "performance" },
  { href: "/paper-trading", label: "가상 검증", description: "실거래 없는 검증 기록", icon: "shield" },
] as const satisfies readonly NavigationItem[];
export const OPERATIONS_NAVIGATION = [
  { href: "/data-health", label: "데이터 상태", description: "수집·분석 작업 상태", icon: "health" },
  { href: "/admin/ai-agents", label: "AI 운영", description: "모델과 운영 상태", icon: "settings" },
  { href: "/trading-readiness", label: "거래 안전", description: "실행 권한과 안전 조건", icon: "shield" },
  { href: "/remediation", label: "보완 작업", description: "해결할 데이터와 판단 공백", icon: "settings" },
] as const satisfies readonly NavigationItem[];
export const ALL_NAVIGATION: readonly NavigationItem[] = [...PRIMARY_NAVIGATION, ...PORTFOLIO_NAVIGATION, ...RESEARCH_NAVIGATION, ...OPERATIONS_NAVIGATION];
export function routeIsActive(pathname: string, href: Route): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}
/** Explicit parents for detail routes; choose one most-specific location. */
export function navigationContext(pathname: string): NavigationItem {
  const alias = pathname.startsWith("/themes/") ? "/cycle-map" : pathname.startsWith("/theses/") ? "/recommendations"
    : pathname.startsWith("/source-documents/") ? "/ai-evidence" : pathname;
  return [...ALL_NAVIGATION].sort((a, b) => b.href.length - a.href.length).find((item) => routeIsActive(alias, item.href)) ?? PRIMARY_NAVIGATION[0];
}
export function navigationResults(query: string): readonly NavigationItem[] {
  const value = query.trim().toLowerCase();
  return ALL_NAVIGATION.filter((item) => !value || `${item.label} ${item.description} ${item.href}`.toLowerCase().includes(value));
}
export function symbolDestination(query: string): string | null {
  const value = query.trim().toUpperCase();
  return /^(?:[A-Z][A-Z0-9.-]{0,9}|[0-9]{6})$/.test(value) ? `/stocks/${encodeURIComponent(value)}` : null;
}
