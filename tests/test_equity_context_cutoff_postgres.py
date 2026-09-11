"""Execute the real equity SELECT on the dedicated disposable CI PostgreSQL only."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from stockanalysis.ai import equity_research_reporting as equity
from tests.test_equity_research_reporting import FakeEquityResearchExecutor

FIXTURES = Path(__file__).parent / 'fixtures'
SQL_EXECUTIONS = 0
POSTGRES_VERSION = None


class EquityCutoffPostgresTests(unittest.TestCase):
    def test_shares_only_later_date_does_not_replace_financial_statement(self):
        setup = """
insert into market.financial_statement_period values
(1,101,'annual','2025-09-27','2025-10-31',null),
(2,101,'annual','2025-10-17','2025-10-31',null);
insert into market.financial_metric_value values (1,'revenue',100),(2,'shares_outstanding',50);
insert into market.financial_metric_normalized (instrument_id,metric_code,metric_value,metric_status,statement_scope,period_end,as_of_date,period_id) values
(101,'net_margin',0.2,'computed','annual','2025-09-27','2026-09-01',1),
(101,'net_margin',null,'unavailable','annual','2025-10-17','2026-09-01',2);
"""
        row = self.context(setup=setup)['financial_metrics'][0]
        self.assertEqual(row['period_end'], '2025-09-27')
        self.assertEqual(row['metric_value'], 0.2)
        self.assertEqual(row['report_date'], '2025-10-31')
        self.assertIsNone(row['source_document_id'])

    def test_genuine_latest_period_keeps_missing_metrics_instead_of_cherry_picking(self):
        setup = """
insert into market.financial_statement_period values
(1,101,'annual','2024-09-28','2024-10-31',null),
(2,101,'annual','2025-09-27','2025-10-31',null);
insert into market.financial_metric_value values (1,'revenue',100),(2,'revenue',120);
insert into market.financial_metric_normalized (instrument_id,metric_code,metric_value,metric_status,statement_scope,period_end,as_of_date,period_id) values
(101,'net_margin',0.2,'computed','annual','2024-09-28','2026-09-01',1),
(101,'net_margin',null,'unavailable','annual','2025-09-27','2026-09-01',2);
"""
        row = self.context(setup=setup)['financial_metrics'][0]
        self.assertEqual(row['period_end'], '2025-09-27')
        self.assertIsNone(row['metric_value'])

    def test_unknown_or_later_report_date_is_not_historical_evidence(self):
        setup = """
insert into market.financial_statement_period values
(1,101,'annual','2025-12-31','2026-09-06',null),
(2,101,'annual','2025-11-30',null,null);
insert into market.financial_metric_value values (1,'revenue',100),(2,'revenue',100);
insert into market.financial_metric_normalized (instrument_id,metric_code,metric_status,statement_scope,period_end,as_of_date,period_id) values
(101,'net_margin','unavailable','annual','2025-12-31','2026-09-01',1),
(101,'net_margin','unavailable','annual','2025-11-30','2026-09-01',2);
"""
        self.assertEqual(self.context(setup=setup)['financial_metrics'], [])

    def test_theme_percentile_is_explicitly_not_a_validated_business_peer(self):
        setup = """
insert into ref.peer_group values (1,'THEME','Macro Rates','classification membership: internal_theme/subtheme/MACRO');
insert into market.peer_relative_snapshot values (101,1,'net_margin',0.2,1,'above_peer','2026-09-01',null,1);
"""
        row = self.context(setup=setup)['peer_relative'][0]
        self.assertFalse(row['business_peer_comparison_verified'])
        self.assertIn('subtheme', row['peer_group_methodology'])
        self.assertEqual(row['metric_value'], 0.2)

    @classmethod
    def setUpClass(cls):
        service = os.getenv('STOCKA_CUTOFF_TEST_CONTAINER', '')
        if not service:
            raise unittest.SkipTest('Dedicated disposable PostgreSQL service required.')
        if os.getenv('GITHUB_ACTIONS') != 'true' or not re.fullmatch(r'[a-f0-9]{12,64}', service):
            raise RuntimeError('Only the explicit GitHub test service is supported; no host/DB URL accepted.')
        cls.command = ['docker', 'exec', '-i', service, 'psql', '-X', '-q', '-A', '-t',
                       '-v', 'ON_ERROR_STOP=1', '-h', '/var/run/postgresql',
                       '-U', 'postgres', '-d', 'stocka_cutoff_test']
        identity = cls.execute("select current_database() || '|' || current_setting('server_version');")
        db, version = identity.strip().split('|', 1)
        if db != 'stocka_cutoff_test':
            raise RuntimeError('Not the disposable test database.')
        global POSTGRES_VERSION
        POSTGRES_VERSION = version

    @classmethod
    def execute(cls, sql):
        result = subprocess.run(cls.command, input=sql, text=True, capture_output=True, timeout=20, check=True)
        global SQL_EXECUTIONS
        SQL_EXECUTIONS += 1
        return result.stdout

    def context(self, *, setup='', zone='UTC', cutoff=date(2026, 9, 5), symbol='AAPL', baseline=False):
        self.assertIn(zone, ('UTC', 'Asia/Seoul', 'America/New_York', 'Pacific/Kiritimati'))
        schema = (FIXTURES / 'equity-cutoff-schema.sql').read_text()
        query = ((FIXTURES / 'equity-cutoff-baseline.sql').read_text() if baseline else
                 equity.render_equity_research_context_sql(symbol=symbol, as_of_date=cutoff, limit=50))
        # DDL and all synthetic input rows are transaction-local and rolled back.
        script = f"begin; set local statement_timeout='10s'; set local timezone='{zone}';\n{schema}\n{setup}\n{query}\nrollback;"
        return json.loads(self.execute(script))

    def test_baseline_future_thesis_and_next_midnight_leak_are_reproduced(self):
        old = self.context(baseline=True)
        fixed = self.context()
        self.assertEqual(old['thesis']['thesis_id'], 900)
        self.assertEqual(fixed['thesis']['thesis_id'], 20)
        self.assertIn(4, [r['event_id'] for r in old['recent_events']])
        self.assertEqual([r['event_id'] for r in fixed['recent_events']], [3, 2, 1])

    def test_baseline_session_timezone_leak_is_reproduced(self):
        utc = self.context(baseline=True, zone='UTC')
        seoul = self.context(baseline=True, zone='Asia/Seoul')
        self.assertNotEqual([r['event_id'] for r in utc['recent_events']], [r['event_id'] for r in seoul['recent_events']])

    def test_same_ids_under_four_session_timezones(self):
        for zone in ('UTC', 'Asia/Seoul', 'America/New_York', 'Pacific/Kiritimati'):
            with self.subTest(zone=zone):
                data = self.context(zone=zone)
                self.assertEqual(data['thesis']['thesis_id'], 20)
                self.assertEqual([r['event_id'] for r in data['recent_events']], [3, 2, 1])
                self.assertFalse(data['query']['point_in_time_complete'])

    def test_eligible_explicit_link_precedes_newer_eligible_thesis(self):
        data = self.context(setup='update signal.recommendation set thesis_id=10;')
        self.assertEqual(data['thesis']['thesis_id'], 10)

    def test_later_recommendation_batch_cannot_supply_preferred_thesis(self):
        data = self.context(setup="update signal.recommendation set thesis_id=10; update signal.recommendation_batch set as_of_date='2026-09-06';")
        self.assertIsNone(data['recommendation'])
        self.assertEqual(data['thesis']['thesis_id'], 20)

    def test_current_active_flag_cannot_reorder_historical_candidates(self):
        for assignment in ("case when thesis_id=10 then 'active' else 'closed' end", "case when thesis_id=20 then 'active' else 'closed' end"):
            data = self.context(setup=f'update signal.recommendation set thesis_id=null; update signal.investment_thesis set status={assignment};')
            self.assertEqual(data['thesis']['thesis_id'], 20)

    def test_future_closure_time_and_status_are_not_presented_as_known(self):
        data = self.context(setup="update signal.investment_thesis set status='closed', closed_at='2026-09-06T00:00:00Z' where thesis_id=20;")
        self.assertEqual(data['thesis']['thesis_id'], 20)
        self.assertIsNone(data['thesis']['closed_at'])
        self.assertIsNone(data['thesis']['status'])
        self.assertEqual(data['thesis']['status_scope'], 'current_record_not_versioned')

    def test_known_closure_is_preserved_without_inventing_active_status(self):
        data = self.context(setup="update signal.investment_thesis set created_at='2026-09-05T12:00:00Z',closed_at='2026-09-05T23:00:00Z',status='closed' where thesis_id=20;")
        self.assertEqual(data['thesis']['status'], 'closed')
        self.assertEqual(datetime.fromisoformat(data['thesis']['closed_at']).astimezone(timezone.utc).hour, 23)

    def test_equal_creation_time_uses_stable_id_tiebreaker(self):
        setup = "insert into signal.investment_thesis (thesis_id,instrument_id,title,summary,status,created_at) values (21,101,'same time','fixture','watch','2026-09-05T23:59:59.999999Z');"
        self.assertEqual(self.context(setup=setup)['thesis']['thesis_id'], 21)

    def test_no_eligible_thesis_is_null_and_not_another_instrument(self):
        data = self.context(setup='delete from signal.investment_thesis where thesis_id in (10,20);')
        self.assertIsNone(data['thesis'])
        self.assertEqual(data['instrument']['primary_symbol'], 'AAPL')
        self.assertEqual(self.context(symbol='MSFT')['thesis']['thesis_id'], 999)

    def test_midnight_bound_is_stable_on_both_us_dst_transition_dates(self):
        for cutoff in (date(2026, 3, 8), date(2026, 11, 1)):
            end = cutoff + timedelta(days=1)
            setup = f"""delete from signal.investment_thesis; delete from event.event;
insert into signal.investment_thesis(thesis_id,instrument_id,title,summary,created_at) values
(1,101,'last microsecond','fixture','{cutoff}T23:59:59.999999Z'), (2,101,'next midnight','fixture','{end}T00:00:00Z');
insert into event.event(event_id,title,summary,event_at) values
(1,'last microsecond','fixture','{cutoff}T23:59:59.999999Z'), (2,'next midnight','fixture','{end}T00:00:00Z');"""
            for zone in ('UTC', 'Asia/Seoul', 'America/New_York'):
                with self.subTest(date=cutoff, zone=zone):
                    data = self.context(setup=setup, zone=zone, cutoff=cutoff)
                    self.assertEqual(data['thesis']['thesis_id'], 1)
                    self.assertEqual([r['event_id'] for r in data['recent_events']], [1])

    def test_actual_selected_query_flows_into_provider_prompt_and_source_inventory(self):
        context = self.context()
        seen = []
        class Executor(FakeEquityResearchExecutor):
            def execute_scalar(self, sql):
                if sql.startswith('-- equity research symbol lookup'):
                    self.scalar_sql.append(sql); return json.dumps(['AAPL'])
                if sql.startswith('-- equity research context lookup'):
                    self.scalar_sql.append(sql); return json.dumps(context)
                return super().execute_scalar(sql)
        def provider(selected, model, effort, budget):
            seen.append(equity.build_codex_oauth_equity_research_prompt(selected, max_context_chars=budget))
            return equity.build_fixture_equity_research_response(selected, model, effort, budget)
        executor = Executor()
        with patch.object(equity.PsqlCommandExecutor, 'from_config', side_effect=AssertionError('No runtime DB')):
            report = equity.run_equity_research_reporting(config=SimpleNamespace(), as_of_date=date(2026,9,5),
                        symbols=('AAPL',), provider=equity.CODEX_OAUTH_PROVIDER, provider_runner=provider,
                        executor=executor, execute=True)
        self.assertEqual(report['status'], 'completed')
        self.assertIn('fixture newest', seen[0])
        self.assertNotIn('must not enter prior day', seen[0])
        framed = json.loads(seen[0].split('<source_data>\n')[1].split('\n</source_data>')[0])
        self.assertFalse(framed['query']['point_in_time_complete'])
        artifact = next(s for s in executor.scalar_sql if 'insert into research.equity_research_artifact' in s)
        self.assertIn("'[1001]'", artifact)
        self.assertNotIn('1004', artifact)

    def test_transaction_fixture_leaves_no_schema_after_execution(self):
        self.context()
        self.assertEqual(self.execute("select count(*) from pg_namespace where nspname in ('ref','market','signal','event','ingest','ai');").strip(), '0')
