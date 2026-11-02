# DANH MỤC HÌNH VẼ VÀ BẢNG BIỂU (FIGURES & TABLES INDEX)
## Đề tài: Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn

Tài liệu này hệ thống hóa toàn bộ danh mục bảng biểu định lượng và hình ảnh trực quan hóa được sử dụng trong bản thảo tiểu luận khoa học. Mọi số liệu và hình ảnh đều được trích xuất trực tiếp từ các thực nghiệm có thể tái lập trong repository.

---

### PHẦN 1: DANH MỤC HÌNH VẼ (FIGURES)

| Số hiệu | Tên hình vẽ (Caption) | Tệp nguồn trong Repository | Chương | Ý nghĩa khoa học và Điểm then chốt |
| :---: | :--- | :--- | :---: | :--- |
| **Hình 3.1** | Tỷ lệ dữ liệu khuyết thiếu trên các thuộc tính bất động sản | `results/eda/missing_values_bar.png` | Chương 3 | Minh họa độ đầy đủ 100% cho 6 trường bắt buộc; tỷ lệ khuyết `ward_name` (14,43% / 72.150 bản ghi), `price` (7,81% / 39.061 bản ghi), `district_name` (2,85% / 14.235 bản ghi). |
| **Hình 3.2** | Phân bố số lượng tin đăng theo loại hình bất động sản | `results/eda/property_type_count.png` | Chương 3 | Phân bố 5 phân khúc: Nhà riêng chiếm ưu thế (46,08%), tiếp theo là Đất (24,12%), Căn hộ (20,82%), Biệt thự (7,32%), Shophouse (1,66%). |
| **Hình 3.3** | Top các tỉnh/thành phố có mật độ tin đăng lớn nhất Việt Nam | `results/eda/province_distribution.png` | Chương 3 | TP. Hồ Chí Minh (37,34%), Hà Nội (34,03%), Đà Nẵng (5,15%), Bình Dương (4,28%), Khánh Hòa (2,78%), Hải Phòng (2,08% / 10.422 tin). Căn cứ chọn Hải Phòng cho Q1 và Hà Nội cho Q2. |
| **Hình 3.4** | Phân bố giá chào bán bất động sản (Thang đo Logarithmic) | `results/eda/price_distribution.png` | Chương 3 | Phân bố lệch phải cực mạnh; trung vị giá đạt 7,4 tỷ VNĐ, khoảng tứ phân vị IQR từ 4,1 tỷ VNĐ ($Q_1$) đến 14,3 tỷ VNĐ ($Q_3$). |
| **Hình 3.5** | Phân bố diện tích bất động sản (Thang đo Logarithmic) | `results/eda/area_distribution.png` | Chương 3 | Phân bố diện tích tập trung tại trung vị 80,0 m², khoảng IQR từ 45,0 m² đến 109,1 m² ($IQR = 64,1$ m²). |
| **Hình 3.6** | Phân bố giá chào bán theo từng loại hình bất động sản (Boxplot) | `results/eda/price_by_property_type_boxplot.png` | Chương 3 | Biệt thự có phân bố giá cao nhất, tiếp đến là Shophouse, Nhà riêng, Đất và Căn hộ chung cư. |
| **Hình 3.7** | Đơn giá chào bán trung vị (Triệu/m²) tại các địa phương trọng điểm | `results/eda/price_per_m2_by_province.png` | Chương 3 | Hà Nội và TP.HCM dẫn đầu về đơn giá trung vị, phản ánh giá trị thương mại và áp lực tập trung dân cư đô thị. |
| **Hình 3.8** | Mật độ tương quan giữa giá và diện tích bất động sản (Hexbin Plot) | `results/eda/price_vs_area_scatter.png` | Chương 3 | Mật độ tích tụ dày đặc tại vùng diện tích 40–100 m² và giá 3–10 tỷ VNĐ; minh họa mối tương quan phi tuyến. |
| **Hình 3.9** | Xu hướng số lượng tin đăng bất động sản theo thời gian đăng tin | `results/eda/monthly_listings_trend.png` | Chương 3 | Khảo sát tính biến thiên theo chu kỳ thời gian từ năm 2023 đến hết 2025; minh chứng tính ổn định của dòng dữ liệu. |
| **Hình 3.10** | Ma trận hệ số tương quan phi tuyến Spearman giữa các biến định lượng | `results/eda/numeric_correlation_heatmap.png` | Chương 3 | Tương quan hạng Spearman giữa diện tích và giá đạt $\rho = 0,584$; tương quan giữa giá và đơn giá đạt $\rho = 0,621$. |
| **Hình 5.1** | Thời gian thực thi trung vị theo quy mô dữ liệu của 4 bài toán truy vấn | `results/benchmark/analysis/execution_time_by_scale.png` | Chương 5 | Trực quan hóa tương quan giữa kích thước bảng và thời gian thực thi (ms, log-scale); làm nổi bật sự phân kỳ giữa Seq Scan và Index Scan. |
| **Hình 5.2** | So sánh hệ số tăng tốc (Speedup Factor) của các phương pháp tối ưu | `results/benchmark/analysis/speedup_comparison.png` | Chương 5 | Biểu đồ cột thể hiện hệ số tăng tốc qua 3 quy mô; Q2 đạt đỉnh 942,37x tại 500K, Q3_D đạt 17,97x, Q1 đạt 4,04x, trong khi Q4 và Q3_C tiệm cận 1,0x. |
| **Hình 5.3** | Chi phí phụ trội lưu trữ (Storage Overhead) của các chỉ mục B-tree | `results/benchmark/analysis/index_storage_overhead.png` | Chương 5 | So sánh dung lượng vật lý (MB) của 4 chỉ mục đo riêng tại 50K, 200K, 500K; chỉ ra Composite Index chiếm dung lượng lớn nhất (28,53 MB tại 500K). |

---

### PHẦN 2: DANH MỤC BẢNG BIỂU (TABLES)

| Số hiệu | Tên bảng (Caption) | Tệp nguồn trong Repository | Chương | Nội dung tóm tắt |
| :---: | :--- | :--- | :---: | :--- |
| **Bảng 2.1** | Ma trận tiêu chí lựa chọn phương thức quét bảng của Bộ tối ưu hóa chi phí (PostgreSQL CBO) | `report/02_co_so_ly_thuyet.md` | Chương 2 | So sánh Seq Scan, Index Scan, và Bitmap Scan theo điều kiện Index, độ chọn lọc và cơ chế I/O. |
| **Bảng 3.1** | Đặc tả cấu trúc lược đồ dữ liệu chuẩn hóa (9 thuộc tính) | `sql/schema.sql`, `docs/data_dictionary.md` | Chương 3 | Tên cột, kiểu dữ liệu SQL chuẩn, tính chất Nullable, Ràng buộc kiểm tra tính toàn vẹn (CHECK constraint). |
| **Bảng 3.2** | Kết quả kiểm toán quá trình thu thập và lọc dòng dữ liệu (500K) | `results/build_report_500000.json` | Chương 3 | Thống kê số dòng nguồn (502.000), số bản ghi bị loại (203), nguyên nhân vi phạm, số bản ghi hợp lệ và thời gian xử lý. |
| **Bảng 3.3** | Thống kê mô tả định lượng vững trên tập dữ liệu 500.000 bản ghi | `results/quality/data_quality_report_500000.json` | Chương 3 | Số lượng quan sát, Min, Q1, Median (80 m²; 7,4 tỷ), Mean, Q3, Max, IQR, Độ lệch chuẩn cho diện tích, giá và đơn giá. |
| **Bảng 4.1** | Đặc tả 10 cấu hình thực nghiệm Benchmark PostgreSQL | `sql/benchmark/queries/`, `sql/benchmark/indexes/` | Chương 4 | Mã cấu hình (Q1_base, Q1_idx, Q2_base, Q2_idx, Q3_A-D, Q4_base, Q4_idx), câu lệnh SQL chính xác 100%, chỉ mục sử dụng và mục tiêu kiểm chứng. |
| **Bảng 5.1** | Kết quả đo lường hiệu năng nạp và xử lý dữ liệu tiền kỳ (500K bản ghi) | `results/processing_benchmark/processing_benchmark.csv` | Chương 5 | Thời gian nạp tệp (CSV vs Parquet, Pandas vs Polars), Đỉnh RAM RSS, Mức tăng RAM ($\Delta$ RSS: Chunked read +19,68 MB, Chunked aggregate +21,09 MB). |
| **Bảng 5.2** | Tổng hợp kết quả đo đạc Benchmark PostgreSQL trên 3 quy mô dữ liệu | `results/benchmark/benchmark_results.csv` | Chương 5 | 30 hàng số liệu: Quy mô, Cấu hình, Scan Type, Dung lượng Index, Thời gian Median, IQR, Min, Max, Shared Hit Blocks, Speedup. |
| **Bảng 5.3** | Diễn biến hiệu năng của bài toán Q1 qua 3 thang đo dữ liệu | `results/benchmark/benchmark_results.csv` | Chương 5 | Thời gian thực thi, số block đọc đệm và hệ số tăng tốc của Q1 qua các quy mô 50K, 200K, 500K dòng. |
| **Bảng 5.4** | So sánh chi tiết hiệu năng bài toán Q2 và Cơ chế Early Termination | `results/benchmark/benchmark_results.csv` | Chương 5 | Phân tích cơ chế Early Termination và triệt tiêu nút Sort; bảng so sánh thời gian và Buffer Shared Hit Blocks (23 vs 12.898). |
| **Bảng 5.5** | Bảng phân rã trực giao 2x2 hiệu năng bài toán Q3 qua 3 thang đo | `results/benchmark/benchmark_results.csv` | Chương 5 | So sánh 4 cấu hình A, B, C, D; tốc độ tăng tốc tương đối, chứng minh vai trò quyết định của vị từ dạng sargable. |
| **Bảng 5.6** | Kết quả thực nghiệm bài toán đối chứng âm Q4 qua 3 thang đo | `results/benchmark/benchmark_results.csv` | Chương 5 | So sánh thời gian thực thi giữa Baseline và Indexed; phân tích lý do Planner giữ nguyên Seq Scan + HashAggregate. |
| **Bảng 5.7** | Chi phí phụ trội lưu trữ vật lý của các chỉ mục B-tree qua các thang đo | `results/benchmark/benchmark_summary.json` | Chương 5 | Dung lượng MB của từng chỉ mục đo riêng tại 50K, 200K, 500K (tổng 46,02 MB tại 500K) và tỷ lệ phần trăm so với dung lượng bảng Heap. |
