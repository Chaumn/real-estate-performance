# DANH MỤC HÌNH VẼ VÀ BẢNG BIỂU (FIGURES & TABLES INDEX)
## Đề tài: Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn

Tài liệu này hệ thống hóa toàn bộ danh mục bảng biểu định lượng và hình ảnh trực quan hóa được sử dụng trong bản thảo tiểu luận khoa học. Mọi số liệu và hình ảnh đều được trích xuất trực tiếp từ các thực nghiệm có thể tái lập trong repository.

---

### PHẦN 1: DANH MỤC HÌNH VẼ (FIGURES)

| Số hiệu | Tên hình vẽ (Caption) | Tệp nguồn trong Repository | Chương | Ý nghĩa khoa học và Điểm then chốt |
| :---: | :--- | :--- | :---: | :--- |
| **Hình 3.1** | Tỷ lệ dữ liệu khuyết thiếu trên các thuộc tính bất động sản | `results/eda/missing_values_bar.png` | Chương 3 | Minh họa 100% độ đầy đủ cho 6 trường bắt buộc; tỷ lệ khuyết `ward_name` (9.58%), `price` (7.81%), `district_name` (0.01%). |
| **Hình 3.2** | Phân bố số lượng tin đăng theo loại hình bất động sản | `results/eda/property_type_count.png` | Chương 3 | Phân bố 5 phân khúc: Nhà ở chiếm ưu thế tuyệt đối (46.08%), tiếp theo là Đất (24.12%), Căn hộ (20.82%), Biệt thự (7.32%), Shophouse (1.66%). |
| **Hình 3.3** | Top 10 tỉnh/thành phố có mật độ tin đăng lớn nhất Việt Nam | `results/eda/province_distribution.png` | Chương 3 | Hà Nội chiếm tỷ trọng áp đảo (34.03%), theo sau là TP. Hồ Chí Minh (19.98%), Đà Nẵng (4.69%), Hải Phòng (3.11%). Căn cứ chọn Hải Phòng cho Q1 và Hà Nội cho Q2. |
| **Hình 3.4** | Phân bố giá chào bán bất động sản (Thang đo Logarithmic) | `results/eda/price_distribution.png` | Chương 3 | Phân bố lệch phải cực mạnh (Skewness > 0); trung vị giá đạt 6.5 tỷ VNĐ, khoảng tứ phân vị IQR từ 4.1 tỷ ($Q_1$) đến 14.3 tỷ ($Q_3$). |
| **Hình 3.5** | Phân bố diện tích bất động sản (Thang đo Logarithmic) | `results/eda/area_distribution.png` | Chương 3 | Phân bố diện tích tập trung tại trung vị 68.0 $m^2$, khoảng IQR từ 45.0 $m^2$ đến 110.0 $m^2$. |
| **Hình 3.6** | Phân bố giá chào bán theo từng loại hình bất động sản (Boxplot) | `results/eda/price_by_property_type_boxplot.png` | Chương 3 | Biệt thự có trung vị giá cao nhất (21.5 tỷ), tiếp đến là Shophouse (15.5 tỷ), Nhà riêng (6.8 tỷ), Đất (4.5 tỷ) và Căn hộ (4.2 tỷ). |
| **Hình 3.7** | Đơn giá chào bán trung vị ($Triệu/m^2$) tại các địa phương trọng điểm | `results/eda/price_per_m2_by_province.png` | Chương 3 | Hà Nội và TP.HCM dẫn đầu về đơn giá trung vị (~100 - 120 triệu/$m^2$), phản ánh áp lực tập trung dân cư và giá trị thương mại lõi đô thị. |
| **Hình 3.8** | Mật độ tương quan giá và diện tích bất động sản (Hexbin Plot) | `results/eda/price_vs_area_scatter.png` | Chương 3 | Thể hiện mật độ tích tụ dày đặc tại vùng diện tích 40–100 $m^2$ và giá 3–10 tỷ VNĐ; xác nhận mối tương quan phi tuyến. |
| **Hình 3.9** | Xu hướng số lượng tin đăng bất động sản theo thời gian (Monthly Trend) | `results/eda/monthly_listings_trend.png` | Chương 3 | Khảo sát tính biến thiên theo chu kỳ thời gian từ tháng 01/2023 đến 12/2025; minh chứng tính ổn định của dòng dữ liệu tin đăng. |
| **Hình 3.10** | Ma trận hệ số tương quan phi tuyến Spearman giữa các biến định lượng | `results/eda/numeric_correlation_heatmap.png` | Chương 3 | Tương quan hạng Spearman giữa diện tích và giá đạt $\rho = 0.58$; tương quan giữa giá và đơn giá đạt $\rho = 0.62$. |
| **Hình 4.1** | Thời gian thực thi trung vị theo quy mô dữ liệu của 4 bài toán truy vấn | `results/benchmark/analysis/execution_time_by_scale.png` | Chương 4 | Trực quan hóa tương quan giữa kích thước bảng và thời gian thực thi (ms, log-scale); làm nổi bật sự phân kỳ giữa Seq Scan $O(N)$ và Index Scan $O(1)$. |
| **Hình 4.2** | So sánh hệ số tăng tốc (Speedup Factor) của các phương pháp tối ưu | `results/benchmark/analysis/speedup_comparison.png` | Chương 4 | Biểu đồ cột thể hiện hệ số tăng tốc qua 3 quy mô; Q2 đạt đỉnh 942.37x tại 500K, Q3_D đạt 17.97x, Q1 đạt 4.04x, trong khi Q4 và Q3_C tiệm cận 1.0x. |
| **Hình 4.3** | Chi phí phụ trội lưu trữ (Storage Overhead) của các chỉ mục B-tree | `results/benchmark/analysis/index_storage_overhead.png` | Chương 4 | So sánh dung lượng vật lý (MB) của 4 chỉ mục tại 50K, 200K, 500K; chỉ ra Composite Index chiếm dung lượng lớn nhất (28.53 MB tại 500K). |

---

### PHẦN 2: DANH MỤC BẢNG BIỂU (TABLES)

| Số hiệu | Tên bảng (Caption) | Tệp nguồn trong Repository | Chương | Nội dung tóm tắt |
| :---: | :--- | :--- | :---: | :--- |
| **Bảng 3.1** | Đặc tả cấu trúc lược đồ cơ sở dữ liệu `public.properties` (9 cột) | `sql/schema.sql`, `docs/data_dictionary.md` | Chương 3 | Tên cột, kiểu dữ liệu SQL chuẩn, tính chất Nullable, Ràng buộc kiểm tra tính toàn vẹn (CHECK constraint). |
| **Bảng 3.2** | Kết quả thu thập và làm sạch dòng dữ liệu trên tập 500.000 bản ghi | `results/build_report_500000.json`, `docs/cleaning_review.md` | Chương 3 | Thống kê số dòng nguồn (502,000), số bản ghi bị loại (203), nguyên nhân vi phạm, số bản ghi hợp lệ và thời gian xử lý. |
| **Bảng 3.3** | Thống kê mô tả các biến định lượng trên tập dữ liệu 500.000 bản ghi | `results/quality/data_quality_report_500000.json` | Chương 3 | Số lượng, Min, P1, P5, Q1, Median, Mean, Q3, P95, P99, Max, Độ lệch chuẩn cho diện tích, giá và đơn giá. |
| **Bảng 3.4** | Đặc tả 10 cấu hình thực nghiệm Benchmark PostgreSQL độc lập | `docs/benchmark_handoff.md`, `sql/benchmark/` | Chương 3 | Mã cấu hình (Q1_base, Q1_idx, Q2_base, Q2_idx, Q3_A-D, Q4_base, Q4_idx), câu lệnh SQL, chỉ mục sử dụng và mục tiêu kiểm chứng. |
| **Bảng 4.1** | Tổng hợp kết quả đo đạc Benchmark PostgreSQL qua 3 thang đo dữ liệu | `results/benchmark/benchmark_results.csv` | Chương 4 | 30 hàng số liệu: Quy mô, Cấu hình, Scan Type, Dung lượng Index, Thời gian Median, IQR, Min, Max, Shared Hit Blocks, Speedup. |
| **Bảng 4.2** | So sánh chi tiết hiệu năng và cơ chế thực thi Q1 (Single-column Index) | `results/benchmark/benchmark_results.csv` | Chương 4 | Thời gian thực thi, số block đọc đệm và hệ số tăng tốc của Q1 qua các quy mô 50K, 200K, 500K dòng. |
| **Bảng 4.3** | So sánh chi tiết hiệu năng và cơ chế thực thi Q2 (Composite Index) | `results/benchmark/benchmark_results.csv` | Chương 4 | Phân tích cơ chế Early Termination và triệt tiêu Heapsort; bảng so sánh thời gian và Buffer Shared Hit Blocks (23 vs 12,898). |
| **Bảng 4.4** | Bảng phân rã trực giao $2 \times 2$ hiệu năng Q3 (Sargability & Indexing) | `results/benchmark/benchmark_results.csv` | Chương 4 | So sánh 4 cấu hình A, B, C, D; tốc độ tăng tốc tương đối, chứng minh vai trò quyết định của vị từ dạng sargable. |
| **Bảng 4.5** | Đánh giá đối chứng Q4 (Aggregation Control - Index không cải thiện) | `results/benchmark/benchmark_results.csv` | Chương 4 | So sánh thời gian thực thi giữa Baseline và Indexed; phân tích lý do Planner giữ nguyên Seq Scan + HashAggregate. |
| **Bảng 4.6** | Phân tích chi phí đánh đổi lưu trữ vật lý của các chỉ mục B-tree | `results/benchmark/benchmark_summary.json` | Chương 4 | Dung lượng MB của từng chỉ mục tại 50K, 200K, 500K và tỷ lệ phần trăm so với dung lượng bảng Heap. |
| **Bảng 4.7** | Kết quả đo lường hiệu năng pipeline tiền xử lý (Pandas vs Polars) | `results/processing_benchmark/processing_benchmark.csv` | Chương 4 | Thời gian nạp tệp (CSV vs Parquet), Đỉnh RAM RSS (Peak RAM), Mức tăng RAM ($\Delta$ RAM), và Kỹ thuật Chunking Stream. |
