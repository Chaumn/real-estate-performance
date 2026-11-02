"""Unit tests for the benchmark analysis and visualization module."""

import csv
from pathlib import Path
import tempfile
import pytest

from scripts.analyze_results import (
    generate_markdown_report,
    load_benchmark_csv,
    plot_execution_time_by_scale,
    plot_speedup_comparison,
    plot_storage_overhead,
)


@pytest.fixture
def sample_benchmark_csv(tmp_path):
    csv_file = tmp_path / "sample_results.csv"
    headers = [
        "scale", "query_id", "config_id", "dominant_scan_type", "indexes_used",
        "index_size_mb", "execution_time_median_ms", "execution_time_iqr_ms",
        "execution_time_min_ms", "execution_time_max_ms", "planning_time_median_ms",
        "shared_hit_blocks_median", "shared_read_blocks_median", "speedup",
    ]
    rows = []
    # 2 scales: 50000, 200000
    for scale, factor in [(50000, 1.0), (200000, 4.0)]:
        rows.extend([
            {"scale": scale, "query_id": "Q1", "config_id": "Q1_baseline", "dominant_scan_type": "Seq Scan", "indexes_used": "", "index_size_mb": 0.0, "execution_time_median_ms": 10.0 * factor, "execution_time_iqr_ms": 0.5, "execution_time_min_ms": 9.5 * factor, "execution_time_max_ms": 10.5 * factor, "planning_time_median_ms": 0.2, "shared_hit_blocks_median": 1000 * factor, "shared_read_blocks_median": 0, "speedup": 1.0},
            {"scale": scale, "query_id": "Q1", "config_id": "Q1_indexed", "dominant_scan_type": "Index Scan", "indexes_used": "idx_properties_province_name", "index_size_mb": 1.5 * factor, "execution_time_median_ms": 1.0, "execution_time_iqr_ms": 0.1, "execution_time_min_ms": 0.9, "execution_time_max_ms": 1.1, "planning_time_median_ms": 0.3, "shared_hit_blocks_median": 50, "shared_read_blocks_median": 0, "speedup": 10.0 * factor},
            {"scale": scale, "query_id": "Q2", "config_id": "Q2_baseline", "dominant_scan_type": "Seq Scan", "indexes_used": "", "index_size_mb": 0.0, "execution_time_median_ms": 15.0 * factor, "execution_time_iqr_ms": 0.6, "execution_time_min_ms": 14.5 * factor, "execution_time_max_ms": 15.5 * factor, "planning_time_median_ms": 0.2, "shared_hit_blocks_median": 1000 * factor, "shared_read_blocks_median": 0, "speedup": 1.0},
            {"scale": scale, "query_id": "Q2", "config_id": "Q2_indexed", "dominant_scan_type": "Index Scan", "indexes_used": "idx_properties_location_price", "index_size_mb": 3.0 * factor, "execution_time_median_ms": 0.5, "execution_time_iqr_ms": 0.05, "execution_time_min_ms": 0.45, "execution_time_max_ms": 0.55, "planning_time_median_ms": 0.3, "shared_hit_blocks_median": 20, "shared_read_blocks_median": 0, "speedup": 30.0 * factor},
            {"scale": scale, "query_id": "Q3", "config_id": "Q3_A", "dominant_scan_type": "Seq Scan", "indexes_used": "", "index_size_mb": 0.0, "execution_time_median_ms": 12.0 * factor, "execution_time_iqr_ms": 0.4, "execution_time_min_ms": 11.5 * factor, "execution_time_max_ms": 12.5 * factor, "planning_time_median_ms": 0.2, "shared_hit_blocks_median": 1000 * factor, "shared_read_blocks_median": 0, "speedup": 1.0},
            {"scale": scale, "query_id": "Q3", "config_id": "Q3_B", "dominant_scan_type": "Seq Scan", "indexes_used": "", "index_size_mb": 0.0, "execution_time_median_ms": 11.8 * factor, "execution_time_iqr_ms": 0.4, "execution_time_min_ms": 11.2 * factor, "execution_time_max_ms": 12.2 * factor, "planning_time_median_ms": 0.2, "shared_hit_blocks_median": 1000 * factor, "shared_read_blocks_median": 0, "speedup": 1.02},
            {"scale": scale, "query_id": "Q3", "config_id": "Q3_C", "dominant_scan_type": "Seq Scan", "indexes_used": "", "index_size_mb": 2.0 * factor, "execution_time_median_ms": 12.0 * factor, "execution_time_iqr_ms": 0.4, "execution_time_min_ms": 11.5 * factor, "execution_time_max_ms": 12.5 * factor, "planning_time_median_ms": 0.25, "shared_hit_blocks_median": 1000 * factor, "shared_read_blocks_median": 0, "speedup": 1.0},
            {"scale": scale, "query_id": "Q3", "config_id": "Q3_D", "dominant_scan_type": "Bitmap Scan", "indexes_used": "idx_properties_published_at", "index_size_mb": 2.0 * factor, "execution_time_median_ms": 0.8, "execution_time_iqr_ms": 0.08, "execution_time_min_ms": 0.75, "execution_time_max_ms": 0.85, "planning_time_median_ms": 0.3, "shared_hit_blocks_median": 40, "shared_read_blocks_median": 0, "speedup": 15.0 * factor},
            {"scale": scale, "query_id": "Q4", "config_id": "Q4_baseline", "dominant_scan_type": "Seq Scan", "indexes_used": "", "index_size_mb": 0.0, "execution_time_median_ms": 25.0 * factor, "execution_time_iqr_ms": 1.0, "execution_time_min_ms": 24.0 * factor, "execution_time_max_ms": 26.0 * factor, "planning_time_median_ms": 0.2, "shared_hit_blocks_median": 1000 * factor, "shared_read_blocks_median": 0, "speedup": 1.0},
            {"scale": scale, "query_id": "Q4", "config_id": "Q4_indexed", "dominant_scan_type": "Seq Scan", "indexes_used": "", "index_size_mb": 1.8 * factor, "execution_time_median_ms": 25.5 * factor, "execution_time_iqr_ms": 1.0, "execution_time_min_ms": 24.5 * factor, "execution_time_max_ms": 26.5 * factor, "planning_time_median_ms": 0.25, "shared_hit_blocks_median": 1000 * factor, "shared_read_blocks_median": 0, "speedup": 0.98},
        ])

    with csv_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    return csv_file


def test_load_benchmark_csv(sample_benchmark_csv):
    records = load_benchmark_csv(sample_benchmark_csv)
    assert len(records) == 20
    assert records[0]["scale"] == 50000
    assert records[0]["config_id"] == "Q1_baseline"
    assert records[1]["speedup"] == 10.0


def test_generate_markdown_report(sample_benchmark_csv, tmp_path):
    records = load_benchmark_csv(sample_benchmark_csv)
    report_file = tmp_path / "test_report.md"
    content = generate_markdown_report(records, report_file)
    assert report_file.is_file()
    assert "Q1 — Single-column Index" in content
    assert "Q2 — Composite Index" in content
    assert "Q3 — Tác động độc lập của Query Rewriting" in content
    assert "Q4 — Aggregation Control" in content
    assert "Speedup" in content


def test_generate_plots(sample_benchmark_csv, tmp_path):
    records = load_benchmark_csv(sample_benchmark_csv)
    p1 = plot_execution_time_by_scale(records, tmp_path)
    p2 = plot_speedup_comparison(records, tmp_path)
    p3 = plot_storage_overhead(records, tmp_path)

    assert p1.is_file() and p1.stat().st_size > 0
    assert p2.is_file() and p2.stat().st_size > 0
    assert p3.is_file() and p3.stat().st_size > 0

