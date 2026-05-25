import { getPortfolioCoverage } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "포트폴리오 커버리지" };

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function riskBudgetLabel(status: string) {
  if (status === "within_budget") {
    return "한도 내";
  }
  if (status === "needs_position_review") {
    return "비중 검토 필요";
  }
  if (status === "missing_position_snapshot") {
    return "스냅샷 없음";
  }
  return koCode(status);
}

function sizeStatusLabel(status: string) {
  if (status === "within_budget") {
    return "한도 내";
  }
  if (status === "below_rebalance_floor") {
    return "작은 비중";
  }
  if (status === "over_single_position_limit") {
    return "한도 초과";
  }
  if (status === "missing_weight") {
    return "비중 없음";
  }
  return koCode(status);
}

function sizeStatusClass(status: string) {
  if (status === "over_single_position_limit") {
    return "risk-high";
  }
  if (status === "below_rebalance_floor" || status === "missing_weight") {
    return "risk-medium";
  }
  return "risk-low";
}

export default async function PortfolioCoveragePage() {
  const response = await getPortfolioCoverage();
  const data = response.data;
  const allocationPolicy = data.allocation_policy;
  const riskBudget = data.risk_budget;
  const hasPositions = data.positions.length > 0;
  const investedWeight = Math.max(0, 1 - (data.summary.cash_weight ?? 0));
  const thesisCoverageRatio = investedWeight > 0
    ? Math.max(0, Math.min(1, (investedWeight - data.summary.missing_thesis_weight) / investedWeight))
    : 0;
  const thesisReady = hasPositions && data.summary.missing_thesis_count === 0;
  const outcomeCoverageRatio = data.summary.weight_coverage_ratio;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          커버리지 지도 • {koLabel(data.portfolio_name)} • {koCode(data.strategy_name)} • {data.as_of_date}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>포트폴리오 커버리지 확인</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
              투자 논리 연결과 성과 측정을 분리해서 본다. 투자 논리가 연결되면 보유 검토는 가능하지만,
              장기 성과 측정 window가 아직 끝나지 않으면 성과 귀속은 계속 대기 상태로 남는다.
            </p>
          </div>
          
          <div style={{ 
            padding: "20px 32px", 
            background: thesisReady ? "rgba(16, 185, 129, 0.1)" : "rgba(245, 158, 11, 0.1)",
            border: `1px solid ${thesisReady ? "rgba(16, 185, 129, 0.2)" : "rgba(245, 158, 11, 0.2)"}`,
            borderRadius: "var(--radius-md)",
            textAlign: "center"
          }}>
            <span className="metric-sub" style={{ color: thesisReady ? "var(--accent-green)" : "var(--accent-amber)" }}>투자 논리 연결률</span>
            <div style={{ fontSize: "2.5rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0" }}>
              {formatPercent(thesisCoverageRatio)}
            </div>
            <div style={{ fontSize: "0.85rem", color: thesisReady ? "var(--accent-green)" : "var(--accent-amber)", fontWeight: 600, textTransform: "uppercase" }}>
              {thesisReady ? "연결됨" : "보강 필요"}
            </div>
          </div>
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card">
          <span className="metric-label">포지션</span>
          <strong className="metric-value">{data.summary.position_count}</strong>
          <span className="metric-sub">
            {hasPositions
              ? `${data.summary.position_count - data.summary.missing_thesis_count}개 투자 논리 연결`
              : "해당 기준일 포지션 스냅샷 없음"}
          </span>
        </article>
        
        <article className="bento-card" style={{ borderColor: data.summary.missing_thesis_count > 0 ? "var(--accent-red)" : "var(--border-light)" }}>
          <span className="metric-label">투자 논리 누락</span>
          <strong className="metric-value" style={{ color: data.summary.missing_thesis_count > 0 ? "var(--accent-red)" : "var(--text-primary)" }}>
            {data.summary.missing_thesis_count}
          </strong>
          <span className="metric-sub">비중 {formatPercent(data.summary.missing_thesis_weight)}</span>
        </article>

        <article className="bento-card">
          <span className="metric-label">성과 측정 커버리지</span>
          <strong className="metric-value">{formatPercent(outcomeCoverageRatio)}</strong>
          <span className="metric-sub">장기 outcome 기준</span>
        </article>

        <article className="bento-card">
          <span className="metric-label">성과 측정 누락</span>
          <strong className="metric-value">{data.summary.missing_outcome_count}</strong>
          <span className="metric-sub">측정 종료 {data.coverage_measurement_end_date}</span>
        </article>

        <article className="bento-card">
          <span className="metric-label">현금 비중</span>
          <strong className="metric-value">{formatPercent(data.summary.cash_weight)}</strong>
          <span className="metric-sub">명시적 배분</span>
        </article>

        <article className="bento-card span-4" style={{ borderColor: riskBudget.status === "needs_position_review" ? "var(--accent-amber)" : "var(--border-light)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">위험 예산 / 포지션 크기</span>
              <h2>보유 비중이 정책 한도 안에 있는지 본다</h2>
            </div>
            <span className={`risk-tag ${riskBudget.status === "needs_position_review" ? "risk-medium" : "risk-low"}`}>
              {riskBudgetLabel(riskBudget.status)}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            추천 점수는 매수·매도 명령이 아니다. 실제 보유 비중은 단일 종목 한도, 리밸런싱 기준,
            투자 논리와 성과 커버리지를 함께 보고 따로 판단한다.
          </p>
          <div className="status-rail compact-rail" aria-label="위험 예산 요약">
            <article className="rail-cell">
              <span>단일 종목 상한</span>
              <strong>{formatPercent(allocationPolicy.max_single_position_weight)}</strong>
              <small>{koCode(allocationPolicy.policy_scope)} 정책</small>
            </article>
            <article className="rail-cell">
              <span>최대 보유</span>
              <strong>{riskBudget.largest_position_symbol || "없음"}</strong>
              <small>{formatPercent(riskBudget.largest_position_weight)}</small>
            </article>
            <article className="rail-cell">
              <span>한도 초과</span>
              <strong>{riskBudget.over_single_position_limit_count}</strong>
              <small>축소/검토 후보</small>
            </article>
            <article className="rail-cell">
              <span>작은 비중</span>
              <strong>{riskBudget.below_rebalance_floor_count}</strong>
              <small>{formatPercent(allocationPolicy.min_rebalance_target_weight)} 미만</small>
            </article>
            <article className="rail-cell">
              <span>투자 비중</span>
              <strong>{formatPercent(riskBudget.invested_weight)}</strong>
              <small>현금 제외</small>
            </article>
          </div>
        </article>

        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">포지션 커버리지</span>
            <h2 style={{ fontSize: "1.5rem" }}>보유 종목 검토 지도</h2>
          </div>
          
          <div className="bento-list" style={{ gap: "8px" }}>
            <div className="bento-list-item" style={{ background: "transparent", borderBottom: "1px solid var(--border-light)", borderRadius: 0, paddingBottom: "16px" }}>
              <div style={{ flexDirection: "row", width: "100%", gap: "24px" }}>
                <span className="metric-sub" style={{ width: "100px" }}>심볼</span>
                <span className="metric-sub" style={{ width: "100px" }}>비중</span>
                <span className="metric-sub" style={{ width: "130px" }}>비중 한도</span>
                <span className="metric-sub" style={{ width: "140px" }}>투자 논리</span>
                <span className="metric-sub" style={{ width: "140px" }}>성과</span>
                <span className="metric-sub" style={{ flex: 1 }}>필요 조치</span>
              </div>
            </div>

            {!hasPositions ? (
              <p className="empty-state">
                이 기준일에 보유 포지션 스냅샷이 없어 커버리지 표를 만들 수 없다. 포트폴리오 포지션 적재 배치가
                최신 영업일 스냅샷을 저장하면 심볼, 비중, 투자 논리, 성과 측정 상태가 여기에 표시된다.
              </p>
            ) : null}
            
            {data.positions.map((position) => (
              <div className="bento-list-item" key={position.instrument_id} style={{ alignItems: "flex-start" }}>
                <div style={{ flexDirection: "row", width: "100%", gap: "24px", alignItems: "center" }}>
                  <strong style={{ width: "100px", fontSize: "1.1rem" }}>{position.symbol}</strong>
                  <span style={{ width: "100px", color: "var(--text-primary)", fontWeight: 500 }}>{formatPercent(position.weight)}</span>
                  <span style={{ width: "130px" }}>
                    <span className={`risk-tag ${sizeStatusClass(position.position_size_status)}`}>
                      {sizeStatusLabel(position.position_size_status)}
                    </span>
                  </span>
                  <span style={{ 
                    width: "140px", 
                    color: position.active_thesis_id ? 'var(--accent-green)' : 'var(--accent-red)'
                  }}>
                    {position.active_thesis_id ? "연결됨" : "논리 누락"}
                  </span>
                  <span style={{ 
                    width: "140px", 
                    color: position.coverage_status === 'covered' ? 'var(--accent-green)' : 'var(--text-secondary)'
                  }}>
                    {position.coverage_status === "missing_outcome" ? "측정 대기" : koCode(position.outcome_status)}
                  </span>
                  <span style={{ flex: 1, color: "var(--text-primary)", fontWeight: 500 }}>
                    {koLabel(position.action)}
                    <small style={{ display: "block", color: "var(--text-secondary)", fontWeight: 400, marginTop: "4px" }}>
                      {position.position_size_note}
                    </small>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
