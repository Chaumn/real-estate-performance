"""
Verification test for report statistics and SQL query consistency.
Directly reads source artifacts and ensures report files are factually accurate.
"""
import json
import re
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "report"
RESULTS_DIR = ROOT / "results"
SQL_DIR = ROOT / "sql" / "benchmark" / "queries"


@pytest.fixture(scope="module")
def source_data():
    with open(RESULTS_DIR / "build_report_500000.json", "r", encoding="utf-8") as f:
        build_rep = json.load(f)
    with open(RESULTS_DIR / "quality" / "data_quality_report_500000.json", "r", encoding="utf-8") as f:
        quality_rep = json.load(f)
    processing_df = pd.read_csv(RESULTS_DIR / "processing_benchmark" / "processing_benchmark.csv")
    benchmark_df = pd.read_csv(RESULTS_DIR / "benchmark" / "benchmark_results.csv")

    with open(SQL_DIR / "q1.sql", "r", encoding="utf-8") as f:
        q1_sql = f.read().strip()
    with open(SQL_DIR / "q2.sql", "r", encoding="utf-8") as f:
        q2_sql = f.read().strip()
    with open(SQL_DIR / "q3_original.sql", "r", encoding="utf-8") as f:
        q3_orig_sql = f.read().strip()
    with open(SQL_DIR / "q3_rewritten.sql", "r", encoding="utf-8") as f:
        q3_rewr_sql = f.read().strip()
    with open(SQL_DIR / "q4.sql", "r", encoding="utf-8") as f:
        q4_sql = f.read().strip()

    return {
        "build": build_rep,
        "quality": quality_rep,
        "processing": processing_df,
        "benchmark": benchmark_df,
        "queries": {
            "q1": q1_sql,
            "q2": q2_sql,
            "q3_orig": q3_orig_sql,
            "q3_rewr": q3_rewr_sql,
            "q4": q4_sql,
        }
    }


def test_missing_values_ground_truth(source_data):
    """Verify ground truth missing values from build & quality reports."""
    build_nulls = source_data["build"]["null_counts"]
    quality_col = source_data["quality"]["column_summary"]

    assert build_nulls["ward_name"] == 72150
    assert quality_col["ward_name"]["missing_count"] == 72150
    assert quality_col["ward_name"]["missing_pct"] == 14.43

    assert build_nulls["district_name"] == 14235
    assert quality_col["district_name"]["missing_count"] == 14235
    assert quality_col["district_name"]["missing_pct"] == 2.85

    assert build_nulls["price"] == 39061
    assert quality_col["price"]["missing_count"] == 39061
    assert quality_col["price"]["missing_pct"] == 7.81


def test_numeric_medians_ground_truth(source_data):
    """Verify ground truth medians for price and area."""
    num_stats = source_data["quality"]["numeric_stats"]
    assert num_stats["price"]["median"] == 7400000000.0  # 7.4 billion VND
    assert num_stats["area"]["median"] == 80.0           # 80 m2


def test_province_distribution_ground_truth(source_data):
    """Verify top provinces distribution in quality report."""
    top_provs = source_data["quality"]["categorical_distributions"]["top_provinces"]
    assert top_provs["Hải Phòng"]["count"] == 10422
    assert top_provs["Hải Phòng"]["pct"] == 2.08
    assert top_provs["Hồ Chí Minh"]["count"] == 186698
    assert top_provs["Hà Nội"]["count"] == 170167


def test_processing_benchmark_ground_truth(source_data):
    """Verify chunked processing delta RSS numbers."""
    df = source_data["processing"]
    scale_500k = df[df["scale"] == 500000]

    chunk_read = scale_500k[scale_500k["operation"] == "Pandas Chunked read_csv (10k)"].iloc[0]
    chunk_agg = scale_500k[scale_500k["operation"] == "Pandas Chunked aggregate (10k)"].iloc[0]

    assert round(chunk_read["delta_ram_mb"], 2) == 19.68
    assert round(chunk_agg["delta_ram_mb"], 2) == 21.09
    # Aggregate delta RAM is above 20 MB!
    assert chunk_agg["delta_ram_mb"] > 20.0


def test_benchmark_index_sizes_ground_truth(source_data):
    """Verify index sizes at scale 500k summing to 46.02 MB."""
    df = source_data["benchmark"]
    scale_500k = df[df["scale"] == 500000]

    q1_idx = scale_500k[scale_500k["config_id"] == "Q1_indexed"]["index_size_mb"].values[0]
    q2_idx = scale_500k[scale_500k["config_id"] == "Q2_indexed"]["index_size_mb"].values[0]
    q3_idx = scale_500k[scale_500k["config_id"] == "Q3_D"]["index_size_mb"].values[0]
    q4_idx = scale_500k[scale_500k["config_id"] == "Q4_indexed"]["index_size_mb"].values[0]

    total_idx_size = q1_idx + q2_idx + q3_idx + q4_idx
    assert round(total_idx_size, 2) == 46.02


def test_sql_queries_ground_truth(source_data):
    """Verify sql query files contain expected canonical elements."""
    q = source_data["queries"]
    assert "province_name = 'Hải Phòng'" in q["q1"]
    assert "SELECT id, name, price, area" in q["q1"]

    assert "ORDER BY price ASC, id ASC" in q["q2"]
    assert "LIMIT 20" in q["q2"]
    assert "price BETWEEN 4100000000 AND 14300000000" in q["q2"]

    assert "published_at::date = DATE '2025-10-15'" in q["q3_orig"]
    assert "published_at >= TIMESTAMP '2025-10-15 00:00:00'" in q["q3_rewr"]
    assert "published_at < TIMESTAMP '2025-10-16 00:00:00'" in q["q3_rewr"]

    assert "GROUP BY property_type_name" in q["q4"]
    assert "ORDER BY total DESC" in q["q4"]


def test_report_markdown_no_stale_statistics():
    """Ensure report markdown files do not contain deprecated or fabricated numbers."""
    md_files = list(REPORT_DIR.glob("*.md"))
    assert len(md_files) > 0

    stale_patterns = [
        (r'15[\.,]541', "Wrong count for Hai Phong (should be 10,422)"),
        (r'47[\.,]904', "Wrong missing count for ward_name (should be 72,150)"),
        (r'9[\.,]58\s*%', "Wrong missing pct for ward_name (should be 14.43%)"),
        (r'53\s*(giá trị|bản ghi|dòng).*(district_name)', "Wrong missing count for district_name (should be 14,235)"),
        (r'0[\.,]01\s*%.*(district_name)', "Wrong missing pct for district_name (should be 2.85%)"),
        (r'6[\.,]50?\s*tỷ', "Wrong median price (should be 7.4 tỷ VNĐ)"),
        (r'68[\.,]0?\s*m[²2]', "Wrong median area (should be 80 m²)"),
        (r'đều dưới 20\s*MB', "Wrong chunked claim (chunked aggregate is 21.09 MB)"),
        (r'SELECT\s+\*\s+FROM\s+(public\.)?properties\s+WHERE\s+province_name', "Simplified Q1 query"),
        (r'SELECT\s+\*\s+FROM\s+(public\.)?properties\s+WHERE\s+published_at', "Simplified Q3 query"),
    ]

    # Audit and validation reports describe the previous errors historically, so exempt them
    exempt_files = {"final_validation.md", "academic_review.md"}

    errors = []
    for f in md_files:
        if f.name in exempt_files:
            continue
        content = f.read_text(encoding="utf-8")
        for pat, desc in stale_patterns:
            matches = re.findall(pat, content, flags=re.IGNORECASE)
            if matches:
                errors.append(f"{f.name}: Found '{pat}' ({desc})")

    if errors:
        pytest.fail(f"Found {len(errors)} stale statistical/query errors in report:\n" + "\n".join(errors))


def test_report_no_stale_checksums():
    """Verify that report markdown files do not contain stale checksums."""
    stale_hashes = [
        "11bc4fe13aafbcbb8be177b94dbba221199a4fe9963f2766dc8257ee7a89849b",
        "84eabf931d8d87d00fef07e60fa0d6a2f8c5b3c59cf6b8f52fe6305a41755106",
        "9ba1afe8ce7edbf6f6df615822be88dd33fca401a4e1564aa6a56e0767e3a89e",
    ]
    exempt_files = {"academic_review.md"}
    errors = []
    for f in REPORT_DIR.glob("*.md"):
        if f.name in exempt_files:
            continue
        content = f.read_text(encoding="utf-8")
        for bad_h in stale_hashes:
            if bad_h in content:
                errors.append(f"{f.name}: Found stale checksum '{bad_h}'")
    assert not errors, f"Stale checksums found:\n" + "\n".join(errors)

