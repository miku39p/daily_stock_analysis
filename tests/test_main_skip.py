# -*- coding: utf-8 -*-
"""Unit tests for main.py skip behavior when STOCK_LIST is empty or unconfigured."""

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


class TestMainSkipLogic(unittest.TestCase):
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
            "force_run": False,
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
        }
        defaults.update(overrides)
        return _DummyConfig(**defaults)

    def _run_main(self, args, config, stock_list_env: str):
        os.environ["STOCK_LIST"] = stock_list_env
        with patch("main.parse_arguments", return_value=args), patch(
            "main.get_config", return_value=config
        ), patch("main._setup_bootstrap_logging"), patch(
            "main._setup_runtime_logging"
        ), patch(
            "main._run_analysis_with_runtime_scheduler_lock"
        ) as mock_run_lock, patch(
            "main.run_full_analysis"
        ) as mock_run_full:
            exit_code = main.main()
        return exit_code, mock_run_lock, mock_run_full

    def test_main_skip_when_stock_list_empty(self):
        args = self._make_args()
        config = self._make_config()
        exit_code, mock_run_lock, mock_run_full = self._run_main(args, config, "")
        self.assertEqual(exit_code, 0)
        mock_run_lock.assert_not_called()
        mock_run_full.assert_not_called()

    def test_main_skip_when_stock_list_whitespace(self):
        args = self._make_args()
        config = self._make_config()
        exit_code, mock_run_lock, mock_run_full = self._run_main(args, config, "   ")
        self.assertEqual(exit_code, 0)
        mock_run_lock.assert_not_called()
        mock_run_full.assert_not_called()

    def test_main_no_skip_when_stock_list_configured(self):
        args = self._make_args()
        config = self._make_config(stock_list=["600519"])
        exit_code, mock_run_lock, mock_run_full = self._run_main(args, config, "600519")
        self.assertEqual(exit_code, 0)
        mock_run_lock.assert_called_once()
        mock_run_full.assert_not_called()

    def test_main_no_skip_when_cli_stocks_provided(self):
        args = self._make_args(stocks="000001")
        config = self._make_config()
        exit_code, mock_run_lock, mock_run_full = self._run_main(args, config, "")
        self.assertEqual(exit_code, 0)
        mock_run_lock.assert_called_once()
        mock_run_full.assert_not_called()

    def test_main_no_skip_when_market_review_only(self):
        """--market-review takes a dedicated path before the empty STOCK_LIST skip."""
        args = self._make_args(market_review=True)
        config = self._make_config(trading_day_check_enabled=False, market_review_region="cn")
        os.environ["STOCK_LIST"] = ""
        with patch("main.parse_arguments", return_value=args), patch(
            "main.get_config", return_value=config
        ), patch("main._setup_bootstrap_logging"), patch(
            "main._setup_runtime_logging"
        ), patch(
            "main._run_analysis_with_runtime_scheduler_lock"
        ) as mock_run_lock, patch(
            "src.core.market_review_runtime.build_market_review_runtime",
            return_value=(MagicMock(), MagicMock(), MagicMock()),
        ), patch(
            "main._run_market_review_with_shared_lock"
        ) as mock_review:
            exit_code = main.main()
        self.assertEqual(exit_code, 0)
        mock_run_lock.assert_not_called()
        mock_review.assert_called_once()


if __name__ == "__main__":
    unittest.main()
