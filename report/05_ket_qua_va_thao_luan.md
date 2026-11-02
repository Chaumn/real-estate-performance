# CHƯƠNG 5: KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN KHOA HỌC

Chương này trình bày toàn bộ số liệu đo đạc thực nghiệm định lượng, phân tích kế hoạch thực thi chi tiết (Execution Plans), khảo sát lưu lượng bộ đệm (Buffer I/O) và mức chiếm dụng tài nguyên bộ nhớ nhằm trả lời dứt khoát ba câu hỏi nghiên cứu **RQ1**, **RQ2** và **RQ3**.

---

## 5.1. Đánh giá chất lượng và Tính đại diện của bộ dữ liệu (Trả lời RQ1)

Từ các kết quả kiểm toán hồ sơ dữ liệu (Data Profiling) và phân tích khám phá (EDA) đã thực hiện tại Chương 3, nhóm nghiên cứu tổng hợp các kết luận khoa học nhằm trả lời **Câu hỏi nghiên cứu 1 (RQ1)**:

1. **Về tính toàn vẹn và độ tin cậy của quy trình làm sạch:**
   - Pipeline nạp luồng kết hợp xáo trộn có kiểm soát (`seed = 42`, `buffer_size = 10,000`, `batch_size = 2,000`) đã xử lý 502.000 dòng từ nguồn `Phuscca/vietnam-real-estates`, loại bỏ 203 bản ghi vi phạm tính toàn vẹn (202 bản ghi thiếu trường bắt buộc, 1 bản ghi diện tích $\le 0$) và xuất ra 500.000 bản ghi chuẩn hóa theo hợp đồng 9 thuộc tính. Sáu trường cốt lõi đạt độ đầy đủ 100,00%.
2. **Về phân tầng giá trị khuyết thiếu nghiệp vụ:**
   - Trường địa bàn cấp xã/phường (`ward_name`) có tỷ lệ khuyết thiếu cao nhất với đúng **72.150 bản ghi** (**14,43%**), phản ánh thói quen đăng tin bất động sản thường chỉ ghi rõ đến cấp quận/huyện.
   - Trường quận/huyện (`district_name`) có tỷ lệ khuyết thiếu thấp với đúng **14.235 bản ghi** (**2,85%**).
   - Trường giá chào bán (`price`) thiếu đúng **39.061 bản ghi** (**7,81%**). Việc bảo toàn các bản ghi này dưới dạng SQL NULL đã giữ nguyên tính chân thực của phân khúc "giá thỏa thuận", không làm sai lệch mẫu số khảo sát diện tích và vùng miền.
3. **Về tính đại diện không gian và loại hình:**
   - Bộ dữ liệu phản ánh cấu trúc tập trung cao độ của thị trường bất động sản Việt Nam: hai đô thị đặc biệt TP. Hồ Chí Minh (186.698 tin, 37,34%) và Hà Nội (170.167 tin, 34,03%) chiếm tới 71,37% tổng số tin đăng toàn quốc. Thành phố Hải Phòng có 10.422 tin đăng (2,08%), tạo nên tập con đại diện phù hợp cho bài toán lọc đơn cột Q1. Về loại hình, phân khúc Nhà riêng chiếm ưu thế tuyệt đối (46,08%), tiếp theo là Đất (24,12%) và Căn hộ chung cư (20,82%).
4. **Về tính chất phân phối định lượng vững:**
   - Do giá bán và diện tích bị chi phối bởi các bất động sản giá trị rất lớn (giá tối đa ghi nhận 920.000 tỷ VNĐ), giá trị trung bình bị kéo lệch rất xa so với thực tế. Các chỉ số thống kê vững khẳng định: trung vị diện tích là **80,0 m²** (khoảng tứ phân vị IQR = 64,1 m², dao động từ 45,0 m² đến 109,1 m²) và trung vị giá chào bán là **7,40 tỷ VNĐ** (khoảng tứ phân vị IQR = 10,20 tỷ VNĐ, dao động từ 4,10 tỷ đến 14,30 tỷ VNĐ). Đây là cơ sở thực nghiệm vững chắc để thiết kế các bài toán lọc khoảng và sắp xếp trong cơ sở dữ liệu.

---

## 5.2. Hiệu năng xử lý dữ liệu với Pandas, Polars, CSV, Parquet và Chunked Processing (Trả lời RQ2)

Bảng 5.1 tổng hợp số liệu đo đạc thực nghiệm từ tệp [`results/processing_benchmark/processing_benchmark.csv`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/processing_benchmark/processing_benchmark.csv) ghi nhận thời gian thực thi (trung vị, trung bình, độ lệch chuẩn) và tài nguyên bộ nhớ RAM (lấy mẫu RSS chu kỳ 1 ms) trên tập dữ liệu 500.000 bản ghi.

**Bảng 5.1: Kết quả đo lường hiệu năng nạp và xử lý dữ liệu tiền kỳ (500.000 bản ghi)**

| Hạng mục tác vụ | Thư viện & Thao tác | Định dạng tệp | Thời gian Median (ms) | Thời gian Mean (ms) | Đỉnh RAM (Peak RSS, MB) | Mức tăng RAM ($\Delta$ RSS, MB) | Kích thước tệp trên đĩa (MB) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Nạp tệp (File Ingestion)** | Pandas `read_csv` | CSV | 3.038,53 ms | 3.089,49 ms | 781,70 MB | +241,37 MB | 93,88 MB |
| | Polars `read_csv` | CSV | **75,27 ms** | 76,25 ms | 801,52 MB | +105,62 MB | 93,88 MB |
| | Pandas `read_parquet` | Parquet | 127,00 ms | 135,81 ms | 931,18 MB | +47,95 MB | **41,42 MB** |
| | Polars `read_parquet` | Parquet | 202,25 ms | 199,19 ms | 811,37 MB | +44,95 MB | **41,42 MB** |
| **Nạp kiểm soát RAM (Chunked)** | Pandas Chunked read (10k) | CSV | 3.723,10 ms | 3.652,93 ms | 437,41 MB | **+19,68 MB** | 93,88 MB |
| | Pandas Chunked aggregate (10k) | CSV | 3.835,01 ms | 3.756,04 ms | 438,54 MB | **+21,09 MB** | 93,88 MB |
| **Lọc và Tổng hợp trong RAM** | Pandas Filter + GroupBy | In-Memory | 55,17 ms | 55,33 ms | 726,17 MB | +5,98 MB | — |
| | Polars Filter + GroupBy | In-Memory | **13,88 ms** | 16,44 ms | 775,43 MB | +4,44 MB | — |

### 5.2.1. Tốc độ nạp tệp: Ưu thế vượt trội của Polars CSV và Định dạng Parquet
1. **So sánh động cơ trên cùng định dạng CSV:** Polars hoàn thành việc đọc tệp CSV 500.000 dòng trong **75,27 ms**, nhanh gấp **40,3 lần** so với Pandas read_csv (**3.038,53 ms**). Sự cách biệt này xuất phát từ kiến trúc nội tại: Polars sử dụng bộ giải mã CSV đa luồng viết bằng Rust, tận dụng tập lệnh vector hóa SIMD của CPU và cơ chế phân bổ bộ nhớ không sao chép (Zero-copy memory allocation) của Apache Arrow, trong khi Pandas phụ thuộc vào vòng lặp C đơn luồng truyền thống kết hợp phân bổ đối tượng Python riêng lẻ.
2. **Ưu thế về không gian và độ trễ của Parquet:** Tệp Parquet chuẩn hóa chỉ chiếm **41,42 MB** trên đĩa cứng, tiết kiệm **55,9% dung lượng** so với định dạng CSV (93,88 MB). Khi nạp tệp Parquet vào Pandas, thời gian đọc giảm mạnh từ 3.038,53 ms xuống còn **127,00 ms** (nhanh hơn 23,9 lần), đồng thời mức tăng RAM chỉ tốn **+47,95 MB** thay vì +241,37 MB của CSV.

### 5.2.2. Phân tích kỹ thuật nạp phân khối Chunked Streaming và Mức tăng RAM
Kết quả đo đạc từ luồng giám sát RAM 1 ms cung cấp bức tranh định lượng rõ ràng:
- Khi nạp trọn gói tệp CSV bằng `pandas.read_csv()`, mức tăng bộ nhớ thực tế là **+241,37 MB** (gấp 2,57 lần kích thước tệp trên đĩa do chi phí phân bổ đối tượng Python và mảng dữ liệu tạm).
- Khi áp dụng kỹ thuật nạp phân khối (`chunksize = 10,000`), tác vụ duyệt khối thông thường khống chế mức tăng RAM ở mức **+19,68 MB** (đỉnh RSS đạt 437,41 MB).
- Tuy nhiên, đối với tác vụ nạp phân khối kết hợp tính toán tổng hợp (`Pandas Chunked aggregate`), mức tăng bộ nhớ ghi nhận là **+21,09 MB** (đỉnh RSS đạt 438,54 MB).
- **Lưu ý khoa học quan trọng:** Kết quả thực nghiệm cho thấy mức tăng RAM của tác vụ tính toán phân khối vượt qua ngưỡng 20 MB (+21,09 MB), do đó **không thể đưa ra kết luận khái quát rằng mọi tác vụ Chunked đều có mức tăng dưới 20 MB**. Trong bài toán tính toán tổng hợp, việc duy trì và tích lũy bảng tổng hợp trung gian qua từng khối lặp tạo ra một chi phí lưu trữ bộ nhớ bổ sung. Mặc dù vậy, mức tăng +21,09 MB vẫn thấp hơn 11,4 lần so với việc nạp toàn bộ tệp (+241,37 MB), minh chứng cho năng lực kiểm soát đỉnh bộ nhớ hiệu quả của kỹ thuật nạp phân khối.

### 5.2.3. Hiệu năng lọc và Tổng hợp dữ liệu trong bộ nhớ
Trong tác vụ lọc 170.167 bản ghi tại Hà Nội và gom nhóm tính giá trung bình theo 5 loại hình bất động sản:
- Pandas Filter + GroupBy mất **55,17 ms** với mức tăng RAM +5,98 MB.
- Polars Filter + GroupBy chỉ mất **13,88 ms** với mức tăng RAM +4,44 MB, nhanh gấp **4,0 lần** Pandas.
Polars đạt được hiệu năng này nhờ cơ chế thực thi song song tự động trên các mảng cột Arrow và thuật toán gom nhóm băm đa luồng (Multi-threaded Hash Aggregation).

---

## 5.3. Đánh giá tối ưu hóa truy vấn PostgreSQL thông qua Q1 – Q4 (Trả lời RQ3)

### 5.3.1. Tổng quan bảng số liệu Benchmark qua 3 quy mô dữ liệu
Quá trình đo đạc 600 lượt chạy trên PostgreSQL 18.3 đã thu thập đầy đủ số liệu kế hoạch thực thi. Bảng 5.2 trình bày kết quả trích xuất từ [`results/benchmark/benchmark_results.csv`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/benchmark/benchmark_results.csv).

> [!NOTE]
> Trong Bảng 5.2 và các phân tích tiếp theo, toàn bộ giá trị tại cột `Shared Hit Blocks` đại diện cho các lần truy cập trang dữ liệu (8 KB) được phục vụ trực tiếp từ vùng nhớ đệm **PostgreSQL Shared Buffers trong RAM** sau 3 lượt warm-up. Số lượng `Shared Read Blocks` (đọc vật lý từ đĩa) trong toàn bộ các phép đo chính thức đều ghi nhận bằng **0.0**, do kích thước dữ liệu ở cả ba quy mô đều nằm trọn vẹn trong vùng đệm của hệ quản trị cơ sở dữ liệu.

**Bảng 5.2: Tổng hợp kết quả đo đạc Benchmark PostgreSQL trên 3 quy mô dữ liệu**

| Quy mô (Dòng) | Mã cấu hình | Bài toán | Kiểu quét chủ đạo | Chỉ mục sử dụng | Dung lượng Index (MB) | Thời gian Median (ms) | IQR (ms) | Min (ms) | Max (ms) | Shared Hit Blocks | Hệ số tăng tốc (Speedup) |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **50.000** | `Q1_baseline` | Q1 | Seq Scan | Không | 0,00 MB | 2,649 ms | 0,095 ms | 2,315 ms | 3,035 ms | 1.288 blk | 1,00x |
| 50.000 | `Q1_indexed` | Q1 | Bitmap Scan | `idx_properties_province_name` | 0,36 MB | 0,323 ms | 0,067 ms | 0,291 ms | 0,620 ms | 704 blk | **8,21x** |
| 50.000 | `Q2_baseline` | Q2 | Seq Scan | Không | 0,00 MB | 4,954 ms | 0,500 ms | 4,787 ms | 8,297 ms | 1.288 blk | 1,00x |
| 50.000 | `Q2_indexed` | Q2 | Index Scan | `idx_properties_location_price` | 2,88 MB | 0,029 ms | 0,014 ms | 0,021 ms | 0,059 ms | **23 blk** | **170,81x** |
| 50.000 | `Q3_A` | Q3 | Seq Scan | Không | 0,00 MB | 3,678 ms | 0,088 ms | 3,590 ms | 3,843 ms | 1.288 blk | 1,00x |
| 50.000 | `Q3_B` | Q3 | Seq Scan | Không | 0,00 MB | 3,263 ms | 0,249 ms | 3,087 ms | 4,389 ms | 1.288 blk | 1,13x |
| 50.000 | `Q3_C` | Q3 | Seq Scan | `idx_properties_published_at` | 1,09 MB | 3,673 ms | 0,087 ms | 3,620 ms | 3,940 ms | 1.288 blk | 1,00x |
| 50.000 | `Q3_D` | Q3 | Bitmap Scan | `idx_properties_published_at` | 1,09 MB | 0,126 ms | 0,026 ms | 0,106 ms | 0,169 ms | 272 blk | **29,31x** |
| 50.000 | `Q4_baseline` | Q4 | Seq Scan | Không | 0,00 MB | 8,733 ms | 0,496 ms | 8,383 ms | 11,470 ms | 1.288 blk | 1,00x |
| 50.000 | `Q4_indexed` | Q4 | Seq Scan | `idx_properties_property_type` | 0,35 MB | 8,661 ms | 0,458 ms | 8,336 ms | 14,879 ms | 1.288 blk | 1,01x |
| **200.000** | `Q1_baseline` | Q1 | Seq Scan | Không | 0,00 MB | 16,959 ms | 3,647 ms | 13,201 ms | 18,504 ms | 5.128 blk | 1,00x |
| 200.000 | `Q1_indexed` | Q1 | Bitmap Scan | `idx_properties_province_name` | 1,38 MB | 2,860 ms | 0,928 ms | 2,201 ms | 4,264 ms | 2.909 blk | **5,93x** |
| 200.000 | `Q2_baseline` | Q2 | Seq Scan | Không | 0,00 MB | 28,375 ms | 59,029 ms | 25,931 ms | 145,245 ms | 5.218 blk | 1,00x |
| 200.000 | `Q2_indexed` | Q2 | Index Scan | `idx_properties_location_price` | 11,42 MB | 0,040 ms | 0,023 ms | 0,025 ms | 0,116 ms | **23 blk** | **718,35x** |
| 200.000 | `Q3_A` | Q3 | Seq Scan | Không | 0,00 MB | 23,805 ms | 1,945 ms | 22,375 ms | 139,022 ms | 5.128 blk | 1,00x |
| 200.000 | `Q3_B` | Q3 | Seq Scan | Không | 0,00 MB | 28,830 ms | 107,282 ms | 23,020 ms | 141,803 ms | 5.128 blk | 0,83x |
| 200.000 | `Q3_C` | Q3 | Seq Scan | `idx_properties_published_at` | 4,30 MB | 24,251 ms | 3,467 ms | 21,868 ms | 138,394 ms | 5.128 blk | 0,98x |
| 200.000 | `Q3_D` | Q3 | Bitmap Scan | `idx_properties_published_at` | 4,30 MB | 0,874 ms | 0,406 ms | 0,524 ms | 1,707 ms | 1.082 blk | **27,24x** |
| 200.000 | `Q4_baseline` | Q4 | Seq Scan | Không | 0,00 MB | 34,967 ms | 53,310 ms | 31,501 ms | 142,100 ms | 5.144 blk | 1,00x |
| 200.000 | `Q4_indexed` | Q4 | Seq Scan | `idx_properties_property_type` | 1,34 MB | 36,247 ms | 53,717 ms | 33,540 ms | 144,977 ms | 5.144 blk | 0,96x |
| **500.000** | `Q1_baseline` | Q1 | Seq Scan | Không | 0,00 MB | 36,600 ms | 3,043 ms | 32,753 ms | 137,343 ms | 12.808 blk | 1,00x |
| 500.000 | `Q1_indexed` | Q1 | Bitmap Scan | `idx_properties_province_name` | 3,40 MB | 9,059 ms | 3,008 ms | 6,182 ms | 12,403 ms | 7.236 blk | **4,04x** |
| 500.000 | `Q2_baseline` | Q2 | Seq Scan | Không | 0,00 MB | 48,061 ms | 4,367 ms | 43,765 ms | 128,079 ms | 12.898 blk | 1,00x |
| 500.000 | `Q2_indexed` | Q2 | Index Scan | `idx_properties_location_price` | 28,53 MB | 0,051 ms | 0,047 ms | 0,029 ms | 0,102 ms | **23 blk** | **942,37x** |
| 500.000 | `Q3_A` | Q3 | Seq Scan | Không | 0,00 MB | 40,060 ms | 6,133 ms | 37,293 ms | 145,030 ms | 12.808 blk | 1,00x |
| 500.000 | `Q3_B` | Q3 | Seq Scan | Không | 0,00 MB | 38,522 ms | 2,161 ms | 35,736 ms | 150,678 ms | 12.808 blk | 1,04x |
| 500.000 | `Q3_C` | Q3 | Seq Scan | `idx_properties_published_at` | 10,73 MB | 42,263 ms | 5,978 ms | 37,766 ms | 143,458 ms | 12.808 blk | 0,95x |
| 500.000 | `Q3_D` | Q3 | Bitmap Scan | `idx_properties_published_at` | 10,73 MB | 2,230 ms | 1,045 ms | 1,618 ms | 3,691 ms | 2.666 blk | **17,97x** |
| 500.000 | `Q4_baseline` | Q4 | Seq Scan | Không | 0,00 MB | 63,278 ms | 3,097 ms | 60,540 ms | 142,209 ms | 12.824 blk | 1,00x |
| 500.000 | `Q4_indexed` | Q4 | Seq Scan | `idx_properties_property_type` | 3,36 MB | 66,480 ms | 4,542 ms | 60,333 | 70,819 ms | 12.824 blk | 0,95x |

![Thời gian thực thi trung vị theo quy mô dữ liệu của 4 bài toán truy vấn](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/benchmark/analysis/execution_time_by_scale.png)
*Hình 5.1: Thời gian thực thi trung vị theo quy mô dữ liệu của 4 bài toán truy vấn*

![So sánh hệ số tăng tốc (Speedup Factor) của các phương pháp tối ưu](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/benchmark/analysis/speedup_comparison.png)
*Hình 5.2: So sánh hệ số tăng tốc (Speedup Factor) của các phương pháp tối ưu*

### 5.3.2. Bài toán Q1: Hiệu quả của chỉ mục đơn cột và Chuyển đổi Bitmap Scan
Bài toán Q1 kiểm thử câu lệnh:
```sql
SELECT id, name, price, area
FROM public.properties
WHERE province_name = 'Hải Phòng';
```
Tại quy mô 500.000 dòng, Hải Phòng có đúng 10.422 bản ghi (chiếm tỷ lệ chọn lọc 2,08%).

**Bảng 5.3: Diễn biến hiệu năng của bài toán Q1 qua 3 thang đo dữ liệu**

| Quy mô dữ liệu | Cấu hình Baseline (ms) | Cấu hình Indexed (ms) | Hệ số tăng tốc (Speedup) | Khối đệm Baseline | Khối đệm Indexed | Giảm tải I/O (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **50.000 dòng** | 2,649 ms | 0,323 ms | **8,21x** | 1.288 blk | 704 blk | 45,3% |
| **200.000 dòng** | 16,959 ms | 2,860 ms | **5,93x** | 5.128 blk | 2.909 blk | 43,3% |
| **500.000 dòng** | 36,600 ms | 9,059 ms | **4,04x** | 12.808 blk | 7.236 blk | 43,5% |

**Phân tích cơ chế thực thi:**
- Trong cấu hình Baseline, PostgreSQL buộc phải quét tuần tự toàn bộ các trang Heap (`Gather -> Seq Scan`), duyệt qua 12.808 trang đệm tại 500K.
- Khi có chỉ mục B-tree `idx_properties_province_name` (dung lượng 3,40 MB), bộ lập lịch chuyển đổi sang **Bitmap Index Scan kết hợp Bitmap Heap Scan**:
  - Giai đoạn 1 (`Bitmap Index Scan`): Duyệt cây B-tree, gom các con trỏ dòng TID thỏa mãn `province_name = 'Hải Phòng'` để tạo một mảng bit trong RAM.
  - Giai đoạn 2 (`Bitmap Heap Scan`): Đọc tuần tự các trang Heap có đánh dấu bit theo thứ tự vật lý, chỉ nạp 7.236 khối đệm thay vì toàn bộ 12.808 khối (giảm 43,5% lưu lượng I/O).
- Hệ số tăng tốc đạt **8,21 lần** tại 50K và duy trì mức **4,04 lần** tại 500K. Xu hướng giảm nhẹ của hệ số tăng tốc khi dữ liệu tăng là phù hợp với lý thuyết: khi số bản ghi kết quả tăng từ 1.042 dòng (50K) lên 10.422 dòng (500K), các bản ghi phân tán trên nhiều trang Heap khác nhau, làm tăng số lượng trang Heap cần truy cập.

### 5.3.3. Bài toán Q2: Đột phá hiệu năng Composite Index, Early Termination và Triệt tiêu nút Sort
Bài toán Q2 thực thi câu lệnh:
```sql
SELECT id, name, price, area, published_at
FROM public.properties
WHERE province_name = 'Hà Nội'
  AND district_name = 'Cầu Giấy'
  AND price BETWEEN 4100000000 AND 14300000000
ORDER BY price ASC, id ASC
LIMIT 20;
```

**Bảng 5.4: So sánh chi tiết hiệu năng bài toán Q2 và Cơ chế Early Termination**

| Quy mô dữ liệu | Cấu hình | Thời gian Median (ms) | Shared Hit Blocks | Nút Sắp xếp trong Kế hoạch thực thi | Hệ số tăng tốc (Speedup) |
| :---: | :--- | :---: | :---: | :--- | :---: |
| **50.000 dòng** | Baseline | 4,954 ms | 1.288 blk | `Sort: top-N heapsort` trong RAM | 1,00x |
| | Indexed | **0,029 ms** | **23 blk** | **Không có (Triệt tiêu hoàn toàn nút Sort)** | **170,81x** |
| **200.000 dòng** | Baseline | 28,375 ms | 5.218 blk | `Sort: top-N heapsort` trong RAM | 1,00x |
| | Indexed | **0,040 ms** | **23 blk** | **Không có (Triệt tiêu hoàn toàn nút Sort)** | **718,35x** |
| **500.000 dòng** | Baseline | 48,061 ms | 12.898 blk | `Sort: top-N heapsort` trong RAM | 1,00x |
| | Indexed | **0,051 ms** | **23 blk** | **Không có (Triệt tiêu hoàn toàn nút Sort)** | **942,37x** |

**Bằng chứng phân tích kế hoạch thực thi thực tế (Execution Plan Evidence):**
Đối chiếu trực tiếp hai tệp kế hoạch thực thi thô tại quy mô 500.000 bản ghi:

1. **Kế hoạch Baseline (`500000_Q2_baseline_run01.json`):**
   ```text
   - Limit (Rows: 20.0, Cost: 18006.85)
     - Gather Merge (Rows: 20.0, Cost: 18317.82)
       - Sort (Rows: 6.67, Cost: 17007.3) sort=['price', 'id']
         - Seq Scan (Rows: 2610.0, Cost: 16974.67)
   Buffers: shared hit=12898
   ```
   PostgreSQL phải quét toàn bộ 12.898 khối đệm, nạp các hàng thỏa mãn vào bộ nhớ và thực thi thuật toán `Top-N Heapsort` (chiếm 27 KB RAM) để tìm ra 20 hàng có giá thấp nhất.

2. **Kế hoạch Indexed (`500000_Q2_indexed_run01.json`):**
   ```text
   - Limit (Rows: 20.0, Cost: 70.95)
     - Index Scan (Rows: 20.0, Cost: 9811.01) index=idx_properties_location_price
   Buffers: shared hit=23
   ```
   Chỉ mục được khởi tạo chính xác:
   ```sql
   CREATE INDEX idx_properties_location_price
   ON public.properties USING btree (province_name, district_name, price, id);
   ```
   **Bằng chứng khẳng định việc loại bỏ nút Sort:** Trong cây kế hoạch thực thi của bản Indexed, **nút Sort hoàn toàn biến mất**. Nhờ chỉ mục tổ hợp B-tree đã tổ chức các khóa lá theo đúng thứ tự lọc đẳng thức (`province_name, district_name`), tiếp đến là khóa sắp xếp (`price`) và khóa phá vỡ trùng lặp (`id`), bộ lập lịch chỉ cần định vị lá đầu tiên, duyệt theo liên kết lá và dừng lại ngay khi thu thập đủ 20 dòng (**Early Termination**).

**Làm rõ chi phí B-tree và giới hạn tiệm cận:**
Không thể tuyên bố rằng Index Scan có độ phức tạp thời gian $O(1)$ trong mọi trường hợp. Chi phí tìm kiếm B-tree thực chất là $O(h + k)$, trong đó chiều cao cây $h \approx 3$ và số dòng cần lấy $k = 20$. 
Trong bài toán Q2, do $k = 20$ là một hằng số nhỏ cố định và các khóa lá nằm liên tục, số lượng trang đệm truy cập được giữ nguyên cố định ở mức đúng **23 Shared Hit Blocks** (3 trang trên chỉ mục B-tree + 20 trang trên bảng Heap) trên cả ba quy mô từ 50K đến 500K. Điều này giúp thời gian thực thi duy trì ở mức cận hằng số cực nhỏ (~0,05 ms), mang lại mức tăng tốc **942,37 lần** tại 500K.

### 5.3.4. Bài toán Q3: Phân tích trực giao 2x2, Vô hiệu hóa Index và Cộng hưởng Sargable
Bài toán Q3 kiểm thử việc lọc theo ngày đăng tin (`2025-10-15`) qua ma trận trực giao $2 \times 2$.

**Bảng 5.5: Bảng phân rã trực giao 2x2 hiệu năng bài toán Q3 qua 3 thang đo**

| Quy mô dữ liệu | Cấu hình A: Gốc, Không Index | Cấu hình B: Viết lại, Không Index | Cấu hình C: Gốc, Có Index | Cấu hình D: Viết lại, Có Index | Tăng tốc B vs A (Chỉ viết lại) | Tăng tốc C vs A (Chỉ đánh Index) | Tăng tốc D vs A (Viết lại + Index) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **50.000 dòng** | 3,678 ms (1.288 blk) | 3,263 ms (1.288 blk) | 3,673 ms (1.288 blk) | **0,126 ms** (272 blk) | 1,13x | 1,00x | **29,31x** |
| **200.000 dòng** | 23,805 ms (5.128 blk) | 28,830 ms (5.128 blk) | 24,251 ms (5.128 blk) | **0,874 ms** (1.082 blk) | 0,83x | 0,98x | **27,24x** |
| **500.000 dòng** | 40,060 ms (12.808 blk) | 38,522 ms (12.808 blk) | 42,263 ms (12.808 blk) | **2,230 ms** (2.666 blk) | 1,04x | 0,95x | **17,97x** |

**Phân tích phát hiện khoa học:**
1. **Hiện tượng vô hiệu hóa chỉ mục do vị từ Non-sargable (Cấu hình C):**
   - Trong Cấu hình C, chỉ mục B-tree `idx_properties_published_at` (10,73 MB tại 500K) đã tồn tại. Tuy nhiên, do câu lệnh sử dụng biểu thức ép kiểu `published_at::date = DATE '2025-10-15'`, bộ lập lịch nhận diện đây là một hàm chưa đánh giá trên cột và không thể ánh xạ lên cây B-tree.
   - Kế hoạch thực thi xác nhận bộ lập lịch thực hiện `Seq Scan` toàn bộ 12.808 trang đệm. **Tỷ lệ sử dụng chỉ mục của Cấu hình C là 0,00%**, và thời gian thực thi (42,26 ms) thậm chí chậm hơn nhẹ so với Cấu hình A (40,06 ms) do chi phí lập kế hoạch. Toàn bộ 10,73 MB lưu trữ của chỉ mục hoàn toàn bị lãng phí.
2. **Vai trò độc lập của Viết lại truy vấn (Cấu hình B):**
   - Khi viết lại sang dạng khoảng sargable $[T_1, T_2)$ nhưng không có chỉ mục, hệ thống vẫn phải quét tuần tự toàn bảng (Speedup = 1,04x tại 500K). Viết lại truy vấn đơn thuần không đem lại cải thiện đáng kể nếu thiếu chỉ mục hỗ trợ.
3. **Hiệu ứng cộng hưởng (Cấu hình D):**
   - Chỉ khi kết hợp đồng thời vị từ sargable và chỉ mục B-tree tương ứng, bộ lập lịch mới kích hoạt `Bitmap Index Scan + Bitmap Heap Scan`, giảm số khối đệm từ 12.808 xuống 2.666 khối (giảm 79,2%) và tăng tốc độ truy vấn **17,97 lần** tại 500K (và **29,31 lần** tại 50K).

### 5.3.5. Bài toán Q4: Đối chứng âm Aggregation Control và Giới hạn của B-tree
Bài toán Q4 thực thi câu lệnh tổng hợp toàn bảng:
```sql
SELECT
    property_type_name,
    COUNT(*) AS total,
    ROUND(AVG(price), 0) AS avg_price
FROM public.properties
GROUP BY property_type_name
ORDER BY total DESC;
```

**Bảng 5.6: Kết quả thực nghiệm bài toán đối chứng âm Q4 qua 3 thang đo**

| Quy mô dữ liệu | Cấu hình Baseline (ms) | Kiểu quét Baseline | Cấu hình Indexed (ms) | Kiểu quét Indexed | Hệ số tăng tốc (Speedup) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **50.000 dòng** | 8,733 ms | Seq Scan | 8,661 ms | Seq Scan | **1,01x** |
| **200.000 dòng** | 34,967 ms | Seq Scan | 36,247 ms | Seq Scan | **0,96x** |
| **500.000 dòng** | 63,278 ms | Seq Scan | 66,480 ms | Seq Scan | **0,95x** |

**Phân tích nguyên lý bộ tối ưu hóa chi phí (CBO):**
- Trong cả cấu hình Baseline và Indexed, kế hoạch thực thi giữ nguyên cấu trúc: `Sort -> Aggregate -> Gather Merge -> Sort -> Aggregate -> Seq Scan` trên toàn bộ 12.824 trang đệm của bảng.
- Dù chỉ mục B-tree `idx_properties_property_type` (3,36 MB) đã được tạo, bộ lập lịch **hoàn toàn không sử dụng chỉ mục**. Lý do là truy vấn yêu cầu tính `AVG(price)` trên toàn bộ 500.000 dòng trong bảng. Do chỉ mục B-tree chỉ chứa cột `property_type_name`, nếu sử dụng Index Scan, hệ thống sẽ phải thực hiện 500.000 lần truy cập ngẫu nhiên (Random I/O) vào các trang Heap để lấy giá trị `price`. Với chi phí `random_page_cost = 4.0`, tổng chi phí ước tính sẽ lớn gấp nhiều lần so với việc quét tuần tự liên tục (`Seq Scan`) toàn bộ các khối đệm vào bộ nhớ băm.
- Kết quả Q4 xác lập bằng chứng đối chứng âm rõ ràng: Chỉ mục B-tree không đem lại lợi ích cho các truy vấn tổng hợp toàn bảng thiếu mệnh đề chọn lọc.

### 5.3.6. Chi phí phụ trội lưu trữ vật lý của các chỉ mục B-tree (46,02 MB tại 500K)
Bảng 5.7 tổng hợp dung lượng vật lý thực tế của các chỉ mục trích xuất từ hàm quản trị `pg_relation_size()`.

**Bảng 5.7: Chi phí phụ trội lưu trữ vật lý của các chỉ mục B-tree qua các thang đo**

| Tên chỉ mục | Bài toán áp dụng | Cột đánh chỉ mục | Dung lượng tại 50K (MB) | Dung lượng tại 200K (MB) | Dung lượng tại 500K (MB) | Tỷ trọng trên tổng Index 500K (%) |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| `idx_properties_province_name` | Q1 | `(province_name)` | 0,36 MB | 1,38 MB | 3,40 MB | 7,4% |
| `idx_properties_location_price` | Q2 | `(province_name, district_name, price, id)` | 2,88 MB | 11,42 MB | 28,53 MB | 62,0% |
| `idx_properties_published_at` | Q3 | `(published_at)` | 1,09 MB | 4,30 MB | 10,73 MB | 23,3% |
| `idx_properties_property_type` | Q4 | `(property_type_name)` | 0,35 MB | 1,34 MB | 3,36 MB | 7,3% |
| **Tổng dung lượng các chỉ mục đo riêng** | — | — | **4,68 MB** | **18,44 MB** | **46,02 MB** | **100,0%** |
| *Dung lượng bảng Heap dữ liệu gốc* | — | *9 thuộc tính bảng properties* | *~10,1 MB* | *~40,5 MB* | *~100,8 MB* | — |
| **Tỷ lệ Tổng Index / Dung lượng Bảng Heap** | — | — | **46,3%** | **45,5%** | **45,6%** | — |

![Chi phí phụ trội lưu trữ (Storage Overhead) của các chỉ mục B-tree](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/benchmark/analysis/index_storage_overhead.png)
*Hình 5.3: Chi phí phụ trội lưu trữ (Storage Overhead) của các chỉ mục B-tree*

> [!IMPORTANT]
> **Làm rõ phương pháp luận về con số 46,02 MB:**
> Con số **46,02 MB** là **tổng dung lượng của 4 chỉ mục được đo đạc riêng lẻ theo từng cấu hình độc lập** (do giao thức đo lường thực hiện xóa và cách ly chỉ mục trước mỗi cấu hình bằng `reset_indexes.sql`). Con số này **không phải là dung lượng lưu trữ đồng thời được quan sát trong một trạng thái cơ sở dữ liệu đơn lẻ duy nhất** chứa cả 4 chỉ mục cùng lúc. Tuy nhiên, phép cộng gộp này phản ánh chính xác tổng chi phí tài nguyên lưu trữ tối thiểu mà hệ thống phải gánh chịu nếu quản trị viên quyết định duy trì đồng thời cả 4 chỉ mục này trong môi trường sản xuất.

Trong đó, chỉ mục Composite `(province_name, district_name, price, id)` chiếm tỷ trọng áp đảo (**28,53 MB**, tương đương **62,0%** tổng dung lượng chỉ mục) do phải lưu trữ cả 4 giá trị thuộc tính kèm con trỏ TID trên từng phần tử lá.

---

## 5.4. Tổng hợp đối chiếu và Ma trận chứng tích thực nghiệm

Quá trình kiểm chứng đối chiếu khẳng định:
1. **Kiểm toán 600 kế hoạch thực thi:** Toàn bộ 600 tệp JSON kế hoạch trong `results/benchmark/raw/` được tính toán mã băm SHA-256 lưu trữ tại [`results/benchmark/raw_manifest.json`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/benchmark/raw_manifest.json). Script kiểm toán tự động [`scripts/verify_benchmark_evidence.py`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/scripts/verify_benchmark_evidence.py) xác nhận toàn bộ các tệp bằng chứng tồn tại đầy đủ, không bị can thiệp và khớp hoàn toàn với số liệu tổng hợp trong Bảng 5.2.
2. **Kiểm thử tự động hồi quy:** Toàn bộ bộ kiểm thử gồm 182 test cases trong `tests/` vận hành ngoại tuyến và đạt trạng thái thông qua (181 passed, 1 skipped), đảm bảo tính toàn vẹn và tính nhất quán dữ liệu của toàn bộ nghiên cứu.

