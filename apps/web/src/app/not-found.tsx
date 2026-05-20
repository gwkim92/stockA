import Link from "next/link";

export default function NotFound() {
  return (
    <section className="bento-card reveal" style={{ 
      minHeight: "400px", 
      display: "flex", 
      flexDirection: "column", 
      alignItems: "center", 
      justifyContent: "center",
      textAlign: "center",
      borderColor: "var(--accent-red)",
      background: "rgba(239, 68, 68, 0.05)"
    }}>
      <div className="bento-badge" style={{ color: "var(--accent-red)", borderColor: "var(--accent-red)", marginBottom: "16px" }}>경로 미등록</div>
      <h1 style={{ fontSize: "clamp(2rem, 3vw, 3rem)", marginBottom: "24px" }}>아직 존재하지 않는 투자 운영 화면이다.</h1>
      <Link className="btn btn-primary" href="/">
        대시보드로 돌아가기
      </Link>
    </section>
  );
}
