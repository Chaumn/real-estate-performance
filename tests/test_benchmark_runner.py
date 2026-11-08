"""Unit tests for the automated PostgreSQL benchmark runner."""

import json
from pathlib import Path
import pytest

from scripts.benchmark_runner import (
    CONFIGURATIONS,
    compute_statistics,
    extract_plan_metrics,
    extract_plan_nodes,
    read_sql_file,
)


def test_configuration_matrix_completeness():
    assert len(CONFIGURATIONS) == 10
    config_ids = [c["config_id"] for c in CONFIGURATIONS]
    expected_ids = [
        "Q1_baseline", "Q1_indexed",
        "Q2_baseline", "Q2_indexed",
        "Q3_A", "Q3_B", "Q3_C", "Q3_D",
        "Q4_baseline", "Q4_indexed",
    ]
    assert config_ids == expected_ids

    # Check each config points to valid files
    for config in CONFIGURATIONS:
        query_sql = read_sql_file(Path("queries") / config["query_file"])
        assert query_sql.startswith("SELECT")
        if config["index_file"]:
            index_sql = read_sql_file(Path("indexes") / config["index_file"])
            assert "CREATE INDEX" in index_sql


def test_compute_statistics_odd_even_counts():
    # Odd count: 5 elements
    odd_data = [10.0, 20.0, 15.0, 30.0, 25.0]
    stats_odd = compute_statistics(odd_data)
    assert stats_odd["median"] == 20.0
    assert stats_odd["min"] == 10.0
    assert stats_odd["max"] == 30.0
    assert stats_odd["mean"] == 20.0

    # Even count: 20 elements (as in official benchmark)
    even_data = list(range(1, 21))
    stats_even = compute_statistics(even_data)
    assert stats_even["median"] == 10.5
    assert stats_even["min"] == 1.0
    assert stats_even["max"] == 20.0
    assert stats_even["mean"] == 10.5
    assert stats_even["iqr"] == 10.0


def test_extract_plan_metrics_seq_scan():
    sample_plan = [
        {
            "Plan": {
                "Node Type": "Seq Scan",
                "Parallel Aware": False,
                "Relation Name": "properties",
                "Alias": "properties",
                "Startup Cost": 0.0,
                "Total Cost": 25000.0,
                "Plan Rows": 12000,
                "Plan Width": 64,
                "Actual Startup Time": 0.05,
                "Actual Total Time": 38.45,
                "Actual Rows": 11500,
                "Actual Loops": 1,
                "Filter": "(province_name = 'Hải Phòng'::text)",
                "Rows Removed by Filter": 488500,
                "Shared Hit Blocks": 18500,
                "Shared Read Blocks": 0,
                "Shared Dirtied Blocks": 0,
                "Shared Written Blocks": 0,
            },
            "Planning Time": 0.25,
            "Triggers": [],
            "Execution Time": 39.12,
        }
    ]

    metrics = extract_plan_metrics(sample_plan)
    assert metrics["planning_time_ms"] == 0.25
    assert metrics["execution_time_ms"] == 39.12
    assert metrics["primary_scan_type"] == "Seq Scan"
    assert metrics["shared_hit_blocks"] == 18500
    assert metrics["shared_read_blocks"] == 0
    assert metrics["actual_rows"] == 11500
    assert metrics["indexes_used"] == []


def test_extract_plan_metrics_index_scan():
    sample_plan = [
        {
            "Plan": {
                "Node Type": "Limit",
                "Parallel Aware": False,
                "Startup Cost": 0.42,
                "Total Cost": 85.2,
                "Plan Rows": 20,
                "Plan Width": 80,
                "Actual Startup Time": 0.03,
                "Actual Total Time": 0.85,
                "Actual Rows": 20,
                "Actual Loops": 1,
                "Shared Hit Blocks": 45,
                "Shared Read Blocks": 2,
                "Plans": [
                    {
                        "Node Type": "Index Scan",
                        "Parent Relationship": "Outer",
                        "Parallel Aware": False,
                        "Scan Direction": "Forward",
                        "Index Name": "idx_properties_location_price",
                        "Relation Name": "properties",
                        "Alias": "properties",
                        "Startup Cost": 0.42,
                        "Total Cost": 1500.0,
                        "Plan Rows": 350,
                        "Actual Startup Time": 0.03,
                        "Actual Total Time": 0.84,
                        "Actual Rows": 20,
                        "Actual Loops": 1,
                    }
                ],
            },
            "Planning Time": 0.35,
            "Triggers": [],
            "Execution Time": 0.92,
        }
    ]

    metrics = extract_plan_metrics(sample_plan)
    assert metrics["planning_time_ms"] == 0.35
    assert metrics["execution_time_ms"] == 0.92
    assert metrics["primary_scan_type"] == "Index Scan"
    assert metrics["indexes_used"] == ["idx_properties_location_price"]
    assert metrics["shared_hit_blocks"] == 45
    assert metrics["shared_read_blocks"] == 2


def test_extract_plan_metrics_bitmap_scan():
    sample_plan = [
        {
            "Plan": {
                "Node Type": "Bitmap Heap Scan",
                "Relation Name": "properties",
                "Alias": "properties",
                "Actual Startup Time": 0.15,
                "Actual Total Time": 2.45,
                "Actual Rows": 120,
                "Actual Loops": 1,
                "Shared Hit Blocks": 85,
                "Shared Read Blocks": 0,
                "Plans": [
                    {
                        "Node Type": "Bitmap Index Scan",
                        "Index Name": "idx_properties_published_at",
                        "Actual Startup Time": 0.08,
                        "Actual Total Time": 0.08,
                        "Actual Rows": 120,
                        "Actual Loops": 1,
                    }
                ],
            },
            "Planning Time": 0.18,
            "Execution Time": 2.55,
        }
    ]

    metrics = extract_plan_metrics(sample_plan)
    assert metrics["primary_scan_type"] == "Bitmap Scan"
    assert "idx_properties_published_at" in metrics["indexes_used"]
    assert metrics["shared_hit_blocks"] == 85


def test_extract_plan_metrics_parallel_workers():
    sample_plan = [
        {
            "Plan": {
                "Node Type": "Gather",
                "Actual Rows": 50,
                "Shared Hit Blocks": 10,
                "Shared Read Blocks": 5,
                "Workers": [
                    {
                        "Worker Number": 0,
                        "Shared Hit Blocks": 100,
                        "Shared Read Blocks": 20,
                    },
                    {
                        "Worker Number": 1,
                        "Shared Hit Blocks": 120,
                        "Shared Read Blocks": 15,
                    },
                ],
                "Plans": [
                    {
                        "Node Type": "Seq Scan",
                        "Relation Name": "properties",
                    }
                ],
            },
            "Planning Time": 0.5,
            "Execution Time": 15.0,
        }
    ]

    metrics = extract_plan_metrics(sample_plan)
    assert metrics["shared_hit_blocks"] == 10
    assert metrics["shared_read_blocks"] == 5
    assert metrics["primary_scan_type"] == "Seq Scan"


def test_compute_statistics_edge_cases():
    empty_stats = compute_statistics([])
    assert empty_stats["median"] == 0.0

    identical_stats = compute_statistics([5.0, 5.0, 5.0, 5.0])
    assert identical_stats["median"] == 5.0
    assert identical_stats["std"] == 0.0
    assert identical_stats["iqr"] == 0.0

