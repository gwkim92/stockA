// Synthetic data only. No model calls, account access or production database.
import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const produced=JSON.parse(execFileSync('python3',[fileURLToPath(new URL('../contracts/research-producer.py',import.meta.url))],{encoding:'utf8',timeout:15000,maxBuffer:1000000}));
const example=name=>JSON.parse(readFileSync(new URL(`../../../../docs/api/frontend/examples/${name}.json`,import.meta.url),'utf8'));
let scenario='healthy',requests=[];
const server=createServer(async(req,res)=>{
 const path=new URL(req.url,'http://127.0.0.1').pathname;
 const send=(status,payload)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(payload));};
 if(path==='/__health')return send(200,{ok:true});
 if(path==='/__requests')return send(200,requests);
 if(path==='/__scenario'&&req.method==='POST'){let body='';for await(const part of req)body+=part;scenario=JSON.parse(body).scenario;requests=[];return send(200,{scenario});}
 requests.push({path,method:req.method});
 if(req.headers.authorization!=='Bearer notebook-fixture-only')return send(401,{error:'auth'});
 if(scenario==='all-down')return send(503,{error:'private-api-error'});
 if(path.startsWith('/api/stocks/')){
  const symbol=path.split('/').pop();const p=example(symbol==='SPY'?'stock-detail-spy':'stock-detail'),d=p.data;
  Object.assign(d,{symbol,name:symbol==='AAPL'?'Apple Inc.':symbol==='SPY'?'SPDR S&P 500 ETF':'Microsoft Corporation',instrument_id:`instrument-${symbol.toLowerCase()}`,as_of_date:'2026-09-05'});
  d.equity_research={artifact_id:'research-fixture-1',provider:scenario==='fallback'?'fixture':'codex_oauth',model_name:'test-only',as_of_date:'2026-09-04',
    korean_summary:'합성 검증 자료: 서비스 매출의 반복성과 현금흐름이 투자 논리를 뒷받침하는지 검토합니다.',
    key_points:['서비스 매출 성장과 고객 유지율을 함께 확인한다.','매출 증가가 현금흐름 개선으로 이어지는지 확인한다.'],
    risks:['규제 비용이 늘거나 고객 유지율이 낮아지면 수익성 가정을 재검토한다.'],
    invalidation_conditions:['현금흐름이 비용 증가를 흡수하지 못하면 기존 판단을 보류한다.'],
    catalysts:['다음 실적에서 서비스 매출과 현금흐름을 다시 대조한다.'],
    source_document_ids:['source-document-1','source-document-2']};
  d.recommendation={recommendation_id:'recommendation-1',linked_thesis_id:'thesis-1',score:0.7};
  d.recent_events=[{event_id:'event-1',title:'Service growth and cash flow',korean_title:'서비스 성장과 현금흐름',source_document_id:'source-document-1',ai_evidence_id:'ai-evidence-1',event_at:'2026-09-03T00:00:00Z'},
    {event_id:'event-2',title:'Risks and regulation',korean_title:'규제 비용과 반대 가능성',source_document_id:'source-document-2',event_at:'2026-09-04T00:00:00Z'}];d.macro_flow_impacts=[];
  if(scenario==='changed')d.equity_research.key_points=['변경된 분석: 비용과 성장의 관계를 다시 확인한다.'];
  if(scenario==='no-sources'){d.equity_research.source_document_ids=[];d.recent_events=[];}
  if(scenario==='no-research'){delete d.equity_research;d.recent_events=[];}
  if(scenario==='blocked')d.professional_source_guardrail={blocked:true,status:'blocked_source'};
  if(scenario==='wrong-company')d.symbol='OTHER';
  if(scenario.startsWith('producer-') && Object.hasOwn(produced,scenario.slice(9))){
    d.equity_research=structuredClone(produced[scenario.slice(9)]);d.recent_events=[];d.macro_flow_impacts=[];
  }
  if(scenario==='producer-malformed-events'){
    d.equity_research=structuredClone(produced.malformed);
    d.macro_flow_impacts=[{source_document_id:'source-document-3',korean_title:'별도 시장 배경 자료'}];
  }
  // Deliberately corrupt transport metadata, not the producer's validation result.
  if(scenario==='producer-metadata-invalid'){
    d.equity_research=structuredClone(produced.valid);
    d.equity_research.data_quality={policy:'unexpected-private-metadata'};
    d.recent_events=[];d.macro_flow_impacts=[];
  }
  if(symbol==='SPY'){delete d.equity_research;d.recent_events=[];}
  return send(200,p);
 }
 if(path.startsWith('/api/source-documents/')){
  if(scenario==='source-down')return send(503,{error:'private-source-body'});
  if(scenario==='source-slow'){res.writeHead(200,{'Content-Type':'application/json'});res.write('{"data":');const timer=setTimeout(()=>res.end('{} }'),30000);res.on('close',()=>clearTimeout(timer));return;}
  const id=path.split('/').pop(),p=example('source-document-detail');p.data.document_id=id;
  p.data.title=id==='source-document-1'?'Service revenue and cash-flow observations':'Regulatory costs and alternative explanations';
  p.data.filed_at=scenario==='future-source'?'2026-09-06T00:00:00Z':'2026-09-03T00:00:00Z';
  p.data.period_end='2026-06-30';p.data.retrieval.fetched_at='2026-09-04T01:00:00Z';p.data.korean_summary=null;
  p.data.excerpts=[{chunk_id:'chunk-1',section:id==='source-document-1'?'Revenue and retention':'Risks and uncertainty',locator:'검증용 발췌 · 01',
    summary:id==='source-document-1'?'Synthetic excerpt summary: service revenue rose 12% year over year. Customer retention and cash conversion require separate review. This is not current company data.':'Synthetic excerpt summary: regulatory costs may offset revenue growth. Customer retention could weaken, and revenue growth alone does not demonstrate higher free cash flow.'}];
  p.links.source_document=`/api/source-documents/${id}`;
  if(scenario==='wrong-source'){p.data.document_id='different-document';p.links.source_document='/api/source-documents/different-document';}
  if(scenario==='literal')p.data.excerpts[0].summary='<script>window.compromised=true</script> stored literal text';
  return send(200,p);
 }
 if(path==='/api/events'){
  const p=example('event-list');p.data.events=[{event_id:'event-1',symbol:'AAPL',title:'Service revenue',korean_title:'서비스 성장 검토',event_at:'2026-09-03T00:00:00Z',source_document_id:'source-document-1',ai_evidence_id:'ai-evidence-1'}];p.pagination={has_more:false,next_cursor:null};return send(200,p);
 }
 if(path==='/api/theses/thesis-1'){const p=example('thesis-detail');p.data.thesis_id='thesis-1';return send(200,p);}
 return send(404,{error:'fixture route unavailable'});
});
server.listen(18770,'127.0.0.1');process.on('SIGTERM',()=>server.close(()=>process.exit(0)));
