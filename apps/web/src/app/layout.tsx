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
  { href: "/", label: "현황" },
  { href: "/data-health", label: "수집" },
  { href: "/intelligence", label: "뉴스·AI" },
  { href: "/stocks", label: "종목" },
  { href: "/recommendations", label: "추천·보유" },
  { href: "/trading-readiness", label: "거래 안전" },
  { href: "/remediation", label: "할 일" },
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
                  {item.label}
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
