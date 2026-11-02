"""Unit tests for the orchestration pipeline module."""

from pathlib import Path
from unittest.mock import patch
import pytest

from scripts.pipeline import step_build_datasets, step_analyze


def test_step_build_datasets_skips_when_files_present(tmp_path):
    with patch("scripts.pipeline.DATA_DIR", tmp_path):
        # Create all three targets
        for t in [50000, 200000, 500000]:
            (tmp_path / f"properties_{t}.csv").write_text("header", encoding="utf-8")
        
        assert step_build_datasets() is True


def test_step_analyze_fails_when_csv_missing(tmp_path):
    with patch("scripts.pipeline.RESULTS_DIR", tmp_path):
        assert step_analyze() is False

