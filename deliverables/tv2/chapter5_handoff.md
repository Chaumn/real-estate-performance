# Bàn giao Chương 5 — kết quả lịch sử

## 5.1 Môi trường thực nghiệm

Metadata lịch sử ghi PostgreSQL 18.3. Thông tin CPU và logical cores giữa các manifest chưa nhất quán; không suy ra cấu hình máy từ thời gian đo. Xem evidence/environment_historical.json.

## 5.2 Vận hành hệ thống

Bộ dữ liệu gồm ba quy mô 50K/200K/500K. Gói có 600 plan lịch sử, 30 trường hợp × 20 lượt. Không có bằng chứng độc lập về 90 warm-up, bất biến database hoặc equivalence đầy đủ; không xem đây là nhật ký vận hành mới.

## 5.3 Kết quả Q1–Q4

Median và IQR được tính lại từ Execution Time của raw JSON; Planning Time không được cộng vào Execution Time. Bảng benchmark_summary là nguồn chung cho dashboard và hình thời gian.

## 5.4 So sánh theo quy mô

FIG03 mô tả quan hệ thời gian với số bản ghi trong cùng bộ evidence lịch sử. Ba tập có quan hệ prefix; không phải ba mẫu độc lập. Không ngoại suy sang quy mô hoặc phần cứng khác.

## 5.5 Phân tích nguyên nhân

Q3 cần so A/B và C/D để xem rewriting, A/C và B/D để xem index. A/D kết hợp hai tác động. Q4 là đối chứng: speedup dưới 1 nghĩa là indexed chậm hơn. FIG06 đếm node scan thực tế, không phải số truy vấn; một plan có thể có nhiều node. Plan hỗ trợ giải thích cơ chế nhưng không tự chứng minh quan hệ nhân quả.

## 5.6 Hạn chế thực nghiệm

Trạng thái HISTORICAL. Revision nguồn trong build report là null. Chưa xác minh môi trường, tải nền, cache, autovacuum, fingerprint database hoặc equivalence tại thời điểm đo. Dung lượng index lấy từ summary lịch sử, không suy ra từ EXPLAIN. FIG08 lấy từ build report, không phải lần đo database mới. Chưa có benchmark mới được nghiệm thu.

## Danh mục hình

- Hình 1: [So sánh baseline và tối ưu](figures/FIG01.png), [SVG](figures/FIG01.svg). Nguồn: `tables/benchmark_summary.csv`. Trạng thái HISTORICAL. Median của 20 lượt; riêng FIG07 dùng index_bytes lịch sử.
- Hình 2: [Speedup theo quy mô](figures/FIG02.png), [SVG](figures/FIG02.svg). Nguồn: `tables/benchmark_summary.csv`. Trạng thái HISTORICAL. Speedup = median baseline / median cấu hình.
- Hình 3: [Khả năng mở rộng](figures/FIG03.png), [SVG](figures/FIG03.svg). Nguồn: `tables/benchmark_summary.csv`. Trạng thái HISTORICAL. Median của 20 lượt; riêng FIG07 dùng index_bytes lịch sử.
- Hình 4: [Q3: Query Rewriting và Index](figures/FIG04.png), [SVG](figures/FIG04.svg). Nguồn: `tables/benchmark_summary.csv`. Trạng thái HISTORICAL. Median của 20 lượt; riêng FIG07 dùng index_bytes lịch sử.
- Hình 5: [Q4: trường hợp đối chứng](figures/FIG05.png), [SVG](figures/FIG05.svg). Nguồn: `tables/benchmark_summary.csv`. Trạng thái HISTORICAL. Median của 20 lượt; riêng FIG07 dùng index_bytes lịch sử.
- Hình 6: [Scan type xuất hiện trong execution plans](figures/FIG06.png), [SVG](figures/FIG06.svg). Nguồn: `evidence/benchmark_raw_plans.zip`. Trạng thái HISTORICAL. Tần suất node scan.
- Hình 7: [Dung lượng index bổ sung](figures/FIG07.png), [SVG](figures/FIG07.svg). Nguồn: `tables/benchmark_summary.csv`. Trạng thái HISTORICAL. Median của 20 lượt; riêng FIG07 dùng index_bytes lịch sử.
- Hình 8: [NULL trong các dataset](figures/FIG08.png), [SVG](figures/FIG08.svg). Nguồn: `evidence/build_report.json`. Trạng thái HISTORICAL. NULL / số bản ghi × 100.

## Danh mục bảng

- Bảng 1: [benchmark_summary](tables/benchmark_summary.csv). Đơn vị và nguồn tại bản Markdown tương ứng; kết quả benchmark là HISTORICAL.
- Bảng 2: [execution_statistics](tables/execution_statistics.csv). Đơn vị và nguồn tại bản Markdown tương ứng; kết quả benchmark là HISTORICAL.
- Bảng 3: [index_analysis](tables/index_analysis.csv). Đơn vị và nguồn tại bản Markdown tương ứng; kết quả benchmark là HISTORICAL.
- Bảng 4: [q3_factorial_analysis](tables/q3_factorial_analysis.csv). Đơn vị và nguồn tại bản Markdown tương ứng; kết quả benchmark là HISTORICAL.
- Bảng 5: [query_comparison](tables/query_comparison.csv). Đơn vị và nguồn tại bản Markdown tương ứng; kết quả benchmark là HISTORICAL.
- Bảng 6: [scaling_analysis](tables/scaling_analysis.csv). Đơn vị và nguồn tại bản Markdown tương ứng; kết quả benchmark là HISTORICAL.
