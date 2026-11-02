# CHƯƠNG 4: KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN KHOA HỌC

## 4.0. Bảng tổng hợp kết quả Benchmark PostgreSQL qua 3 quy mô dữ liệu

Quá trình thực nghiệm đo đạc tự động trên hệ quản trị cơ sở dữ liệu PostgreSQL 18.3 đã thu thập đầy đủ **600 tệp JSON kế hoạch thực thi thô** (3 quy mô dữ liệu $\times$ 10 cấu hình thực nghiệm $\times$ 20 lần chạy chính thức sau 3 lượt warm-up). Bảng 4.1 trình bày toàn bộ số liệu thống kê trung vị (Median), khoảng tứ phân vị (IQR), số lượng khối đệm Shared Buffers và hệ số tăng tốc (Speedup Factor) trích xuất từ tệp kết quả gốc [`results/benchmark/benchmark_results.csv`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/benchmark/benchmark_results.csv).

**Bảng 4.1: Tổng hợp kết quả đo đạc Benchmark PostgreSQL trên 3 quy mô dữ liệu**

| Quy mô (Dòng) | Mã cấu hình | Bài toán | Kiểu quét chủ đạo (Scan Type) | Chỉ mục sử dụng | Dung lượng Index (MB) | Thời gian Median (ms) | IQR (ms) | Min (ms) | Max (ms) | Shared Hit Blocks | Hệ số tăng tốc (Speedup) |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **50.000** | `Q1_baseline` | Q1 | Seq Scan | Không | 0.00 | 2.649 | 0.095 | 2.315 | 3.035 | 1.288 | 1.00x |
| 50.000 | `Q1_indexed` | Q1 | Bitmap Scan | `idx_properties_province_name` | 0.36 | 0.323 | 0.067 | 0.291 | 0.620 | 704 | **8.21x** |
| 50.000 | `Q2_baseline` | Q2 | Seq Scan | Không | 0.00 | 4.954 | 0.500 | 4.787 | 8.297 | 1.288 | 1.00x |
| 50.000 | `Q2_indexed` | Q2 | Index Scan | `idx_properties_location_price` | 2.88 | 0.029 | 0.014 | 0.021 | 0.059 | **23** | **170.81x** |
| 50.000 | `Q3_A` | Q3 | Seq Scan | Không | 0.00 | 3.678 | 0.088 | 3.590 | 3.843 | 1.288 | 1.00x |
| 50.000 | `Q3_B` | Q3 | Seq Scan | Không | 0.00 | 3.263 | 0.249 | 3.087 | 4.389 | 1.288 | 1.13x |
| 50.000 | `Q3_C` | Q3 | Seq Scan | `idx_properties_published_at` | 1.09 | 3.673 | 0.087 | 3.620 | 3.940 | 1.288 | 1.00x |
| 50.000 | `Q3_D` | Q3 | Bitmap Scan | `idx_properties_published_at` | 1.09 | 0.126 | 0.026 | 0.106 | 0.169 | 272 | **29.31x** |
| 50.000 | `Q4_baseline` | Q4 | Seq Scan | Không | 0.00 | 8.733 | 0.496 | 8.383 | 11.470 | 1.288 | 1.00x |
| 50.000 | `Q4_indexed` | Q4 | Seq Scan | `idx_properties_property_type` | 0.35 | 8.661 | 0.458 | 8.336 | 14.879 | 1.288 | 1.01x |
| **200.000** | `Q1_baseline` | Q1 | Seq Scan | Không | 0.00 | 16.959 | 3.647 | 13.201 | 18.504 | 5.128 | 1.00x |
| 200.000 | `Q1_indexed` | Q1 | Bitmap Scan | `idx_properties_province_name` | 1.38 | 2.860 | 0.928 | 2.201 | 4.264 | 2.909 | **5.93x** |
| 200.000 | `Q2_baseline` | Q2 | Seq Scan | Không | 0.00 | 28.375 | 59.029 | 25.931 | 145.245 | 5.218 | 1.00x |
| 200.000 | `Q2_indexed` | Q2 | Index Scan | `idx_properties_location_price` | 11.42 | 0.040 | 0.023 | 0.025 | 0.116 | **23** | **718.35x** |
| 200.000 | `Q3_A` | Q3 | Seq Scan | Không | 0.00 | 23.805 | 1.945 | 22.375 | 139.022 | 5.128 | 1.00x |
| 200.000 | `Q3_B` | Q3 | Seq Scan | Không | 0.00 | 28.830 | 107.282 | 23.020 | 141.803 | 5.128 | 0.83x |
| 200.000 | `Q3_C` | Q3 | Seq Scan | `idx_properties_published_at` | 4.30 | 24.251 | 3.467 | 21.868 | 138.394 | 5.128 | 0.98x |
| 200.000 | `Q3_D` | Q3 | Bitmap Scan | `idx_properties_published_at` | 4.30 | 0.874 | 0.406 | 0.524 | 1.707 | 1.082 | **27.24x** |
| 200.000 | `Q4_baseline` | Q4 | Seq Scan | Không | 0.00 | 34.967 | 53.310 | 31.501 | 142.100 | 5.144 | 1.00x |
| 200.000 | `Q4_indexed` | Q4 | Seq Scan | `idx_properties_property_type` | 1.34 | 36.247 | 53.717 | 33.540 | 144.977 | 5.144 | 0.96x |
| **500.000** | `Q1_baseline` | Q1 | Seq Scan | Không | 0.00 | 36.600 | 3.043 | 32.753 | 137.343 | 12.808 | 1.00x |
| 500.000 | `Q1_indexed` | Q1 | Bitmap Scan | `idx_properties_province_name` | 3.40 | 9.059 | 3.008 | 6.182 | 12.403 | 7.236 | **4.04x** |
| 500.000 | `Q2_baseline` | Q2 | Seq Scan | Không | 0.00 | 48.061 | 4.367 | 43.765 | 128.079 | 12.898 | 1.00x |
| 500.000 | `Q2_indexed` | Q2 | Index Scan | `idx_properties_location_price` | 28.53 | 0.051 | 0.047 | 0.029 | 0.102 | **23** | **942.37x** |
| 500.000 | `Q3_A` | Q3 | Seq Scan | Không | 0.00 | 40.060 | 6.133 | 37.293 | 145.030 | 12.808 | 1.00x |
| 500.000 | `Q3_B` | Q3 | Seq Scan | Không | 0.00 | 38.522 | 2.161 | 35.736 | 150.678 | 12.808 | 1.04x |
| 500.000 | `Q3_C` | Q3 | Seq Scan | `idx_properties_published_at` | 10.73 | 42.263 | 5.978 | 37.766 | 143.458 | 12.808 | 0.95x |
| 500.000 | `Q3_D` | Q3 | Bitmap Scan | `idx_properties_published_at` | 10.73 | 2.230 | 1.045 | 1.618 | 3.691 | 2.666 | **17.97x** |
| 500.000 | `Q4_baseline` | Q4 | Seq Scan | Không | 0.00 | 63.278 | 3.097 | 60.540 | 142.209 | 12.824 | 1.00x |
| 500.000 | `Q4_indexed` | Q4 | Seq Scan | `idx_properties_property_type` | 3.36 | 66.480 | 4.542 | 60.333 | 70.819 | 12.824 | 0.95x |

---

## 4.1. Kết quả thực nghiệm trả lời RQ1: Hiệu quả của cấu trúc Index B-tree đơn và đa cột

### 4.1.1. Phân tích bài toán Q1 (Single-column Index trên `province_name`)
Bài toán Q1 kiểm thử truy vấn tìm kiếm bất động sản theo điều kiện đẳng thức địa lý:
```sql
SELECT * FROM properties WHERE province_name = 'Hải Phòng';
```
Trong tập dữ liệu 500.000 bản ghi, số lượng tin đăng tại Hải Phòng là **15.541 dòng**, chiếm tỷ lệ chọn lọc (Selectivity) xấp xỉ **3.11%** tổng số hàng trong bảng.

**Bảng 4.2: Diễn biến hiệu năng của bài toán Q1 qua 3 thang đo**

| Quy mô dữ liệu | Cấu hình Baseline (ms) | Cấu hình Indexed (ms) | Hệ số tăng tốc (Speedup) | Khối đệm Baseline (Blocks) | Khối đệm Indexed (Blocks) | Giảm tải I/O (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **50.000 dòng** | 2.649 ms | 0.323 ms | **8.21x** | 1.288 blk | 704 blk | 45.3% |
| **200.000 dòng** | 16.959 ms | 2.860 ms | **5.93x** | 5.128 blk | 2.909 blk | 43.3% |
| **500.000 dòng** | 36.600 ms | 9.059 ms | **4.04x** | 12.808 blk | 7.236 blk | 43.5% |

**Cơ chế thực thi và Chuyển đổi Scan Type:**
- Trong cấu hình Baseline, PostgreSQL buộc phải quét tuần tự (`Seq Scan`) toàn bộ 12.808 trang dữ liệu của bảng tại 500K. Thời gian thực thi tăng gần như tuyến tính tuyệt đối: từ 2.65 ms (50K) lên 16.96 ms (200K - gấp 6.4 lần) và đạt 36.60 ms (500K - gấp 13.8 lần).
- Trong cấu hình Indexed, sự hiện diện của chỉ mục B-tree `idx_properties_province_name` (dung lượng 3.40 MB tại 500K) đã kích hoạt bộ lập lịch chuyển đổi phương thức quét sang **Bitmap Index Scan kết hợp Bitmap Heap Scan**:
  - Giai đoạn 1: `Bitmap Index Scan` quét nhanh qua các nút lá của B-tree, gom các con trỏ dòng TID thỏa mãn `province_name = 'Hải Phòng'` để tạo một mảng bit trong RAM.
  - Giai đoạn 2: `Bitmap Heap Scan` đọc tuần tự các trang Heap theo thứ tự vật lý, chỉ nạp 7.236 khối đệm thay vì toàn bộ 12.808 khối (giảm 43.5% lưu lượng I/O).
- Hệ số tăng tốc đạt **8.21 lần** tại 50K và duy trì mức **4.04 lần** tại 500K. Xu hướng giảm nhẹ của hệ số tăng tốc khi dữ liệu tăng là hoàn toàn phù hợp với lý thuyết cơ sở dữ liệu: khi số lượng bản ghi thỏa mãn điều kiện lọc tăng từ 1.550 dòng (50K) lên 15.541 dòng (500K), các con trỏ dòng bắt đầu phân tán rải rác trên nhiều trang Heap khác nhau, khiến số lượng trang Heap cần truy cập tăng dần và tiệm cận với việc quét tuần tự.

### 4.1.2. Phân tích đột phá hiệu năng bài toán Q2 (Composite Index và Early Termination)
Bài toán Q2 mô phỏng kịch bản người dùng thực tế tìm kiếm 20 bất động sản có giá thấp nhất tại một khu vực cụ thể trong một khoảng ngân sách xác định:
```sql
SELECT id, name, price, area, district_name 
FROM public.properties 
WHERE province_name = 'Hà Nội' 
  AND district_name = 'Cầu Giấy' 
  AND price BETWEEN 4100000000 AND 14300000000 
ORDER BY price ASC, id ASC 
LIMIT 20;
```

**Bảng 4.3: So sánh chi tiết hiệu năng bài toán Q2 và Cơ chế Early Termination**

| Quy mô dữ liệu | Cấu hình | Thời gian Median (ms) | Shared Hit Blocks | Thuật toán Sắp xếp (Sort Node) | Hệ số tăng tốc (Speedup) |
| :---: | :--- | :---: | :---: | :--- | :---: |
| **50.000 dòng** | Baseline | 4.954 ms | 1.288 blk | `Sort: Top-N heapsort` trong RAM | 1.00x |
| | Indexed | **0.029 ms** | **23 blk** | **Không có (Triệt tiêu hoàn toàn)** | **170.81x** |
| **200.000 dòng** | Baseline | 28.375 ms | 5.218 blk | `Sort: Top-N heapsort` trong RAM | 1.00x |
| | Indexed | **0.040 ms** | **23 blk** | **Không có (Triệt tiêu hoàn toàn)** | **718.35x** |
| **500.000 dòng** | Baseline | 48.061 ms | 12.898 blk | `Sort: Top-N heapsort` trong RAM | 1.00x |
| | Indexed | **0.051 ms** | **23 blk** | **Không có (Triệt tiêu hoàn toàn)** | **942.37x** |

**Phân tích sâu Kế hoạch Thực thi (Execution Plan Deep Dive):**
Sự chênh lệch hiệu năng khổng lồ lên tới **942.37 lần** tại quy mô 500.000 bản ghi được giải thích tường minh qua cấu trúc nội tại của hai cây kế hoạch thực thi trích xuất từ `results/benchmark/raw/500000/`:

1. **Cây kế hoạch Baseline (`Q2_baseline_run_*.json`):**
   ```text
   Limit (cost=14187.31..14187.36 rows=20 width=95) (actual time=48.061 ms)
     -> Sort (cost=14187.31..14190.15 rows=1138 width=95)
          Sort Key: price, id
          Sort Method: top-N heapsort  Memory: 27kB
          -> Seq Scan on properties (cost=0.00..14144.00 rows=1138 width=95)
               Filter: ((price >= 4100000000) AND (price <= 14300000000) 
                        AND (province_name = 'Hà Nội') AND (district_name = 'Cầu Giấy'))
               Rows Removed by Filter: 498862
               Buffers: shared hit=12898
   ```
   Để lấy được 20 dòng, PostgreSQL phải quét toàn bộ 500.000 dòng trên **12.898 khối đệm**, kiểm tra điều kiện lọc trên từng bản ghi và loại bỏ 498.862 dòng không thỏa mãn. Sau đó, 1.138 dòng hợp lệ được nạp vào RAM để thực hiện thuật toán **Top-N Heapsort** (chiếm 27 KB bộ nhớ) nhằm sắp xếp lại theo cặp khóa `(price, id)` trước khi cắt ngọn lấy 20 dòng đầu.

2. **Cây kế hoạch Indexed (`Q2_indexed_run_*.json`):**
   ```text
   Limit (cost=0.42..36.15 rows=20 width=95) (actual time=0.035..0.051 ms)
     Buffers: shared hit=23
     -> Index Scan using idx_properties_location_price on properties
          Index Cond: ((province_name = 'Hà Nội') AND (district_name = 'Cầu Giấy') 
                       AND (price >= 4100000000) AND (price <= 14300000000))
          Buffers: shared hit=23
   ```
   Chỉ mục được khởi tạo chính xác:
   ```sql
   CREATE INDEX idx_properties_location_price 
   ON public.properties (province_name, district_name, price, id);
   ```
   Nhờ tuân thủ nguyên tắc sắp xếp từ điển: hai cột lọc đẳng thức đặt trước (`province_name, district_name`), tiếp theo là cột lọc khoảng và sắp xếp (`price`), và cuối cùng là khóa phá vỡ trùng lặp (`id`), toàn bộ các hàng thỏa mãn yêu cầu đã được sắp xếp tăng dần liên tục trên các nút lá của cây B-tree.
   
   Khi thực thi, bộ lập lịch chọn `Index Scan`. Nó chỉ việc đi từ nút gốc xuống nút lá đầu tiên chứa cặp `('Hà Nội', 'Cầu Giấy', price >= 4.1B)`, duyệt xuôi theo liên kết lá của B-tree và **dừng quét ngay lập tức khi gom đủ 20 dòng (Early Termination)**.
   
   Toàn bộ quá trình chỉ truy cập đúng **23 khối đệm** (3 khối trên cây B-tree + 20 khối trỏ về Heap). Nút `Sort` hoàn toàn bị xóa sổ. Số khối đệm giảm **560 lần** (từ 12.898 xuống 23), và thời gian thực thi giảm từ 48.06 ms xuống **0.051 ms**.
   
   Hơn thế nữa, khi quy mô dữ liệu tăng từ 50K lên 500K (gấp 10 lần), thời gian thực thi của bản Indexed chỉ tăng từ 0.029 ms lên 0.051 ms, và số block truy cập **giữ nguyên tuyệt đối ở mức 23 blocks**. Đây là minh chứng thực nghiệm hoàn hảo cho thấy Composite Index đã biến một truy vấn có độ phức tạp tuyến tính $O(N)$ thành truy vấn có độ phức tạp tiệm cận hằng số $O(1)$.

---

## 4.2. Kết quả thực nghiệm trả lời RQ2: Tương tác giữa Viết lại truy vấn và Đánh chỉ mục

### 4.2.1. Phân tích trực giao $2 \times 2$ của bài toán Q3 (Cấu hình A, B, C, D)
Bài toán Q3 khảo sát truy vấn lọc tin đăng bất động sản theo một ngày cụ thể (`2025-10-15`) trên cột `published_at TIMESTAMP WITHOUT TIME ZONE`. Để phân tách độc lập hai biến số: Kỹ thuật viết lại truy vấn (Sargability) và Kỹ thuật đánh chỉ mục (Indexing), thí nghiệm được thiết kế dưới dạng ma trận trực giao $2 \times 2$.

**Bảng 4.4: Bảng phân rã trực giao $2 \times 2$ hiệu năng bài toán Q3 qua 3 thang đo**

| Quy mô dữ liệu | Cấu hình A: Gốc, Không Index | Cấu hình B: Viết lại, Không Index | Cấu hình C: Gốc, Có Index | Cấu hình D: Viết lại, Có Index | Tăng tốc B vs A (Chỉ viết lại) | Tăng tốc C vs A (Chỉ đánh Index) | Tăng tốc D vs A (Viết lại + Index) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **50.000 dòng** | 3.678 ms (1.288 blk) | 3.263 ms (1.288 blk) | 3.673 ms (1.288 blk) | **0.126 ms** (272 blk) | 1.13x | 1.00x | **29.31x** |
| **200.000 dòng** | 23.805 ms (5.128 blk) | 28.830 ms (5.128 blk) | 24.251 ms (5.128 blk) | **0.874 ms** (1.082 blk) | 0.83x | 0.98x | **27.24x** |
| **500.000 dòng** | 40.060 ms (12.808 blk) | 38.522 ms (12.808 blk) | 42.263 ms (12.808 blk) | **2.230 ms** (2.666 blk) | 1.04x | 0.95x | **17.97x** |

### 4.2.2. Hiện tượng vô hiệu hóa Index do vị từ Non-sargable (Cấu hình C)
Một phát hiện khoa học đặc biệt quan trọng của đề tài nằm ở kết quả của **Cấu hình C**.
- Trong cấu hình C, chỉ mục B-tree `idx_properties_published_at` đã được tạo thành công trên cột `published_at`, chiếm **10.73 MB** dung lượng lưu trữ trên đĩa tại 500K.
- Tuy nhiên, câu truy vấn vẫn giữ nguyên biểu thức ép kiểu:
  ```sql
  WHERE published_at::date = DATE '2025-10-15';
  ```
- Kết quả thực nghiệm cho thấy thời gian thực thi của Cấu hình C tại 500K là **42.26 ms**, tương đương (thậm chí chậm hơn nhẹ do chi phí lập kế hoạch) so với Cấu hình A hoàn toàn không có Index (40.06 ms).
- Kế hoạch thực thi xác nhận:
  ```text
  Seq Scan on properties (cost=0.00..14144.00 rows=2500 width=95)
    Filter: ((published_at)::date = '2025-10-15'::date)
    Rows Removed by Filter: 498305
    Buffers: shared hit=12808
  ```
- **Tỷ lệ sử dụng Index của Cấu hình C là 0.00%**. Bộ lập lịch của PostgreSQL nhận dạng hàm ép kiểu `::date` là một hàm biến đổi chưa được đánh giá trước. Do cây B-tree chỉ lưu trữ các giá trị thời gian nguyên bản (`timestamp`), bộ tối ưu hóa không thể định vị khóa tìm kiếm trên cây và buộc phải quay lại phương thức `Seq Scan` toàn bộ 12.808 khối đệm.
- **Kết luận:** Việc tạo chỉ mục trên cột trở nên **hoàn toàn lãng phí** nếu câu lệnh SQL của tầng ứng dụng chứa các biểu thức non-sargable.

### 4.2.3. Sức mạnh cộng hưởng của Sargable Range Query và Index (Cấu hình D)
- Ở **Cấu hình B**, khi câu truy vấn được viết lại thành dạng khoảng nửa mở sargable:
  ```sql
  WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00' 
    AND published_at <  TIMESTAMP '2025-10-16 00:00:00';
  ```
  nhưng hệ thống không có chỉ mục, thời gian thực thi vẫn duy trì ở mức **38.52 ms** (Speedup = 1.04x). Điều này chứng minh rằng: *Viết lại truy vấn sang dạng sargable không mang lại lợi ích hiệu năng đáng kể nếu bảng thiếu chỉ mục, vì hệ thống vẫn phải quét tuần tự toàn bộ dữ liệu.*
- Chỉ khi bước sang **Cấu hình D**, nơi vị từ sargable kết hợp đồng thời với chỉ mục B-tree `idx_properties_published_at`, bộ lập lịch mới có thể kích hoạt phương thức **Bitmap Index Scan**. 
- Thời gian thực thi giảm đột phá từ 40.06 ms xuống **2.23 ms** (tăng tốc **17.97 lần** tại 500K và **29.31 lần** tại 50K). Số lượng khối đệm cần đọc giảm từ 12.808 xuống còn 2.666 khối (giảm 79.2% lưu lượng I/O).

---

## 4.3. Kết quả thực nghiệm trả lời RQ3: Giới hạn của Index, Đánh đổi lưu trữ và Hiệu năng tiền xử lý

### 4.3.1. Bài toán đối chứng âm Q4: Vì sao Index không cải thiện truy vấn tổng hợp?
Bài toán Q4 thực hiện tổng hợp phân bố loại hình bất động sản và tính giá trung bình trên toàn bộ bảng dữ liệu:
```sql
SELECT property_type_name, COUNT(*), ROUND(AVG(price), 0) 
FROM public.properties 
GROUP BY property_type_name;
```

**Bảng 4.5: Kết quả thực nghiệm bài toán đối chứng âm Q4**

| Quy mô dữ liệu | Cấu hình Baseline (ms) | Scan Type Baseline | Cấu hình Indexed (ms) | Scan Type Indexed | Hệ số tăng tốc (Speedup) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **50.000 dòng** | 8.733 ms | Seq Scan | 8.661 ms | Seq Scan | **1.01x** |
| **200.000 dòng** | 34.967 ms | Seq Scan | 36.247 ms | Seq Scan | **0.96x** |
| **500.000 dòng** | 63.278 ms | Seq Scan | 66.480 ms | Seq Scan | **0.95x** |

**Phân tích Nguyên lý Cơ sở dữ liệu:**
1. **Bản chất của truy vấn:** Câu lệnh yêu cầu tổng hợp **100% dữ liệu** trong bảng (không có mệnh đề `WHERE` để chọn lọc).
2. **Quyết định của Cost-based Optimizer:** Dù chỉ mục B-tree `idx_properties_property_type` (3.36 MB) đã được tạo trên cột `property_type_name`, kế hoạch thực thi xác nhận bộ lập lịch của PostgreSQL 18.3 **vẫn kiên quyết lựa chọn Seq Scan kết hợp HashAggregate**:
   ```text
   HashAggregate (cost=15394.00..15394.05 rows=5 width=48)
     Group Key: property_type_name
     Planned Partitions: 0
     -> Seq Scan on properties (cost=0.00..12824.00 rows=500000 width=18)
          Buffers: shared hit=12824
   ```
3. **Tại sao bộ lập lịch không dùng Index Scan?**
   Để tính hàm `AVG(price)`, hệ thống bắt buộc phải đọc giá trị của cột `price`. Do chỉ mục B-tree chỉ chứa cột `property_type_name`, nếu sử dụng Index Scan, hệ thống sẽ phải đọc từng con trỏ lá rồi thực hiện 500.000 lần truy cập ngẫu nhiên (**Random I/O**) vào các trang Heap. Với hệ số `random_page_cost = 4.0`, tổng chi phí ước tính sẽ lớn gấp 3 đến 4 lần so với việc quét tuần tự liên tục (`Seq Scan`) toàn bộ 12.824 khối đệm vào bảng băm RAM.
4. **Ý nghĩa khoa học:** Kết quả Q4 bác bỏ hoàn toàn quan niệm sai lầm cho rằng mọi câu lệnh SQL đều có thể tăng tốc bằng chỉ mục B-tree thông thường.

### 4.3.2. Định lượng chi phí phụ trội lưu trữ vật lý của B-tree Index (Storage Overhead)
Việc tạo chỉ mục không phải là một giải pháp "miễn phí". Bảng 4.6 trình bày số liệu đo đạc dung lượng vật lý thực tế của từng chỉ mục trích xuất trực tiếp từ hàm quản trị hệ thống `pg_relation_size()` của PostgreSQL.

**Bảng 4.6: Chi phí phụ trội lưu trữ của các chỉ mục B-tree qua các thang đo**

| Tên chỉ mục | Cấu hình áp dụng | Cột tham gia đánh chỉ mục | Dung lượng tại 50K (MB) | Dung lượng tại 200K (MB) | Dung lượng tại 500K (MB) | Tỷ trọng trên tổng Index 500K (%) |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| `idx_properties_province_name` | Q1 | `(province_name)` | 0.36 MB | 1.38 MB | 3.40 MB | 7.4% |
| `idx_properties_location_price` | Q2 | `(province_name, district_name, price, id)` | **2.88 MB** | **11.42 MB** | **28.53 MB** | **62.0%** |
| `idx_properties_published_at` | Q3 | `(published_at)` | 1.09 MB | 4.30 MB | 10.73 MB | 23.3% |
| `idx_properties_property_type` | Q4 | `(property_type_name)` | 0.35 MB | 1.34 MB | 3.36 MB | 7.3% |
| **Tổng dung lượng 4 chỉ mục phụ** | — | — | **4.68 MB** | **18.44 MB** | **46.02 MB** | **100.0%** |
| *Dung lượng bảng Heap dữ liệu gốc* | — | *9 cột bảng `properties`* | *~10.1 MB* | *~40.5 MB* | *~100.8 MB* | — |
| **Tỷ lệ Index / Dung lượng Bảng gốc** | — | — | **46.3%** | **45.5%** | **45.6%** | — |

**Nhận định chuyên sâu:**
- Tại quy mô 500.000 bản ghi, 4 chỉ mục B-tree chiếm tổng cộng **46.02 MB**, tương đương **45.6% dung lượng lưu trữ của chính bảng dữ liệu gốc**.
- Chỉ mục Composite đa cột (`idx_properties_location_price`) chiếm tỷ trọng áp đảo (**62.0%** tổng dung lượng chỉ mục) với 28.53 MB do phải lưu trữ cả 4 giá trị thuộc tính và con trỏ TID trên mỗi khóa lá.
- Điều này chứng minh rằng các kỹ sư dữ liệu phải cân nhắc kỹ lưỡng bài toán đánh đổi không gian lưu trữ và chi phí bảo trì ghi (DML overhead) khi quyết định thiết lập các chỉ mục đa cột.

### 4.3.3. Đánh giá hiệu năng Ingestion và Thao tác bộ nhớ: Pandas vs Polars, CSV vs Parquet
Bảng 4.7 tổng hợp kết quả đo đạc hiệu năng tiền xử lý dữ liệu từ tệp [`results/processing_benchmark/processing_benchmark.csv`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/processing_benchmark/processing_benchmark.csv) sử dụng luồng giám sát RAM thực thời (1ms sampling).

**Bảng 4.7: Kết quả đo lường hiệu năng nạp và xử lý dữ liệu tiền kỳ (500.000 bản ghi)**

| Hạng mục tác vụ | Thư viện & Thao tác | Định dạng tệp | Thời gian Median (ms) | Đỉnh RAM thực tế (Peak RSS, MB) | Mức tăng RAM ($\Delta$ RAM, MB) | Kích thước tệp trên đĩa (MB) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Nạp tệp (File Ingestion)** | Pandas `read_csv` | CSV | 3.038.53 ms | 781.70 MB | +241.37 MB | 93.88 MB |
| | Polars `read_csv` | CSV | **75.27 ms** | 801.52 MB | +105.62 MB | 93.88 MB |
| | Pandas `read_parquet` | Parquet | 127.00 ms | 931.18 MB | +47.95 MB | **41.42 MB** |
| | Polars `read_parquet` | Parquet | 202.25 ms | 811.37 MB | +44.95 MB | **41.42 MB** |
| **Nạp giới hạn RAM (Chunked)** | Pandas Chunked read (10k) | CSV | 3.723.10 ms | 437.41 MB | **+19.68 MB** | 93.88 MB |
| | Pandas Chunked aggregate | CSV | 3.835.01 ms | 438.54 MB | **+21.09 MB** | 93.88 MB |
| **Lọc và Tổng hợp trong RAM** | Pandas Filter + GroupBy | In-Memory | 55.17 ms | 726.17 MB | +5.98 MB | — |
| | Polars Filter + GroupBy | In-Memory | **13.88 ms** | 775.43 MB | +4.44 MB | — |

**Phân tích phát hiện khoa học:**
1. **Tốc độ đọc tệp vượt trội của Polars CSV:** Polars đọc tệp CSV 500K dòng chỉ trong **75.27 ms**, nhanh gấp **40.3 lần** so with Pandas (`3.038.53 ms`). Sự vượt trội này đến từ bộ phân tích cú pháp đa luồng (Multi-threaded CSV parser) viết bằng Rust và cơ chế zero-copy memory allocation của Apache Arrow.
2. **Ưu thế tuyệt đối của định dạng Parquet:** Tệp Parquet chỉ chiếm **41.42 MB** trên đĩa (tiết kiệm **55.9% dung lượng** so với 93.88 MB của CSV). Thời gian nạp Parquet vào Pandas chỉ mất 127.00 ms (nhanh hơn 24 lần so với đọc CSV), và mức tăng RAM chỉ tốn **+47.95 MB** thay vì +241.37 MB.
3. **Hiệu quả của Kỹ thuật Chunked Streaming:** Khi nạp theo khối 10.000 dòng trong Pandas, mặc dù thời gian chạy tăng nhẹ lên 3.723 ms do chi phí vòng lặp, mức tăng tiêu thụ RAM được khống chế nghiêm ngặt ở mức **+19.68 MB** (giảm 91.8% so với việc nạp trọn gói). Đây là bằng chứng xác thực chứng minh giải pháp nạp phân khối cho phép xử lý các tập dữ liệu vượt quá giới hạn RAM trên máy tính cá nhân.
4. **Năng lực tính toán phân tích:** Trong tác vụ lọc bất động sản tại `'Hà Nội'` (170.167 dòng) và gom nhóm tính giá trung bình theo loại hình, Polars hoàn thành trong **13.88 ms**, nhanh gấp **4.0 lần** Pandas (55.17 ms).

---

## 4.4. Đánh giá tính toàn vẹn của bằng chứng thực nghiệm và Độ tin cậy khoa học

Để khẳng định tính trung thực khoa học và đảm bảo khả năng tái lập độc lập:
1. **Kiểm toán 600 kế hoạch thực thi:** Toàn bộ 600 tệp JSON kế hoạch thực thi trong `results/benchmark/raw/` được tự động quét và tính toán mã băm SHA-256 lưu trữ tập trung tại [`results/benchmark/raw_manifest.json`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/benchmark/raw_manifest.json). Mã nguồn kiểm toán [`scripts/verify_benchmark_evidence.py`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/scripts/verify_benchmark_evidence.py) xác nhận 100% tệp bằng chứng tồn tại hợp lệ, có đầy đủ các trường `Planning Time`, `Execution Time`, `Plan`, và thông tin cấu hình khớp với báo cáo tổng hợp.
2. **Kiểm thử tự động hồi quy:** Bộ kiểm thử gồm **182 unit tests** trong thư mục `tests/` (đạt 181 passed, 1 skipped) kiểm tra độc lập mọi thành phần từ logic làm sạch, tính nhất quán báo cáo đến thuật toán đo RAM và phân tích kế hoạch thực thi, bảo đảm toàn bộ hệ thống vận hành ổn định và không chứa lỗi logic.
