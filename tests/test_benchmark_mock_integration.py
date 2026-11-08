"""End-to-end integration test verifying benchmark execution, export, and analysis."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from scripts.benchmark_runner import BenchmarkRunner, CONFIGURATIONS
from scripts.analyze_results import analyze_all


@pytest.fixture
def mock_db_environment():
    """Mock database connection, cursor, and EXPLAIN ANALYZE results."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Mock environment queries
    mock_cursor.fetchone.side_effect = [
        # SELECT version(), current_database(), current_user;
        {"version": "PostgreSQL 17.2 on x86_64", "current_database": "real_estate_db", "current_user": "postgres"},
        # SHOW server_version_num;
        {"server_version_num": "170002"},
        # SHOW client_encoding;
        {"client_encoding": "UTF8"},
        # SHOW TimeZone;
        {"TimeZone": "Asia/Ho_Chi_Minh"},
        # SELECT datcollate, datctype FROM pg_database ...
        {"datcollate": "C.UTF-8", "datctype": "C.UTF-8"},
        # SELECT COUNT(*), MIN(id), MAX(id) FROM public.properties (for scale 50000)
        (50000, 1, 50000),
        # Q3 diff count (EXCEPT ALL)
        (0,),
    ]

    # Mock pg_settings inspection
    mock_cursor.fetchall.side_effect = [
        [
            {"name": "shared_buffers", "setting": "16384", "unit": "8kB", "source": "configuration file"},
            {"name": "work_mem", "setting": "4096", "unit": "kB", "source": "configuration file"},
        ],
        # INDEX_INSPECTION_SQL calls (per config)
        [
            {"index_name": "properties_pkey", "indisprimary": True, "indisvalid": True, "index_definition": "PRIMARY KEY (id)", "index_bytes": 1048576},
            {"index_name": "idx_properties_province_name", "indisprimary": False, "indisvalid": True, "index_definition": "CREATE INDEX ...", "index_bytes": 2097152},
        ],
    ]

    return mock_conn, mock_cursor


def test_full_benchmark_to_analysis_pipeline(tmp_path, monkeypatch):
    monkeypatch.setattr('scripts.benchmark_validation.csv_fingerprint', lambda p: {'rows':50000,'content_sha256':'fixture'})
    monkeypatch.setattr('scripts.benchmark_validation.database_fingerprint', lambda c: {'rows':50000,'content_sha256':'fixture'})
    monkeypatch.setattr('scripts.benchmark_validation.result_digest', lambda *args: 'fixture-result')
    """Test running benchmark with mocked database, exporting results, and running analysis."""
    output_dir = tmp_path / "benchmark_out"
    analysis_dir = tmp_path / "analysis_out"

    # Create mock plan response
    mock_explain_plan = [
        {
            "Plan": {
                "Node Type": "Index Scan",
                "Index Name": "idx_properties_province_name",
                "Actual Rows": 1200,
                "Actual Loops": 1,
                "Shared Hit Blocks": 45,
                "Shared Read Blocks": 0,
            },
            "Planning Time": 0.25,
            "Execution Time": 1.45,
        }
    ]

    with patch("scripts.benchmark_runner.psycopg.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Handle cursor calls
        def mock_fetchone():
            return {"version": "PostgreSQL 17.2", "current_database": "real_estate_db", "current_user": "postgres",
                    "server_version_num": "170002", "client_encoding": "UTF8", "TimeZone": "UTC",
                    "datcollate": "en_US.UTF-8", "datctype": "en_US.UTF-8"}
        
        mock_cursor.fetchone.return_value = (50000, 1, 50000)
        mock_cursor.fetchall.return_value = [
            {"name": "shared_buffers", "setting": "16384", "unit": "8kB", "source": "default"},
            {"index_name": "properties_pkey", "indisprimary": True, "indisvalid": True, "index_bytes": 1024, "index_definition": "PK"},
            {"index_name": "idx_properties_province_name", "indisprimary": False, "indisvalid": True, "index_bytes": 2048, "index_definition": "INDEX"},
        ]

        runner = BenchmarkRunner(connection_settings={"host": "localhost", "port": 5432, "dbname": "real_estate_db", "user": "postgres", "password": ""})
        
        # Patch execute_explain_analyze to return realistic execution
        with patch.object(runner, "execute_explain_analyze", return_value=(mock_explain_plan, {
            "planning_time_ms": 0.25,
            "execution_time_ms": 1.45,
            "total_time_ms": 1.70,
            "primary_scan_type": "Index Scan",
            "all_scan_types": ["Index Scan"],
            "indexes_used": ["idx_properties_province_name"],
            "actual_rows": 1200,
            "actual_loops": 1,
            "shared_hit_blocks": 45,
            "shared_read_blocks": 0,
            "shared_dirtied_blocks": 0,
            "shared_written_blocks": 0,
            "temp_read_blocks": 0,
            "temp_written_blocks": 0,
        })):
            with patch.object(runner, "inspect_environment", return_value={
                "postgresql_version": "PostgreSQL 17.2",
                "database": "real_estate_db",
                "user": "postgres",
                "pg_settings": {},
            }):
                with patch.object(runner, "prepare_configuration", return_value={
                    "supplemental_index_name": "idx_properties_province_name",
                    "index_bytes": 2097152,
                    "active_indexes": [],
                }):
                    benchmark_res = runner.run_benchmark(
                        scales=[50000],
                        configs_to_run=["Q1_baseline", "Q1_indexed"],
                        warmup_runs=1,
                        official_runs=3,
                        output_dir=output_dir,
                        check_equivalence=False,
                    )

    # Verify outputs
    experiments = list(output_dir.iterdir())
    assert len(experiments) == 1
    output_dir = experiments[0]
    assert (output_dir / 'experiment.json').is_file()
    assert len(list(output_dir.glob('*warmup*.json'))) == 2
    csv_file = output_dir / "benchmark_results.csv"
    json_file = output_dir / "benchmark_summary.json"
    env_file = output_dir / "environment_info.json"

    assert csv_file.is_file()
    assert json_file.is_file()
    assert env_file.is_file()

    # Run analysis pipeline on the generated results
    analysis_res = analyze_all(
        input_csv=csv_file,
        output_dir=analysis_dir,
        generate_plots=True,
    )

    assert analysis_res["report_path"].is_file()
    assert len(analysis_res["plots"]) >= 2
    for plot_path in analysis_res["plots"]:
        assert plot_path.is_file()

