"""Feature Engineering module for real estate dataset.

Generates derived business, temporal, spatial, and statistical indicator features
while preserving the strict 9-column schema contract of the benchmark dataset.
Enriched data is exported to separate parquet/csv artifacts.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


AREA_BINS = [0, 30, 60, 100, 200, np.inf]
AREA_LABELS = ["Dưới 30m2", "30-60m2", "60-100m2", "100-200m2", "Trên 200m2"]

PRICE_BINS = [0, 2e9, 5e9, 10e9, 20e9, np.inf]
PRICE_LABELS = ["Dưới 2 tỷ", "2 - 5 tỷ", "5 - 10 tỷ", "10 - 20 tỷ", "Trên 20 tỷ"]


def calculate_iqr_bounds(series: pd.Series) -> tuple[float, float]:
    """Calculate IQR-based lower and upper bounds for outlier detection."""
    valid = pd.to_numeric(series, errors="coerce").dropna()
    if len(valid) == 0:
        return 0.0, 0.0
    q1 = float(valid.quantile(0.25))
    q3 = float(valid.quantile(0.75))
    iqr = q3 - q1
    lower_bound = max(0.0, q1 - 1.5 * iqr)
    upper_bound = q3 + 1.5 * iqr
    return lower_bound, upper_bound


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive features from raw 9-column real estate DataFrame.

    Returns a new DataFrame containing all original columns plus derived features.
    Original DataFrame is NOT mutated.
    """
    enriched = df.copy()

    # 1. Price per square meter (VND/m2)
    numeric_price = pd.to_numeric(enriched["price"], errors="coerce")
    numeric_area = pd.to_numeric(enriched["area"], errors="coerce")
    valid_m2_mask = numeric_price.notna() & (numeric_price > 0) & numeric_area.notna() & (numeric_area > 0)

    enriched["price_per_m2"] = np.nan
    enriched.loc[valid_m2_mask, "price_per_m2"] = (
        numeric_price.loc[valid_m2_mask] / numeric_area.loc[valid_m2_mask]
    )

    # 2. Temporal Features from published_at
    timestamps = pd.to_datetime(enriched["published_at"], errors="coerce")
    enriched["published_year"] = timestamps.dt.year.astype("Int64")
    enriched["published_month"] = timestamps.dt.month.astype("Int64")
    enriched["published_day"] = timestamps.dt.day.astype("Int64")
    enriched["published_quarter"] = timestamps.dt.quarter.astype("Int64")
    enriched["published_day_of_week"] = timestamps.dt.dayofweek.astype("Int64")
    enriched["is_weekend"] = timestamps.dt.dayofweek.isin([5, 6]).astype(int)

    # 3. Discretized Bins (Area and Price)
    enriched["area_segment"] = pd.cut(
        numeric_area,
        bins=AREA_BINS,
        labels=AREA_LABELS,
        right=False,
    ).astype(str)
    enriched["area_segment"] = enriched["area_segment"].replace("nan", "Không xác định")

    # For price, handle NaN explicitly as "Thỏa thuận"
    price_seg = pd.cut(
        numeric_price,
        bins=PRICE_BINS,
        labels=PRICE_LABELS,
        right=False,
    ).astype(str)
    price_seg = price_seg.mask(numeric_price.isna(), "Thỏa thuận")
    enriched["price_segment"] = price_seg.replace("nan", "Thỏa thuận")

    # 4. Location completeness indicators
    enriched["has_district"] = enriched["district_name"].notna().astype(int)
    enriched["has_ward"] = enriched["ward_name"].notna().astype(int)

    # 5. Outlier indicator flags using IQR
    price_low, price_high = calculate_iqr_bounds(numeric_price)
    area_low, area_high = calculate_iqr_bounds(numeric_area)

    enriched["is_price_outlier"] = (
        numeric_price.notna()
        & ((numeric_price < price_low) | (numeric_price > price_high))
    ).astype(int)

    enriched["is_area_outlier"] = (
        numeric_area.notna()
        & ((numeric_area < area_low) | (numeric_area > area_high))
    ).astype(int)

    # 6. Text metadata features
    name_str = enriched["name"].fillna("").astype(str)
    enriched["name_length"] = name_str.str.len()
    enriched["name_word_count"] = name_str.str.split().str.len()

    return enriched


def export_features(
    input_path: Path,
    output_dir: Path = Path("results/features"),
    file_format: str = "parquet",
) -> Path:
    """Read CSV, engineer features, and export to parquet/csv."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Doc tap du lieu goc tu: {input_path}...", flush=True)
    df = pd.read_csv(input_path)

    print(f"Dang sinh cac dac trung moi cho {len(df):,} dong...", flush=True)
    enriched = compute_features(df)

    stem = input_path.stem
    if file_format == "parquet":
        output_file = output_dir / f"{stem}_enriched.parquet"
        enriched.to_parquet(output_file, index=False, engine="pyarrow", compression="snappy")
    else:
        output_file = output_dir / f"{stem}_enriched.csv"
        enriched.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"Xuat thanh cong {len(enriched):,} dong x {len(enriched.columns)} cot!")
    print(f"File xuat: {output_file} ({output_file.stat().st_size / (1024*1024):.2f} MB)")
    return output_file


def summarize_features(enriched: pd.DataFrame) -> dict[str, Any]:
    """Generate statistical summary of engineered features."""
    return {
        "total_rows": len(enriched),
        "total_columns": len(enriched.columns),
        "new_feature_names": [
            col for col in enriched.columns if col not in [
                "id", "name", "property_type_name", "province_name",
                "district_name", "ward_name", "price", "area", "published_at"
            ]
        ],
        "area_segment_distribution": enriched["area_segment"].value_counts().to_dict(),
        "price_segment_distribution": enriched["price_segment"].value_counts().to_dict(),
        "weekend_percentage": round(float(enriched["is_weekend"].mean()) * 100, 2),
        "price_outlier_count": int(enriched["is_price_outlier"].sum()),
        "area_outlier_count": int(enriched["is_area_outlier"].sum()),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/properties_500000.csv"),
        help="Duong dan file CSV du lieu da lam sach",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/features"),
        help="Thu muc xuat ket qua dac trung",
    )
    parser.add_argument(
        "--format",
        choices=["parquet", "csv"],
        default="parquet",
        help="Dinh dang file xuat (parquet mac dinh, toi uu toc do va dung luong)",
    )
    args = parser.parse_args(argv)

    if not args.input.exists():
        sys.exit(f"Loi: Khong tim thay {args.input}")

    out = export_features(args.input, args.output_dir, args.format)
    print(f"Hoan tat Feature Engineering tai: {out}")


if __name__ == "__main__":
    main()

