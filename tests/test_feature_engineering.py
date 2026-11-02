"""Unit tests for the Feature Engineering module."""

import numpy as np
import pandas as pd
import pytest

from scripts.feature_engineering import (
    compute_features,
    calculate_iqr_bounds,
    summarize_features,
    export_features,
)


@pytest.fixture
def mock_raw_df():
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "name": [
            "Bán nhà 3 tầng phố cổ Hà Nội",
            "Căn hộ chung cư Vinhomes",
            "Đất nền ngoại thành diện tích cực lớn",
            "Nhà trọ giá rẻ",
        ],
        "property_type_name": ["Nhà riêng", "Căn hộ chung cư", "Đất", "Phòng trọ"],
        "province_name": ["Hà Nội", "Hà Nội", "Hà Nội", "Hồ Chí Minh"],
        "district_name": ["Hoàn Kiếm", "Gia Lâm", None, "Quận 1"],
        "ward_name": ["Hàng Bạc", None, None, "Bến Nghé"],
        "price": [15_000_000_000.0, 3_000_000_000.0, None, 500_000_000.0],
        "area": [50.0, 75.0, 1500.0, 20.0],
        "published_at": [
            "2025-05-10 14:00:00.000",  # Saturday
            "2025-05-12 09:30:00.000",  # Monday
            "2025-06-01 10:00:00.000",  # Sunday
            "2025-07-04 16:45:00.000",  # Friday
        ],
    })


def test_compute_features_derived_columns(mock_raw_df):
    enriched = compute_features(mock_raw_df)

    # Schema integrity: original 9 columns preserved
    for col in mock_raw_df.columns:
        assert col in enriched.columns

    # Check price_per_m2
    # Row 0: 15B / 50m2 = 300,000,000 / m2
    assert enriched.loc[0, "price_per_m2"] == pytest.approx(300_000_000.0)
    # Row 2: Price is None -> price_per_m2 must be NaN
    assert pd.isna(enriched.loc[2, "price_per_m2"])

    # Temporal features
    assert enriched.loc[0, "published_year"] == 2025
    assert enriched.loc[0, "published_month"] == 5
    assert enriched.loc[0, "published_day"] == 10
    assert enriched.loc[0, "is_weekend"] == 1  # Saturday
    assert enriched.loc[1, "is_weekend"] == 0  # Monday
    assert enriched.loc[2, "is_weekend"] == 1  # Sunday

    # Bins
    assert enriched.loc[0, "area_segment"] == "30-60m2"
    assert enriched.loc[2, "area_segment"] == "Trên 200m2"
    assert enriched.loc[3, "area_segment"] == "Dưới 30m2"

    assert enriched.loc[0, "price_segment"] == "10 - 20 tỷ"
    assert enriched.loc[1, "price_segment"] == "2 - 5 tỷ"
    assert enriched.loc[2, "price_segment"] == "Thỏa thuận"

    # Indicators
    assert enriched.loc[0, "has_district"] == 1
    assert enriched.loc[2, "has_district"] == 0
    assert enriched.loc[0, "has_ward"] == 1
    assert enriched.loc[1, "has_ward"] == 0

    # Text metadata
    assert enriched.loc[0, "name_length"] == len("Bán nhà 3 tầng phố cổ Hà Nội")
    assert enriched.loc[0, "name_word_count"] == 8


def test_calculate_iqr_bounds():
    s = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    low, high = calculate_iqr_bounds(s)
    assert low >= 0
    assert high > low


def test_summarize_features(mock_raw_df):
    enriched = compute_features(mock_raw_df)
    summary = summarize_features(enriched)
    assert summary["total_rows"] == 4
    assert "price_per_m2" in summary["new_feature_names"]
    assert "area_segment_distribution" in summary


def test_export_features(tmp_path, mock_raw_df):
    csv_in = tmp_path / "raw_test.csv"
    mock_raw_df.to_csv(csv_in, index=False)

    out_file = export_features(csv_in, output_dir=tmp_path / "out", file_format="parquet")
    assert out_file.exists()
    assert out_file.suffix == ".parquet"

    # Verify read back
    read_df = pd.read_parquet(out_file)
    assert len(read_df) == 4
    assert "price_per_m2" in read_df.columns
