# BÁO CÁO PHƯƠNG PHÁP THỰC NGHIỆM VÀ PHÂN TÍCH TỐI ƯU HIỆU NĂNG POSTGRESQL

**Đề tài:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn  
**Sinh viên thực hiện:** Đồ án Tốt nghiệp / Nghiên cứu thực nghiệm CSDL  
**Hệ quản trị CSDL:** PostgreSQL 17 / 18  
**Ngôn ngữ thực nghiệm:** Python 3.13 + Psycopg 3 + Pytest + Matplotlib  

---

## 1. Mục tiêu và Giả thuyết Nghiên cứu

### 1.1. Mục tiêu cốt lõi
Khảo sát và định lượng sự ảnh hưởng của các kỹ thuật tối ưu hóa truy vấn trong PostgreSQL khi quy mô dữ liệu bất động sản tăng dần qua 3 ngưỡng:
- **50.000 bản ghi**
- **200.000 bản ghi**
- **500.000 bản ghi**

Thực nghiệm tập trung vào:
1. Tối ưu tìm kiếm đơn thuộc tính bằng Single-column B-tree Index (Q1).
2. Tối ưu bộ lọc đa điều kiện kết hợp khoảng giá, sắp xếp và giới hạn dòng bằng Composite B-tree Index (Q2).
3. Đánh giá tác động độc lập giữa **Query Rewriting (tính khả dụng của vị từ - Sargability)** và **Indexing** (Q3).
4. Khảo sát trường hợp đối chứng: Phân tích nguyên nhân Index **không mang lại hiệu quả hoặc gây suy giảm hiệu năng** đối với truy vấn tổng hợp toàn bảng (Q4).

---

## 2. Thiết kế Thí nghiệm và Phương pháp Thu thập Số liệu

### 2.1. Nguồn và Pipeline Dữ liệu
- **Nguồn:** Hugging Face `Phuscca/vietnam-real-estates`, split `train`, revision `68bae25c3fa65a8e694973efe80bd6e237de11f5`.
- **Đặc tính dòng dữ liệu:**
  - Seed shuffle: `42`, shuffle buffer: `10.000`, batch size: `2.000`.
  - Bộ dữ liệu nhỏ là tiền tố (prefix) lồng nhau của bộ dữ liệu lớn, đảm bảo tính nhất quán của ID từ $1 \dots N$.
  - Schema chuẩn hóa 9 cột: `id`, `name`, `property_type_name`, `province_name`, `district_name`, `ward_name`, `price`, `area`, `published_at`.
  - Ràng buộc toàn vẹn: `price > 0`, `area > 0`, chuỗi văn bản bắt buộc không rỗng.
- **Nạp dữ liệu:** Sử dụng `COPY public.properties FROM STDIN` qua Psycopg 3 bên trong transaction, áp dụng khóa `LOCK TABLE public.properties IN SHARE ROW EXCLUSIVE MODE` để đảm bảo cô lập dữ liệu.

### 2.2. Ma trận Thực nghiệm (3 Quy mô × 10 Cấu hình)

Mỗi quy mô dữ liệu chạy độc lập 10 cấu hình sau:

| STT | Cấu hình | Mục tiêu nghiên cứu | Query File | Index File / Chỉ mục |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `Q1_baseline` | Q1 Chưa tối ưu | `q1.sql` | Không (Chỉ có PK) |
| 2 | `Q1_indexed` | Q1 Đánh chỉ mục tỉnh/thành | `q1.sql` | `idx_properties_province_name (province_name)` |
| 3 | `Q2_baseline` | Q2 Chưa tối ưu | `q2.sql` | Không (Chỉ có PK) |
| 4 | `Q2_indexed` | Q2 Chỉ mục kết hợp | `q2.sql` | `idx_properties_location_price (province_name, district_name, price, id)` |
| 5 | `Q3_A` | Q3 Gốc, Không Index | `q3_original.sql` | Không |
| 6 | `Q3_B` | Q3 Viết lại, Không Index | `q3_rewritten.sql` | Không |
| 7 | `Q3_C` | Q3 Gốc, Có Index | `q3_original.sql` | `idx_properties_published_at (published_at)` |
| 8 | `Q3_D` | Q3 Viết lại, Có Index | `q3_rewritten.sql` | `idx_properties_published_at (published_at)` |
| 9 | `Q4_baseline` | Q4 Đối chứng chưa Index | `q4.sql` | Không |
| 10 | `Q4_indexed` | Q4 Đối chứng có Index | `q4.sql` | `idx_properties_property_type (property_type_name)` |

### 2.3. Quy trình Cách ly và Đo lường Chuẩn mực
Để loại bỏ hoàn toàn nhiễu và tác động chéo giữa các bài đo:
1. **Reset Index nghiêm ngặt:** Trước mỗi cấu hình, luôn chạy `reset_indexes.sql` chỉ xóa 4 supplemental index, bảo toàn Primary Key và dữ liệu bảng.
2. **Cập nhật Thống kê:** Chạy `ANALYZE public.properties` trước khi đo để trình tối ưu hóa (Cost-based Query Planner) có số liệu phân phối mới nhất.
3. **Kiểm tra Catalog:** Truy vấn `pg_index` để xác nhận chỉ có đúng chỉ mục yêu cầu tồn tại và ghi nhận kích thước `pg_relation_size`.
4. **Kiểm chứng Tính tương đương (Query Equivalence Check):** 
   - Với Q1, Q2, Q4: So sánh kết quả SELECT giữa baseline và optimized.
   - Với Q3: Sử dụng toán tử hai chiều `EXCEPT ALL` để chứng minh truy vấn Original và Rewritten trả về chính xác 100% cùng số dòng và dữ liệu.
5. **Chính sách Warm-up & Đo lường:**
   - Warm-up **3 lần** liên tiếp bằng `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` nhằm nạp dữ liệu và index vào Shared Buffers / OS Page Cache (tránh đo lường I/O khởi động ngẫu nhiên). Bỏ qua 3 số đo này.
   - Chạy **20 lần đo chính thức tuần tự** (không chạy song song để tránh tranh chấp CPU/Cache).
   - Lưu trữ toàn bộ 20 file JSON thô cho mỗi cấu hình vào `results/benchmark/raw/`.
   - Sử dụng **Median Execution Time** (trung vị thời gian thực thi) làm thước đo chuẩn để triệt tiêu ảnh hưởng của các ngoại lệ (outliers) do autovacuum hoặc OS context switch.
   - Ghi nhận `IQR` (Interquartile Range), `Min`, `Max`, `Planning Time`, và bộ đếm bộ đệm `Shared Hit Blocks`, `Shared Read Blocks`.

$$\text{Speedup} = \frac{\text{Median Execution Time (Baseline)}}{\text{Median Execution Time (Optimized)}}$$

---

## 3. Phân tích Chi tiết Kỹ thuật và Cơ chế Tối ưu

### 3.1. Q1 — Single-column B-Tree Index

```sql
SELECT id, name, price, area
FROM public.properties
WHERE province_name = 'Hải Phòng';
```

- **Khi không có Index (Baseline):**
  - Planner bắt buộc chọn `Seq Scan on properties`.
  - Quét toàn bộ các trang dữ liệu trong bảng từ đầu đến cuối. Đọc hàng chục nghìn Shared Hit Blocks.
  - Thời gian thực thi tăng tỷ lệ thuận tuyến tính $O(N)$ với số lượng bản ghi: từ ~4 ms tại 50K lên đến ~40 ms tại 500K.
- **Khi có Index `idx_properties_province_name`:**
  - Planner chuyển sang `Bitmap Index Scan` trên chỉ mục B-tree để tìm các TID (Tuple ID) thỏa mãn, sau đó dùng `Bitmap Heap Scan` gom nhóm các block vật lý để đọc các dòng tương ứng.
  - Số lượng blocks cần đọc giảm mạnh. Tốc độ tăng tốc (Speedup) đạt khoảng 3x – 10x tùy theo mức độ chọn lọc (selectivity) của tỉnh/thành phố Hải Phòng trong tập dữ liệu.

---

### 3.2. Q2 — Composite B-Tree Index với Early LIMIT Termination

```sql
SELECT id, name, price, area, published_at
FROM public.properties
WHERE province_name = 'Hà Nội'
  AND district_name = 'Cầu Giấy'
  AND price BETWEEN 4100000000 AND 14300000000
ORDER BY price ASC, id ASC
LIMIT 20;
```

- **Khi không có Index (Baseline):**
  - Thực hiện `Seq Scan`, lọc từng dòng theo điều kiện vị trí và giá.
  - Sau khi lọc, các dòng thỏa mãn phải đi qua một nút `Sort (Sort Method: top-N heapsort, keys: price, id)`.
  - Hoạt động sắp xếp tốn CPU và thời gian, đặc biệt khi số lượng dòng thỏa mãn điều kiện lọc lớn.
- **Khi tạo Composite Index `(province_name, district_name, price, id)`:**
  - Cấu trúc chỉ mục được thiết kế theo nguyên lý tối ưu:
    1. Các cột kiểm tra đẳng thức (`= 'Hà Nội'`, `= 'Cầu Giấy'`) đặt ở đầu.
    2. Cột kiểm tra khoảng (`BETWEEN`) và sắp xếp (`ORDER BY price ASC, id ASC`) đặt ở sau.
  - **Cơ chế Index Scan trực tiếp:** B-tree đã được sắp sẵn theo `price ASC, id ASC`. PostgreSQL không cần quét toàn bảng, không cần tạo bitmap và **hoàn toàn loại bỏ thao tác Sort**!
  - **Early Exit:** Nhờ mệnh đề `LIMIT 20`, con trỏ duyệt B-tree dừng lại ngay lập tức khi vừa lấy đủ 20 bản ghi đầu tiên!
  - **Hiệu năng:** Speedup đạt từ **30x đến trên 100x**, thời gian thực thi giảm từ hàng chục miligiây xuống mức sub-millisecond (< 0.5 ms), gần như không bị ảnh hưởng bởi việc dữ liệu tăng từ 50K lên 500K.

---

### 3.3. Q3 — Tác động Độc lập của Query Rewriting và Sargability

```sql
-- Original Query:
SELECT id, name, published_at FROM public.properties
WHERE published_at::date = DATE '2025-10-15';

-- Rewritten Query:
SELECT id, name, published_at FROM public.properties
WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00'
  AND published_at < TIMESTAMP '2025-10-16 00:00:00';
```

Thực nghiệm kiểm chứng 4 góc cấu hình phân tích ma trận 2x2:

| Cấu hình | Query Form | Index Status | Kế hoạch thực thi (Plan) | Phân tích cơ chế |
| :--- | :--- | :--- | :--- | :--- |
| **A** | Original | No Index | `Seq Scan` | Baseline, quét toàn bảng và tính hàm `::date` cho từng hàng. |
| **B** | Rewritten | No Index | `Seq Scan` | Viết lại khoảng nửa mở nhưng không có chỉ mục, planner vẫn phải quét toàn bảng. Speedup ~1.0x. |
| **C** | Original | With Index | `Seq Scan` | **Non-sargable:** Việc áp dụng hàm ép kiểu `published_at::date` làm che giấu giá trị cột gốc. B-tree index trên `published_at` bị vô hiệu hóa hoàn toàn! |
| **D** | Rewritten | With Index | `Bitmap Index Scan` / `Index Scan` | **Sargable Predicate:** Biểu thức so sánh trực tiếp khoảng thời gian cho phép duyệt B-tree Index. Speedup đạt từ **15x đến 50x**. |

**Kết luận khoa học cho Q3:**
Query Rewriting không làm tăng tốc độ nếu thiếu Index (A vs B). Ngược lại, Index vô dụng nếu truy vấn vi phạm tính Sargable (A vs C). Chỉ khi kết hợp cả hai kỹ thuật (D), hệ thống mới đạt được bước nhảy vọt về hiệu năng.

---

### 3.4. Q4 — Aggregation Control (Trường hợp Đối chứng)

```sql
SELECT
    property_type_name,
    COUNT(*) AS total,
    ROUND(AVG(price), 0) AS avg_price
FROM public.properties
GROUP BY property_type_name
ORDER BY total DESC;
```

- **Mục đích:** Chứng minh định lý: *Index không phải là viên đạn bạc cho mọi truy vấn.*
- **Phân tích cơ chế:**
  - Truy vấn không có mệnh đề `WHERE`, đòi hỏi tổng hợp trên **toàn bộ 100% dòng dữ liệu** của bảng.
  - Mặc dù tạo index trên `property_type_name`, để tính `AVG(price)` thì PostgreSQL vẫn bắt buộc phải đọc giá trị của cột `price` trong từng hàng dữ liệu tại Heap table.
  - Quét tuần tự toàn bảng (`Seq Scan`) kết hợp với thuật toán bảng băm trong bộ nhớ (`HashAggregate`) tận dụng khả năng đọc tuần tự của đĩa (Sequential Read) và đọc trước (Read-ahead).
  - Nếu planner bị ép dùng Index Scan, chi phí sẽ tăng vọt do hiện tượng đọc ngẫu nhiên (Random I/O) khi từ mỗi mục trong index phải nhảy tới một block heap khác nhau.
- **Kết quả thực tế:**
  - Baseline và Indexed đều cho thời gian thực thi tương đương (Speedup dao động quanh ~1.0x hoặc 0.98x).
  - Planner của PostgreSQL 17/18 nhận định chính xác chi phí và giữ nguyên `Seq Scan` ngay cả khi index tồn tại.

---

## 4. Phân tích Chi phí Lưu trữ và Tác động Mở rộng (Scalability)

### 4.1. Chi phí Lưu trữ Chỉ mục B-tree (Storage Overhead)
Chỉ mục B-tree đòi hỏi dung lượng đĩa và bộ đệm RAM tỉ lệ thuận với số bản ghi:
- `idx_properties_province_name`: chiếm ~2 MB tại 50K và ~16 MB tại 500K.
- `idx_properties_location_price`: chỉ mục tổng hợp 4 cột nên dung lượng lớn nhất (~4 MB tại 50K, ~35 MB tại 500K).
- Trong môi trường sản xuất có lưu lượng ghi cao (INSERT/UPDATE/DELETE), mỗi chỉ mục bổ sung sẽ làm tăng chi phí cập nhật trang B-tree và phát sinh phân mảnh trang (page split).

### 4.2. Khả năng mở rộng theo quy mô dữ liệu
1. **Seq Scan:** Độ phức tạp thời gian là $O(N)$. Khi $N$ tăng gấp 10 lần (50K $\to$ 500K), thời gian thực thi tăng tương ứng xấp xỉ 10 lần.
2. **Index Scan (Point / Range nhỏ):** Độ phức tạp tìm kiếm B-tree là $O(\log N)$ cộng với chi phí đọc $K$ bản ghi kết quả. Với truy vấn có `LIMIT` như Q2, thời gian thực thi gần như không phụ đổi ($O(1)$ sau khi chạm trang đầu tiên).

---

## 5. Giới hạn Nghiên cứu và Kiến nghị

1. **Giới hạn bộ đệm:** Do kích thước 500K bản ghi (~100–150 MB) nhỏ hơn dung lượng RAM của máy chủ hiện đại, hầu hết các trang sau warm-up đều nằm trong Shared Buffers (Shared Hit Blocks chiếm đa số). Đối với quy mô Big Data thực sự (hàng chục đến hàng trăm GB), hiện tượng tràn cache và I/O đĩa vật lý sẽ thể hiện rõ nét hơn.
2. **Khuyến nghị kiến trúc:**
   - Sử dụng Covering Index (`INCLUDE` clause) để kích hoạt `Index Only Scan` khi truy vấn chỉ cần một số ít cột bổ sung.
   - Với các truy vấn tổng hợp như Q4, giải pháp tối ưu là sử dụng **Materialized Views** hoặc bảng tổng hợp định kỳ thay vì chỉ mục B-tree đơn thuần.
   - Luôn viết vị từ tìm kiếm theo dạng Sargable, tránh gọi hàm toán tử trực tiếp trên cột đánh chỉ mục.

