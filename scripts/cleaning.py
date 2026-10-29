"""Shared cleaning rules for real estate DataFrames."""

import numpy as np
import pandas as pd


COLUMNS = [
    "name",
    "property_type_name",
    "province_name",
    "district_name",
    "ward_name",
    "price",
    "area",
    "published_at",
]

TEXT_COLUMNS = [
    "name",
    "property_type_name",
    "province_name",
    "district_name",
    "ward_name",
]

REQUIRED_COLUMNS = ["name", "property_type_name", "province_name"]


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Return cleaned data and row counts without modifying the input.

    Keep source indices so callers can attach source-row IDs. Only missing
    required text, invalid area, or invalid dates remove rows. Missing prices
    and optional locations remain NULL; duplicates and outliers are retained.
    Invalid counts are computed independently before filtering, so a row can
    contribute to several counts but is counted only once in removed_rows.
    """
    missing_cols = set(COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Thieu cot: {missing_cols}")

    df = df[COLUMNS].copy()
    original_count = len(df)

    for col in TEXT_COLUMNS:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace("", pd.NA)

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    invalid_price = df["price"].notna() & (
        ~np.isfinite(df["price"]) | (df["price"] <= 0)
    )
    df.loc[invalid_price, "price"] = np.nan

    df["area"] = pd.to_numeric(df["area"], errors="coerce")
    invalid_area = (
        df["area"].isna() | ~np.isfinite(df["area"]) | (df["area"] <= 0)
    )

    df["published_at"] = pd.to_datetime(
        df["published_at"], format="ISO8601", errors="coerce"
    )
    invalid_date = df["published_at"].isna()
    invalid_required = df[REQUIRED_COLUMNS].isna().any(axis=1)
    invalid_rows = invalid_area | invalid_date | invalid_required
    df = df.loc[~invalid_rows].copy()

    report = {
        "original_rows": original_count,
        "invalid_required": int(invalid_required.sum()),
        "invalid_area": int(invalid_area.sum()),
        "invalid_date": int(invalid_date.sum()),
        "invalid_price": int(invalid_price.sum()),
        "removed_rows": int(invalid_rows.sum()),
        "cleaned_rows": len(df),
        "missing_price_after_cleaning": int(df["price"].isna().sum()),
        "missing_district_after_cleaning": int(df["district_name"].isna().sum()),
    }
    return df, report
