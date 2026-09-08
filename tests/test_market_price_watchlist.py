from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from stockanalysis.operations.market_price_watchlist import prepare_priority_watchlist
from stockanalysis.operations.market_price_free_backfill import run_market_price_daily_from_env


class ActivePriceWatchlistTests(unittest.TestCase):
    def test_active_coverage_preserves_configured_file_and_priority(self):
        with tempfile.TemporaryDirectory() as root:
            source, target = Path(root)/'configured.csv', Path(root)/'generated.csv'
            original = 'symbol,role\nAAPL,core\nMSFT,core\n'
            source.write_text(original)
            executor = Mock()
            executor.execute_scalar.return_value = json.dumps([
                {'symbol': 'AMD', 'latest_trade_date': None},
                {'symbol': 'MSFT', 'latest_trade_date': '2026-07-01'},
                {'symbol': 'AAPL', 'latest_trade_date': '2026-09-04'},
            ])
            result = prepare_priority_watchlist(source_path=str(source), destination=target, executor=executor)
            with target.open() as stream: rows = list(csv.DictReader(stream))
            self.assertEqual([r['symbol'] for r in rows], ['AMD', 'MSFT', 'AAPL'])
            self.assertEqual(rows[1]['role'], 'core')
            self.assertEqual(result['selected_symbol_count'], 3)
            self.assertEqual(source.read_text(), original)

    def test_invalid_or_incomplete_response_preserves_previous_generated_file(self):
        with tempfile.TemporaryDirectory() as root:
            source, target = Path(root)/'configured.csv', Path(root)/'generated.csv'
            source.write_text('symbol\nAAPL\n'); target.write_text('prior-valid-file')
            for rows in [[], [{'symbol': 'MSFT'}], [{'symbol': 'AAPL'}, {'symbol': 'AAPL'}], [{'symbol': 'aapl'}]]:
                with self.subTest(rows=rows):
                    executor = Mock(); executor.execute_scalar.return_value = json.dumps(rows)
                    with self.assertRaises(ValueError):
                        prepare_priority_watchlist(source_path=str(source), destination=target, executor=executor)
                    self.assertEqual(target.read_text(), 'prior-valid-file')

    def test_daily_runner_uses_extended_watchlist_without_raising_budget(self):
        with tempfile.TemporaryDirectory() as root:
            source, ledger = Path(root)/'configured.csv', Path(root)/'budget.json'
            source.write_text('symbol\nAAPL\n')
            env = {
                'STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV': str(source),
                'STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH': str(ledger),
                'STOCKANALYSIS_MARKET_PRICE_PROVIDER': 'twelve_data',
                'STOCKANALYSIS_MARKET_PRICE_INCLUDE_ACTIVE_RECOMMENDATIONS': 'true',
                'STOCKANALYSIS_MARKET_PRICE_DAILY_BUDGET': '24',
                'STOCKANALYSIS_MARKET_PRICE_MAX_REQUESTS_PER_RUN': '6',
            }
            executor = Mock(); executor.execute_scalar.return_value = '[{"symbol":"AMD"},{"symbol":"AAPL"}]'
            with patch('stockanalysis.operations.market_price_free_backfill.run_market_price_free_backfill', return_value={}) as backfill:
                result = run_market_price_daily_from_env(config=object(), env=env, executor=executor)
            args = backfill.call_args.kwargs
            self.assertEqual(args['daily_budget'], 24)
            self.assertEqual(args['max_requests_per_run'], 6)
            self.assertEqual(args['ledger_path'], str(ledger))
            self.assertEqual(result['watchlist_selection']['selected_symbol_count'], 2)
            self.assertNotEqual(args['watchlist_path'], str(source))

    def test_database_failure_is_not_silently_replaced_with_narrow_watchlist(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root)/'configured.csv'; source.write_text('symbol\nAAPL\n')
            executor = Mock(); executor.execute_scalar.side_effect = RuntimeError('unavailable')
            with self.assertRaisesRegex(RuntimeError, 'unavailable'):
                prepare_priority_watchlist(source_path=str(source), destination=Path(root)/'generated.csv', executor=executor)


if __name__ == '__main__':
    unittest.main()
