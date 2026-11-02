"""Unit tests for the Data Profiling and Data Quality analysis module."""

import json
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

from scripts.data_quality import (
    compute_column_summary,
    compute_numeric_stats,
    compute_grouped_outliers,
    compute_duplicate_stats,
    compute_categorical_distributions,
    profile_dataset,
    generate_markdown_report,
    normalize_text_for_dedup,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5, 6],
        "name": [
            "Bán nhà Ba Đình",
            "Bán nhà Ba Đình!",
            "Căn hộ Cầu Giấy",
            "Đất nền Hòa Lạc",
            "Biệt thự Tây Hồ",
            "Nhà phố Hà Đông",
        ],
        "property_type_name": [
            "Nhà riêng",
            "Nhà riêng",
            "Căn hộ chung cư",
            "Đất",
            "Biệt thự",
            "Nhà riêng",
        ],
        "province_name": [
            "Hà Nội",
            "Hà Nội",
            "Hà Nội",
            "Hà Nội",
            "Hà Nội",
            "Hà Nội",
        ],
        "district_name": [
            "Ba Đình",
            "Ba Đình",
            "Cầu Giấy",
            None,
            "Tây Hồ",
            "Hà Đông",
        ],
        "ward_name": [
            "Kim Mã",
            "Kim Mã",
            None,
            None,
            "Quảng An",
            "Văn Quán",
        ],
        "price": [5000000000.0, 5000000000.0, 3000000000.0, None, 50000000000.0, 4000000000.0],
        "area": [50.0, 50.0, 70.0, 100.0, 300.0, 45.0],
        "published_at": [
            "2025-01-01 10:00:00.000",
            "2025-01-01 10:05:00.000",
            "2025-01-02 11:00:00.000",
            "2025-01-03 12:00:00.000",
            "2025-01-04 13:00:00.000",
            "2025-01-05 14:00:00.000",
        ],
    })


def test_compute_column_summary(sample_df):
    summary = compute_column_summary(sample_df)
    assert "price" in summary
    assert summary["price"]["total_count"] == 6
    assert summary["price"]["missing_count"] == 1
    assert summary["price"]["non_null_count"] == 5
    assert summary["district_name"]["missing_count"] == 1
    assert summary["ward_name"]["missing_count"] == 2
    assert summary["id"]["missing_count"] == 0


def test_compute_numeric_stats():
    # 1, 2, 3, 4, 5, 6, 7, 8, 9, 100 (100 is an outlier)
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 100.0, None])
    stats = compute_numeric_stats(s, "test_col")
    assert stats["name"] == "test_col"
    assert stats["count"] == 10
    assert stats["missing_count"] == 1
    assert stats["min"] == 1.0
    assert stats["max"] == 100.0
    assert stats["outlier_count_high"] >= 1
    assert stats["outlier_pct"] > 0


def test_compute_numeric_stats_empty():
    s = pd.Series([], dtype=float)
    stats = compute_numeric_stats(s, "empty_col")
    assert stats["count"] == 0
    assert stats["min"] is None


def test_compute_grouped_outliers():
    df = pd.DataFrame({
        "type": ["A"] * 105 + ["B"] * 50,
        "val": [10.0] * 100 + [1000.0] * 5 + [20.0] * 50,
    })
    res = compute_grouped_outliers(df, "val", "type", min_sample=100)
    assert "A" in res
    assert "B" not in res  # less than min_sample
    assert res["A"]["outlier_count"] == 5


def test_compute_duplicate_stats(sample_df):
    stats = compute_duplicate_stats(sample_df)
    assert stats["total_rows"] == 6
    assert stats["id_duplicates"] == 0
    assert stats["suspected_duplicates"] >= 2  # rows 0 and 1 are duplicate listings


def test_normalize_text_for_dedup():
    s = pd.Series(["Bán nhà Ba Đình!", "  Bán   nhà, Ba Đình.  "])
    norm = normalize_text_for_dedup(s)
    assert norm.iloc[0] == norm.iloc[1]


def test_profile_dataset(sample_df):
    profile = profile_dataset(sample_df)
    assert profile["total_rows"] == 6
    assert profile["total_columns"] == 9
    assert profile["validity_checks"]["status"] == "PASS"
    assert "numeric_stats" in profile
    assert "price" in profile["numeric_stats"]
    assert "area" in profile["numeric_stats"]
    assert "price_per_m2" in profile["numeric_stats"]


def test_generate_markdown_report(sample_df):
    profile = profile_dataset(sample_df)
    reports = {
        "50000": profile,
        "200000": profile,
        "500000": profile,
    }
    md = generate_markdown_report(reports)
    assert "# Báo Cáo Chất Lượng Dữ Liệu" in md
    assert "Missing Value Analysis" in md
    assert "IQR" in md

