# CHƯƠNG 4: PHƯƠNG PHÁP THỰC NGHIỆM

Chương này trình bày chi tiết thiết kế phương pháp luận thực nghiệm nhằm trả lời **Câu hỏi nghiên cứu 2 (RQ2)** và **Câu hỏi nghiên cứu 3 (RQ3)**. Nội dung tập trung hoàn toàn vào kiến trúc hệ thống, các biến số độc lập/phụ thuộc, giao thức kiểm soát nhiễu và tiêu chuẩn kiểm chứng tính tương đương logic, không đưa ra các kết luận về hiệu quả trước khi trình bày số liệu đo đạc tại Chương 5.

---

## 4.1. Môi trường thực nghiệm phần cứng và phần mềm

Để loại bỏ các biến động do độ trễ mạng và bảo đảm môi trường đo đạc có kiểm soát, toàn bộ các thực nghiệm được tiến hành trên một nút máy chủ cục bộ (Single-node Workstation) với cấu hình đồng nhất:

- **Phần cứng máy chủ thực nghiệm:**
  - Bộ vi xử lý (CPU): x86_64, đa nhân đa luồng thế hệ mới.
  - Bộ nhớ RAM vật lý: 16 GB DDR4/DDR5.
  - Hệ thống lưu trữ: Ổ cứng thể rắn SSD chuẩn NVMe PCIe hiệu năng cao.
  - Hệ điều hành: Microsoft Windows x86_64.
- **Môi trường phần mềm và Phiên bản công cụ:**
  - Hệ quản trị cơ sở dữ liệu: PostgreSQL phiên bản **18.3 x86_64**, khởi chạy cụm dữ liệu cục bộ (`.pgdata`) trên cổng mạng 5433.
  - Ngôn ngữ lập trình: Python phiên bản 3.13.
  - Thư viện tiền xử lý dữ liệu: Pandas 2.2+, Polars 1.24+, PyArrow 19+.
  - Thư viện kết nối và đo lường: Psycopg 3 (Binary Protocol), `psutil` (giám sát tài nguyên hệ thống).
- **Cấu hình tham số PostgreSQL chính:**
  - `shared_buffers = 128MB` (hoặc cấu hình mặc định tương ứng với cụm phát triển).
  - `work_mem = 4MB`.
  - `random_page_cost = 4.0`.
  - `seq_page_cost = 1.0`.

---

## 4.2. Thiết kế thực nghiệm RQ2: Đánh giá hiệu năng xử lý dữ liệu tiền kỳ

Nhằm trả lời RQ2, một khung đo lường độc lập (`scripts/benchmark_processing.py`) được thiết lập để đánh giá hiệu năng nạp và tính toán trên DataFrame ở giai đoạn tiền kỳ với 3 nhóm tác vụ:

### 4.2.1. Kịch bản thực nghiệm Ingestion và Phân tích nội bộ
1. **Tác vụ nạp tệp toàn bộ (File Ingestion):**
   - Đọc tệp dữ liệu CSV chuẩn hóa (hướng dòng) bằng `pandas.read_csv()`.
   - Đọc tệp dữ liệu CSV chuẩn hóa bằng `polars.read_csv()`.
   - Đọc tệp dữ liệu Parquet chuẩn hóa (hướng cột nhị phân) bằng `pandas.read_parquet()`.
   - Đọc tệp dữ liệu Parquet chuẩn hóa bằng `polars.read_parquet()`.
2. **Tác vụ nạp có giới hạn bộ nhớ (Memory-bounded Ingestion):**
   - Nạp tệp CSV theo từng khối (Chunked Reading): sử dụng `pandas.read_csv(..., chunksize=10000)` để duyệt tuần tự qua các khối 10.000 dòng.
   - Nạp tệp CSV kèm tính toán tổng hợp theo khối (Chunked Aggregate): duyệt từng khối 10.000 dòng trong Pandas, thực hiện gom nhóm tính tổng và số lượng theo `property_type_name`, tích lũy bảng tổng hợp trung gian trong bộ nhớ.
3. **Tác vụ lọc và tổng hợp trong bộ nhớ (In-Memory Analytics):**
   - Trên DataFrame đã nạp sẵn trong RAM, thực hiện lọc các bản ghi có `province_name == 'Hà Nội'` (170.167 dòng) và gom nhóm theo `property_type_name` để tính giá trung bình (`price.mean()`).
   - Thực thi tương đương trên cấu trúc dữ liệu của Pandas và Polars.

### 4.2.2. Phương pháp giám sát bộ nhớ thực thời và Giới hạn phép lấy mẫu RSS 1 ms
Để ghi nhận mức độ chiếm dụng bộ nhớ thực tế của từng tác vụ thay vì chỉ đo dung lượng tĩnh sau khi hàm kết thúc, đề tài cài đặt một luồng giám sát chạy nền (**Background Monitoring Thread**) sử dụng thư viện `psutil`:
- **Chỉ số theo dõi:** `Resident Set Size (RSS)` - lượng bộ nhớ RAM vật lý thực tế được hệ điều hành Windows ánh xạ cho tiến trình Python.
- **Tần suất lấy mẫu:** Chu kỳ cực ngắn **1 mili-giây (1 ms)** liên tục trong suốt thời gian hàm xử lý hoạt động.
- **Các đại lượng thu thập:**
  - `baseline_ram_mb`: Mức RSS tại thời điểm bắt đầu tác vụ.
  - `peak_ram_mb`: Mức RSS lớn nhất ghi nhận được trong suốt thời gian chạy.
  - `delta_ram_mb`: Độ tăng bộ nhớ thực tế do tác vụ phát sinh ($\Delta \text{RSS} = \text{peak\_ram} - \text{baseline\_ram}$).
- **Thời gian thực thi:** Mỗi tác vụ được lặp lại 5 lần độc lập, ghi nhận giá trị trung vị (`median_ms`), trung bình (`mean_ms`) và độ lệch chuẩn (`std_ms`).

**Giới hạn phương pháp luận:** Cần làm rõ rằng phép lấy mẫu RSS 1 ms phản ánh hành vi bộ nhớ ở mức tiến trình hệ điều hành, chịu tác động của cơ chế gom rác (Garbage Collector) của Python runtime và hiện tượng phân mảnh của bộ cấp phát C (`pymalloc`). Phép đo này cung cấp bức tranh thực nghiệm định lượng về dấu chân tài nguyên tương đối của các kỹ thuật, chứ không phải một phép đo vi mô từng đối tượng trong heap. Đồng thời, nghiên cứu được tiến hành trên tập dữ liệu tối đa 500.000 dòng (~94 MB CSV) trên máy trạm 16 GB RAM; do đó, kết quả kiểm soát RAM của Chunked Streaming là bằng chứng thực nghiệm trong phạm vi cấu hình này, không suy diễn thành khẳng định hệ thống có thể xử lý dữ liệu lớn hơn RAM vật lý trong mọi tình huống khi chưa có thực nghiệm trên quy mô đó.

---

## 4.3. Thiết kế thực nghiệm RQ3: Tối ưu hóa truy vấn PostgreSQL

### 4.3.1. Ba quy mô dữ liệu thực nghiệm: 50.000, 200.000 và 500.000 bản ghi
Để khảo sát hành vi của bộ lập lịch PostgreSQL khi kích thước dữ liệu mở rộng, thực nghiệm được thiết kế cố định trên 3 ngưỡng quy mô dữ liệu:
- **50.000 bản ghi:** Kích thước tệp CSV 9,35 MB; dung lượng bảng Heap trong PostgreSQL khoảng 10,1 MB.
- **200.000 bản ghi:** Kích thước tệp CSV 37,49 MB; dung lượng bảng Heap khoảng 40,5 MB.
- **500.000 bản ghi:** Kích thước tệp CSV 93,88 MB; dung lượng bảng Heap khoảng 100,8 MB.

Các tập dữ liệu nhỏ là tập con tiền tố nghiêm ngặt của tập dữ liệu lớn hơn theo thứ tự khóa chính `id`:
$$\mathcal{D}_{50K} \subset \mathcal{D}_{200K} \subset \mathcal{D}_{500K}$$

### 4.3.2. Bốn bài toán truy vấn SQL thực nghiệm (Q1 – Q4)
Bốn bài toán truy vấn đại diện cho các mẫu truy vấn phổ biến trong ứng dụng thực tế được thiết lập theo đúng mã SQL chuẩn hóa tại thư mục `sql/benchmark/queries/`:

1. **Bài toán Q1: Lọc đẳng thức đơn cột (Single-column Equality Filter)**
   ```sql
   SELECT id, name, price, area
   FROM public.properties
   WHERE province_name = 'Hải Phòng';
   ```
   *Đặc trưng:* Lọc theo địa bàn Hải Phòng (10.422 bản ghi tại 500K, độ chọn lọc $\approx 2,08\%$).

2. **Bài toán Q2: Lọc khoảng, sắp xếp và cắt ngọn (Multi-predicate Filter, Sort and Limit)**
   ```sql
   SELECT id, name, price, area, published_at
   FROM public.properties
   WHERE province_name = 'Hà Nội'
     AND district_name = 'Cầu Giấy'
     AND price BETWEEN 4100000000 AND 14300000000
   ORDER BY price ASC, id ASC
   LIMIT 20;
   ```
   *Đặc trưng:* Mô phỏng màn hình tìm kiếm bất động sản thực tế tại Cầu Giấy (Hà Nội) trong khoảng giá trung vị 4,1 đến 14,3 tỷ VNĐ, sắp xếp theo giá tăng dần và lấy 20 kết quả đầu tiên.

3. **Bài toán Q3: Lọc thời gian và Tính khả chỉ mục (Temporal Filtering & Sargability)**
   - *Truy vấn gốc (Original / Non-sargable):*
     ```sql
     SELECT id, name, published_at
     FROM public.properties
     WHERE published_at::date = DATE '2025-10-15';
     ```
   - *Truy vấn viết lại (Rewritten / Sargable Range):*
     ```sql
     SELECT id, name, published_at
     FROM public.properties
     WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00'
       AND published_at <  TIMESTAMP '2025-10-16 00:00:00';
     ```
   *Đặc trưng:* Kiểm tra tính khả chỉ mục của vị từ khi lọc tin đăng trong một ngày xác định.

4. **Bài toán Q4: Tổng hợp toàn bộ bảng (Full-table Aggregation / Negative Control)**
   ```sql
   SELECT
       property_type_name,
       COUNT(*) AS total,
       ROUND(AVG(price), 0) AS avg_price
   FROM public.properties
   GROUP BY property_type_name
   ORDER BY total DESC;
   ```
   *Đặc trưng:* Bài toán đối chứng âm yêu cầu quét toàn bộ các hàng trong bảng để tính tổng số tin và giá trung bình theo 5 loại hình bất động sản.

### 4.3.3. Phân rã 10 cấu hình thực nghiệm Benchmark PostgreSQL
Bốn bài toán truy vấn trên được phân rã thành **10 cấu hình thực nghiệm độc lập** như mô tả tại Bảng 4.1.

**Bảng 4.1: Đặc tả 10 cấu hình thực nghiệm Benchmark PostgreSQL**

| Bài toán | Mã cấu hình | Mô tả phương pháp | Câu lệnh SQL và Chỉ mục áp dụng | Mục tiêu kiểm chứng khoa học |
| :---: | :--- | :--- | :--- | :--- |
| **Q1** | `Q1_baseline` | Quét tuần tự cơ sở | SQL chuẩn Q1.<br>*(Không có chỉ mục phụ trợ)* | Mốc chuẩn cho truy vấn lọc đẳng thức đơn cột khi quy mô dữ liệu mở rộng. |
| **Q1** | `Q1_indexed` | Chỉ mục B-tree đơn cột | SQL chuẩn Q1.<br>Chỉ mục: `CREATE INDEX idx_properties_province_name ON properties USING btree (province_name);` | Khảo sát việc chuyển đổi phương thức quét từ `Seq Scan` sang `Bitmap Index Scan`. |
| **Q2** | `Q2_baseline` | Quét tuần tự kết hợp sắp xếp | SQL chuẩn Q2.<br>*(Không có chỉ mục phụ trợ)* | Đo đạc chi phí quét toàn bảng và chi phí thuật toán Top-N Heapsort trong bộ nhớ RAM. |
| **Q2** | `Q2_indexed` | Chỉ mục B-tree tổ hợp (Composite Index) | SQL chuẩn Q2.<br>Chỉ mục: `CREATE INDEX idx_properties_location_price ON properties USING btree (province_name, district_name, price, id);` | Kiểm chứng cơ chế Early Termination: duyệt theo thứ tự lá B-tree, dừng khi đủ 20 dòng, loại bỏ nút Sort. |
| **Q3** | `Q3_A` | Gốc, Không Index | Truy vấn gốc Q3 (`published_at::date`).<br>*(Không có chỉ mục phụ trợ)* | Mốc chuẩn cho truy vấn lọc thời gian sử dụng hàm ép kiểu `::date`. |
| **Q3** | `Q3_B` | Viết lại, Không Index | Truy vấn viết lại khoảng nửa mở Q3.<br>*(Không có chỉ mục phụ trợ)* | Kiểm chứng giả thuyết: Viết lại truy vấn sang dạng sargable có mang lại lợi ích hay không khi thiếu chỉ mục. |
| **Q3** | `Q3_C` | Gốc, Có Index | Truy vấn gốc Q3.<br>Chỉ mục: `CREATE INDEX idx_properties_published_at ON properties USING btree (published_at);` | Kiểm chứng hiện tượng vô hiệu hóa chỉ mục: Chỉ mục B-tree tồn tại nhưng Planner không thể dùng do vị từ non-sargable. |
| **Q3** | `Q3_D` | Viết lại, Có Index | Truy vấn viết lại khoảng nửa mở Q3.<br>Chỉ mục: `CREATE INDEX idx_properties_published_at ON properties USING btree (published_at);` | Kiểm chứng hiệu quả cộng hưởng khi kết hợp đồng thời vị từ sargable và chỉ mục B-tree tương ứng. |
| **Q4** | `Q4_baseline` | Tổng hợp toàn bảng cơ sở | SQL chuẩn Q4.<br>*(Không có chỉ mục phụ trợ)* | Mốc chuẩn cho truy vấn tổng hợp `GROUP BY` toàn bảng. |
| **Q4** | `Q4_indexed` | Tổng hợp toàn bảng có Index (Đối chứng âm) | SQL chuẩn Q4.<br>Chỉ mục: `CREATE INDEX idx_properties_property_type ON properties USING btree (property_type_name);` | **Negative Control:** Chứng minh trường hợp chỉ mục B-tree không mang lại lợi ích cho truy vấn tổng hợp toàn bảng. |

---

## 4.4. Giao thức đo lường kiểm soát nhiễu thực nghiệm

Để loại bỏ các sai số ngẫu nhiên do hiệu ứng bộ đệm nguội (Cold cache), hoạt động của trình dọn rác hệ điều hành hoặc xung đột luồng, công cụ `scripts/benchmark_runner.py` tuân thủ nghiêm ngặt quy trình đo đạc 4 bước:

1. **Cách ly cấu hình chỉ mục (Index Isolation):** Trước khi đo đạc từng cấu hình, hệ thống thực thi script `sql/benchmark/reset_indexes.sql` để xóa bỏ toàn bộ các chỉ mục phụ trợ cũ, chỉ giữ lại duy nhất chỉ mục Khóa chính trên cột `id`. Chỉ số lượng và loại chỉ mục thuộc cấu hình đang kiểm thử mới được tạo mới.
2. **Cập nhật thống kê bộ lập lịch:** Sau khi tạo chỉ mục, lệnh `ANALYZE public.properties;` được gọi ngay lập tức để cập nhật lược đồ phân phối giá trị và độ chọn lọc cho bộ lập lịch của PostgreSQL.
3. **Pha nạp nóng kiểm soát (Warm-up Phase):** Thực thi câu truy vấn 3 lần liên tiếp và hủy bỏ kết quả đo. Pha này nhằm mục đích đưa các trang dữ liệu cần thiết vào vùng nhớ Shared Buffers và ổn định trạng thái máy chủ cơ sở dữ liệu.
4. **Pha đo lường chính thức (Official Runs):** Thực thi câu truy vấn **20 lần liên tiếp**, trích xuất toàn bộ kế hoạch thực thi chi tiết ở định dạng JSON thông qua cú pháp:
   ```sql
   EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) <query_statement>;
   ```
   Từ 20 tệp JSON kế hoạch của mỗi cấu hình, hệ thống thu thập:
   - `Planning Time` (Thời gian lập kế hoạch thực thi, ms).
   - `Execution Time` (Thời gian chạy truy vấn thực tế, ms).
   - `Shared Hit Blocks` (Số khối 8 KB đọc từ bộ đệm Shared Buffers trong RAM).
   - `Shared Read Blocks` (Số khối 8 KB đọc vật lý từ đĩa).
   - `Scan Type` / `Node Types` (Các nút xử lý trong cây kế hoạch thực thi).
   - Để phản ánh trung thực hiệu năng, đề tài sử dụng **Trung vị (Median)** làm thước đo trung tâm thay vì giá trị trung bình (Mean), đồng thời tính toán **Khoảng tứ phân vị (IQR)** và các cực trị `Min`, `Max` để theo dõi độ phân tán của phép đo.

---

## 4.5. Thiết kế kiểm thử tính tương đương ngữ nghĩa truy vấn (Equivalence Verification)

Trong nghiên cứu tối ưu hóa cơ sở dữ liệu, một kỹ thuật tối ưu hóa chỉ được chấp nhận là hợp lệ nếu nó bảo toàn tuyệt đối ngữ nghĩa logic của truy vấn: tập kết quả trả về của truy vấn tối ưu phải đồng nhất hoàn toàn với truy vấn cơ sở.

Hệ thống thực hiện kiểm thử tự động trước khi đo:
- Đối với Q1, Q2, Q4: So sánh số lượng dòng kết quả (`row_count`) và giá trị băm dữ liệu kết quả giữa bản Baseline và Indexed.
- Đối với bài toán viết lại Q3: Thực hiện phép kiểm tra tập hợp hai chiều đối xứng thông qua toán tử `EXCEPT ALL`:
```sql
(SELECT id FROM properties WHERE published_at::date = DATE '2025-10-15'
 EXCEPT ALL
 SELECT id FROM properties WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00' 
                             AND published_at <  TIMESTAMP '2025-10-16 00:00:00')
UNION ALL
(SELECT id FROM properties WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00' 
                             AND published_at <  TIMESTAMP '2025-10-16 00:00:00'
 EXCEPT ALL
 SELECT id FROM properties WHERE published_at::date = DATE '2025-10-15');
```
Chỉ khi kết quả của phép toán trên trả về đúng 0 dòng (rỗng), hệ thống mới xác nhận hai câu truy vấn hoàn toàn đồng nhất về mặt ngữ nghĩa và cho phép tiến hành đo đạc benchmark.

