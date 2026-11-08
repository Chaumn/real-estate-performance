# Danh mục hình FIG01–FIG08

QA được báo cáo trước đây: PASS cho Chrome headless DOM và contact sheet (nhãn tiếng Việt, không thấy clipping), xem evidence/prior_validation.json. Chưa có bằng chứng tái hiện tương tác CDP; CDP interaction: NOT_VERIFIED. Lần này không chạy lại browser, visual QA, PostgreSQL hoặc benchmark.

| Hình | Nội dung | Nguồn | Tạo hình / QA |
|---|---|---|---|
| FIG01 | Baseline và tối ưu | tables/benchmark_summary.csv; median 20 lượt; FIG02 = baseline median / configuration median | PNG 300 DPI + SVG đã tạo, giữ nguyên bytes; contact sheet PASS được báo cáo trước đây |
| FIG02 | Speedup | tables/benchmark_summary.csv; median 20 lượt; FIG02 = baseline median / configuration median | PNG 300 DPI + SVG đã tạo, giữ nguyên bytes; contact sheet PASS được báo cáo trước đây |
| FIG03 | Khả năng mở rộng | tables/benchmark_summary.csv; median 20 lượt; FIG02 = baseline median / configuration median | PNG 300 DPI + SVG đã tạo, giữ nguyên bytes; contact sheet PASS được báo cáo trước đây |
| FIG04 | Q3 factorial | tables/benchmark_summary.csv; median 20 lượt; FIG02 = baseline median / configuration median | PNG 300 DPI + SVG đã tạo, giữ nguyên bytes; contact sheet PASS được báo cáo trước đây |
| FIG05 | Q4 đối chứng | tables/benchmark_summary.csv; median 20 lượt; FIG02 = baseline median / configuration median | PNG 300 DPI + SVG đã tạo, giữ nguyên bytes; contact sheet PASS được báo cáo trước đây |
| FIG06 | Tần suất node scan | evidence/benchmark_raw_plans.zip; đếm node scan, không đếm truy vấn | PNG 300 DPI + SVG đã tạo, giữ nguyên bytes; contact sheet PASS được báo cáo trước đây |
| FIG07 | Dung lượng index | tables/benchmark_summary.csv và evidence/{scale}_validation.json catalog.index_bytes | PNG 300 DPI + SVG đã tạo, giữ nguyên bytes; contact sheet PASS được báo cáo trước đây |
| FIG08 | Tỷ lệ NULL dataset | evidence/build_report.json (dataset quality/build report) | PNG 300 DPI + SVG đã tạo, giữ nguyên bytes; contact sheet PASS được báo cáo trước đây |
