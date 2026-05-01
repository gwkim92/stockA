import type { Metadata, Viewport } from "next";
import { IBM_Plex_Sans, Newsreader } from "next/font/google";
import Link from "next/link";

import "./globals.css";

const displayFont = Newsreader({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700"],
  display: "swap",
});

const bodyFont = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Stockanalysis Cockpit",
    template: "%s | Stockanalysis Cockpit",
  },
  description: "Read-only investment cockpit for cycle, thesis, remediation, and data-health review.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f4efe4",
};

const navItems = [
  { href: "/", label: "Cockpit" },
  { href: "/remediation", label: "Remediation" },
  { href: "/data-health", label: "Data Health" },
  { href: "/cycles", label: "Cycles" },
  { href: "/recommendations/AAPL-2024-11-01", label: "Recommendation" },
  { href: "/theses/AAPL-bootstrap-v1", label: "Thesis" },
  { href: "/portfolio/coverage", label: "Coverage" },
] as const;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${displayFont.variable} ${bodyFont.variable}`}>
        <div className="grain" aria-hidden="true" />
        <header className="shell topbar">
          <Link className="brand" href="/">
            <span className="brandMark">SA</span>
            <span>
              <strong>Stockanalysis</strong>
              <small>long-horizon operating cockpit</small>
            </span>
          </Link>
          <nav className="nav" aria-label="Primary navigation">
            {navItems.map((item) => (
              <Link href={item.href} key={item.href}>
                {item.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="shell pageFrame">{children}</main>
      </body>
    </html>
  );
}
