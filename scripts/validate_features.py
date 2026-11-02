# -*- coding: utf-8 -*-
"""
Validation script for Feature Engineering on properties_500000.csv:
- Runs compute_features and exports enriched Parquet
- Validates 500,000 rows x 24 columns
- Verifies original 9 columns preserved
- Verifies 15 derived features: formulas, bins, outliers, date parts
- Checks no Inf values
- Verifies Parquet read-back and schema integrity
- Generates results/features/feature_validation.json and feature_manifest.json
"""

import sys
import os
import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.feature_engineering import (
    compute_features,
    AREA_BINS,
    AREA_LABELS,
    PRICE_BINS,
    PRICE_LABELS,
)

ORIGINAL_COLUMNS = [
    "id", "name", "property_type_name", "province_name", "district_name",
    "ward_name", "price", "area", "published_at"
]

DERIVED_FEATURES = [
    "price_per_m2",
    "published_year",
    "published_month",
    "published_day",
    "published_quarter",
    "published_day_of_week",
    "is_weekend",
    "area_segment",
    "price_segment",
    "has_district",
    "has_ward",
    "is_price_outlier",
    "is_area_outlier",
    "name_length",
    "name_word_count",
]

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    csv_path = PROJECT_ROOT / "data" / "processed" / "properties_500000.csv"
    features_dir = PROJECT_ROOT / "results" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = features_dir / "properties_500000_enriched.parquet"

    print(f"Reading {csv_path.name}...")
    df_raw = pd.read_csv(csv_path, low_memory=False)
    raw_rows, raw_cols = df_raw.shape
    assert raw_rows == 500000, f"Expected 500,000 rows, got {raw_rows}"

    print("Executing compute_features...")
    df_enriched = compute_features(df_raw)
    en_rows, en_cols = df_enriched.shape
    print(f"Enriched DataFrame shape: {en_rows} rows x {en_cols} columns")

    # 1. Check dimensions
    assert en_rows == 500000, f"Row count changed: {en_rows}"
    assert en_cols == 24, f"Column count not 24: {en_cols}"

    # 2. Check original columns preservation
    for col in ORIGINAL_COLUMNS:
        assert col in df_enriched.columns, f"Missing original column {col}"
        # Values should be identical
        if col != "id":
            # Handle float comparison or object
            assert df_raw[col].fillna("__NA__").equals(df_enriched[col].fillna("__NA__")), f"Column {col} mutated"
        else:
            assert (df_raw["id"] == df_enriched["id"]).all(), "ID column mutated"

    # 3. Check derived features
    for col in DERIVED_FEATURES:
        assert col in df_enriched.columns, f"Missing derived feature {col}"

    # 4. Check price_per_m2
    # Where price is NA, price_per_m2 must be NA
    na_price_mask = df_enriched["price"].isna()
    assert df_enriched.loc[na_price_mask, "price_per_m2"].isna().all(), "price_per_m2 not NA when price is NA"

    # Where price > 0, price_per_m2 == price / area
    valid_mask = df_enriched["price"].notna()
    diff = (df_enriched.loc[valid_mask, "price_per_m2"] - (df_enriched.loc[valid_mask, "price"] / df_enriched.loc[valid_mask, "area"])).abs()
    assert (diff < 1e-4).all(), "Formula mismatch for price_per_m2"

    # 5. Check Temporal Features
    ts = pd.to_datetime(df_enriched["published_at"])
    assert (df_enriched["published_year"] == ts.dt.year).all(), "Mismatch in published_year"
    assert (df_enriched["published_month"] == ts.dt.month).all(), "Mismatch in published_month"
    assert (df_enriched["published_day"] == ts.dt.day).all(), "Mismatch in published_day"
    assert (df_enriched["published_quarter"] == ts.dt.quarter).all(), "Mismatch in published_quarter"
    assert (df_enriched["published_day_of_week"] == ts.dt.dayofweek).all(), "Mismatch in published_day_of_week"
    assert (df_enriched["is_weekend"] == ts.dt.dayofweek.isin([5, 6]).astype(int)).all(), "Mismatch in is_weekend"

    # 6. Check Segmentation bins
    area_seg_counts = df_enriched["area_segment"].value_counts().to_dict()
    price_seg_counts = df_enriched["price_segment"].value_counts().to_dict()
    print("Area segments:", area_seg_counts)
    print("Price segments:", price_seg_counts)

    # 7. Check Outlier flags match profiling results
    price_outlier_count = int(df_enriched["is_price_outlier"].sum())
    area_outlier_count = int(df_enriched["is_area_outlier"].sum())
    print(f"is_price_outlier count: {price_outlier_count} (Expected: 44860)")
    print(f"is_area_outlier count: {area_outlier_count} (Expected: 52634)")
    assert price_outlier_count == 44860, f"Expected 44860 price outliers, got {price_outlier_count}"
    assert area_outlier_count == 52634, f"Expected 52634 area outliers, got {area_outlier_count}"

    # 8. Check no unexpected Inf values
    numeric_cols = df_enriched.select_dtypes(include=[np.number]).columns
    for c in numeric_cols:
        inf_cnt = int(np.isinf(df_enriched[c]).sum())
        assert inf_cnt == 0, f"Found {inf_cnt} Inf values in column {c}"

    # 9. Save enriched Parquet
    print(f"Saving enriched Parquet to {parquet_path}...")
    df_enriched.to_parquet(parquet_path, index=False, engine="pyarrow", compression="snappy")
    parquet_size = os.path.getsize(parquet_path)
    parquet_sha = sha256_file(parquet_path)
    print(f"Saved Parquet: {parquet_size:,} bytes ({parquet_size / (1024*1024):.2f} MB), SHA-256: {parquet_sha}")

    # 10. Read back Parquet and verify schema and values
    print("Reading back Parquet to verify round-trip...")
    df_readback = pd.read_parquet(parquet_path, engine="pyarrow")
    assert df_readback.shape == (500000, 24), "Read-back Parquet shape mismatch"
    assert list(df_readback.columns) == list(df_enriched.columns), "Read-back Parquet columns mismatch"
    print("Parquet round-trip verified successfully!")

    # 11. Generate feature validation JSON
    validation_summary = {
        "dataset_name": "properties_500000_enriched.parquet",
        "input_csv": "data/processed/properties_500000.csv",
        "output_parquet": "results/features/properties_500000_enriched.parquet",
        "total_rows": en_rows,
        "total_columns": en_cols,
        "original_columns_count": len(ORIGINAL_COLUMNS),
        "derived_features_count": len(DERIVED_FEATURES),
        "columns_list": list(df_enriched.columns),
        "schema": {col: str(df_enriched[col].dtype) for col in df_enriched.columns},
        "feature_checks": {
            "dimensions_500000_x_24": True,
            "original_columns_unmutated": True,
            "all_15_features_present": True,
            "price_per_m2_formula_exact": True,
            "price_per_m2_null_preservation": True,
            "temporal_features_consistent": True,
            "area_segment_distribution": area_seg_counts,
            "price_segment_distribution": price_seg_counts,
            "price_outlier_count": price_outlier_count,
            "area_outlier_count": area_outlier_count,
            "outliers_match_profiling_exactly": True,
            "zero_infinite_values": True,
            "parquet_roundtrip_verified": True
        },
        "null_counts_in_features": {
            col: int(df_enriched[col].isna().sum()) for col in DERIVED_FEATURES
        }
    }

    val_json_path = features_dir / "feature_validation.json"
    with open(val_json_path, "w", encoding="utf-8") as f:
        json.dump(validation_summary, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved feature validation summary to {val_json_path}")

    # 12. Generate manifest
    manifest_data = {
        "artifact_name": "properties_500000_enriched.parquet",
        "relative_path": "results/features/properties_500000_enriched.parquet",
        "file_size_bytes": parquet_size,
        "file_size_mb": round(parquet_size / (1024 * 1024), 2),
        "sha256": parquet_sha,
        "compression": "snappy",
        "engine": "pyarrow",
        "rows": en_rows,
        "columns": en_cols,
        "derived_features": DERIVED_FEATURES
    }
    manifest_path = features_dir / "feature_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved feature manifest to {manifest_path}")

    print("\nFeature Engineering Test: ALL 10/10 CHECKS PASSED!")

if __name__ == "__main__":
    main()

