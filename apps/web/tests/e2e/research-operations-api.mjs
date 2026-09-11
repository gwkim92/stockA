// Synthetic UI scenarios. This server cannot call a model or change production.
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
const example = JSON.parse(readFileSync(new URL('../../../../docs/api/frontend/examples/data-health.json', import.meta.url), 'utf8'));
let scenario = 'mixed';
createServer(async (req, res) => {
  const send = (status, body) => { res.writeHead(status, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(body)); };
  if (req.url === '/__health') return send(200, { ok: true });
  if (req.url === '/__scenario' && req.method === 'POST') { let body=''; for await (const part of req) body += part; scenario=JSON.parse(body).scenario; return send(200, {scenario}); }
  if (req.headers.authorization !== 'Bearer operations-fixture-only') return send(401, {});
  if (req.method !== 'GET' || req.url !== '/api/data-health') return send(404, {});
  const payload = structuredClone(example);
  const states = ['due', 'waiting_for_source', 'reconcile', 'attempt_recorded', 'result_changed', 'retry_wait', 'current'];
  const rows = states.map((state, index) => ({symbol: ['AAPL','EROK','MSFT','ADBE','ADI','ADSK','A'][index], state,
    source_run_id: state === 'waiting_for_source' ? null : 123, source_collected_at: state === 'waiting_for_source' ? null : '2026-09-11T12:00:00Z',
    claim_id: index > 1 ? 456 + index : null, retry_after: state === 'retry_wait' ? '2026-09-12T12:00:00Z' : null, failure_code: null}));
  payload.data.research_refresh = {status: 'attention_required', observed_at: '2026-09-11T15:00:00Z', as_of_date: '2026-09-11',
    budget_resets_at: '2026-09-12T00:00:00Z', model_name: 'synthetic-no-model-call', daily_used: 5, daily_limit: 5, daily_remaining: 0,
    total_count: 7, attention_count: 3, counts: Object.fromEntries(states.map(state=>[state,1])), rows};
  if (scenario === 'unavailable') payload.data.research_refresh = {status:'unavailable', rows:[], counts:{}, daily_used:null, daily_limit:null};
  if (scenario === 'empty') Object.assign(payload.data.research_refresh, {status:'loaded',rows:[],counts:{},total_count:0,attention_count:0,daily_used:0,daily_remaining:5});
  send(200, payload);
}).listen(18773, '127.0.0.1');
