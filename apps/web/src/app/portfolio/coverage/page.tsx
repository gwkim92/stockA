import { getPortfolioCoverage, getTradingReadiness } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "포트폴리오 커버리지" };

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function recordString(record: Record<string, unknown> | undefined, key: string) {
  const value = record?.[key];
  return typeof value === "string" ? value : "";
}

function recordNumber(record: Record<string, unknown> | undefined, key: string) {
  const value = record?.[key];
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
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

function concentrationStatusLabel(status: string) {
  if (status === "within_budget") {
    return "집중도 한도 내";
  }
  if (status === "needs_concentration_review") {
    return "집중도 검토 필요";
  }
  if (status === "classification_gap") {
    return "분류 보강 필요";
  }
  if (status === "missing_position_snapshot") {
    return "스냅샷 없음";
  }
  return koCode(status);
}

function concentrationStatusClass(status: string) {
  if (status === "needs_concentration_review") {
    return "risk-high";
  }
  if (status === "classification_gap" || status === "missing_position_snapshot") {
    return "risk-medium";
  }
  return "risk-low";
}

function exposureStatusLabel(status: string) {
  if (status === "over_limit") {
    return "한도 초과";
  }
  if (status === "within_limit") {
    return "한도 내";
  }
  return koCode(status);
}

function candidateSeverityClass(severity: string) {
  if (severity === "high") {
    return "risk-high";
  }
  if (severity === "medium") {
    return "risk-medium";
  }
  return "risk-low";
}

function candidateDirectionLabel(direction: string) {
  if (direction === "overweight") {
    return "과대 보유";
  }
  if (direction === "underweight") {
    return "과소 보유";
  }
  return koCode(direction);
}

type ExposureRow = {
  exposure_key: string;
  exposure_name: string;
  exposure_weight: number;
  position_count: number;
  symbols: string[];
  limit: number;
  excess_weight: number;
  status: string;
};

function ExposureList({ empty, items }: { empty: string; items: ExposureRow[] }) {
  if (items.length === 0) {
    return <p className="empty-state" style={{ margin: 0 }}>{empty}</p>;
  }

  return (
    <div className="bento-list" style={{ gap: "8px" }}>
      {items.map((item) => (
        <div className="bento-list-item" key={item.exposure_key}>
          <div>
            <span className={`risk-tag ${item.status === "over_limit" ? "risk-high" : "risk-low"}`}>
              {exposureStatusLabel(item.status)}
            </span>
            <strong>{koLabel(item.exposure_name)}</strong>
            <span>
              {item.symbols.join(", ") || "심볼 없음"} · {item.position_count}개 포지션
            </span>
          </div>
          <div style={{ textAlign: "right", minWidth: "120px" }}>
            <strong>{formatPercent(item.exposure_weight)}</strong>
            <small style={{ display: "block", color: "var(--text-secondary)" }}>
              한도 {formatPercent(item.limit)}
            </small>
          </div>
        </div>
      ))}
    </div>
  );
}

export default async function PortfolioCoveragePage() {
  const [response, tradingResponse] = await Promise.all([getPortfolioCoverage(), getTradingReadiness()]);
  const data = response.data;
  const riskGuardrail = tradingResponse.data.portfolio_risk_budget_guardrail;
  const benchmarkDrift = riskGuardrail.benchmark_drift;
  const benchmarkDriftCalculated = benchmarkDrift?.drift_calculated === true;
  const benchmarkCode = recordString(benchmarkDrift, "benchmark_code") || "벤치마크";
  const benchmarkActiveShare = recordNumber(benchmarkDrift, "active_share");
  const benchmarkSource = recordString(benchmarkDrift, "benchmark_source") || recordString(benchmarkDrift, "source_type");
  const allocationPolicy = data.allocation_policy;
  const riskBudget = data.risk_budget;
  const candidateReview = riskBudget.rebalance_candidate_review;
  const concentration = riskBudget.concentration;
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

        <article className="bento-card span-4" style={{ borderColor: riskGuardrail.paper_validation_input_allowed ? "var(--border-light)" : "var(--accent-red)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">저장된 위험 예산 검증</span>
              <h2>이 검증 결과가 가상 거래를 막고 있는지 본다</h2>
            </div>
            <span className={`risk-tag ${riskGuardrail.paper_validation_input_allowed ? "risk-low" : "risk-high"}`}>
              {riskGuardrail.paper_validation_input_allowed ? "입력 가능" : "입력 차단"}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            화면에서 계산한 집중도와 별도로, backend guardrail runner가 저장한 최신 결과를 paper validation이 읽는다.
            이 값이 차단이면 가상 거래 검증은 충돌 수가 0이어도 실패 상태로 남는다.
          </p>
          <div className="status-rail compact-rail" aria-label="저장된 위험 예산 검증 요약">
            <article className="rail-cell">
              <span>검증 ID</span>
              <strong>{riskGuardrail.eval_run_id || "없음"}</strong>
              <small>{riskGuardrail.status}</small>
            </article>
            <article className="rail-cell">
              <span>판정</span>
              <strong>{koCode(riskGuardrail.risk_gate_decision)}</strong>
              <small>{riskGuardrail.effective_snapshot_date || "기준일 없음"}</small>
            </article>
            <article className="rail-cell rail-critical">
              <span>차단 사유</span>
              <strong>{riskGuardrail.blocking_reasons.length}</strong>
              <small>{riskGuardrail.blocking_reasons.map((reason) => koCode(reason)).join(", ") || "없음"}</small>
            </article>
            <article className="rail-cell">
              <span>벤치마크 drift</span>
              <strong>
                {benchmarkDriftCalculated ? formatPercent(benchmarkActiveShare) : "미계산"}
              </strong>
              <small>
                {benchmarkDriftCalculated
                  ? `${benchmarkCode} · ${benchmarkSource || "구성비 저장됨"}`
                  : "구성비 없으면 추정하지 않음"}
              </small>
            </article>
          </div>
        </article>

        <article className="bento-card span-4" style={{ borderColor: candidateReview.candidate_count > 0 ? "var(--accent-red)" : "var(--border-light)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">벤치마크 대비 리밸런싱 검토</span>
              <h2>SPY와 비교해 어느 종목 비중이 과하게 다른지 본다</h2>
            </div>
            <span className={`risk-tag ${candidateReview.candidate_count > 0 ? "risk-high" : "risk-low"}`}>
              {candidateReview.candidate_count > 0 ? "검토 후보 있음" : "큰 괴리 없음"}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            이 표는 주문 지시가 아니다. {candidateReview.benchmark_code || benchmarkCode} 기준 active weight가 큰 종목을
            thesis, 세금/비용, 섹터 집중도와 함께 검토하기 위한 읽기 전용 후보 목록이다.
          </p>
          <div className="status-rail compact-rail" aria-label="벤치마크 리밸런싱 검토 요약" style={{ marginBottom: "20px" }}>
            <article className="rail-cell">
              <span>active share</span>
              <strong>{formatPercent(candidateReview.active_share)}</strong>
              <small>{candidateReview.benchmark_source || benchmarkSource || "source 없음"}</small>
            </article>
            <article className="rail-cell">
              <span>구성비 커버리지</span>
              <strong>{formatPercent(candidateReview.composition_coverage_weight)}</strong>
              <small>{candidateReview.source_as_of_date || "기준일 없음"}</small>
            </article>
            <article className="rail-cell rail-critical">
              <span>검토 후보</span>
              <strong>{candidateReview.candidate_count}</strong>
              <small>자동 주문 {candidateReview.automatic_order_allowed ? "허용" : "금지"}</small>
            </article>
            <article className="rail-cell">
              <span>주문 경계</span>
              <strong>{koCode(candidateReview.order_boundary)}</strong>
              <small>broker submit {candidateReview.broker_submit_allowed ? "허용" : "금지"}</small>
            </article>
          </div>
          {candidateReview.candidates.length === 0 ? (
            <p className="empty-state" style={{ margin: 0 }}>
              현재 threshold 기준에서 별도 리밸런싱 검토 후보가 없다.
            </p>
          ) : (
            <div className="ledger-table-wrap">
              <table className="ledger-table data-health-table">
                <thead>
                  <tr>
                    <th scope="col">순위</th>
                    <th scope="col">종목</th>
                    <th scope="col">상태</th>
                    <th scope="col">현재/벤치마크</th>
                    <th scope="col">active weight</th>
                    <th scope="col">검토 이유</th>
                  </tr>
                </thead>
                <tbody>
                  {candidateReview.candidates.map((candidate) => (
                    <tr key={`${candidate.priority}-${candidate.symbol}-${candidate.direction}`}>
                      <td>{candidate.priority.toString().padStart(2, "0")}</td>
                      <td><strong>{candidate.symbol}</strong></td>
                      <td>
                        <span className={`risk-tag ${candidateSeverityClass(candidate.severity)}`}>
                          {candidateDirectionLabel(candidate.direction)}
                        </span>
                      </td>
                      <td>{formatPercent(candidate.current_weight)} / {formatPercent(candidate.benchmark_weight)}</td>
                      <td>{formatPercent(candidate.active_weight)}</td>
                      <td>
                        {candidate.rationale}
                        <small style={{ display: "block", color: "var(--text-secondary)", marginTop: "4px" }}>
                          {koCode(candidate.order_boundary)}
                        </small>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        <article className="bento-card span-4" style={{ borderColor: concentration.status === "needs_concentration_review" ? "var(--accent-red)" : "var(--border-light)" }}>
          <div className="section-heading">
            <div>
              <span className="metric-sub">섹터·테마 집중도</span>
              <h2>한 종목이 아니라 같은 흐름에 얼마나 몰렸는지 본다</h2>
            </div>
            <span className={`risk-tag ${concentrationStatusClass(concentration.status)}`}>
              {concentrationStatusLabel(concentration.status)}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
            같은 섹터나 테마에 여러 종목이 묶이면 종목 수가 분산되어 보여도 실제 위험은 한 방향으로 움직일 수 있다.
            이 표는 주문 지시가 아니라 포트폴리오 검토 우선순위를 정하기 위한 노출도 지도다.
          </p>
          <div className="status-rail compact-rail" aria-label="집중도 정책 요약" style={{ marginBottom: "20px" }}>
            <article className="rail-cell">
              <span>섹터 한도</span>
              <strong>{formatPercent(concentration.max_sector_weight)}</strong>
              <small>초과 시 집중도 검토</small>
            </article>
            <article className="rail-cell">
              <span>테마 한도</span>
              <strong>{formatPercent(concentration.max_theme_weight)}</strong>
              <small>상위 흐름 노출</small>
            </article>
            <article className="rail-cell">
              <span>미분류 한도</span>
              <strong>{formatPercent(concentration.max_unclassified_weight)}</strong>
              <small>데이터 품질 gap</small>
            </article>
            <article className="rail-cell">
              <span>미분류 비중</span>
              <strong>{formatPercent(concentration.unclassified_weight)}</strong>
              <small>{concentration.unclassified_symbols.join(", ") || "없음"}</small>
            </article>
            <article className="rail-cell">
              <span>초과 그룹</span>
              <strong>{concentration.over_limit_count}</strong>
              <small>섹터/테마 합산</small>
            </article>
          </div>

          <div className="bento-grid">
            <article className="bento-card span-2">
              <span className="metric-sub">섹터 노출</span>
              <h3 style={{ fontSize: "1.15rem", margin: "6px 0 12px" }}>산업 방향으로 묶인 위험</h3>
              <ExposureList empty="섹터 분류가 아직 없다. 종목 분류 데이터를 보강해야 한다." items={concentration.sector_exposures} />
            </article>
            <article className="bento-card span-2">
              <span className="metric-sub">테마 노출</span>
              <h3 style={{ fontSize: "1.15rem", margin: "6px 0 12px" }}>거시·테마 흐름으로 묶인 위험</h3>
              <ExposureList empty="테마 분류가 아직 없다. 뉴스/사이클 연결을 먼저 보강해야 한다." items={concentration.theme_exposures} />
            </article>
          </div>
        </article>

        <article className="bento-card span-4">
          <div className="section-heading">
            <div>
              <span className="metric-sub">리밸런싱 우선순위</span>
              <h2>바로 주문하지 않고 무엇을 먼저 검토할지 정한다</h2>
            </div>
            <span className="risk-tag risk-medium">읽기 전용</span>
          </div>
          {riskBudget.rebalance_priorities.length === 0 ? (
            <p className="empty-state" style={{ margin: 0 }}>
              현재 정책 기준에서 우선 검토할 포지션이 없다.
            </p>
          ) : (
            <div className="bento-list">
              {riskBudget.rebalance_priorities.map((priority) => (
                <div className="bento-list-item" key={`${priority.symbol}-${priority.action}`}>
                  <div>
                    <span className="metric-sub">우선순위 {priority.priority}</span>
                    <strong>{priority.symbol} · {formatPercent(priority.current_weight)}</strong>
                    <span>{koCode(priority.action)}</span>
                  </div>
                  <span style={{ color: "var(--text-secondary)", maxWidth: "520px" }}>
                    {priority.reason}
                  </span>
                </div>
              ))}
            </div>
          )}
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
