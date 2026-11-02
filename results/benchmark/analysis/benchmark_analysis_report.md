# Báo Cáo Phân Tích Thực Nghiệm Tối Ưu Hiệu Năng PostgreSQL

## 1. Tổng quan thí nghiệm

- **Hệ quản trị CSDL:** PostgreSQL 17/18
- **Quy mô dữ liệu kiểm thử:** 50,000, 200,000, 500,000 bản ghi
- **Chính sách đo lường:** Warm-up 3 lần + 20 lần đo tuần tự, lấy **Median Execution Time** làm chỉ số trọng tâm.
- **Số cấu hình kiểm thử:** 10 cấu hình độc lập (Q1: 2, Q2: 2, Q3: 4, Q4: 2).

---

## 2. Bảng kết quả tổng hợp chi tiết

| Scale | Config ID | Query | Scan Type | Index Used | Index (MB) | Median Exec (ms) | IQR (ms) | Speedup | Shared Hit Blk |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| 50,000 | `Q1_baseline` | Q1 | Seq Scan | None | 0.00 | 2.648 | 0.095 | **1.00x** | 1288 |
| 50,000 | `Q1_indexed` | Q1 | Bitmap Scan | idx_properties_province_name | 0.36 | 0.323 | 0.067 | **8.21x** | 704 |
| 50,000 | `Q2_baseline` | Q2 | Seq Scan | None | 0.00 | 4.954 | 0.500 | **1.00x** | 1288 |
| 50,000 | `Q2_indexed` | Q2 | Index Scan | idx_properties_location_price | 2.88 | 0.029 | 0.013 | **170.81x** | 23 |
| 50,000 | `Q3_A` | Q3 | Seq Scan | None | 0.00 | 3.678 | 0.088 | **1.00x** | 1288 |
| 50,000 | `Q3_B` | Q3 | Seq Scan | None | 0.00 | 3.263 | 0.248 | **1.13x** | 1288 |
| 50,000 | `Q3_C` | Q3 | Seq Scan | None | 1.09 | 3.673 | 0.087 | **1.00x** | 1288 |
| 50,000 | `Q3_D` | Q3 | Bitmap Scan | idx_properties_published_at | 1.09 | 0.126 | 0.026 | **29.31x** | 272 |
| 50,000 | `Q4_baseline` | Q4 | Seq Scan | None | 0.00 | 8.732 | 0.496 | **1.00x** | 1288 |
| 50,000 | `Q4_indexed` | Q4 | Seq Scan | None | 0.35 | 8.661 | 0.458 | **1.01x** | 1288 |
| 200,000 | `Q1_baseline` | Q1 | Seq Scan | None | 0.00 | 16.959 | 3.647 | **1.00x** | 5128 |
| 200,000 | `Q1_indexed` | Q1 | Bitmap Scan | idx_properties_province_name | 1.38 | 2.860 | 0.927 | **5.93x** | 2909 |
| 200,000 | `Q2_baseline` | Q2 | Seq Scan | None | 0.00 | 28.375 | 59.029 | **1.00x** | 5218 |
| 200,000 | `Q2_indexed` | Q2 | Index Scan | idx_properties_location_price | 11.42 | 0.040 | 0.023 | **718.35x** | 23 |
| 200,000 | `Q3_A` | Q3 | Seq Scan | None | 0.00 | 23.805 | 1.945 | **1.00x** | 5128 |
| 200,000 | `Q3_B` | Q3 | Seq Scan | None | 0.00 | 28.829 | 107.282 | **0.83x** | 5128 |
| 200,000 | `Q3_C` | Q3 | Seq Scan | None | 4.30 | 24.250 | 3.466 | **0.98x** | 5128 |
| 200,000 | `Q3_D` | Q3 | Bitmap Scan | idx_properties_published_at | 4.30 | 0.874 | 0.406 | **27.24x** | 1082 |
| 200,000 | `Q4_baseline` | Q4 | Seq Scan | None | 0.00 | 34.967 | 53.309 | **1.00x** | 5144 |
| 200,000 | `Q4_indexed` | Q4 | Seq Scan | None | 1.34 | 36.246 | 53.717 | **0.96x** | 5144 |
| 500,000 | `Q1_baseline` | Q1 | Seq Scan | None | 0.00 | 36.599 | 3.043 | **1.00x** | 12808 |
| 500,000 | `Q1_indexed` | Q1 | Bitmap Scan | idx_properties_province_name | 3.40 | 9.059 | 3.008 | **4.04x** | 7236 |
| 500,000 | `Q2_baseline` | Q2 | Seq Scan | None | 0.00 | 48.061 | 4.367 | **1.00x** | 12898 |
| 500,000 | `Q2_indexed` | Q2 | Index Scan | idx_properties_location_price | 28.53 | 0.051 | 0.047 | **942.37x** | 23 |
| 500,000 | `Q3_A` | Q3 | Seq Scan | None | 0.00 | 40.060 | 6.133 | **1.00x** | 12808 |
| 500,000 | `Q3_B` | Q3 | Seq Scan | None | 0.00 | 38.522 | 2.160 | **1.04x** | 12808 |
| 500,000 | `Q3_C` | Q3 | Seq Scan | None | 10.73 | 42.263 | 5.978 | **0.95x** | 12808 |
| 500,000 | `Q3_D` | Q3 | Bitmap Scan | idx_properties_published_at | 10.73 | 2.229 | 1.044 | **17.97x** | 2666 |
| 500,000 | `Q4_baseline` | Q4 | Seq Scan | None | 0.00 | 63.278 | 3.097 | **1.00x** | 12824 |
| 500,000 | `Q4_indexed` | Q4 | Seq Scan | None | 3.36 | 66.480 | 4.542 | **0.95x** | 12824 |

---

## 3. Phân tích chi tiết từng bài toán tối ưu

### 3.1. Q1 — Single-column Index (Tìm theo tỉnh/thành phố)

- **Truy vấn:** Lọc các bất động sản tại `'Hải Phòng'`.
- **Cơ chế:**
  - *Baseline:* Thực hiện `Seq Scan` toàn bộ bảng `public.properties`. Chi phí và thời gian thực thi tăng tuyến tính theo số lượng bản ghi.
  - *Indexed (`idx_properties_province_name`):* PostgreSQL chuyển sang `Bitmap Heap Scan` hoặc `Index Scan`. Chỉ cần đọc các block chứa con trỏ hàng tương ứng.
- **Đánh giá hiệu năng:**
  - **50,000 dòng:** Baseline `2.65 ms` -> Indexed `0.32 ms` (Speedup: **8.21x**, Dung lượng Index: `0.36 MB`).
  - **200,000 dòng:** Baseline `16.96 ms` -> Indexed `2.86 ms` (Speedup: **5.93x**, Dung lượng Index: `1.38 MB`).
  - **500,000 dòng:** Baseline `36.60 ms` -> Indexed `9.06 ms` (Speedup: **4.04x**, Dung lượng Index: `3.40 MB`).

### 3.2. Q2 — Composite Index (Bộ lọc kết hợp vị trí, khoảng giá, sắp xếp và LIMIT)

- **Truy vấn:** Tìm 20 BĐS giá thấp nhất tại Hà Nội, Cầu Giấy trong khoảng 4.1 tỷ - 14.3 tỷ.
- **Cơ chế:**
  - *Baseline:* Phải quét toàn bộ bảng (`Seq Scan`), lọc các dòng thỏa mãn, sau đó sắp xếp trong bộ nhớ (`Sort` top-N heapsort) rồi lấy 20 dòng đầu.
  - *Indexed (`idx_properties_location_price`):* Index bao phủ thứ tự `(province_name, district_name, price, id)`. Planner sử dụng `Index Scan` duyệt trực tiếp cây B-tree theo đúng thứ tự sắp xếp và **dừng ngay khi đủ 20 dòng (early exit)**.
- **Đánh giá hiệu năng:** Tốc độ tăng vượt bậc (thường đạt hàng chục đến hàng trăm lần) do triệt tiêu hoàn toàn chi phí quét bảng và chi phí sắp xếp.
  - **50,000 dòng:** Baseline `4.95 ms` -> Indexed `0.03 ms` (Speedup: **170.81x**).
  - **200,000 dòng:** Baseline `28.38 ms` -> Indexed `0.04 ms` (Speedup: **718.35x**).
  - **500,000 dòng:** Baseline `48.06 ms` -> Indexed `0.05 ms` (Speedup: **942.37x**).

### 3.3. Q3 — Tác động độc lập của Query Rewriting và Indexing (Sargability)

- **Thực nghiệm 4 cấu hình:**
  - **A (Original, No Index):** `WHERE published_at::date = DATE '2025-10-15'` -> `Seq Scan`.
  - **B (Rewritten, No Index):** `WHERE published_at >= TIMESTAMP '...' AND published_at < TIMESTAMP '...'` -> `Seq Scan`. Viết lại query khi không có Index không làm giảm thời gian quét bảng đáng kể.
  - **C (Original, With Index):** Giữ nguyên hàm ép kiểu `::date`. Dù có Index `idx_properties_published_at`, B-tree index **KHÔNG THỂ SỬ DỤNG** do biểu thức áp dụng trên cột (non-sargable predicate). Planner buộc phải `Seq Scan`.
  - **D (Rewritten, With Index):** Khoảng thời gian nửa mở giúp biểu thức trở thành sargable predicate. Planner lập tức chuyển sang `Bitmap Index Scan` / `Index Scan`, đem lại tốc độ tối đa.
- **Bảng phân rã hiệu năng Q3:**

| Scale | A: Orig NoIdx | B: Rewrite NoIdx | C: Orig WithIdx | D: Rewrite WithIdx | Speedup B vs A | Speedup C vs A | Speedup D vs A |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 50,000 | 3.68 ms | 3.26 ms | 3.67 ms | 0.13 ms | 1.13x | 1.00x | **29.31x** |
| 200,000 | 23.80 ms | 28.83 ms | 24.25 ms | 0.87 ms | 0.83x | 0.98x | **27.24x** |
| 500,000 | 40.06 ms | 38.52 ms | 42.26 ms | 2.23 ms | 1.04x | 0.95x | **17.97x** |

### 3.4. Q4 — Aggregation Control (Trường hợp đối chứng - Index không cải thiện)

- **Truy vấn:** `GROUP BY property_type_name, COUNT(*), ROUND(AVG(price), 0)`.
- **Cơ chế:**
  - Truy vấn yêu cầu tổng hợp **toàn bộ dữ liệu trong bảng**.
  - Ngay cả khi tạo Index trên `property_type_name`, để tính `AVG(price)`, PostgreSQL vẫn cần truy cập toàn bộ các hàng trong bảng để đọc cột `price`.
  - Việc duyệt qua Index sau đó đọc từng dòng Heap ngẫu nhiên (Random I/O) kém hiệu quả hơn nhiều so với việc quét tuần tự toàn bảng (`Seq Scan`) kết hợp giải thuật gom nhóm băm (`HashAggregate`).
- **Kết luận quan trọng:** Index không phải lúc nào cũng nhanh hơn. Với truy vấn aggregate toàn bảng không có WHERE chọn lọc, Index B-tree đơn cột không mang lại lợi ích và planner thường bỏ qua hoặc nếu dùng sẽ gây suy giảm hiệu năng.
  - **50,000 dòng:** Baseline `8.73 ms` (Seq Scan) vs Indexed `8.66 ms` (Seq Scan) -> Speedup: **1.01x**.
  - **200,000 dòng:** Baseline `34.97 ms` (Seq Scan) vs Indexed `36.25 ms` (Seq Scan) -> Speedup: **0.96x**.
  - **500,000 dòng:** Baseline `63.28 ms` (Seq Scan) vs Indexed `66.48 ms` (Seq Scan) -> Speedup: **0.95x**.

---

## 4. Phân tích chi phí lưu trữ (Storage Overhead)

| Index Name | Áp dụng cho | Cột | Dung lượng tại 50K | Dung lượng tại 200K | Dung lượng tại 500K |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `idx_properties_province_name` | Q1 | `(province_name)` | 0.36 MB | 1.38 MB | 3.40 MB |
| `idx_properties_location_price` | Q2 | `(province_name, district_name, price, id)` | 2.88 MB | 11.42 MB | 28.53 MB |
| `idx_properties_published_at` | Q3 | `(published_at)` | 1.09 MB | 4.30 MB | 10.73 MB |
| `idx_properties_property_type` | Q4 | `(property_type_name)` | 0.35 MB | 1.34 MB | 3.36 MB |

---

## 5. Kết luận khoa học và khuyến nghị

1. **Tối ưu B-tree đơn cột (Q1):** Rất hiệu quả cho các trường có tính chọn lọc cao hoặc vừa phải (`province_name`). Giảm số lượng block cần đọc qua bộ đệm.
2. **Tối ưu Composite Index (Q2):** Đạt hiệu quả cao nhất khi kết hợp lọc khoảng và sắp xếp + LIMIT. Cần sắp xếp thứ tự cột trong Index: `(equality_col_1, equality_col_2, range_or_sort_col)` để tận dụng tối đa chỉ mục.
3. **Viết lại truy vấn (Q3):** Index chỉ phát huy tác dụng khi vị từ là sargable. Tránh tuyệt đối việc áp dụng hàm hoặc ép kiểu trực tiếp trên cột được đánh chỉ mục trong mệnh đề `WHERE`.
4. **Kiểm soát tổng hợp (Q4):** Tránh lạm dụng index cho các truy vấn aggregate toàn bảng. Cần cân nhắc Materialized Views hoặc thống kê định kỳ thay vì chỉ mục B-tree thông thường.
