// Synthetic browser data derived from the repository's API contract examples, never a live source.
import { readFileSync } from "node:fs";
const example = name => JSON.parse(readFileSync(new URL(`../../../../docs/api/frontend/examples/${name}.json`, import.meta.url), "utf8"));
export function discoveryFixture(path, scenario) {
  if (!["/api/stocks", "/api/cycles", "/api/market-map"].includes(path)) return null;
  const today = new Date().toISOString().slice(0, 10), asOf = scenario === "historical" ? "2001-01-01" : today;
  let envelope;
  if (path === "/api/stocks") {
    envelope = example("stock-list");
    const base = envelope.data.stocks[0];
    envelope.data.stocks = [
      { ...base, latest_price: { ...base.latest_price, trade_date: asOf }, recommendation: { ...base.recommendation, recommendation_id: "recommendation-1", as_of_date: asOf }, position: { portfolio_name: "Long Term Paper", weight: 0.15, snapshot_date: asOf } },
      { ...structuredClone(base), symbol: "SPY", name: "SPDR S&P 500 ETF", instrument_id: "instrument-502", latest_price: { ...base.latest_price, close: 540, trade_date: asOf, change_pct: -0.008 }, recommendation: null, position: null },
      { ...structuredClone(base), symbol: "EROK", name: "EROK · 자료 확인", instrument_id: "instrument-503", latest_price: { trade_date: null, close: null, change_pct: null }, recommendation: { recommendation_id: "recommendation-2", score: null, as_of_date: asOf } },
      { ...structuredClone(base), symbol: "005930", name: "삼성전자", instrument_id: "instrument-504", market_code: "KR", currency_code: "KRW", latest_price: { trade_date: asOf, close: 72000, change_pct: 0 }, recommendation: null, position: null },
    ];
    delete envelope.data.stocks[2].position;
    envelope.data.stock_count = 4;
    envelope.data.summary.latest_price_date = asOf;
  } else if (path === "/api/cycles") {
    envelope = example("cycle-state-list");
    envelope.data.cycle_states = [
      { theme_key: "semiconductor", theme_name: "반도체", state: "expanding", previous_state: "forming", confidence: 0.81, instrument_count: 12, top_symbols: ["AAPL", "NVDA"], features: { event_intensity: 0.8, price_momentum: 0.6, fundamental_quality: 0.73 } },
      { theme_key: "power_infrastructure", theme_name: "전력 인프라", state: "confirming", previous_state: "expanding", confidence: 0.76, instrument_count: 6, top_symbols: ["GEV"], features: { event_intensity: 0.72, price_momentum: 0.55, fundamental_quality: 0.6 } },
      { theme_key: "healthcare", theme_name: "헬스케어", state: "forming", previous_state: "unknown", confidence: null, instrument_count: 3, top_symbols: ["LLY"], features: { event_intensity: 0, price_momentum: null, fundamental_quality: null } },
    ];
  } else {
    envelope = example("market-map");
    const dollar = envelope.data.groups[0].indicators[0];
    envelope.data.groups = [
      { group_code: "dollar", group_name: "달러", indicators: [{ ...dollar, indicator_code: "DXY", display_name: "달러 지수", quality_note_ko: "검증용 달러 지수 관측 기록입니다. 실제 투자 정보가 아닙니다.", latest_observation_date: asOf, latest_value: 102.3, return_1d: 0.002, return_5d: 0.01, return_20d: -0.014, return_60d: null, freshness_status: "fresh" }] },
      { group_code: "rates", group_name: "금리", indicators: [{ ...structuredClone(dollar), indicator_code: "US_10Y", display_name: "미국 10년 금리", quality_note_ko: "검증용 금리 기록입니다. 비교 기간의 변화율은 아직 측정되지 않았습니다.", latest_observation_date: asOf, latest_value: 4.1, return_1d: null, return_5d: null, return_20d: null, return_60d: null, freshness_status: "fresh" }] },
      { group_code: "metals", group_name: "금속", indicators: [{ ...structuredClone(dollar), indicator_code: "XAG_USD", display_name: "은 프록시 지수", quality_note_ko: "오래된 검증용 프록시 기록입니다. 최신 원천 확인 전에는 방향성 판단에 사용하지 않습니다.", preferred_provider: "fred", latest_observation_date: "2001-01-01", latest_value: 150, return_1d: null, return_5d: null, return_20d: 0.03, freshness_status: "stale" }, { ...structuredClone(dollar), indicator_code: "GOLD", display_name: "금 지표", quality_note_ko: "검증용 미측정 상태입니다. 값을 추정해 채우지 않습니다.", latest_observation_date: null, latest_value: null, return_1d: null, return_20d: null, freshness_status: "unknown" }] },
    ];
    envelope.data.correlations = [{ as_of_date: asOf, lookback_days: 60, primary_display_name: "AAPL", comparison_display_name: "달러 지수", correlation: -0.45, beta: -0.7, observation_count: 43, summary_ko: "테스트용 동조성 기록" }];
    envelope.data.snapshot_as_of_date = asOf;
  }
  envelope.data.as_of_date = asOf;
  envelope.generated_at = new Date().toISOString();
  if (scenario === "empty") envelope.data[path === "/api/stocks" ? "stocks" : path === "/api/cycles" ? "cycle_states" : "groups"] = [];
  if (scenario === "discovery-invalid") delete envelope.data[path === "/api/stocks" ? "stocks" : path === "/api/cycles" ? "cycle_states" : "groups"];
  if (scenario === "discovery-unknown") {
    envelope.data.as_of_date = null; envelope.data.snapshot_as_of_date = null;
    if (path === "/api/market-map") { delete envelope.data.regimes; delete envelope.data.correlations; delete envelope.data.quality_flags; }
  }
  return envelope;
}
