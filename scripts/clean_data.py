
from pathlib import Path

import pandas as pd

if __package__:
    from .cleaning import clean_dataframe
else:
    from cleaning import clean_dataframe


INPUT_PATH = Path("data/raw/sample_5000.csv")
OUTPUT_PATH = Path("data/processed/cleaned_5000.csv")
REPORT_PATH = Path("results/cleaning_report_5000.csv")

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Khong tim thay: {INPUT_PATH}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 1. Doc du lieu
    raw = pd.read_csv(INPUT_PATH)
    # ID theo thu tu dong nguon, tao truoc khi loc
    source_ids = pd.Series(range(1, len(raw) + 1), index=raw.index)
    df, report = clean_dataframe(raw)
    df.insert(0, "id", source_ids.loc[df.index])

    # 2. Kiem tra ket qua
    assert df["id"].is_unique
    assert df["area"].gt(0).all()
    assert df["published_at"].notna().all()

    # 3. Luu du lieu
    df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d %H:%M:%S.%f"
    )

    # 4. Bao cao lam sach
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
