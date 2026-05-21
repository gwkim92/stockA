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

const navGroups = [
  {
    label: "운영",
    items: [
      { href: "/", label: "현황" },
      { href: "/data-health", label: "수집" },
      { href: "/remediation", label: "할 일" },
    ],
  },
  {
    label: "분석",
    items: [
      { href: "/intelligence", label: "분석 지도" },
      { href: "/events", label: "뉴스·이벤트" },
      { href: "/ai-evidence/ai-evidence-15", label: "AI 후보" },
      { href: "/cycles", label: "사이클" },
    ],
  },
  {
    label: "투자",
    items: [
      { href: "/stocks", label: "종목" },
      { href: "/recommendations", label: "추천" },
      { href: "/portfolio/coverage", label: "보유 검토" },
      { href: "/performance", label: "성과" },
    ],
  },
  {
    label: "거래",
    items: [
      { href: "/paper-trading", label: "가상 거래" },
      { href: "/trading-readiness", label: "거래 안전" },
      { href: "/themes/ANNUAL_REPORTING", label: "테마 예시" },
    ],
  },
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
              {navGroups.map((group) => (
                <section className="navGroup" aria-label={`${group.label} 화면`} key={group.label}>
                  <span className="navGroupTitle">{group.label}</span>
                  <div className="navGroupLinks">
                    {group.items.map((item) => (
                      <Link href={item.href as Route} key={item.href}>
                        {item.label}
                      </Link>
                    ))}
                  </div>
                </section>
              ))}
            </nav>
          </header>
          <main className="pageFrame">{children}</main>
        </div>
      </body>
    </html>
  );
}
