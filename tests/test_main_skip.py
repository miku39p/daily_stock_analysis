# -*- coding: utf-8 -*-
"""Unit tests to verify main.py skip behavior when STOCK_LIST is empty or unconfigured."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import main


class TestMainSkipLogic(unittest.TestCase):
    def setUp(self):
        # Backup environment variables
        self.original_env = dict(os.environ)

    def tearDown(self):
        # Restore environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch("main.parse_arguments")
    @patch("main.run_full_analysis")
    @patch("main.setup_logging")
    def test_main_skip_when_stock_list_empty(
        self, mock_setup_logging, mock_run_full_analysis, mock_parse_arguments
    ):
        """Test that main skips analysis run when STOCK_LIST is configured but empty."""
        # Configure arguments: standard run, no stocks specified, no market-review
        mock_args = MagicMock()
        mock_args.stocks = None
        mock_args.schedule = False
        mock_args.market_review = False
        mock_args.backtest = False
        mock_args.webui = False
        mock_args.webui_only = False
        mock_args.serve = False
        mock_args.serve_only = False
        mock_args.debug = False
        mock_parse_arguments.return_value = mock_args

        # Set STOCK_LIST environment variable to empty string
        os.environ["STOCK_LIST"] = ""

        # Call main()
        exit_code = main()

        # Verify it skipped execution (returned 0 and did not call run_full_analysis)
        self.assertEqual(exit_code, 0)
        mock_run_full_analysis.assert_not_called()

    @patch("main.parse_arguments")
    @patch("main.run_full_analysis")
    @patch("main.setup_logging")
    def test_main_skip_when_stock_list_whitespace(
        self, mock_setup_logging, mock_run_full_analysis, mock_parse_arguments
    ):
        """Test that main skips analysis run when STOCK_LIST is configured with only whitespace."""
        # Configure arguments: standard run, no stocks specified, no market-review
        mock_args = MagicMock()
        mock_args.stocks = None
        mock_args.schedule = False
        mock_args.market_review = False
        mock_args.backtest = False
        mock_args.webui = False
        mock_args.webui_only = False
        mock_args.serve = False
        mock_args.serve_only = False
        mock_args.debug = False
        mock_parse_arguments.return_value = mock_args

        # Set STOCK_LIST environment variable to whitespace string
        os.environ["STOCK_LIST"] = "   "

        # Call main()
        exit_code = main()

        # Verify it skipped execution (returned 0 and did not call run_full_analysis)
        self.assertEqual(exit_code, 0)
        mock_run_full_analysis.assert_not_called()

    @patch("main.parse_arguments")
    @patch("main.run_full_analysis")
    @patch("main.setup_logging")
    def test_main_no_skip_when_stock_list_configured(
        self, mock_setup_logging, mock_run_full_analysis, mock_parse_arguments
    ):
        """Test that main does not skip analysis run when STOCK_LIST is properly configured."""
        # Configure arguments: standard run, no stocks specified, no market-review
        mock_args = MagicMock()
        mock_args.stocks = None
        mock_args.schedule = False
        mock_args.market_review = False
        mock_args.backtest = False
        mock_args.webui = False
        mock_args.webui_only = False
        mock_args.serve = False
        mock_args.serve_only = False
        mock_args.debug = False
        mock_parse_arguments.return_value = mock_args

        # Set STOCK_LIST environment variable to a valid stock list
        os.environ["STOCK_LIST"] = "600519"

        # Call main()
        exit_code = main()

        # Verify it did not skip execution (called run_full_analysis)
        self.assertEqual(exit_code, 0)
        mock_run_full_analysis.assert_called_once()

    @patch("main.parse_arguments")
    @patch("main.run_full_analysis")
    @patch("main.setup_logging")
    def test_main_no_skip_when_cli_stocks_provided(
        self, mock_setup_logging, mock_run_full_analysis, mock_parse_arguments
    ):
        """Test that main does not skip analysis run when STOCK_LIST is empty but CLI stocks are provided."""
        # Configure arguments: standard run, stocks specified in CLI, no market-review
        mock_args = MagicMock()
        mock_args.stocks = "000001"
        mock_args.schedule = False
        mock_args.market_review = False
        mock_args.backtest = False
        mock_args.webui = False
        mock_args.webui_only = False
        mock_args.serve = False
        mock_args.serve_only = False
        mock_args.debug = False
        mock_parse_arguments.return_value = mock_args

        # Set STOCK_LIST environment variable to empty string
        os.environ["STOCK_LIST"] = ""

        # Call main()
        exit_code = main()

        # Verify it did not skip execution (called run_full_analysis)
        self.assertEqual(exit_code, 0)
        mock_run_full_analysis.assert_called_once()


if __name__ == "__main__":
    unittest.main()
