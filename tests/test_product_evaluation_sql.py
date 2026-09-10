"""Behavioral SQL regressions. Run against a disposable, migrated local database only.

STOCKA_TEST_PG_PORT=15439 PYTHONPATH=src .venv/bin/python -m unittest tests.test_product_evaluation_sql
Every scenario rolls its data back. No production configuration is read.
"""
import json
import os
import shutil
import subprocess
import unittest
from datetime import date
from stockanalysis.frontend.live_adapter import (
    render_frontend_stock_list_state_sql, render_frontend_stock_detail_state_sql,
    render_frontend_performance_outcomes_state_sql, render_frontend_dashboard_state_sql,
    _build_professional_source_guardrail_payload, _valuation_method_data_quality,
)
from stockanalysis.operations.professional_equity_analysis import (render_financial_forecast_inputs_upsert_sql, render_sum_of_parts_valuation_preview_sql, render_sum_of_parts_valuation_upsert_sql, render_valuation_snapshot_upsert_sql)

PORT = os.environ.get('STOCKA_TEST_PG_PORT')
PSQL = shutil.which('psql') or '/opt/homebrew/opt/postgresql@16/bin/psql'
TODAY = date(2026, 9, 10)
SETUP = """
insert into ref.market values ('QA', 'Regression', 'US', 'USD', 'UTC', true);
insert into ref.exchange (market_code,mic_code,name,timezone) values ('QA','XQAT','Regression','UTC');
insert into ref.issuer (legal_name,display_name,country_code,issuer_type) values ('Regression','Regression','US','company');
insert into ref.instrument (issuer_id,exchange_id,market_code,primary_symbol,instrument_type,currency_code,name)
select (select issuer_id from ref.issuer where legal_name='Regression'),(select exchange_id from ref.exchange where mic_code='XQAT'),'QA',symbol,'stock','USD',symbol||' Company'
from (select 'AAA'||lpad(n::text,3,'0') as symbol from generate_series(1,60) n union all select 'NVDA') symbols;
insert into market.daily_price_bar (instrument_id,trade_date,open,high,low,close,adjusted_close,volume)
select instrument_id,'2026-09-10',100,100,100,100,100,10 from ref.instrument where market_code='QA';
insert into portfolio.portfolio (portfolio_name,base_currency,market_code,strategy_name) values ('QA Portfolio','USD','QA','regression');
"""

FINANCE_SETUP = """
insert into ops.pipeline_run(run_kind,pipeline_name,status) values ('test','qa-finance','succeeded');
insert into market.financial_statement_period (instrument_id,statement_scope,fiscal_year,period_start,period_end,currency_code)
select instrument_id,'annual',y,make_date(y,1,1),make_date(y,12,31),'USD' from ref.instrument cross join (values(2012),(2025)) years(y) where primary_symbol='NVDA';
insert into market.financial_metric_value(period_id,metric_code,metric_value,unit)
select period_id,code,value,'USD' from market.financial_statement_period cross join (values('revenue',1000),('operating_cash_flow',120),('capital_expenditure',20)) m(code,value);
insert into market.financial_metric_normalized(instrument_id,as_of_date,period_id,statement_scope,fiscal_year,period_end,metric_code,metric_value,metric_unit,metric_status)
select instrument_id,'2026-09-09',period_id,'annual',fiscal_year,period_end,code,
case when fiscal_year=2012 then value else null end,'ratio',case when fiscal_year=2012 then 'computed' else 'unavailable' end
from market.financial_statement_period cross join (values('free_cash_flow_margin',0.193),('capex_intensity',0.035),('revenue_growth_yoy',0.9)) m(code,value);
"""

@unittest.skipUnless(PORT, 'requires an explicitly selected disposable local Postgres port')
class ProductEvaluationSqlTests(unittest.TestCase):
    def execute(self, sql):
        result = subprocess.run([PSQL, '-X', '-qAt', '-h', '127.0.0.1', '-p', PORT, '-d', 'postgres', '-v', 'ON_ERROR_STOP=1'],
            input='begin;\n'+SETUP+'\n'+sql+'\nrollback;', text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]

    def test_search_scans_all_rows_before_pagination_and_treats_wildcards_literally(self):
        first, found, literal, next_page = self.execute('\n'.join([
            render_frontend_stock_list_state_sql(as_of_date=TODAY, page_limit=50),
            render_frontend_stock_list_state_sql(as_of_date=TODAY, search_query=' nvDa '),
            render_frontend_stock_list_state_sql(as_of_date=TODAY, search_query="%' OR true --"),
            render_frontend_stock_list_state_sql(as_of_date=TODAY, page_offset=50),
        ]))
        self.assertEqual(first['stock_count'], 61)
        self.assertNotIn('NVDA', [r['symbol'] for r in first['stocks']])
        self.assertEqual([r['symbol'] for r in found['stocks']], ['NVDA'])
        self.assertEqual(found['matched_stock_count'], 1)
        self.assertEqual(literal['stocks'], [])
        self.assertIn('NVDA', [r['symbol'] for r in next_page['stocks']])

    def test_no_run_and_run_without_holdings_are_not_coverage_passes(self):
        query = render_frontend_performance_outcomes_state_sql(portfolio_name='QA Portfolio',measurement_end_date=TODAY)
        without, empty, missing = self.execute(query+"""
insert into performance.attribution_run (portfolio_id,snapshot_date,measurement_start_date,measurement_end_date,methodology)
select portfolio_id,'2026-09-10','2026-08-10','2026-09-10','test' from portfolio.portfolio where portfolio_name='QA Portfolio';
"""+query+"""
insert into portfolio.position_snapshot (portfolio_id,instrument_id,snapshot_date,quantity,market_price,market_value,weight)
select p.portfolio_id,i.instrument_id,'2026-09-10',1,100,100,0.5 from portfolio.portfolio p cross join ref.instrument i where p.portfolio_name='QA Portfolio' and i.primary_symbol='NVDA';
"""+query)
        for result in [without, empty]:
            self.assertEqual(result['quality_gates'][0]['status'], 'not_evaluated')
            self.assertIsNone(result['summary']['excluded_weight'])
        self.assertEqual(missing['quality_gates'][0]['status'], 'blocked')
        self.assertEqual(missing['summary']['excluded_weight'], 0.5)

    def test_unknown_excluded_position_weight_is_not_zero(self):
        result, = self.execute("""
insert into performance.attribution_run (portfolio_id,snapshot_date,measurement_start_date,measurement_end_date,methodology)
select portfolio_id,'2026-09-10','2026-08-10','2026-09-10','test' from portfolio.portfolio where portfolio_name='QA Portfolio';
insert into portfolio.position_snapshot (portfolio_id,instrument_id,snapshot_date,quantity,market_price,market_value,weight)
select p.portfolio_id,i.instrument_id,'2026-09-10',1,100,100,null from portfolio.portfolio p cross join ref.instrument i where p.portfolio_name='QA Portfolio' and i.primary_symbol='NVDA';
"""+render_frontend_performance_outcomes_state_sql(portfolio_name='QA Portfolio',measurement_end_date=TODAY))
        self.assertEqual(result['quality_gates'][0]['status'],'blocked')
        self.assertIsNone(result['summary']['excluded_weight'])

    def test_latest_missing_metrics_do_not_resurrect_2012_values_in_display_or_forecast(self):
        setup = FINANCE_SETUP
        # Resolve the generated run ID inside SQL without hardcoding fixture IDs.
        forecast = render_financial_forecast_inputs_upsert_sql(as_of_date=TODAY,source_run_id=987654321).replace('987654321::bigint', "(select run_id from ops.pipeline_run where pipeline_name='qa-finance')::bigint")
        result = self.execute(setup+render_frontend_stock_detail_state_sql(symbol='NVDA',as_of_date=TODAY)+forecast+"""
select json_build_object('fcf',free_cash_flow_margin,'capex',capex_intensity,'growth',revenue_growth_rate,'assumptions',assumptions_json)
from market.financial_forecast_input where scenario_key='base' and forecast_year=1;
""")
        model, generated, inputs = result
        self.assertEqual(model['financial_statement_model']['computed_metric_count'], 0)
        metrics = model['financial_statement_model']['metrics']
        self.assertTrue(all(m['period_end']=='2025-12-31' for m in metrics))
        self.assertTrue(all(m['metric_value'] is None for m in metrics))
        self.assertAlmostEqual(inputs['fcf'],0.1)
        self.assertAlmostEqual(inputs['capex'],0.02)
        self.assertAlmostEqual(inputs['growth'],0.03)
        self.assertEqual(inputs['assumptions']['input_period_policy'],'same_revenue_period_v1')
        self.assertIn('revenue_growth_rate',inputs['assumptions']['defaulted_inputs'])
        for family in inputs['assumptions']['input_lineage'].values():
            self.assertTrue(all(row['period_end']=='2025-12-31' and row['period_id'] for row in family.values()))

    def test_unpriced_registered_stock_remains_searchable(self):
        added = """insert into ref.instrument (issuer_id,exchange_id,market_code,primary_symbol,instrument_type,currency_code,name)
select issuer_id,exchange_id,market_code,'NOQUOTE',instrument_type,currency_code,'No quote yet' from ref.instrument where primary_symbol='NVDA';"""
        result, = self.execute(added+render_frontend_stock_list_state_sql(as_of_date=TODAY,search_query='NOQUOTE',scope='attention'))
        self.assertEqual(result['matched_stock_count'],1)
        self.assertEqual(result['stock_count'],62)
        self.assertEqual(result['summary']['priced_stock_count'],61)
        self.assertIsNone(result['stocks'][0]['latest_price']['close'])

    def test_latest_revenue_period_survives_a_later_shares_only_period(self):
        result, = self.execute(FINANCE_SETUP+"""
insert into market.financial_statement_period(instrument_id,statement_scope,fiscal_year,period_start,period_end,currency_code)
select instrument_id,'annual',2026,'2026-02-20','2026-02-20','USD' from ref.instrument where primary_symbol='NVDA';
insert into market.financial_metric_value(period_id,metric_code,metric_value,unit)
select period_id,'shares_outstanding',100,'shares' from market.financial_statement_period where period_end='2026-02-20';
insert into market.financial_metric_normalized(instrument_id,as_of_date,period_id,statement_scope,fiscal_year,period_end,metric_code,metric_unit,metric_status)
select instrument_id,'2026-09-09',period_id,'annual',2026,period_end,'free_cash_flow_margin','ratio','unavailable' from market.financial_statement_period where period_end='2026-02-20';
"""+render_frontend_stock_detail_state_sql(symbol='NVDA',as_of_date=TODAY))
        self.assertEqual(result['financial_statement_model']['latest_period_end'],'2025-12-31')
        self.assertTrue(all(r['period_end']=='2025-12-31' for r in result['financial_statement_model']['metrics']))

    def test_legacy_forecasts_and_legacy_sotp_do_not_feed_a_new_valuation(self):
        forecast = render_financial_forecast_inputs_upsert_sql(as_of_date=TODAY,source_run_id=987654321)
        sotp = render_sum_of_parts_valuation_upsert_sql(as_of_date=TODAY,source_run_id=987654321)
        valuation = render_valuation_snapshot_upsert_sql(as_of_date=TODAY,source_run_id=987654321)
        sql = FINANCE_SETUP+"""
insert into market.financial_metric_value(period_id,metric_code,metric_value,unit)
select period_id,'shares_outstanding',100,'shares' from market.financial_statement_period where period_end='2025-12-31';
"""+forecast+"""
update market.financial_forecast_input set assumptions_json = assumptions_json - 'input_period_policy', free_cash_flow=9000000;
"""+render_sum_of_parts_valuation_preview_sql(as_of_date=TODAY)+sotp+"""
select json_build_object('value',fair_value_base,'source',assumptions_json->>'fcf_source') from market.sum_of_parts_component where component_key='operating_business_fcf';
update market.sum_of_parts_component set assumptions_json = assumptions_json - 'forecast_input_period_policy', fair_value_base=9000000;
"""+valuation+"""
select json_build_object('sotp_count',count(*) filter(where method='sum_of_parts'),'growth',max((assumptions_json->>'growth_rate')::numeric) filter(where method='dcf_lite')) from market.valuation_snapshot;
"""
        results=self.execute(sql.replace('987654321::bigint',"(select run_id from ops.pipeline_run where pipeline_name='qa-finance')::bigint"))
        self.assertEqual(results[1]['forecast_input_count'],0)
        self.assertAlmostEqual(results[3]['value'],18)
        self.assertEqual(results[3]['source'],'latest_financial_metric_value')
        self.assertEqual(results[-1]['sotp_count'],0)
        self.assertAlmostEqual(results[-1]['growth'],0.03)

    def test_open_review_history_groups_current_action_and_preserves_occurrences(self):
        result, = self.execute("""
insert into portfolio.review(portfolio_id,review_date,review_source,overall_summary)
select portfolio_id,d,'test','review' from portfolio.portfolio cross join (values(date '2026-09-01'),(date '2026-09-09')) days(d) where portfolio_name='QA Portfolio';
insert into portfolio.remediation_ticket(portfolio_review_id,instrument_id,action,remediation_type,suggested_runner,suggested_next_step,latest_reason,risk_level)
select r.portfolio_review_id,i.instrument_id,'reduce_watch','allocation','manual','review',r.review_date::text,'high' from portfolio.review r cross join ref.instrument i where i.primary_symbol='NVDA';
"""+render_frontend_dashboard_state_sql(portfolio_name='QA Portfolio'))
        self.assertEqual(result['open_ticket_count'],2)
        self.assertEqual(len(result['top_actions']),1)
        self.assertEqual(result['top_actions'][0]['review_date'],'2026-09-09')
        self.assertEqual(result['top_actions'][0]['occurrence_count'],2)

class FinancialInputBoundaryTests(unittest.TestCase):
    def test_current_period_without_computed_inputs_is_not_professional_ready(self):
        result=_build_professional_source_guardrail_payload(financial_statement_model={'status':'data_gap','computed_metric_count':0},fund_instrument_analysis=None)
        self.assertFalse(result['professional_decision_use_allowed'])
        self.assertFalse(result['paper_validation_input_allowed'])

    def test_nested_legacy_sotp_forecast_is_not_sufficient_input(self):
        result=_valuation_method_data_quality('sum_of_parts',{'sotp_component_count':1,'has_operating_business_component':True,'sotp_components':[{'assumptions':{'forecast_row_count':15}}]},0.8,0.1)
        self.assertEqual(result['status'],'limited')
        self.assertEqual(result['input_period_status'],'unverified_legacy')
