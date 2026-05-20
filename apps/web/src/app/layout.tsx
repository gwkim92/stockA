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
  { href: "/", index: "00", label: "전체 현황" },
  { href: "/data-health", index: "01", label: "데이터 수집" },
  { href: "/intelligence", index: "02", label: "분석 지도" },
  { href: "/stocks", index: "03", label: "종목" },
  { href: "/paper-trading", index: "04", label: "가상 거래" },
  { href: "/trading-readiness", index: "05", label: "거래 안전" },
  { href: "/remediation", index: "06", label: "해야 할 일" },
  { href: "/cycles", index: "07", label: "사이클" },
  { href: "/events", index: "08", label: "이벤트" },
  { href: "/themes/ANNUAL_REPORTING", index: "09", label: "테마" },
  { href: "/recommendations/AAPL-2024-11-01", index: "10", label: "추천" },
  { href: "/theses/AAPL-bootstrap-v1", index: "11", label: "투자 논리" },
  { href: "/portfolio/coverage", index: "12", label: "보유 검토" },
  { href: "/performance", index: "13", label: "성과" },
  { href: "/ai-evidence/ai-evidence-1", index: "14", label: "AI 근거" },
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
                <Link href={item.href as Route} key={item.href}>
                  <span className="navIndex">{item.index}</span>
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
