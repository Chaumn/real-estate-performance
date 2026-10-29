
from pathlib import Path

import pandas as pd
from datasets import load_dataset


# Cấu hình
DATASET_NAME = "Phuscca/vietnam-real-estates"
SAMPLE_SIZE = 5000

RAW_DIR = Path("data/raw")
RESULTS_DIR = Path("results")

RAW_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("Dang ket noi Hugging Face...")

    dataset = load_dataset(
        DATASET_NAME,
        split="train",
        streaming=True
    )

    # Chỉ lấy dữ liệu mẫu để khảo sát
    df = pd.DataFrame(list(dataset.take(SAMPLE_SIZE)))

    if df.empty:
        raise ValueError("Khong lay duoc du lieu!")

    print(f"\nSo ban ghi: {len(df)}")
    print(f"So cot: {len(df.columns)}")

    print("\nDanh sach cot:")
    print(df.dtypes.to_string())

    print("\n5 ban ghi dau:")
    cols = [
        "name", "province_name", "district_name",
        "price", "area", "published_at"
    ]
    print(df[cols].head().to_string(index=False))

    # Thống kê dữ liệu thiếu
    profile = pd.DataFrame({
        "column": df.columns,
        "dtype": df.dtypes.astype(str).values,
        "missing_count": df.isna().sum().values,
        "missing_percent": (
            df.isna().mean() * 100
        ).round(2).values
    })

    print("\nThong ke gia tri thieu:")
    print(profile.to_string(index=False))

    print("\nSo ban ghi trung hoan toan:",
          df.duplicated().sum())

    # Lưu kết quả
    df.to_csv(
        RAW_DIR / "sample_5000.csv",
        index=False,
        encoding="utf-8-sig"
    )

    profile.to_csv(
        RESULTS_DIR / "data_profile_5000.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\nDa luu du lieu va bao cao!")


if __name__ == "__main__":
    main()
