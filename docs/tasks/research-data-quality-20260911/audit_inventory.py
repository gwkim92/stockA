"""Bounded SELECT-only audit of persisted collection evidence, no provider/model calls."""
import json
import os
from datetime import datetime, timezone
from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor

os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
os.environ['PGOPTIONS']='-c default_transaction_read_only=on -c statement_timeout=30000'
db=PsqlCommandExecutor.from_config(RuntimeConfig.from_env())
queries={
'sources': "select source_name,source_kind,license_type,trust_score,is_active from ingest.data_source order by source_name",
'prices': "select i.primary_symbol,count(*) bars,min(trade_date) first_date,max(trade_date) last_date,count(*) filter(where close<>adjusted_close) adjusted_rows from market.daily_price_bar p join ref.instrument i using(instrument_id) group by i.primary_symbol order by i.primary_symbol",
'price_providers': "select r.pipeline_name,count(*) bars,min(p.trade_date),max(p.trade_date) from market.daily_price_bar p left join ops.pipeline_run r on r.run_id=p.source_run_id group by r.pipeline_name",
'financial_coverage': "select i.primary_symbol,p.statement_scope,count(distinct p.period_id) periods,count(*) facts,min(p.period_end) first_period,max(p.period_end) last_period,max(p.report_date) last_report,count(*) filter(where p.source_document_id is null) facts_without_document from market.financial_statement_period p join ref.instrument i using(instrument_id) join market.financial_metric_value m using(period_id) group by i.primary_symbol,p.statement_scope order by i.primary_symbol,p.statement_scope",
'sample_periods': "select i.primary_symbol,p.*,jsonb_object_agg(m.metric_code,m.metric_value) metrics from market.financial_statement_period p join ref.instrument i using(instrument_id) join market.financial_metric_value m using(period_id) where i.primary_symbol in ('AAPL','NVDA','ARM') and p.period_end>='2024-01-01' group by i.primary_symbol,p.period_id order by i.primary_symbol,p.period_end desc,p.statement_scope",
'normalized_latest': "select primary_symbol,metric_status,count(*),min(period_end),max(period_end),min(as_of_date),max(as_of_date) from (select distinct on (n.instrument_id,n.metric_code) i.primary_symbol,n.* from market.financial_metric_normalized n join ref.instrument i using(instrument_id) where n.statement_scope='annual' order by n.instrument_id,n.metric_code,n.as_of_date desc,n.period_end desc) n group by primary_symbol,metric_status order by primary_symbol,metric_status",
'macro': "select s.series_code,s.frequency,count(o.*) observations,min(observation_date),max(observation_date),count(*) filter(where o.released_at is null) missing_release,count(distinct revision_number) revisions from macro.series s left join macro.observation o using(series_id) group by s.series_id order by s.series_code",
'news': "select s.source_name,d.document_type,count(*) documents,min(d.published_at),max(d.published_at),max(d.ingested_at),count(*) filter(where nullif(d.raw_storage_uri,'') is not null) raw_linked,count(*) filter(where nullif(d.summary,'') is not null) summarized,count(*) filter(where d.korean_summary is not null) translated from ingest.source_document d join ingest.data_source s using(data_source_id) group by s.source_name,d.document_type order by s.source_name,d.document_type",
'chunks': "select coalesce(c.chunk_metadata->>'source','unspecified') chunk_source,count(*) chunks,count(distinct document_id) documents,min(length(c.text_preview)) min_chars,percentile_disc(0.5) within group(order by length(c.text_preview)) median_chars,max(length(c.text_preview)) max_chars from ai.document_chunk c group by coalesce(c.chunk_metadata->>'source','unspecified')",
'news_recent': "select count(*) documents,count(*) filter(where nullif(d.raw_storage_uri,'') is not null) raw_linked,count(*) filter(where length(d.summary)>300) summary_gt300,count(*) filter(where exists(select 1 from ai.document_chunk c where c.document_id=d.document_id and length(c.text_preview)>500)) chunk_gt500 from ingest.source_document d where d.document_type='news_article' and d.published_at>='2026-09-04'",
'peer_groups': "select g.group_code,g.name,g.methodology,jsonb_agg(i.primary_symbol order by i.primary_symbol) members from ref.peer_group g join ref.peer_group_member m using(peer_group_id) join ref.instrument i using(instrument_id) where m.valid_to is null group by g.peer_group_id order by g.group_code",
'latest_jobs': "select distinct on (pipeline_name) pipeline_name,run_id,status,started_at,ended_at from ops.pipeline_run where run_kind='ingest' or pipeline_name ~ '(news|macro|financial|peer|sec|price|market)' order by pipeline_name,run_id desc",
'sample_sources': "select d.document_id,d.document_type,d.title,d.summary,d.url,d.published_at,d.ingested_at,d.korean_title,d.korean_summary,d.raw_storage_uri,(select jsonb_agg(jsonb_build_object('text',c.text_preview,'metadata',c.chunk_metadata)) from ai.document_chunk c where c.document_id=d.document_id) chunks from ingest.source_document d where document_id in (41362,41303,41143,41083,40343,40883,41558,41459,22,41361,36751,1100)",
'sample_artifacts': "select a.* from research.equity_research_artifact a where artifact_id in (492,493,494)",
'estimates': "select count(*) rows,count(distinct instrument_id) symbols,max(as_of_date) last_date from market.estimate_snapshot",
'protected_counts': "select (select count(*) from signal.recommendation) recommendations,(select count(*) from performance.recommendation_outcome) outcomes,(select count(*) from portfolio.position_snapshot) positions"
}
result={'observed_at':datetime.now(timezone.utc).isoformat(),'database_writes':False}
for name,sql in queries.items():
    if name == 'news_recent':
        sql = sql.replace("document_type='news_article'", "document_type='news_rss_item'")
    if name == 'normalized_latest':
        sql = sql.replace('min(period_end),max(period_end),min(as_of_date),max(as_of_date)', 'min(period_end) first_period,max(period_end) last_period,min(as_of_date) first_run_date,max(as_of_date) last_run_date')
    if name == 'news':
        sql = sql.replace('min(d.published_at),max(d.published_at),max(d.ingested_at)', 'min(d.published_at) first_published,max(d.published_at) last_published,max(d.ingested_at) last_ingested')
    result[name]=json.loads(db.execute_scalar("select coalesce(jsonb_agg(t),'[]'::jsonb)::text from ("+sql+") t;"))
print(json.dumps(result,ensure_ascii=False))
