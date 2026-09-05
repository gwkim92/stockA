import type { Metadata, Viewport } from "next";

import { DevelopmentDiagnostics } from "@/components/shell/DevelopmentDiagnostics";
import { WorkspaceShell } from "@/components/shell/WorkspaceShell";

import "./globals.css";
import "../styles/tokens.css";
import "../styles/workspace-overrides.css";

export const metadata: Metadata = {
  title: {
    default: "stockA · 투자 리서치",
    template: "%s | stockA",
  },
  description: "시장, 사이클, 뉴스, 기업 가치와 포트폴리오 위험을 연결하는 중장기 투자 리서치 워크스페이스.",
  icons: {
    icon: "/icon.svg",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f6f7fb",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        <DevelopmentDiagnostics />
        <WorkspaceShell>{children}</WorkspaceShell>
      </body>
    </html>
  );
}
