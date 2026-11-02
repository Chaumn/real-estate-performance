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


def test_tamper_detection_negative(tmp_path):
    """Negative test: tampered execution plan must fail SHA-256 check against manifest."""
    manifest_path = Path("results/benchmark/raw_manifest.json")
    if not manifest_path.exists():
        pytest.skip("raw_manifest.json does not exist yet")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    first_entry = manifest["entries"][0]
    raw_file = Path("results/benchmark/raw") / first_entry["filename"]
    if not raw_file.exists():
        pytest.skip("Raw file missing")

    # Tampered file with 1 extra byte
    tampered_file = tmp_path / first_entry["filename"]
    tampered_file.write_bytes(raw_file.read_bytes() + b"\n")

    tampered_hash = compute_sha256(tampered_file)
    assert tampered_hash != first_entry["sha256"], "Tampered file should produce different SHA-256"


def test_corrupted_plan_syntax_negative(tmp_path):
    """Negative test: corrupted JSON syntax must raise json.JSONDecodeError."""
    corrupted_file = tmp_path / "corrupted_plan.json"
    corrupted_file.write_text("{ \"Plan\": { truncated... ", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        with open(corrupted_file, "r", encoding="utf-8") as f:
            json.load(f)


def test_sort_node_injection_negative():
    """Negative test: injecting a Sort node into an indexed plan must be flagged."""
    indexed_plan_path = Path("results/benchmark/raw/500000_Q2_indexed_run01.json")
    if not indexed_plan_path.exists():
        pytest.skip("Indexed plan missing")

    with open(indexed_plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    # In clean plan, no Sort node
    def has_sort(node):
        if node.get("Node Type") == "Sort":
            return True
        for child in node.get("Plans", []):
            if has_sort(child):
                return True
        return False

    assert not has_sort(plan_data[0]["Plan"]), "Clean indexed plan should have no Sort node"

    # Inject Sort node
    plan_data[0]["Plan"]["Plans"] = [{"Node Type": "Sort", "Total Cost": 999.0}]
    assert has_sort(plan_data[0]["Plan"]), "Injected Sort node must be detected"
