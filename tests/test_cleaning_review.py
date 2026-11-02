"""Comprehensive Cleaning Review and Edge Case Validation Tests.

Validates that cleaning preserving Vietnamese diacritics, complex CSV quoting,
extreme legitimate values, ISO8601 variations, and schema contract integrity.
"""

import io
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from scripts.cleaning import COLUMNS, REQUIRED_COLUMNS, clean_dataframe


@pytest.fixture
def base_row():
    return {
        "name": "Bán nhà mặt phố Giảng Võ, Ba Đình, Hà Nội - Sổ đỏ chính chủ",
        "property_type_name": "Nhà riêng",
        "province_name": "Thành phố Hà Nội",
        "district_name": "Quận Ba Đình",
        "ward_name": "Phường Giảng Võ",
        "price": 15_500_000_000.0,
        "area": 85.5,
        "published_at": "2025-05-10T14:30:00.000000",
    }


def test_vietnamese_diacritics_preservation(base_row):
    """Ensure Vietnamese tone marks and special characters are preserved 100%."""
    vietnamese_title = "Đất nền dự án Phước Vĩnh Tây, Cần Giuộc, Long An - Giá siêu đầu tư!"
    row = {**base_row, "name": vietnamese_title, "province_name": "Tỉnh Long An"}
    df = pd.DataFrame([row])
    cleaned, report = clean_dataframe(df)

    assert len(cleaned) == 1
    assert cleaned.iloc[0]["name"] == vietnamese_title
    assert cleaned.iloc[0]["province_name"] == "Tỉnh Long An"
    # Ensure characters like 'Đ', 'ướ', 'ĩ', 'ề' exist verbatim
    assert "Đ" in cleaned.iloc[0]["name"]
    assert "ướ" in cleaned.iloc[0]["name"]
    assert "ĩ" in cleaned.iloc[0]["name"]


def test_csv_quoting_with_newlines_and_quotes(base_row, tmp_path):
    """Ensure names containing quotes, commas, and multiline text survive CSV serialization."""
    tricky_name = 'Bán biệt thự "Hoa Sữa 05", KĐT Vinhomes Riverside,\n view hồ thoáng đãng!'
    row = {**base_row, "name": tricky_name}
    df = pd.DataFrame([row])
    cleaned, _ = clean_dataframe(df)

    csv_file = tmp_path / "test_tricky_export.csv"
    cleaned.to_csv(csv_file, index=False, encoding="utf-8-sig")

    # Read back and verify exact character match
    read_back = pd.read_csv(csv_file)
    assert len(read_back) == 1
    assert read_back.iloc[0]["name"] == tricky_name


def test_extreme_legitimate_values_retained(base_row):
    """Ensure massive commercial values and large farm areas are not dropped."""
    row = {
        **base_row,
        "price": 950_000_000_000_000.0,  # 950 nghìn tỷ
        "area": 25_000_000.0,  # 25 triệu m2
    }
    df = pd.DataFrame([row])
    cleaned, report = clean_dataframe(df)

    assert len(cleaned) == 1
    assert cleaned.iloc[0]["price"] == 950_000_000_000_000.0
    assert cleaned.iloc[0]["area"] == 25_000_000.0
    assert report["removed_rows"] == 0


def test_zero_and_negative_price_coerced_without_dropping_row(base_row):
    """Zero and negative prices should become NaN, but the record must be retained."""
    rows = [
        {**base_row, "price": 0.0},
        {**base_row, "price": -5000000.0},
        {**base_row, "price": None},
    ]
    df = pd.DataFrame(rows)
    cleaned, report = clean_dataframe(df)

    assert len(cleaned) == 3
    assert cleaned["price"].isna().all()
    assert report["removed_rows"] == 0
    assert report["invalid_price"] == 2  # 0.0 and -5000000.0 counted as invalid_price


def test_schema_columns_order_and_types(base_row):
    """Ensure clean_dataframe always emits the exact 8 COLUMNS in order."""
    row_with_extra = {**base_row, "extra_col_1": 123, "extra_col_2": "test"}
    df = pd.DataFrame([row_with_extra])
    cleaned, _ = clean_dataframe(df)

    assert list(cleaned.columns) == COLUMNS
    assert "extra_col_1" not in cleaned.columns


def test_iso8601_format_variations(base_row):
    """Validate ISO8601 variations with and without microseconds, space or T separator."""
    rows = [
        {**base_row, "published_at": "2025-06-15T08:00:00"},
        {**base_row, "published_at": "2025-06-15 08:00:00"},
        {**base_row, "published_at": "2025-06-15T08:00:00.123456"},
    ]
    df = pd.DataFrame(rows)
    cleaned, report = clean_dataframe(df)

    assert len(cleaned) == 3
    assert report["invalid_date"] == 0
    assert report["removed_rows"] == 0


def test_whitespace_and_tab_stripping_on_all_text_columns():
    """Ensure all text columns strip spaces, tabs, and convert whitespace-only to NA."""
    df = pd.DataFrame([{
        "name": "  Căn hộ studio đẹp   ",
        "property_type_name": "\tChung cư\t",
        "province_name": "  Đà Nẵng  ",
        "district_name": "   \n\t  ",
        "ward_name": " ",
        "price": 1_200_000_000.0,
        "area": 35.0,
        "published_at": "2025-03-01T00:00:00",
    }])
    cleaned, report = clean_dataframe(df)

    assert len(cleaned) == 1
    row = cleaned.iloc[0]
    assert row["name"] == "Căn hộ studio đẹp"
    assert row["property_type_name"] == "Chung cư"
    assert row["province_name"] == "Đà Nẵng"
    assert pd.isna(row["district_name"])
    assert pd.isna(row["ward_name"])
