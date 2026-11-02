"""Unit tests for the dashboard server and HTTP handlers."""

import json
from pathlib import Path
import pytest
from unittest.mock import MagicMock

from scripts.dashboard import BenchmarkDashboardHandler, DASHBOARD_HTML


def test_dashboard_html_contains_critical_components():
    assert "PostgreSQL Real Estate Performance Benchmark Dashboard" in DASHBOARD_HTML
    assert "scaleSelect" in DASHBOARD_HTML
    assert "querySelect" in DASHBOARD_HTML
    assert "configSelect" in DASHBOARD_HTML
    assert "execChart" in DASHBOARD_HTML
    assert "speedupChart" in DASHBOARD_HTML
    assert "planContainer" in DASHBOARD_HTML
    assert "sqlContainer" in DASHBOARD_HTML


def test_dashboard_handler_get_html(tmp_path):
    handler = BenchmarkDashboardHandler.__new__(BenchmarkDashboardHandler)
    handler.path = "/"
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = MagicMock()

    handler.do_GET()

    handler.send_response.assert_called_with(200)
    handler.send_header.assert_called_with("Content-Type", "text/html; charset=utf-8")
    assert handler.wfile.write.call_count == 1

