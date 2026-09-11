from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import unittest

from stockanalysis.ingest.sec.companyfacts import normalize_companyfacts_payload, run_sec_companyfacts_upsert
from stockanalysis.ingest.sec.sql import render_sec_companyfacts_upsert_sql
from stockanalysis.operations.professional_equity_analysis import render_financial_metric_normalization_upsert_sql
from tests.test_sec_companyfacts import FakeExecutor

FIXTURES = Path(__file__).parent / 'fixtures'


def observed(symbol):
    return json.loads((FIXTURES / 'sec_financial_periods_observed.json').read_text())[symbol]


def fact(*, start='2024-01-01', end='2024-12-31', fy=2024, fp='FY', form='10-K',
         accn='filing-2024', filed='2025-02-01', val=100):
    item = dict(end=end, fy=fy, fp=fp, form=form, accn=accn, filed=filed, val=val)
    if start is not None:
        item['start'] = start
    return item


def payload(**concepts):
    return {'cik': 123, 'entityName': 'Test', 'facts': {'us-gaap': {
        concept: {'units': {'USD': items}} for concept, items in concepts.items()}}}


class FinancialPeriodIntegrityTests(unittest.TestCase):
    def test_arm_comparatives_use_represented_year_not_filing_year(self):
        result = normalize_companyfacts_payload(observed('ARM'))
        rows = {r.period_end.isoformat(): r for r in result.values if r.metric_code == 'revenue' and r.statement_scope == 'annual'}
        for end, year, revenue in [('2024-03-31',2024,3233000000), ('2025-03-31',2025,4007000000), ('2026-03-31',2026,4920000000)]:
            self.assertEqual((rows[end].fiscal_year, rows[end].metric_value), (year, Decimal(revenue)))
        self.assertEqual(rows['2024-03-31'].source_evidence['fy'], 2026)

    def test_nvda_fiscal_year_is_not_calendar_frame_year(self):
        rows = normalize_companyfacts_payload(observed('NVDA')).values
        row = next(r for r in rows if r.metric_code == 'revenue' and r.period_end == date(2025,4,27))
        self.assertEqual((row.fiscal_year,row.fiscal_quarter), (2026,1))
        self.assertEqual(row.source_evidence['frame'], 'CY2025Q1')

    def test_real_quarter_and_ytd_cash_flow_are_not_mixed(self):
        for symbol, end, revenue in [('AAPL','2026-06-27',109417000000),('NVDA','2026-07-26',96221000000)]:
            result = normalize_companyfacts_payload(observed(symbol))
            rows = {r.metric_code:r for r in result.values if r.period_end.isoformat()==end and r.statement_scope=='quarterly'}
            self.assertEqual(rows['revenue'].metric_value, Decimal(revenue))
            self.assertNotIn('operating_cash_flow',rows)
            self.assertLessEqual((rows['revenue'].period_end-rows['revenue'].period_start).days,109)
            rejected = [r for r in result.excluded_facts if r['concept']=='NetCashProvidedByUsedInOperatingActivities' and r['end']==end]
            self.assertTrue(rejected)
            self.assertTrue(all(r['exclusion_reason']=='non_statement_duration_or_duration_shares' for r in rejected))

    def test_same_filing_and_exact_start_are_required(self):
        old = fact()
        new = fact(accn='amended',filed='2025-03-01',val=110,form='10-K/A')
        result=normalize_companyfacts_payload(payload(Revenues=[old,new],NetIncomeLoss=[fact(val=20)]))
        self.assertEqual([r.metric_code for r in result.values],['revenue'])
        self.assertEqual(result.values[0].metric_value,110)

    def test_duration_conflict_excludes_statement(self):
        result=normalize_companyfacts_payload(payload(Revenues=[fact()], NetIncomeLoss=[fact(start='2024-01-05')]))
        self.assertEqual(result.values,())
        self.assertTrue(result.excluded_facts)

    def test_first_quarter_reported_cash_flow_can_be_used(self):
        row=fact(start='2024-01-01',end='2024-03-31',fp='Q1',form='10-Q',filed='2024-05-01')
        result=normalize_companyfacts_payload(payload(Revenues=[row],NetCashProvidedByUsedInOperatingActivities=[{**row,'val':30}]))
        self.assertEqual({r.metric_code for r in result.values},{'revenue','operating_cash_flow'})

    def test_missing_filed_nonfinite_and_unknown_quarter_are_excluded(self):
        for bad in [dict(filed=None),dict(val='NaN'),dict(val='Infinity')]:
            result=normalize_companyfacts_payload(payload(Revenues=[{**fact(),**bad}]))
            self.assertEqual(result.values,())
        result=normalize_companyfacts_payload(payload(Revenues=[fact(start='2024-01-01',end='2024-03-31',form='10-Q',fp='FY')]))
        self.assertEqual(result.values,())

    def test_conflicting_preferred_fact_is_not_selected_by_input_order(self):
        for values in [[fact(val=100),fact(val=120)],[fact(val=120),fact(val=100)]]:
            result=normalize_companyfacts_payload(payload(Revenues=values))
            self.assertEqual(result.values,())
            self.assertIn('conflicting_values_in_same_filing',{r['exclusion_reason'] for r in result.excluded_facts})

    def test_sql_keeps_period_together_even_for_tiny_chunks(self):
        result=normalize_companyfacts_payload(payload(Revenues=[fact()],NetIncomeLoss=[fact(val=20)]))
        sql=render_sec_companyfacts_upsert_sql(result,instrument_id=1,source_run_id=1,chunk_size=1)
        self.assertEqual(sql.count('insert into market.financial_statement_period'),1)

    def test_run_ledger_contains_exact_source_duration_and_exclusions(self):
        executor=FakeExecutor()
        run_sec_companyfacts_upsert('320193',config=object(),executor=executor,
            companyfacts_json_path=str(FIXTURES/'sec_companyfacts_CIK0000320193.json'))
        config_sql=next(s for s in executor.scalar_sql if 'insert into ops.pipeline_run' in s)
        for field in ['selected_facts','concept','start','accn','filed','period_policy']:
            self.assertIn(field,config_sql)

    def test_normalization_scopes_symbols_and_requires_known_publication(self):
        sql=render_financial_metric_normalization_upsert_sql(as_of_date=date(2026,9,11),source_run_id=1,symbols=('ARM','AAPL'))
        self.assertIn("instrument.primary_symbol in ('AAPL', 'ARM')",sql)
        self.assertIn('period.report_date <=',sql)
        with self.assertRaises(ValueError):
            render_financial_metric_normalization_upsert_sql(as_of_date=date.today(),source_run_id=1,symbols=("A';DROP",))
