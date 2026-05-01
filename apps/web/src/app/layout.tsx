import type { Metadata, Viewport } from "next";
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
    default: "Stockanalysis Dashboard",
    template: "%s | Stockanalysis Dashboard",
  },
  description: "Modern modular investment cockpit for cycle, thesis, remediation, and data-health review.",
  icons: {
    icon: "/icon.svg",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0a0a0b",
};

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/remediation", label: "Remediation" },
  { href: "/data-health", label: "Data Health" },
  { href: "/cycles", label: "Cycles" },
  { href: "/events", label: "Events" },
  { href: "/themes/ANNUAL_REPORTING", label: "Themes" },
  { href: "/recommendations/AAPL-2024-11-01", label: "Recs" },
  { href: "/theses/AAPL-bootstrap-v1", label: "Thesis" },
  { href: "/portfolio/coverage", label: "Coverage" },
  { href: "/performance", label: "Performance" },
  { href: "/ai-evidence/sec-event-aapl-10k-20240928", label: "Evidence" },
] as const;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${displayFont.variable} ${bodyFont.variable}`}>
        <div className="shell">
          <header className="topbar reveal">
            <Link className="brand" href="/">
              <div className="brandMark">SA</div>
              <div className="brandText">
                <strong>Stockanalysis</strong>
                <small>Terminal</small>
              </div>
            </Link>
            <nav className="nav" aria-label="Primary navigation">
              {navItems.map((item) => (
                <Link href={item.href} key={item.href}>
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
