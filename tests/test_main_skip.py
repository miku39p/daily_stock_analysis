# -*- coding: utf-8 -*-
"""Tests for empty STOCK_LIST behavior: skip stocks, keep market review."""

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tests.litellm_stub import ensure_litellm_stub

ensure_litellm_stub()

import main
from src.config import Config


class _DummyConfig(SimpleNamespace):
    def validate(self):
        return []

    def refresh_stock_list(self):
        self.stock_list = list(getattr(self, "stock_list", []) or [])


class TestEmptyStockListMarketOnly(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_path = Path(self.temp_dir.name) / ".env"
        self.env_path.write_text("STOCK_LIST=\n", encoding="utf-8")
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.env_patch = patch.dict(os.environ, {"ENV_FILE": str(self.env_path)}, clear=False)
        self.env_patch.start()
        Config.reset_instance()
        self.original_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)
        Config.reset_instance()
        self.env_patch.stop()
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def _make_args(self, **overrides):
        defaults = {
            "debug": False,
            "stocks": None,
            "webui": False,
            "webui_only": False,
            "serve": False,
            "serve_only": False,
            "host": None,
            "port": None,
            "backtest": False,
            "market_review": False,
            "schedule": False,
            "no_run_immediately": False,
            "check_notify": False,
            "no_notify": False,
            "no_market_review": False,
            "dry_run": False,
            "force_run": True,
            "single_notify": False,
            "no_context_snapshot": False,
            "workers": None,
        }
        defaults.update(overrides)
        return SimpleNamespace(**defaults)

    def _make_config(self, **overrides):
        defaults = {
            "log_dir": str(Path(self.temp_dir.name) / "logs"),
            "webui_enabled": False,
            "schedule_enabled": False,
            "schedule_time": "18:00",
            "schedule_run_immediately": True,
            "run_immediately": True,
            "stock_list": [],
            "market_review_enabled": True,
            "market_review_region": "cn",
            "trading_day_check_enabled": False,
            "single_stock_notify": False,
            "merge_email_notification": False,
            "daily_market_context_enabled": False,
            "analysis_delay": 0,
        }
        defaults.update(overrides)
        return _DummyConfig(**defaults)

    def test_run_full_analysis_skips_stocks_when_watchlist_empty(self):
        args = self._make_args()
        config = self._make_config(stock_list=[])
        pipeline = MagicMock()
        pipeline.run.return_value = [{"code": "SHOULD_NOT_RUN"}]

        with patch("main._refresh_stock_index_cache_for_analysis"), patch(
            "src.core.market_review.run_market_review", return_value="ok"
        ) as mock_review, patch(
            "src.core.pipeline.StockAnalysisPipeline", return_value=pipeline
        ), patch(
            "main._run_market_review_with_shared_lock",
            side_effect=lambda config, fn, **kwargs: fn(**kwargs),
        ):
            ok = main.run_full_analysis(config, args, stock_codes=[])

        self.assertTrue(ok)
        pipeline.run.assert_not_called()
        mock_review.assert_called_once()

    def test_run_full_analysis_runs_stocks_when_watchlist_present(self):
        args = self._make_args(no_market_review=True)
        config = self._make_config(stock_list=["300750"], market_review_enabled=False)
        pipeline = MagicMock()
        pipeline.run.return_value = [{"code": "300750"}]

        with patch("main._refresh_stock_index_cache_for_analysis"), patch(
            "src.core.pipeline.StockAnalysisPipeline", return_value=pipeline
        ):
            ok = main.run_full_analysis(config, args, stock_codes=["300750"])

        self.assertTrue(ok)
        pipeline.run.assert_called_once()
        self.assertEqual(pipeline.run.call_args.kwargs.get("stock_codes"), ["300750"])


if __name__ == "__main__":
    unittest.main()
