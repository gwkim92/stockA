export default function Loading() {
  return (
    <div className="pageStack">
      <section className="bento-card reveal" aria-busy="true" style={{ 
        minHeight: "400px", 
        display: "flex", 
        flexDirection: "column", 
        alignItems: "center", 
        justifyContent: "center",
        textAlign: "center",
        background: "rgba(255, 255, 255, 0.02)"
      }}>
        <div className="bento-badge" style={{ 
          color: "var(--text-secondary)", 
          borderColor: "var(--border-light)", 
          marginBottom: "16px",
          animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite" 
        }}>
          운영 데이터를 불러오는 중
        </div>
        <h1 style={{ fontSize: "clamp(2rem, 3vw, 3rem)" }}>투자 운영 스냅샷 준비 중</h1>
        
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: .5; }
          }
        `}} />
      </section>
    </div>
  );
}
