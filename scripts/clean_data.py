
from pathlib import Path

import numpy as np
import pandas as pd


INPUT_PATH = Path("data/raw/sample_5000.csv")
OUTPUT_PATH = Path("data/processed/cleaned_5000.csv")
REPORT_PATH = Path("results/cleaning_report_5000.csv")

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


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Khong tim thay: {INPUT_PATH}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 1. Doc du lieu
    raw = pd.read_csv(INPUT_PATH)
    missing_cols = set(COLUMNS) - set(raw.columns)

    if missing_cols:
        raise ValueError(f"Thieu cot: {missing_cols}")

    df = raw[COLUMNS].copy()
    original_count = len(df)

    # ID theo thu tu dong nguon, tao truoc khi loc
    df.insert(0, "id", range(1, original_count + 1))

    # 2. Chuan hoa chuoi
    for col in TEXT_COLUMNS:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace("", pd.NA)

    # 3. Chuan hoa gia
    df["price"] = pd.to_numeric(
        df["price"], errors="coerce"
    )

    invalid_price = (
        df["price"].notna()
        & (
            ~np.isfinite(df["price"])
            | (df["price"] <= 0)
        )
    )

    df.loc[invalid_price, "price"] = np.nan

    # 4. Chuan hoa dien tich
    df["area"] = pd.to_numeric(
        df["area"], errors="coerce"
    )

    invalid_area = (
        ~np.isfinite(df["area"])
        | (df["area"] <= 0)
    )

    # 5. Chuyen ngay dang thanh datetime
    df["published_at"] = pd.to_datetime(
    df["published_at"],
    format="ISO8601",
    errors="coerce"
    )

    invalid_date = df["published_at"].isna()

    # 6. Kiem tra cac truong bat buoc
    required_columns = [
        "name",
        "property_type_name",
        "province_name",
    ]

    invalid_required = (
        df[required_columns].isna().any(axis=1)
    )

    # 7. Loai bo ban ghi khong hop le
    invalid_rows = (
        invalid_area
        | invalid_date
        | invalid_required
    )

    df = df.loc[~invalid_rows].copy()

    # 8. Kiem tra ket qua
    assert df["id"].is_unique
    assert df["area"].gt(0).all()
    assert df["published_at"].notna().all()

    # 9. Luu du lieu
    df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d %H:%M:%S.%f"
    )

    # 10. Bao cao lam sach
    report = {
        "original_rows": original_count,
        "invalid_required": int(invalid_required.sum()),
        "invalid_area": int(invalid_area.sum()),
        "invalid_date": int(invalid_date.sum()),
        "invalid_price": int(invalid_price.sum()),
        "removed_rows": int(invalid_rows.sum()),
        "cleaned_rows": len(df),
        "missing_price_after_cleaning": int(
            df["price"].isna().sum()
        ),
        "missing_district_after_cleaning": int(
            df["district_name"].isna().sum()
        ),
    }

    pd.DataFrame([report]).to_csv(
        REPORT_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n=== KET QUA LAM SACH ===")
    for key, value in report.items():
        print(f"{key}: {value}")

    print("\n5 ban ghi sau khi xu ly:")
    print(df.head().to_string(index=False))

    print("\nHoan thanh!")
    print(f"Data: {OUTPUT_PATH}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
