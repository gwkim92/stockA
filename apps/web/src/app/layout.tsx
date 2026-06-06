import type { Metadata, Viewport } from "next";
import type { Route } from "next";
import { Plus_Jakarta_Sans, Space_Grotesk } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const displayFont = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700", "800"],
  display: "swap",
});

const bodyFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "스톡애널리시스 대시보드",
    template: "%s | 스톡애널리시스 대시보드",
  },
  description: "사이클, 투자 논리, 보완 작업, 데이터 상태를 점검하는 장기 투자 운영 화면.",
  icons: {
    icon: "/icon.svg",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f3f4f0",
};

const navItems = [
  { href: "/", label: "현황", step: "01", description: "오늘 먼저 볼 판단 지도" },
  { href: "/data-health", label: "수집", step: "02", description: "데이터 수집과 자동화 상태" },
  { href: "/intelligence", label: "뉴스·AI", step: "03", description: "뉴스 해석과 AI 근거" },
  { href: "/cycle-map", label: "사이클", step: "04", description: "거시, 도메인, 테마, 종목 흐름 지도" },
  { href: "/stocks", label: "종목", step: "05", description: "종목별 뉴스, 흐름, 분석" },
  { href: "/recommendations", label: "추천·보유", step: "06", description: "추천 후보와 보유 검토" },
  { href: "/trading-readiness", label: "거래 안전", step: "07", description: "주문 차단과 안전 경계" },
  { href: "/remediation", label: "할 일", step: "08", description: "수정이 필요한 운영 항목" },
] as const;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body className={`${displayFont.variable} ${bodyFont.variable}`}>
        <div className="shell">
          <header className="topbar reveal">
            <Link className="brand" href="/" aria-label="스톡애널리시스 홈">
              <div className="brandMark" aria-hidden="true">
                <span />
                <span />
                <span />
                <span />
              </div>
              <div className="brandText">
                <strong>스톡애널리시스</strong>
                <small>중장기 투자 운영 시스템</small>
              </div>
            </Link>
            <nav className="nav" aria-label="주요 내비게이션">
              {navItems.map((item) => (
                <Link
                  aria-label={`${item.step}. ${item.label}: ${item.description}`}
                  data-step={item.step}
                  href={item.href as Route}
                  key={item.href}
                  title={item.description}
                >
                  <span>{item.label}</span>
                </Link>
              ))}
            </nav>
          </header>
          <main className="pageFrame">{children}</main>
        </div>
      </body>
    </html>
  );
}
