# -*- coding: utf-8 -*-
"""
Auditing script for the 3 processed datasets:
- properties_50000.csv
- properties_200000.csv
- properties_500000.csv

Computes all statistics directly from raw CSV files and compares with results/ JSONs.
Generates:
- results/validation/data_validation_50000.json
- results/validation/data_validation_200000.json
- results/validation/data_validation_500000.json
- results/validation/cross_validation_report.json
- results/validation/dataset_nesting_audit.json
"""

import os
import sys
import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.data_quality import (
    compute_duplicate_stats,
    compute_numeric_stats,
    compute_grouped_outliers,
    compute_column_summary,
    compute_categorical_distributions,
)
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
VALIDATION_DIR = RESULTS_DIR / "validation"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    50000: PROCESSED_DIR / "properties_50000.csv",
    200000: PROCESSED_DIR / "properties_200000.csv",
    500000: PROCESSED_DIR / "properties_500000.csv",
}

EXPECTED_COLUMNS = [
    "id", "name", "property_type_name", "province_name", "district_name",
    "ward_name", "price", "area", "published_at"
]

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def compute_percentiles(series: pd.Series):
    valid = pd.to_numeric(series, errors="coerce").dropna()
    if len(valid) == 0:
        return {}
    p_values = [1, 5, 25, 50, 75, 95, 99]
    res = {f"p{p}": float(np.percentile(valid, p)) for p in p_values}
    res["min"] = float(valid.min())
    res["max"] = float(valid.max())
    res["mean"] = float(valid.mean())
    res["std"] = float(valid.std())
    res["median"] = float(valid.median())
    res["count"] = int(len(valid))
    return res

def audit_single_dataset(scale: int, csv_path: Path):
    print(f"\n==========================================")
    print(f"Auditing Dataset Scale: {scale} rows ({csv_path.name})")
    print(f"==========================================")

    file_size = os.path.getsize(csv_path)
    file_sha256 = sha256_file(csv_path)

    # 1. Read CSV
    df = pd.read_csv(csv_path, dtype={"id": np.int64}, low_memory=False)
    actual_rows, actual_cols = df.shape
    columns = list(df.columns)
    columns_match = (columns == EXPECTED_COLUMNS)

    # 2. ID integrity
    min_id = int(df["id"].min())
    max_id = int(df["id"].max())
    distinct_ids = int(df["id"].nunique())
    is_id_unique = (distinct_ids == actual_rows)
    is_id_contiguous = (min_id == 1 and max_id == actual_rows and is_id_unique)

    # 3. Missing values
    null_counts = {col: int(df[col].isna().sum()) for col in columns}
    null_percentages = {col: round(null_counts[col] / actual_rows * 100, 4) for col in columns}

    # 4. Invalid price and area
    invalid_area = int(((df["area"].isna()) | (df["area"] <= 0)).sum())
    invalid_price = int(((df["price"].notna()) & (df["price"] <= 0)).sum())

    # 5. Published date parsing
    parsed_dates = pd.to_datetime(df["published_at"], errors="coerce")
    invalid_dates = int(parsed_dates.isna().sum())

    # Text fields trimming check
    whitespace_issues = {}
    for text_col in ["name", "property_type_name", "province_name", "district_name", "ward_name"]:
        s = df[text_col].dropna().astype(str)
        leading_trailing_ws = int((s != s.str.strip()).sum())
        whitespace_issues[text_col] = leading_trailing_ws

    # 6. Duplicates (Comprehensive Quality Library Analysis)
    duplicate_stats = compute_duplicate_stats(df, sample_limit=10)

    # 7. Numeric Stats & Outliers
    numeric_stats = {
        "price": compute_numeric_stats(df["price"], "price"),
        "area": compute_numeric_stats(df["area"], "area"),
        "price_per_m2": compute_numeric_stats(df["price"] / df["area"], "price_per_m2"),
    }

    # 8. Grouped outliers
    grouped_outliers = {
        "price_by_property_type": compute_grouped_outliers(df, "price", "property_type_name"),
        "area_by_property_type": compute_grouped_outliers(df, "area", "property_type_name"),
    }

    # 9. Categorical distributions
    cat_distributions = compute_categorical_distributions(df)

    audit_result = {
        "scale": scale,
        "filename": csv_path.name,
        "file_size_bytes": file_size,
        "sha256": file_sha256,
        "shape": {"rows": actual_rows, "columns": actual_cols},
        "columns": columns,
        "columns_order_correct": columns_match,
        "id_integrity": {
            "min_id": min_id,
            "max_id": max_id,
            "distinct_ids": distinct_ids,
            "is_unique": is_id_unique,
            "is_contiguous_1_to_n": is_id_contiguous
        },
        "missing_values": {
            "counts": null_counts,
            "percentages": null_percentages
        },
        "data_hygiene": {
            "invalid_area_le_zero_or_nan": invalid_area,
            "invalid_price_le_zero": invalid_price,
            "invalid_dates": invalid_dates,
            "whitespace_issues": whitespace_issues
        },
        "duplicates": duplicate_stats,
        "numeric_stats": numeric_stats,
        "grouped_outliers": grouped_outliers,
        "categorical_distributions": cat_distributions
    }

    out_json = VALIDATION_DIR / f"data_validation_{scale}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(audit_result, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved validation results to: {out_json}")

    return df, audit_result


def audit_subset_nesting(dfs):
    print("\n==========================================")
    print("Auditing Subset Nesting (50K in 200K in 500K)")
    print("==========================================")
    df_50 = dfs[50000]
    df_200 = dfs[200000]
    df_500 = dfs[500000]

    # Check exact prefix matching
    prefix_50_in_200 = df_200.iloc[:50000].equals(df_50)
    prefix_200_in_500 = df_500.iloc[:200000].equals(df_200)

    print(f"50K is exact prefix of 200K: {prefix_50_in_200}")
    print(f"200K is exact prefix of 500K: {prefix_200_in_500}")

    nesting_result = {
        "d50k_is_prefix_of_d200k": bool(prefix_50_in_200),
        "d200k_is_prefix_of_d500k": bool(prefix_200_in_500),
        "d50k_rows": len(df_50),
        "d200k_rows": len(df_200),
        "d500k_rows": len(df_500)
    }

    out_nesting = VALIDATION_DIR / "dataset_nesting_audit.json"
    with open(out_nesting, "w", encoding="utf-8") as f:
        json.dump(nesting_result, f, indent=2)
    print(f"[+] Saved nesting audit to: {out_nesting}")
    return nesting_result


def compare_with_existing_reports(audits):
    print("\n==========================================")
    print("Comparing Audit Results Against Existing JSONs in results/")
    print("==========================================")
    discrepancies = []

    for scale in [50000, 200000, 500000]:
        q_path = RESULTS_DIR / "quality" / f"data_quality_report_{scale}.json"
        if not q_path.is_file():
            continue
        with open(q_path, "r", encoding="utf-8") as f:
            q_data = json.load(f)

        # 1. Missing values
        for col, col_info in q_data.get("column_summary", {}).items():
            expected_missing = col_info.get("missing_count")
            actual_missing = audits[scale]["missing_values"]["counts"].get(col)
            if actual_missing != expected_missing:
                discrepancies.append(f"{scale} missing {col}: actual={actual_missing}, report={expected_missing}")

        # 2. Suspected duplicates
        expected_suspected = q_data.get("duplicate_analysis", {}).get("suspected_duplicates")
        actual_suspected = audits[scale]["duplicates"]["suspected_duplicates"]
        if expected_suspected is not None and expected_suspected != actual_suspected:
            discrepancies.append(f"{scale} suspected duplicates: actual={actual_suspected}, report={expected_suspected}")
        else:
            print(f"  [MATCH] {scale} suspected duplicates: {actual_suspected}")

        # 3. Exact duplicates excluding ID
        expected_exact = q_data.get("duplicate_analysis", {}).get("exact_duplicates_excl_id")
        actual_exact = audits[scale]["duplicates"]["exact_duplicates_excl_id"]
        if expected_exact is not None and expected_exact != actual_exact:
            discrepancies.append(f"{scale} exact duplicates excl id: actual={actual_exact}, report={expected_exact}")
        else:
            print(f"  [MATCH] {scale} exact duplicates excl id: {actual_exact}")

        # 4. Outliers
        expected_p_out = q_data.get("numeric_stats", {}).get("price", {}).get("outlier_count_total")
        actual_p_out = audits[scale]["numeric_stats"]["price"]["outlier_count_total"]
        if expected_p_out is not None and expected_p_out != actual_p_out:
            discrepancies.append(f"{scale} price outliers: actual={actual_p_out}, report={expected_p_out}")
        else:
            print(f"  [MATCH] {scale} price outliers: {actual_p_out}")

        expected_a_out = q_data.get("numeric_stats", {}).get("area", {}).get("outlier_count_total")
        actual_a_out = audits[scale]["numeric_stats"]["area"]["outlier_count_total"]
        if expected_a_out is not None and expected_a_out != actual_a_out:
            discrepancies.append(f"{scale} area outliers: actual={actual_a_out}, report={expected_a_out}")
        else:
            print(f"  [MATCH] {scale} area outliers: {actual_a_out}")

    print(f"\nDiscrepancies found across all 3 scales: {len(discrepancies)}")
    for d in discrepancies:
        print(f"  [DISCREPANCY] {d}")

    comparison_report = {
        "discrepancies_count": len(discrepancies),
        "discrepancies": discrepancies,
        "is_100_percent_consistent": (len(discrepancies) == 0)
    }
    with open(VALIDATION_DIR / "cross_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(comparison_report, f, indent=2)
    print(f"[+] Saved cross validation report to: {VALIDATION_DIR / 'cross_validation_report.json'}")


if __name__ == "__main__":
    dfs = {}
    audits = {}
    for scale, path in DATASETS.items():
        df, audit_res = audit_single_dataset(scale, path)
        dfs[scale] = df
        audits[scale] = audit_res

    audit_subset_nesting(dfs)
    compare_with_existing_reports(audits)
    print("\nAuditing complete!")
