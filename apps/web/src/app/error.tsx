"use client";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <section className="bento-card reveal" style={{ 
      minHeight: "400px", 
      display: "flex", 
      flexDirection: "column", 
      alignItems: "center", 
      justifyContent: "center",
      textAlign: "center",
      borderColor: "var(--accent-amber)",
      background: "rgba(245, 158, 11, 0.05)"
    }}>
      <div className="bento-badge" style={{ color: "var(--accent-amber)", borderColor: "var(--accent-amber)", marginBottom: "16px" }}>데이터 서버 연결 실패</div>
      <h1 style={{ fontSize: "clamp(2rem, 3vw, 3rem)", marginBottom: "16px" }}>투자 운영 데이터를 불러오지 못했다</h1>
      <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", marginBottom: "32px", maxWidth: "600px" }}>{error.message}</p>
      <button className="btn btn-primary" onClick={() => reset()} type="button">
        다시 연결
      </button>
    </section>
  );
}
