"""Unit tests for the Data Processing Performance Benchmark module."""

from pathlib import Path
import pandas as pd
import pytest

from scripts.benchmark_processing import (
    get_current_process_memory_mb,
    measure_execution,
    ensure_parquet_file,
    run_benchmark_for_scale,
    generate_processing_markdown_report,
)


@pytest.fixture
def tiny_csv(tmp_path):
    csv_file = tmp_path / "tiny_properties.csv"
    df = pd.DataFrame({
        "id": list(range(1, 101)),
        "name": [f"Bất động sản {i}" for i in range(1, 101)],
        "property_type_name": ["Nhà", "Căn hộ chung cư"] * 50,
        "province_name": ["Hà Nội", "Hồ Chí Minh"] * 50,
        "district_name": ["Cầu Giấy", "Quận 1"] * 50,
        "ward_name": ["Dịch Vọng", "Bến Nghé"] * 50,
        "price": [float(i * 100_000_000) for i in range(1, 101)],
        "area": [float(40 + i) for i in range(1, 101)],
        "published_at": ["2025-05-01 10:00:00.000"] * 100,
    })
    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    return csv_file


def test_get_current_process_memory_mb():
    mem = get_current_process_memory_mb()
    assert isinstance(mem, float)
    assert mem > 1.0


def test_measure_execution():
    def dummy_task():
        # Allocate some memory and compute
        data = [i ** 2 for i in range(50000)]
        return sum(data)

    metrics = measure_execution(dummy_task, warmups=1, iterations=3)
    assert "median_ms" in metrics
    assert "mean_ms" in metrics
    assert "std_ms" in metrics
    assert "baseline_ram_mb" in metrics
    assert "peak_ram_mb" in metrics
    assert "delta_ram_mb" in metrics
    assert metrics["runs"] == 3
    assert metrics["median_ms"] >= 0.0
    assert metrics["peak_ram_mb"] >= metrics["baseline_ram_mb"]


def test_ensure_parquet_file(tiny_csv, tmp_path):
    parquet_path = tmp_path / "tiny.parquet"
    size = ensure_parquet_file(tiny_csv, parquet_path)
    assert parquet_path.exists()
    assert size > 0


def test_run_benchmark_for_scale(tiny_csv, tmp_path):
    parquet_path = tmp_path / "tiny_test.parquet"
    results = run_benchmark_for_scale(
        csv_path=tiny_csv,
        parquet_path=parquet_path,
        scale=100,
        warmups=1,
        iterations=2,
    )
    assert len(results) == 8
    operations = [r["operation"] for r in results]
    assert "Pandas read_csv" in operations
    assert "Polars read_csv" in operations
    assert "Pandas read_parquet" in operations
    assert "Polars read_parquet" in operations
    assert "Pandas Chunked read_csv (10k)" in operations
    assert "Pandas Chunked aggregate (10k)" in operations
    assert "Pandas Filter + GroupBy" in operations
    assert "Polars Filter + GroupBy" in operations
    for r in results:
        assert "baseline_ram_mb" in r
        assert "peak_ram_mb" in r
        assert "delta_ram_mb" in r
        assert r["peak_ram_mb"] >= r["baseline_ram_mb"]


def test_generate_processing_markdown_report(tiny_csv, tmp_path):
    parquet_path = tmp_path / "tiny_test.parquet"
    results = run_benchmark_for_scale(
        csv_path=tiny_csv,
        parquet_path=parquet_path,
        scale=100,
        warmups=1,
        iterations=2,
    )
    md = generate_processing_markdown_report(results)
    assert "# Báo Cáo Đo Lường Hiệu Năng Xử Lý Dữ Liệu" in md
    assert "Pandas vs. Polars" in md
    assert "CSV vs. Parquet" in md
    assert "Baseline RSS" in md
    assert "Peak RSS" in md
