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
      <div className="bento-badge" style={{ color: "var(--accent-red)", borderColor: "var(--accent-red)", marginBottom: "16px" }}>Route Not Mapped</div>
      <h1 style={{ fontSize: "clamp(2rem, 3vw, 3rem)", marginBottom: "24px" }}>This cockpit route does not exist yet.</h1>
      <Link className="btn btn-primary" href="/">
        Return to Cockpit
      </Link>
    </section>
  );
}
