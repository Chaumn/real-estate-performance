"""Exploratory Data Analysis (EDA) module for Real Estate Performance project.

Generates publication-quality figures, descriptive metrics, and insights
across univariate, bivariate, and multivariate relationships.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Visual styling setup
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Segoe UI"]
plt.rcParams["axes.unicode_minus"] = False


def plot_price_distribution(df: pd.DataFrame, output_path: Path) -> None:
    """Plot price distribution (Raw histogram clipped at P99 & Log10 distribution)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    valid_prices = df["price"].dropna()
    p99 = valid_prices.quantile(0.99)
    # Convert to Billion VND (tỷ đồng)
    prices_bil = valid_prices[valid_prices <= p99] / 1e9

    sns.histplot(prices_bil, bins=50, kde=True, ax=axes[0], color="#2b5c8f")
    axes[0].set_title("Phân Bố Giá Bán (< P99: 130 tỷ VNĐ)", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Giá Bán (Tỷ VNĐ)", fontsize=11)
    axes[0].set_ylabel("Số Lượng Tin Đăng", fontsize=11)

    # Log10 scale distribution
    log_prices = np.log10(valid_prices[valid_prices > 0])
    sns.histplot(log_prices, bins=50, kde=True, ax=axes[1], color="#d95f02")
    axes[1].set_title("Phân Bố Giá Bán Theo Log10 Scale", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Log10(Giá VNĐ)", fontsize=11)
    axes[1].set_ylabel("Mật Độ / Tần Suất", fontsize=11)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_area_distribution(df: pd.DataFrame, output_path: Path) -> None:
    """Plot area distribution (Raw histogram clipped at P99 & Log10 distribution)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    valid_areas = df["area"].dropna()
    valid_areas = valid_areas[valid_areas > 0]
    p99 = valid_areas.quantile(0.99)
    areas_clipped = valid_areas[valid_areas <= p99]

    sns.histplot(areas_clipped, bins=50, kde=True, ax=axes[0], color="#2ca02c")
    axes[0].set_title("Phân Bố Diện Tích (< P99: 2,229 m²)", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Diện Tích (m²)", fontsize=11)
    axes[0].set_ylabel("Số Lượng Tin Đăng", fontsize=11)

    log_areas = np.log10(valid_areas)
    sns.histplot(log_areas, bins=50, kde=True, ax=axes[1], color="#9467bd")
    axes[1].set_title("Phân Bố Diện Tích Theo Log10 Scale", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Log10(Diện Tích m²)", fontsize=11)
    axes[1].set_ylabel("Mật Độ / Tần Suất", fontsize=11)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_property_type_count(df: pd.DataFrame, output_path: Path) -> None:
    """Plot bar chart of listing counts by property type."""
    fig, ax = plt.subplots(figsize=(10, 6))

    counts = df["property_type_name"].value_counts().reset_index()
    counts.columns = ["property_type_name", "count"]

    sns.barplot(data=counts, x="count", y="property_type_name", hue="property_type_name", palette="viridis", legend=False, ax=ax)
    ax.set_title("Số Lượng Tin Đăng Theo Loại Bất Động Sản", fontsize=13, fontweight="bold")
    ax.set_xlabel("Số Lượng Bản Ghi", fontsize=11)
    ax.set_ylabel("Loại Bất Động Sản", fontsize=11)

    total = len(df)
    for i, row in counts.iterrows():
        pct = (row["count"] / total) * 100
        ax.text(row["count"] + (total * 0.005), i, f"{row['count']:,} ({pct:.1f}%)", va="center", fontsize=10)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_province_distribution(df: pd.DataFrame, output_path: Path) -> None:
    """Plot top 15 provinces with highest listing volume."""
    fig, ax = plt.subplots(figsize=(11, 7))

    top_provinces = df["province_name"].value_counts().head(15).reset_index()
    top_provinces.columns = ["province_name", "count"]

    sns.barplot(data=top_provinces, x="count", y="province_name", hue="province_name", palette="mako", legend=False, ax=ax)
    ax.set_title("Top 15 Tỉnh/Thành Phố Có Khối Lượng Tin Đăng Lớn Nhất", fontsize=13, fontweight="bold")
    ax.set_xlabel("Số Lượng Tin Đăng", fontsize=11)
    ax.set_ylabel("Tỉnh / Thành Phố", fontsize=11)

    total = len(df)
    for i, row in top_provinces.iterrows():
        pct = (row["count"] / total) * 100
        ax.text(row["count"] + (total * 0.003), i, f"{row['count']:,} ({pct:.1f}%)", va="center", fontsize=9)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_monthly_listings_trend(df: pd.DataFrame, output_path: Path) -> None:
    """Plot monthly trend of listing publications."""
    fig, ax = plt.subplots(figsize=(12, 5))

    ts = pd.to_datetime(df["published_at"], format="ISO8601", errors="coerce")
    monthly = ts.dt.to_period("M").value_counts().sort_index().reset_index()
    monthly.columns = ["month_period", "count"]
    monthly["month_str"] = monthly["month_period"].astype(str)

    # Plot last 24 periods if many
    if len(monthly) > 24:
        monthly = monthly.tail(24)

    sns.lineplot(data=monthly, x="month_str", y="count", marker="o", color="#1f77b4", linewidth=2.5, ax=ax)
    ax.set_title("Xu Hướng Số Lượng Tin Đăng Theo Tháng", fontsize=13, fontweight="bold")
    ax.set_xlabel("Tháng Đăng Tin (YYYY-MM)", fontsize=11)
    ax.set_ylabel("Số Lượng Tin Đăng", fontsize=11)
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_price_vs_area_scatter(df: pd.DataFrame, output_path: Path, sample_size: int = 15000) -> None:
    """Plot price vs area using hexbin with logarithmic scale for dense data."""
    valid = df.dropna(subset=["price", "area"]).copy()
    valid = valid[(valid["price"] > 0) & (valid["area"] > 0)]

    # Clip outliers at P99 for visual clarity
    p99_price = valid["price"].quantile(0.99)
    p99_area = valid["area"].quantile(0.99)
    filtered = valid[(valid["price"] <= p99_price) & (valid["area"] <= p99_area)]

    if len(filtered) > sample_size:
        plot_data = filtered.sample(n=sample_size, random_state=42)
    else:
        plot_data = filtered

    fig, ax = plt.subplots(figsize=(10, 6))
    x = plot_data["area"]
    y = plot_data["price"] / 1e9  # Tỷ đồng

    hb = ax.hexbin(x, y, gridsize=40, cmap="Blues", mincnt=1, bins="log")
    cb = fig.colorbar(hb, ax=ax)
    cb.set_label("Log10(Mật độ tin đăng)")

    # Overlay trend line
    sns.regplot(
        x=x,
        y=y,
        scatter=False,
        ax=ax,
        color="#e41a1c",
        line_kws={"linewidth": 2, "label": "Đường xu hướng hồi quy tuyến tính"},
    )

    ax.set_title("Mối Quan Hệ Giữa Diện Tích và Giá Bán (Mật Độ Hexbin & Hồi Quy)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Diện Tích (m²)", fontsize=11)
    ax.set_ylabel("Giá Bán (Tỷ VNĐ)", fontsize=11)
    ax.legend(loc="upper left")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_price_by_property_type_boxplot(df: pd.DataFrame, output_path: Path) -> None:
    """Plot boxplot of price (Log scale) grouped by property type."""
    valid = df.dropna(subset=["price"]).copy()
    valid = valid[valid["price"] > 0]
    valid["price_bil"] = valid["price"] / 1e9

    # Filter to types with >= 100 rows
    top_types = valid["property_type_name"].value_counts()[lambda x: x >= 100].index
    filtered = valid[valid["property_type_name"].isin(top_types)].copy()

    # Order by median price descending
    order = (
        filtered.groupby("property_type_name")["price_bil"]
        .median()
        .sort_values(ascending=False)
        .index
    )

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.boxplot(
        data=filtered,
        x="property_type_name",
        y="price_bil",
        order=order,
        hue="property_type_name",
        palette="Set2",
        legend=False,
        ax=ax,
        showfliers=False,  # Hide extreme points to focus on IQR boxes
    )
    ax.set_title("Phân Bố Giá Bán Theo Loại Bất Động Sản (Không bao gồm fliers ngoại lệ)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Loại Bất Động Sản", fontsize=11)
    ax.set_ylabel("Giá Bán (Tỷ VNĐ)", fontsize=11)
    plt.xticks(rotation=25, ha="right")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_price_per_m2_by_province(df: pd.DataFrame, output_path: Path) -> None:
    """Plot median price/m² for top 15 provinces."""
    valid = df.dropna(subset=["price", "area"]).copy()
    valid = valid[(valid["price"] > 0) & (valid["area"] > 0)]
    valid["price_per_m2_mil"] = (valid["price"] / valid["area"]) / 1e6  # Triệu VNĐ / m²

    top_provs = valid["province_name"].value_counts().head(15).index
    filtered = valid[valid["province_name"].isin(top_provs)]

    median_m2 = (
        filtered.groupby("province_name")["price_per_m2_mil"]
        .median()
        .reset_index()
        .sort_values(by="price_per_m2_mil", ascending=False)
    )

    fig, ax = plt.subplots(figsize=(11, 7))
    sns.barplot(
        data=median_m2,
        x="price_per_m2_mil",
        y="province_name",
        hue="province_name",
        palette="rocket",
        legend=False,
        ax=ax,
    )
    ax.set_title("Trung Vị Đơn Giá (Triệu VNĐ/m²) Tại Top 15 Tỉnh/Thành Phố", fontsize=13, fontweight="bold")
    ax.set_xlabel("Trung Vị Đơn Giá (Triệu VNĐ / m²)", fontsize=11)
    ax.set_ylabel("Tỉnh / Thành Phố", fontsize=11)

    for i, row in median_m2.reset_index(drop=True).iterrows():
        ax.text(
            row["price_per_m2_mil"] + 1.0,
            i,
            f"{row['price_per_m2_mil']:.1f} tr/m²",
            va="center",
            fontsize=9,
            fontweight="semibold",
        )

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_numeric_correlation_heatmap(df: pd.DataFrame, output_path: Path) -> None:
    """Plot correlation heatmap among numeric features and temporal components."""
    data = pd.DataFrame()
    data["price"] = pd.to_numeric(df["price"], errors="coerce")
    data["area"] = pd.to_numeric(df["area"], errors="coerce")
    valid_mask = data["price"].notna() & data["area"].notna() & (data["area"] > 0) & (data["price"] > 0)
    data["price_per_m2"] = np.nan
    data.loc[valid_mask, "price_per_m2"] = data.loc[valid_mask, "price"] / data.loc[valid_mask, "area"]

    dates = pd.to_datetime(df["published_at"], format="ISO8601", errors="coerce")
    data["published_year"] = dates.dt.year
    data["published_month"] = dates.dt.month
    data["published_day"] = dates.dt.day

    # Compute Spearman rank correlation (robust to extreme values)
    corr = data.corr(method="spearman")

    fig, ax = plt.subplots(figsize=(8, 6))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(
        corr,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title("Ma Trận Tương Quan Thứ Hạng Spearman (Numeric & Temporal Features)", fontsize=12, fontweight="bold")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_missing_values_bar(df: pd.DataFrame, output_path: Path) -> None:
    """Plot bar chart of missing value percentages per column."""
    fig, ax = plt.subplots(figsize=(9, 5))

    missing = (df.isna().mean() * 100).reset_index()
    missing.columns = ["column", "missing_pct"]
    missing = missing.sort_values(by="missing_pct", ascending=False)

    sns.barplot(data=missing, x="missing_pct", y="column", hue="column", palette="crest", legend=False, ax=ax)
    ax.set_title("Tỷ Lệ Dữ Liệu Khuyết Thiếu Theo Từng Cột (%)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Tỷ Lệ Thiếu (%)", fontsize=11)
    ax.set_ylabel("Thuộc Tính", fontsize=11)

    for i, row in missing.reset_index(drop=True).iterrows():
        ax.text(
            row["missing_pct"] + 0.3,
            i,
            f"{row['missing_pct']:.2f}%",
            va="center",
            fontsize=9,
            fontweight="semibold",
        )

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def generate_all_eda_charts(df: pd.DataFrame, output_dir: Path) -> list[Path]:
    """Execute all EDA plot functions and return paths of created figures."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []

    plots = [
        ("price_distribution.png", plot_price_distribution),
        ("area_distribution.png", plot_area_distribution),
        ("property_type_count.png", plot_property_type_count),
        ("province_distribution.png", plot_province_distribution),
        ("monthly_listings_trend.png", plot_monthly_listings_trend),
        ("price_vs_area_scatter.png", plot_price_vs_area_scatter),
        ("price_by_property_type_boxplot.png", plot_price_by_property_type_boxplot),
        ("price_per_m2_by_province.png", plot_price_per_m2_by_province),
        ("numeric_correlation_heatmap.png", plot_numeric_correlation_heatmap),
        ("missing_values_bar.png", plot_missing_values_bar),
    ]

    for fname, func in plots:
        fpath = output_dir / fname
        print(f"  -> Dang sinh bieu do: {fname}...", flush=True)
        func(df, fpath)
        generated.append(fpath)

    return generated


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/properties_500000.csv"),
        help="Duong dan tap du lieu CSV can phan tich",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/eda"),
        help="Thu muc luu tru bieu do PNG",
    )
    args = parser.parse_args(argv)

    if not args.input.exists():
        sys.exit(f"Loi: Khong tim thay file du lieu {args.input}")

    print(f"Dang tai du lieu: {args.input}...", flush=True)
    df = pd.read_csv(args.input)
    print(f"Da nap {len(df):,} dong. Bat dau sinh bo bieu do EDA vao {args.output_dir}...")
    generated = generate_all_eda_charts(df, args.output_dir)
    print(f"Hoan thanh xuat {len(generated)} bieu do EDA tai: {args.output_dir}")


if __name__ == "__main__":
    main()
