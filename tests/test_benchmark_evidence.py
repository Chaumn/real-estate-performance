"""Unit tests for Benchmark Raw Evidence Provenance and Verification."""

import json
from pathlib import Path
import pytest

from scripts.verify_benchmark_evidence import (
    compute_sha256,
    extract_plan_metrics,
    audit_raw_evidence,
)


def test_compute_sha256(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("benchmark_provenance", encoding="utf-8")
    h = compute_sha256(f)
    assert isinstance(h, str)
    assert len(h) == 64


def test_extract_plan_metrics():
    mock_plan = [{
        "Plan": {
            "Node Type": "Index Scan",
            "Index Name": "idx_properties_province_name",
        },
        "Planning Time": 0.123,
        "Execution Time": 4.567,
    }]
    p_time, e_time, scan_type = extract_plan_metrics(mock_plan)
    assert p_time == 0.123
    assert e_time == 4.567
    assert scan_type == "Index Scan"


def test_raw_manifest_completeness():
    manifest_path = Path("results/benchmark/raw_manifest.json")
    if not manifest_path.exists():
        pytest.skip("raw_manifest.json does not exist yet")

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["status"] == "VERIFIED"
    assert data["total_files"] == 600
    assert 50000 in data["scales_audited"]
    assert 200000 in data["scales_audited"]
    assert 500000 in data["scales_audited"]
    assert "Q2_indexed" in data["configs_audited"]
    assert len(data["entries"]) == 600
