"""Unit tests for the Exploratory Data Analysis (EDA) module."""

from pathlib import Path
import pandas as pd
import pytest

from scripts.run_eda import (
    generate_all_eda_charts,
    plot_price_distribution,
    plot_area_distribution,
    plot_property_type_count,
    plot_province_distribution,
    plot_monthly_listings_trend,
    plot_price_vs_area_scatter,
    plot_price_by_property_type_boxplot,
    plot_price_per_m2_by_province,
    plot_numeric_correlation_heatmap,
    plot_missing_values_bar,
)


@pytest.fixture
def mock_eda_df():
    data = []
    types = ["Nhà riêng", "Căn hộ chung cư", "Đất", "Biệt thự/Nhà liền kề", "Shophouse"]
    provinces = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Bình Dương", "Đồng Nai"]
    for i in range(150):
        data.append({
            "id": i + 1,
            "name": f"Bất động sản số {i+1}",
            "property_type_name": types[i % len(types)],
            "province_name": provinces[i % len(provinces)],
            "district_name": f"Quận {i % 10}" if i % 5 != 0 else None,
            "ward_name": f"Phường {i % 15}" if i % 4 != 0 else None,
            "price": float((i + 1) * 100_000_000) if i % 7 != 0 else None,
            "area": float(30.0 + (i % 80)),
            "published_at": f"2025-0{(i % 9) + 1:02d}-15 10:00:00.000000",
        })
    return pd.DataFrame(data)


def test_generate_all_eda_charts(mock_eda_df, tmp_path):
    output_dir = tmp_path / "eda_test_out"
    generated = generate_all_eda_charts(mock_eda_df, output_dir)

    assert len(generated) == 10
    for img_path in generated:
        assert img_path.exists()
        assert img_path.stat().st_size > 1000  # non-trivial PNG size


def test_individual_plots_with_edge_empty_prices(tmp_path):
    # Test handling where some prices are NaN
    df = pd.DataFrame({
        "price": [None, None, 1000000.0],
        "area": [50.0, 60.0, 70.0],
        "property_type_name": ["Nhà", "Nhà", "Nhà"],
        "province_name": ["Hà Nội", "Hà Nội", "Hà Nội"],
        "published_at": ["2025-01-01", "2025-01-02", "2025-01-03"],
    })
    p = tmp_path / "test_price.png"
    plot_price_distribution(df, p)
    assert p.exists()

