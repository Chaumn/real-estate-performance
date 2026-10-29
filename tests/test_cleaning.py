from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts import clean_data
from scripts.cleaning import COLUMNS, clean_dataframe


@pytest.fixture
def valid_row():
    return {
        "name": "Nha ban",
        "property_type_name": "Nha rieng",
        "province_name": "Ha Noi",
        "district_name": "Ba Dinh",
        "ward_name": "Dien Bien",
        "price": 2_000_000_000,
        "area": 50,
        "published_at": "2026-01-02T03:04:05",
    }


def test_mixed_iso8601_timestamps(valid_row):
    raw = pd.DataFrame([
        {**valid_row, "published_at": "2026-01-02T03:04:05"},
        {**valid_row, "published_at": "2026-01-02T03:04:05.123456"},
    ])

    cleaned, report = clean_dataframe(raw)

    assert cleaned["published_at"].tolist() == [
        pd.Timestamp("2026-01-02 03:04:05"),
        pd.Timestamp("2026-01-02 03:04:05.123456"),
    ]
    assert report["invalid_date"] == 0
    assert report["removed_rows"] == 0


@pytest.mark.parametrize(
    "price, invalid_price",
    [(None, 0), (np.nan, 0), (pd.NA, 0), ("bad", 0), (0, 1), (-1, 1),
     (np.inf, 1), (-np.inf, 1)],
)
def test_invalid_price_becomes_null_without_removing_row(
    valid_row, price, invalid_price
):
    cleaned, report = clean_dataframe(pd.DataFrame([{**valid_row, "price": price}]))

    assert len(cleaned) == 1
    assert cleaned["price"].isna().all()
    assert report["invalid_price"] == invalid_price
    assert report["removed_rows"] == 0
    assert report["missing_price_after_cleaning"] == 1


@pytest.mark.parametrize("area", [None, np.nan, pd.NA, "bad", 0, -1, np.inf, -np.inf])
def test_invalid_area_removes_row(valid_row, area):
    cleaned, report = clean_dataframe(pd.DataFrame([{**valid_row, "area": area}]))

    assert cleaned.empty
    assert report["invalid_area"] == 1
    assert report["removed_rows"] == 1


def test_nullable_numeric_area_removes_missing_values(valid_row):
    raw = pd.DataFrame([valid_row, valid_row])
    raw["area"] = pd.Series([pd.NA, 50], dtype="Float64")

    cleaned, report = clean_dataframe(raw)

    assert cleaned.index.tolist() == [1]
    assert report["invalid_area"] == 1
    assert report["removed_rows"] == 1


@pytest.mark.parametrize("column", ["name", "property_type_name", "province_name"])
@pytest.mark.parametrize("value", [None, pd.NA, "", " \t "])
def test_missing_required_text_removes_row(valid_row, column, value):
    cleaned, report = clean_dataframe(pd.DataFrame([{**valid_row, column: value}]))

    assert cleaned.empty
    assert report["invalid_required"] == 1
    assert report["removed_rows"] == 1


@pytest.mark.parametrize("value", [None, pd.NA, "", " \t "])
def test_optional_locations_remain_null(valid_row, value):
    raw = pd.DataFrame([{**valid_row, "district_name": value, "ward_name": value}])

    cleaned, report = clean_dataframe(raw)

    assert len(cleaned) == 1
    assert cleaned[["district_name", "ward_name"]].isna().all().all()
    assert report["missing_district_after_cleaning"] == 1
    assert report["invalid_required"] == 0
    assert report["removed_rows"] == 0


@pytest.mark.parametrize("value", [None, "bad", "2026-02-30T03:04:05"])
def test_invalid_date_removes_row(valid_row, value):
    cleaned, report = clean_dataframe(
        pd.DataFrame([{**valid_row, "published_at": value}])
    )

    assert cleaned.empty
    assert report["invalid_date"] == 1
    assert report["removed_rows"] == 1


def test_overlapping_invalid_reasons_remove_row_once(valid_row):
    raw = pd.DataFrame([
        {**valid_row, "name": None, "area": 0, "published_at": "bad"},
        valid_row,
    ])

    cleaned, report = clean_dataframe(raw)

    assert cleaned.index.tolist() == [1]
    assert report["invalid_required"] == 1
    assert report["invalid_area"] == 1
    assert report["invalid_date"] == 1
    assert report["removed_rows"] == 1
    assert report["cleaned_rows"] == 1


def test_normalization_preserves_input_indices_duplicates_and_extreme_values(valid_row):
    row = {
        **valid_row,
        "name": "  Nha ban \t",
        "property_type_name": " Nha rieng ",
        "province_name": " Ha Noi ",
        "district_name": " Ba Dinh ",
        "ward_name": " Dien Bien ",
        "price": "1e30",
        "area": "1e20",
        "unused": "ignored",
    }
    raw = pd.DataFrame([row, row], index=[7, 7])
    original = raw.copy(deep=True)

    cleaned, report = clean_dataframe(raw)

    pd.testing.assert_frame_equal(raw, original)
    assert cleaned.columns.tolist() == COLUMNS
    assert cleaned.index.tolist() == [7, 7]
    assert cleaned["name"].tolist() == [valid_row["name"]] * 2
    for column in ["property_type_name", "province_name", "district_name", "ward_name"]:
        assert cleaned[column].tolist() == [valid_row[column]] * 2
    assert cleaned["price"].eq(1e30).all()
    assert cleaned["area"].eq(1e20).all()
    assert report["removed_rows"] == 0


def test_missing_columns_raise_clear_error(valid_row):
    raw = pd.DataFrame([valid_row]).drop(columns="area")

    with pytest.raises(ValueError, match="Thieu cot:.*area"):
        clean_dataframe(raw)


def test_empty_dataframe():
    cleaned, report = clean_dataframe(pd.DataFrame(columns=COLUMNS))

    assert cleaned.empty
    assert cleaned.columns.tolist() == COLUMNS
    assert all(value == 0 for value in report.values())


def test_sample_script_preserves_source_ids_and_csv_format(valid_row, tmp_path, monkeypatch):
    input_path = tmp_path / "sample.csv"
    output_path = tmp_path / "processed" / "cleaned.csv"
    report_path = tmp_path / "results" / "report.csv"
    pd.DataFrame([
        {**valid_row, "published_at": "2026-01-02T03:04:05.123456"},
        {**valid_row, "name": None},
        {**valid_row, "price": None, "district_name": None},
    ]).to_csv(input_path, index=False)
    monkeypatch.setattr(clean_data, "INPUT_PATH", input_path)
    monkeypatch.setattr(clean_data, "OUTPUT_PATH", output_path)
    monkeypatch.setattr(clean_data, "REPORT_PATH", report_path)

    clean_data.main()

    output_bytes = output_path.read_bytes()
    assert output_bytes.startswith(b"\xef\xbb\xbf")
    assert report_path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert b"2026-01-02 03:04:05.123456" in output_bytes
    assert b"2026-01-02 03:04:05.000000" in output_bytes
    output = pd.read_csv(output_path)
    assert output.columns.tolist() == ["id", *COLUMNS]
    assert output["id"].tolist() == [1, 3]
    assert pd.isna(output.loc[1, "price"])
    assert pd.isna(output.loc[1, "district_name"])
    assert pd.read_csv(report_path).loc[0, "removed_rows"] == 1


def test_sample_5000_regression():
    sample_path = Path(__file__).resolve().parents[1] / "data/raw/sample_5000.csv"
    if not sample_path.exists():
        pytest.skip("Local sample_5000.csv is not available")

    cleaned, report = clean_dataframe(pd.read_csv(sample_path))

    assert len(cleaned) == 4997
    assert report == {
        "original_rows": 5000,
        "invalid_required": 3,
        "invalid_area": 0,
        "invalid_date": 0,
        "invalid_price": 0,
        "removed_rows": 3,
        "cleaned_rows": 4997,
        "missing_price_after_cleaning": 380,
        "missing_district_after_cleaning": 165,
    }
