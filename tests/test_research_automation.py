from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from stockanalysis.ai.equity_research_reporting import _bounded_context_for_prompt
from stockanalysis.ai_agents.prompt_contract import render_source_data
from stockanalysis.operations.research_maintenance import run_research_maintenance, maintenance_lock
from tests.test_equity_research_reporting import _context_payload


class ResearchAutomationTests(unittest.TestCase):
    def test_oversized_thesis_retains_identity_financial_records_and_explicit_omissions(self):
        context = _context_payload()
        context['thesis'] = {'thesis_id': 42, 'thesis_summary': '근거 문장 ' * 15000}
        context['recommendation'] = {'rationale': '오래된 판단 ' * 15000}
        bounded = _bounded_context_for_prompt(context, max_context_chars=16000)
        self.assertEqual(bounded['instrument'], context['instrument'])
        self.assertTrue(bounded['financial_metrics'])
        self.assertIsNone(bounded['thesis'])
        self.assertEqual(bounded['input_selection']['omitted']['thesis_records'], 1)
        self.assertEqual(bounded['input_selection']['omitted']['recommendation_records'], 1)
        self.assertLessEqual(len(render_source_data(bounded, max_chars=16000)),16000)
        self.assertEqual(_bounded_context_for_prompt(bounded,max_context_chars=16000), bounded)

    def test_single_worker_lock_and_preview_do_not_create_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'private'
            class DB:
                def execute_scalar(self, sql): return '[]'
            report=run_research_maintenance(config=None,as_of_date=date(2026,9,11),artifact_root=root,executor=DB())
            self.assertEqual(report['status'],'planned')
            self.assertFalse(root.exists())
            with maintenance_lock(root):
                with self.assertRaises(BlockingIOError):
                    with maintenance_lock(root): pass

    def test_source_failure_isolated_next_company_runs_and_lost_ack_is_reconciled(self):
        from stockanalysis.ingest.market.universe import MarketUniverseRecord
        from stockanalysis.ingest.sec.companyfacts import normalize_companyfacts_payload
        from tests.test_financial_period_integrity import observed
        result=normalize_companyfacts_payload(observed('ARM'))
        class DB:
            def __init__(self): self.next_id=10; self.apply_count=0
            def execute_scalar(self, sql):
                if "at time zone 'UTC'" in sql: return '2026-09-11'
                if sql.startswith('-- research maintenance queue'):
                    return json.dumps([{'primary_symbol':s,'instrument_id':i,'state':'due'} for i,s in enumerate(('BAD','ARM'),1)])
                if 'jsonb_agg(run_id)' in sql: return '[]'
                if sql.startswith('insert into ops.pipeline_run'):
                    self.next_id+=1; return str(self.next_id)
                if 'for update nowait' in sql: return 'failed' if 'run_id=12' in sql else 'succeeded'
                raise AssertionError(sql[:100])
            def execute_non_query(self, sql):
                if sql.startswith('begin;'):
                    self.apply_count+=1
                    raise ConnectionError('commit response lost')
        with tempfile.TemporaryDirectory() as directory, \
            patch('stockanalysis.operations.research_maintenance.load_market_universe_records',return_value=(MarketUniverseRecord(result.cik,'ARM','ARM','Nasdaq'),)), \
            patch('stockanalysis.operations.research_maintenance._load_companyfacts_payload',return_value=observed('ARM')), \
            patch('stockanalysis.operations.research_maintenance.load_sec_filings_sync_result') as filings, \
            patch('stockanalysis.operations.research_maintenance.time.sleep'):
            filings.return_value.filings=()
            db=DB()
            report=run_research_maintenance(config=None,as_of_date=date(2026,9,11),artifact_root=Path(directory),executor=db,execute=True)
            self.assertEqual([r['status'] for r in report['results']],['failed','succeeded'])
            self.assertEqual(db.apply_count,1)
            self.assertTrue(report['results'][1]['reconciled'])
            self.assertEqual(report['status'],'attention')
            self.assertTrue((Path(directory)/'research-maintenance/status.json').exists())


if __name__ == '__main__': unittest.main()
