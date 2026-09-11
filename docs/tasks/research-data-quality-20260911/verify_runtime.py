"""Verify deployed reads and exact report annotations. No model calls or DB writes."""
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
import urllib.request

from stockanalysis.ai.equity_research_reporting import load_equity_research_context
from stockanalysis.frontend.research_content_review import report_fingerprint
from stockanalysis.frontend.research_review_records import REVIEW_RECORDS
from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.psql import PsqlCommandExecutor
from stockanalysis.operations.env_file import load_env_file_values
from activate_runtime import identity

BASE = Path('/opt/stockanalysis/runtime/research-data-quality-20260911')


def main():
    ident = identity()
    values = load_env_file_values('/opt/stockanalysis/runtime/frontend-api.env')
    os.environ.update(load_env_file_values('/opt/stockanalysis/runtime/data-operations.env'))
    os.environ['PGOPTIONS'] = '-c default_transaction_read_only=on -c statement_timeout=20000'
    config = RuntimeConfig.from_env()
    executor = PsqlCommandExecutor.from_config(config)

    def get(path):
        request = urllib.request.Request('http://127.0.0.1:8787' + path, headers={
            'Authorization': 'Bearer ' + values['STOCKANALYSIS_FRONTEND_API_READ_TOKEN']})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    def fingerprint():
        result = {}
        for table in ['signal.recommendation', 'signal.recommendation_score_component',
                      'portfolio.position_snapshot', 'ref.benchmark_composition',
                      'performance.recommendation_outcome', 'market.financial_statement_period',
                      'market.financial_metric_value', 'market.financial_metric_normalized',
                      'research.equity_research_artifact']:
            result[table] = json.loads(executor.execute_scalar(
                "select json_build_object('count',count(*),'hash',md5(coalesce(string_agg(row_hash,',' order by row_hash),'')))::text "
                "from (select md5(to_jsonb(r)::text) row_hash from " + table + " r) hashes;"))
        return result

    before = fingerprint()
    checked = []
    for symbol, expected_period, artifact in [('NVDA', '2026-01-25', '492'),
                                             ('AAPL', '2025-09-27', '493'),
                                             ('ARM', '2025-03-31', '494')]:
        report = get('/api/stocks/' + symbol)['data']['equity_research']
        assert report['artifact_id'] == 'equity-research-artifact-' + artifact
        assert report_fingerprint(report) in REVIEW_RECORDS
        assert report['content_review']['status'] == 'needs_source_correction'
        assert report['content_review']['human_approved'] is False
        assert len(report['content_review']['findings']) == 3
        assert report['generation']['content_review_status'] == 'needs_source_correction'
        context = load_equity_research_context(config=config, symbol=symbol, as_of_date=date(2026, 9, 10))
        metrics = context['financial_metrics']
        assert {str(row['period_end']) for row in metrics} == {expected_period}
        assert any(row['metric_status'] == 'computed' for row in metrics)
        assert context['peer_relative'] and all(row['business_peer_comparison_verified'] is False for row in context['peer_relative'])
        checked.append({'symbol': symbol, 'artifact_id': report['artifact_id'],
                        'fingerprint': report_fingerprint(report), 'review': report['content_review']['status'],
                        'financial_period': expected_period,
                        'metric_statuses': {status: sum(row['metric_status'] == status for row in metrics)
                                            for status in ('computed', 'insufficient_history', 'unavailable')}})

    def reports(value):
        if isinstance(value, dict):
            if 'artifact_id' in value and 'generation' in value:
                yield value
            else:
                for item in value.values():
                    yield from reports(item)
        elif isinstance(value, list):
            for item in value:
                yield from reports(item)

    recommendation = list(reports(get('/api/recommendations/recommendation-1501')))
    assert any(row['artifact_id'] == 'equity-research-artifact-493' and
               row['content_review']['status'] == 'needs_source_correction' for row in recommendation)
    other = get('/api/stocks/SPY')['data'].get('equity_research')
    if other:
        assert other['content_review']['status'] == 'not_recorded'
    after = fingerprint()
    assert before == after, 'Protected data changed during verification; inspect concurrent jobs before retrying.'
    result = {'observed_at': datetime.now(timezone.utc).isoformat(), 'identity': ident,
              'reports': checked, 'recommendation_link_verified': True,
              'protected_tables_unchanged': after, 'database_writes': False, 'model_calls': 0}
    (BASE / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
