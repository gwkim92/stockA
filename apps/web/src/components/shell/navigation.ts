import type { Route } from "next";

export type NavigationItem = {
  readonly href: Route;
  readonly label: string;
  readonly description: string;
};

export const PRIMARY_NAVIGATION = [
  { href: "/", label: "오늘", description: "오늘의 시장과 투자 우선순위" },
  { href: "/market-map", label: "시장", description: "지수·금리·달러·원자재·변동성" },
  { href: "/intelligence", label: "리서치", description: "사이클·뉴스·AI 투자 근거" },
  { href: "/stocks", label: "종목", description: "종목별 기업 분석과 가격 흐름" },
  { href: "/recommendations", label: "추천", description: "추천 후보와 판단 경계" },
  { href: "/portfolio/coverage", label: "포트폴리오", description: "보유 위험과 성과" },
] as const satisfies readonly NavigationItem[];

export const RESEARCH_NAVIGATION = [
  { href: "/cycle-map", label: "사이클 지도", description: "거시에서 종목까지 이어지는 흐름" },
  { href: "/events", label: "뉴스 원장", description: "수집된 원천 뉴스" },
  { href: "/ai-evidence", label: "AI 근거", description: "구조화·검증된 투자 근거" },
] as const satisfies readonly NavigationItem[];

export const PORTFOLIO_NAVIGATION = [
  { href: "/performance", label: "성과", description: "추천과 보유의 사후 성과" },
  { href: "/paper-trading", label: "가상 검증", description: "거래 전 안전 검증" },
] as const satisfies readonly NavigationItem[];

export const OPERATIONS_NAVIGATION = [
  { href: "/data-health", label: "데이터 상태", description: "수집·분석·자동화 상태" },
  { href: "/admin/ai-agents", label: "AI 운영", description: "모델·비용·OAuth 상태" },
  { href: "/trading-readiness", label: "거래 안전", description: "주문 권한과 안전장치" },
  { href: "/remediation", label: "보완 작업", description: "해결해야 할 판단 공백" },
] as const satisfies readonly NavigationItem[];

export function routeIsActive(pathname: string, href: Route): boolean {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
