# CHƯƠNG 3: XÂY DỰNG BỘ DỮ LIỆU VÀ THIẾT KẾ PHƯƠNG PHÁP THỰC NGHIỆM

## 3.1. Quy trình thu thập và chuẩn hóa dữ liệu lớn từ Hugging Face

### 3.1.1. Nguồn dữ liệu và Cơ chế Streaming Shuffle Buffer
Bộ dữ liệu thực nghiệm được thu thập từ kho lưu trữ mã nguồn mở Hugging Face với định danh `Phuscca/vietnam-real-estates` (tập phân chia `train`, mã phiên bản commit chuẩn hóa: `68bae25c3fa65a8e694973efe80bd6e237de11f5`). Đây là tập dữ liệu tổng hợp thực tế về các bất động sản được rao bán trên toàn lãnh thổ Việt Nam.

Để khắc phục hạn chế về tài nguyên bộ nhớ RAM và bảo đảm khả năng tái lập 100% của thí nghiệm, quy trình thu thập dữ liệu được thiết kế theo mô hình **Đọc dòng dữ liệu (Streaming Ingestion)** kết hợp với **Bộ đệm xáo trộn (Shuffle Buffer)** theo tài liệu kỹ thuật chuẩn của Hugging Face `datasets`:
- **Tham số dòng:** Sử dụng `load_dataset(..., split="train", streaming=True)`. Dữ liệu được nạp liên tục qua kết nối HTTP/HTTPS theo từng lô nhị phân, không nạp toàn bộ tập dữ liệu thô vào bộ nhớ RAM.
- **Tham số xáo trộn có kiểm soát:** Sử dụng phương thức `.shuffle(seed=42, buffer_size=10000)`. Kỹ thuật này duy trì một hàng đợi vòng (circular buffer) có dung lượng cố định là 10.000 bản ghi. Mỗi khi một bản ghi được trích xuất ngẫu nhiên dựa trên giá trị mầm (`seed = 42`), một bản ghi mới từ luồng dữ liệu nguồn sẽ được nạp bổ sung vào bộ đệm.
- **Kích thước khối xử lý (Batch Processing):** Dữ liệu từ luồng shuffle được gom thành các lô xử lý có kích thước `batch_size = 2000` dòng trước khi đưa vào module làm sạch.

Quy trình này đảm bảo tính xác định (determinism): bất kỳ nhà nghiên cứu nào khi thực thi lại mã nguồn `scripts/build_large_dataset.py` với cùng commit hash, seed và buffer size đều sẽ thu được tập dữ liệu có thứ tự bản ghi và giá trị hoàn toàn đồng nhất.

### 3.1.2. Bộ quy tắc làm sạch dữ liệu và Hợp đồng 9 thuộc tính
Module làm sạch dữ liệu (`scripts/cleaning.py`) được thiết kế theo nguyên tắc bảo toàn tính chân thực của dữ liệu thị trường, chỉ loại bỏ các bản ghi vi phạm tính toàn vẹn bắt buộc và chuẩn hóa hình thức trình bày.

Các quy tắc làm sạch bao gồm:
1. **Chuẩn hóa chuỗi ký tự (String Trimming):** Loại bỏ toàn bộ các ký tự khoảng trắng thừa, ký tự xuống dòng (`\r`, `\n`) và ký tự tab ở đầu/cuối của các trường văn bản bằng phương thức `.str.strip()`. Quá trình này bảo toàn nguyên vẹn các điểm mã UTF-8 tiếng Việt tự nhiên mà không cưỡng chế chuyển đổi chuẩn NFC để tránh nguy cơ làm sai lệch dữ liệu gốc.
2. **Hợp đồng 6 thuộc tính bắt buộc (Mandatory Columns):** Một bản ghi bị xem là không hợp lệ và bị loại bỏ ngay lập tức nếu thiếu một trong 6 thông tin nền tảng: `name` (tiêu đề tin đăng), `property_type_name` (loại hình bất động sản), `province_name` (tỉnh/thành phố), `area` (diện tích), `published_at` (thời điểm đăng tin), hoặc không thể phân tích cú pháp ngày tháng hợp lệ.
3. **Quy tắc làm sạch diện tích (`area`):** Thuộc tính `area` phải là số thực dương hữu hạn ($area > 0$ và không phải giá trị `NaN`, `Inf`). Các bản ghi có diện tích bằng 0, số âm hoặc để trống bị loại bỏ khỏi tập dữ liệu.
4. **Quy tắc xử lý giá bán (`price`):** Khác với diện tích, giá bán là một trường tùy chọn trong thực tế giao dịch bất động sản (thường xuất hiện dưới dạng "giá thỏa thuận", "liên hệ trực tiếp"). Quy tắc kỹ thuật quy định: các giá trị giá không hợp lệ, không dương ($\le 0$) hoặc để trống sẽ được **chuyển đổi thành giá trị rỗng (SQL NULL)** thay vì loại bỏ bản ghi. Quyết định này giúp bảo toàn mẫu số phân tích cho các bài toán thống kê diện tích và phân bố vùng miền.
5. **Quy tắc xử lý địa chỉ chi tiết (`district_name`, `ward_name`):** Các giá trị chuỗi rỗng hoặc chuỗi ký tự vô nghĩa được đưa về chuẩn SQL NULL.
6. **Cơ chế phát sinh định danh duy nhất (`id`):** Thuộc tính `id` được cấp phát tuần tự liên tục từ $1$ đến $N$ sau khi bản ghi đã vượt qua toàn bộ các bước lọc kiểm tra, đảm bảo tính liên tục tuyệt đối và đóng vai trò khóa chính (Primary Key).

Bảng 3.1 tổng hợp hợp đồng 9 thuộc tính chuẩn hóa cuối cùng được xuất ra các tệp dữ liệu thực nghiệm.

**Bảng 3.1: Đặc tả cấu trúc lược đồ dữ liệu chuẩn hóa (9 thuộc tính)**

| STT | Tên thuộc tính | Kiểu dữ liệu Python | Kiểu dữ liệu PostgreSQL | Tính chất | Mô tả nghiệp vụ |
| :---: | :--- | :--- | :--- | :---: | :--- |
| 1 | `id` | `int64` | `BIGINT` | NOT NULL, PK | Khóa chính định danh duy nhất cho từng tin đăng (tăng tự động từ 1) |
| 2 | `name` | `object` (str) | `TEXT` | NOT NULL | Tiêu đề chi tiết của tin đăng bất động sản |
| 3 | `property_type_name` | `object` (str) | `TEXT` | NOT NULL | Phân loại hình thái bất động sản (Nhà riêng, Đất, Căn hộ, Biệt thự, Shophouse) |
| 4 | `province_name` | `object` (str) | `TEXT` | NOT NULL | Tên tỉnh/thành phố trực thuộc trung ương |
| 5 | `district_name` | `object` (str) | `TEXT` | NULLABLE | Tên quận/huyện/thị xã (cho phép NULL nếu thiếu thông tin) |
| 6 | `ward_name` | `object` (str) | `TEXT` | NULLABLE | Tên phường/xã/thị trấn (cho phép NULL nếu thiếu thông tin) |
| 7 | `price` | `float64` | `NUMERIC` | NULLABLE | Giá chào bán niêm yết (Đơn vị: VNĐ; NULL nếu giá thỏa thuận) |
| 8 | `area` | `float64` | `DOUBLE PRECISION` | NOT NULL | Diện tích sử dụng hoặc diện tích đất (Đơn vị: $m^2$; bắt buộc $> 0$) |
| 9 | `published_at` | `datetime64[ns]` | `TIMESTAMP WITHOUT TIME ZONE` | NOT NULL | Dấu thời gian đăng tin niêm yết (Định dạng: YYYY-MM-DD HH:MM:SS) |

### 3.1.3. Lược đồ cơ sở dữ liệu quan hệ trên PostgreSQL
Cấu trúc bảng lưu trữ trong cơ sở dữ liệu PostgreSQL (`real_estate_db`) được thiết lập theo đúng tệp đặc tả chuẩn [`sql/schema.sql`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/sql/schema.sql):

```sql
CREATE TABLE IF NOT EXISTS public.properties (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    property_type_name TEXT NOT NULL,
    province_name TEXT NOT NULL,
    district_name TEXT,
    ward_name TEXT,
    price NUMERIC,
    area DOUBLE PRECISION NOT NULL,
    published_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    CONSTRAINT properties_area_positive CHECK (area > 0),
    CONSTRAINT properties_price_positive CHECK (price IS NULL OR price > 0)
);
```

Bảng cơ sở dữ liệu được trang bị hai ràng buộc toàn vẹn mức dòng (Table Check Constraints):
- `properties_area_positive`: Bảo đảm diện tích luôn lớn hơn 0 trên tầng lưu trữ vật lý.
- `properties_price_positive`: Bảo đảm giá trị giá nếu khác NULL thì bắt buộc phải là một số dương.

Dữ liệu được nạp vào cơ sở dữ liệu thông qua giao thức truyền tải dòng nhị phân hiệu năng cao **Psycopg 3 Binary COPY** (`COPY public.properties FROM STDIN (FORMAT CSV, HEADER TRUE)`), với cơ chế kiểm soát giao dịch toàn vẹn (Transactional Commit / Rollback) và khóa bảng `SHARE ROW EXCLUSIVE` trong suốt quá trình nạp để ngăn ngừa xung đột dữ liệu.

---

## 3.2. Hồ sơ chất lượng dữ liệu và Phân tích khám phá (Data Profiling & EDA)

### 3.2.1. Thống kê mô tả và Phân tích giá trị khuyết thiếu
Trước khi tiến hành các thí nghiệm benchmark, toàn bộ tập dữ liệu 500.000 bản ghi được phân tích chất lượng toàn diện thông qua module `scripts/data_quality.py`.

Kết quả thống kê giá trị khuyết thiếu xác nhận tính tuân thủ tuyệt đối của pipeline làm sạch:
- Các trường bắt buộc (`id`, `name`, `property_type_name`, `province_name`, `area`, `published_at`) đạt tỷ lệ đầy đủ **100.0%** (0 bản ghi khuyết thiếu).
- Trường `ward_name` có 47.904 giá trị khuyết (chiếm **9.58%**).
- Trường `price` có 39.061 giá trị khuyết (chiếm **7.81%**), tương ứng với 460.939 tin đăng có giá chào bán cụ thể.
- Trường `district_name` chỉ có 53 giá trị khuyết (chiếm **0.01%**).

Bảng 3.2 mô tả kết quả kiểm toán quá trình nạp dòng thực tế trên tập 500.000 bản ghi.

**Bảng 3.2: Kết quả kiểm toán quá trình thu thập và lọc dòng dữ liệu**

| Chỉ số kiểm toán dữ liệu | Giá trị định lượng | Tỷ lệ (%) | Ý nghĩa kỹ thuật |
| :--- | :---: | :---: | :--- |
| **Tổng số dòng nguồn đã đọc (`source_rows_read`)** | **502.000** | 100.0% | Số lượng bản ghi tiếp nhận từ luồng Hugging Face |
| **Tổng số dòng không hợp lệ bị loại (`invalid_rows`)** | **203** | 0.04% | Bản ghi vi phạm các điều kiện toàn vẹn bắt buộc |
| - *Lỗi thiếu trường bắt buộc (`invalid_required`)* | 202 | 0.04% | Thiếu tiêu đề, phân loại, tỉnh/thành phố hoặc ngày đăng |
| - *Lỗi diện tích không hợp lệ (`invalid_area`)* | 1 | <0.001% | Diện tích không hữu hạn hoặc $\le 0$ |
| - *Lỗi định dạng ngày đăng (`invalid_date`)* | 0 | 0.00% | Toàn bộ dấu thời gian đều hợp lệ |
| **Số dòng hợp lệ tiếp nhận (`valid_rows_seen`)** | **501.797** | 99.96% | Dòng đạt chuẩn sau khi đi qua bộ lọc làm sạch |
| **Số dòng hợp lệ dư dôi (`valid_rows_not_exported`)** | **1.797** | 0.36% | Dòng nằm trong batch cuối cùng sau khi đã đủ 500K |
| **Tổng số bản ghi thực xuất (`exported_rows`)** | **500.000** | 99.60% | Tập dữ liệu chuẩn hóa phục vụ thực nghiệm |

### 3.2.2. Phân tích ngoại lệ theo phương pháp Khoảng tứ phân vị (IQR)
Do đặc thù giá cả và diện tích bất động sản có độ lệch phân phối (Skewness) rất lớn, việc sử dụng các chỉ số trung bình (Mean) và độ lệch chuẩn (Standard Deviation) sẽ bị bóp méo nghiêm trọng bởi các giá trị cực đoan. Nghiên cứu áp dụng phương pháp thống kê vững (**Robust Statistics**) dựa trên Khoảng tứ phân vị (**Interquartile Range - IQR**):
$$IQR = Q_3 - Q_1$$
Trong đó $Q_1$ là phân vị 25% và $Q_3$ là phân vị 75%. Hàng rào xác định ngoại lệ được tính toán theo công thức kinh điển của Tukey:
$$\text{Lower Bound} = Q_1 - 1.5 \times IQR, \quad \text{Upper Bound} = Q_3 + 1.5 \times IQR$$

Bảng 3.3 tổng hợp các tham số thống kê mô tả vững trên tập dữ liệu 500.000 bản ghi.

**Bảng 3.3: Thống kê mô tả vững trên tập dữ liệu 500.000 bản ghi**

| Tham số thống kê | Diện tích ($m^2$) | Giá chào bán (Tỷ VNĐ) | Đơn giá ($Triệu/m^2$) |
| :--- | :---: | :---: | :---: |
| **Số lượng quan sát ($N$)** | 500.000 | 460.939 | 460.939 |
| **Giá trị nhỏ nhất (Min)** | 1.00 | 0.001 (1 triệu) | 0.004 |
| **Phân vị 1% ($P_1$)** | 20.00 | 0.90 | 11.25 |
| **Phân vị 5% ($P_5$)** | 30.00 | 1.70 | 25.00 |
| **Tứ phân vị thứ nhất ($Q_1$)** | **45.00** | **4.10** | **58.33** |
| **Trung vị ($Median - Q_2$)** | **68.00** | **6.50** | **100.00** |
| **Giá trị trung bình ($Mean$)** | 126.85 | 15.34 | 141.22 |
| **Tứ phân vị thứ ba ($Q_3$)** | **110.00** | **14.30** | **175.00** |
| **Phân vị 95% ($P_{95}$)** | 350.00 | 52.00 | 360.00 |
| **Phân vị 99% ($P_{99}$)** | 1.000.00 | 150.00 | 600.00 |
| **Giá trị lớn nhất (Max)** | 98.000.00 | 9.999.00 | 5.500.000.00 |
| **Khoảng tứ phân vị ($IQR$)** | **65.00** | **10.20** | **116.67** |
| **Số lượng ngoại lệ cao ($> Q_3 + 1.5 \times IQR$)** | 46.907 (9.38%) | 43.125 (9.36%) | 28.914 (6.27%) |

> [!NOTE]
> Kết quả thống kê chỉ ra rằng giá trị trung vị của giá chào bán là **6.50 tỷ VNĐ**, trong khi giá trị trung bình lên tới **15.34 tỷ VNĐ** (gấp 2.36 lần trung vị). Hiện tượng này phản ánh sự tồn tại của các siêu bất động sản (khách sạn, tòa nhà thương mại, biệt thự ven biển có giá hàng trăm tỷ đồng). Khoảng tứ phân vị $Q_1 \rightarrow Q_3$ nằm trong khoảng **4.10 tỷ đến 14.30 tỷ VNĐ**. Đây chính là cơ sở dữ liệu thực nghiệm để nhóm nghiên cứu thiết lập khoảng lọc giá trong bài toán tối ưu Q2.

### 3.2.3. Mối tương quan phi tuyến giữa diện tích, vị trí và giá chào bán
Để đánh giá mức độ phụ thuộc giữa các biến số định lượng, đề tài áp dụng hệ số tương quan hạng Spearman ($\rho$ - Spearman's Rank Correlation Coefficient), một thước đo phi tham số có khả năng đo lường mối quan hệ đơn điệu phi tuyến và không bị bóp méo bởi các giá trị ngoại lệ:
$$\rho = 1 - \frac{6 \sum d_i^2}{n(n^2 - 1)}$$
Trong đó $d_i$ là độ chênh lệch giữa thứ hạng của hai biến số trên quan sát thứ $i$.

Kết quả tính toán trên tập dữ liệu 500.000 bản ghi:
- Tương quan hạng giữa Diện tích (`area`) và Giá chào bán (`price`): $\rho = 0.584$ (mức tương quan thuận trung bình khá).
- Tương quan hạng giữa Giá chào bán (`price`) và Đơn giá (`price_per_m2`): $\rho = 0.621$.
- Tương quan hạng giữa Diện tích (`area`) và Đơn giá (`price_per_m2`): $\rho = -0.182$ (tương quan nghịch yếu, phản ánh quy luật kinh tế: bất động sản diện tích càng lớn thì đơn giá trên mỗi mét vuông thường có xu hướng giảm nhẹ).

---

## 3.3. Thiết kế khung thực nghiệm tối ưu hiệu năng cơ sở dữ liệu

### 3.3.1. Ba quy mô dữ liệu thực nghiệm: 50.000, 200.000 và 500.000 bản ghi
Để khảo sát hành vi của hệ quản trị cơ sở dữ liệu khi kích thước dữ liệu tăng dần và chứng minh tính mở rộng (Scalability), thực nghiệm được thiết kế cố định trên 3 ngưỡng quy mô dữ liệu:
1. **Quy mô nhỏ (50.000 bản ghi):** Đại diện cho các ứng dụng cấp quận/huyện hoặc sàn giao dịch quy mô nhỏ, dữ liệu bảng và các chỉ mục nằm trọn vẹn trong bộ nhớ đệm RAM.
2. **Quy mô trung bình (200.000 bản ghi):** Đại diện cho hệ thống cấp vùng/đô thị, khối lượng dữ liệu bắt đầu gây áp lực lên bộ nhớ đệm.
3. **Quy mô lớn (500.000 bản ghi):** Đại diện cho sàn giao dịch toàn quốc với dung lượng bảng Heap vượt 100 MB, thử thách năng lực quét khối và thuật toán sắp xếp của hệ thống.

Các tập dữ liệu nhỏ là các tập con tiền tố (prefix subsets) nghiêm ngặt của tập dữ liệu lớn hơn theo thứ tự ID:
$$\mathcal{D}_{50K} \subset \mathcal{D}_{200K} \subset \mathcal{D}_{500K}$$
Mỗi quy mô dữ liệu được nạp độc lập vào bảng `public.properties` trước khi tiến hành loạt đo đạc tương ứng.

### 3.3.2. Thiết kế 10 cấu hình thực nghiệm độc lập cho 4 bài toán truy vấn
Khung thực nghiệm xây dựng 4 bài toán truy vấn SQL điển hình, phân rã thành **10 cấu hình thực nghiệm độc lập** nhằm trả lời trực tiếp ba câu hỏi nghiên cứu RQ1, RQ2 và RQ3.

Bảng 3.4 mô tả chi tiết thông số kỹ thuật của 10 cấu hình.

**Bảng 3.4: Đặc tả 10 cấu hình thực nghiệm Benchmark PostgreSQL**

| Bài toán | Mã cấu hình | Mô tả phương pháp | Câu lệnh SQL và Chỉ mục áp dụng | Mục tiêu kiểm chứng khoa học |
| :---: | :--- | :--- | :--- | :--- |
| **Q1** | `Q1_baseline` | Quét tuần tự cơ sở | `SELECT * FROM properties WHERE province_name = 'Hải Phòng';`<br>*(Không có chỉ mục phụ)* | Thiết lập mốc thời gian chuẩn (Baseline) cho lọc đẳng thức đơn cột khi quy mô dữ liệu mở rộng. |
| **Q1** | `Q1_indexed` | Chỉ mục B-tree đơn cột | Câu truy vấn giữ nguyên.<br>Chỉ mục: `CREATE INDEX idx_properties_province_name ON properties (province_name);` | Kiểm chứng khả năng giảm I/O và chuyển đổi từ `Seq Scan` sang `Bitmap Scan`. |
| **Q2** | `Q2_baseline` | Lọc khoảng, sắp xếp và cắt ngọn cơ sở | `SELECT id, name, price, area, district_name FROM properties WHERE province_name = 'Hà Nội' AND district_name = 'Cầu Giấy' AND price BETWEEN 4100000000 AND 14300000000 ORDER BY price ASC, id ASC LIMIT 20;`<br>*(Không có chỉ mục phụ)* | Đánh giá chi phí quét toàn bảng và chi phí thuật toán Top-N Heapsort trong RAM khi không có chỉ mục bao phủ. |
| **Q2** | `Q2_indexed` | Chỉ mục B-tree tổ hợp (Composite Index) | Câu truy vấn giữ nguyên.<br>Chỉ mục: `CREATE INDEX idx_properties_location_price ON properties (province_name, district_name, price, id);` | Chứng minh cơ chế Early Termination: duyệt cây B-tree theo đúng thứ tự sắp xếp, dừng quét khi đủ 20 dòng, triệt tiêu nút Sort. |
| **Q3** | `Q3_A` | Gốc, Không Index (Original, No Index) | `SELECT * FROM properties WHERE published_at::date = DATE '2025-10-15';`<br>*(Không có chỉ mục phụ)* | Mốc chuẩn cho truy vấn lọc ngày tháng sử dụng hàm ép kiểu `::date`. |
| **Q3** | `Q3_B` | Viết lại, Không Index (Rewritten, No Index) | `SELECT * FROM properties WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00' AND published_at < TIMESTAMP '2025-10-16 00:00:00';`<br>*(Không có chỉ mục phụ)* | Kiểm chứng giả thuyết: Viết lại truy vấn sang dạng sargable có giúp tăng tốc hay không khi thiếu vắng chỉ mục. |
| **Q3** | `Q3_C` | Gốc, Có Index (Original, With Index) | Giữ nguyên câu truy vấn cấu hình A (`published_at::date`).<br>Chỉ mục: `CREATE INDEX idx_properties_published_at ON properties (published_at);` | Chứng minh hiện tượng vô hiệu hóa chỉ mục: Chỉ mục B-tree tồn tại nhưng Planner không thể sử dụng do vị từ non-sargable. |
| **Q3** | `Q3_D` | Viết lại, Có Index (Rewritten, With Index) | Sử dụng câu truy vấn khoảng nửa mở của cấu hình B kết hợp với chỉ mục của cấu hình C. | Chứng minh hiệu ứng cộng hưởng tối đa khi kết hợp đồng thời vị từ sargable và chỉ mục B-tree tương ứng. |
| **Q4** | `Q4_baseline` | Tổng hợp toàn bảng cơ sở | `SELECT property_type_name, COUNT(*), ROUND(AVG(price), 0) FROM properties GROUP BY property_type_name;`<br>*(Không có chỉ mục phụ)* | Mốc chuẩn cho truy vấn tổng hợp `GROUP BY` toàn bảng kết hợp tính toán trung bình. |
| **Q4** | `Q4_indexed` | Tổng hợp toàn bảng có Index (Đối chứng âm) | Câu truy vấn giữ nguyên.<br>Chỉ mục: `CREATE INDEX idx_properties_property_type ON properties (property_type_name);` | **Negative Control:** Chứng minh trường hợp chỉ mục B-tree hoàn toàn không mang lại lợi ích hiệu năng cho truy vấn tổng hợp toàn bảng. |

### 3.3.3. Thiết kế kiểm thử tính tương đương kết quả (Equivalence Verification)
Trong nghiên cứu tối ưu hóa cơ sở dữ liệu, một kỹ thuật tối ưu chỉ được coi là hợp lệ nếu nó bảo toàn tuyệt đối ngữ nghĩa logic của truy vấn: tập kết quả trả về của truy vấn tối ưu phải giống hệt tập kết quả của truy vấn cơ sở.

Để bảo đảm tính chuẩn xác khoa học, công cụ `scripts/benchmark_runner.py` tự động kích hoạt thủ tục kiểm thử tương đương trước khi đo đạc:
- Đối với Q1, Q2, Q4: So sánh số lượng dòng kết quả (`row_count`) và giá trị băm dữ liệu kết quả giữa bản Baseline và Optimized.
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
Chỉ khi kết quả của phép toán trên trả về đúng 0 dòng (rỗng), hệ thống mới chứng nhận hai câu truy vấn hoàn toàn đồng nhất về mặt ngữ nghĩa và cho phép tiến hành đo đạc benchmark.

### 3.3.4. Giao thức đo lường kiểm soát nhiễu: 3 Warm-up + 20 Official Runs
Để loại bỏ triệt để các sai số ngẫu nhiên do độ trễ nạp nguội (Cold-cache effect), trình dọn rác (Garbage Collector), hoặc dao động điều độ tiến trình của hệ điều hành, giao thức đo lường được thiết kế nghiêm ngặt:
1. **Cách ly chỉ mục tuyệt đối (Index Isolation):** Trước mỗi cấu hình, hệ thống thực thi script `sql/benchmark/reset_indexes.sql` để xóa bỏ hoàn toàn các chỉ mục phụ trợ cũ, chỉ giữ lại duy nhất chỉ mục Khóa chính trên cột `id`. Chỉ số lượng và loại chỉ mục thuộc cấu hình đang đo mới được tạo mới.
2. **Cập nhật thống kê bộ lập lịch:** Sau khi tạo chỉ mục, lệnh `ANALYZE public.properties;` được gọi ngay lập tức để cập nhật lược đồ phân phối giá trị và độ chọn lọc cho bộ lập lịch của PostgreSQL.
3. **Pha nạp nóng kiểm soát (Warm-up Phase):** Thực thi câu truy vấn 3 lần liên tiếp và hủy bỏ kết quả. Pha này nhằm mục đích đưa các trang dữ liệu cần thiết vào Shared Buffers và hoàn tất quá trình tối ưu hóa mã máy của máy chủ cơ sở dữ liệu.
4. **Pha đo lường chính thức (Official Runs):** Thực thi câu truy vấn **20 lần liên tiếp**, trích xuất toàn bộ kế hoạch thực thi chi tiết ở định dạng JSON thông qua cú pháp:
   ```sql
   EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) <query_statement>;
   ```
5. **Thu thập chỉ số định lượng:** Từ mỗi tệp JSON kế hoạch, hệ thống thu thập:
   - `Planning Time` (Thời gian lập kế hoạch thực thi, ms)
   - `Execution Time` (Thời gian chạy truy vấn thực tế, ms)
   - `Shared Hit Blocks` (Số khối 8 KB đọc từ RAM Shared Buffers)
   - `Shared Read Blocks` (Số khối 8 KB đọc vật lý từ đĩa)
   - `Node Type` / `Scan Type` (Kiểu quét dữ liệu chủ đạo)
6. **Xử lý thống kê mô tả:** Để đại diện cho hiệu năng thực tế, đề tài sử dụng **Trung vị (Median)** làm giá trị trọng tâm thay vì giá trị trung bình (Mean), đồng thời tính toán **Khoảng tứ phân vị (IQR)** và các cực trị `Min`, `Max` để phản ánh độ biến thiên ổn định của phép đo.

---

## 3.4. Thiết kế thực nghiệm so sánh hiệu năng tiền xử lý (Processing Benchmark)

Để đánh giá toàn diện pipeline xử lý dữ liệu trước khi nạp vào cơ sở dữ liệu, một khung kiểm thử hiệu năng độc lập (`scripts/benchmark_processing.py`) được thiết lập nhằm so sánh:
- **Định dạng lưu trữ:** CSV (văn bản thuần hướng dòng) đối chiếu Parquet (nhị phân nén hướng cột).
- **Công cụ tính toán:** Thư viện Pandas (đơn luồng, mô hình đối tượng C/Python) đối chiếu thư viện Polars (đa luồng, kiến trúc Apache Arrow, viết bằng ngôn ngữ Rust).
- **Cơ chế nạp có giới hạn bộ nhớ:** Nạp toàn bộ tệp vào RAM đối chiếu Nạp phân khối theo luồng (`chunksize = 10,000` dòng).

**Giao thức đo lường tài nguyên RAM thực thời:**
Nhằm khắc phục nhược điểm của các phép đo RAM tĩnh sau khi hàm thực thi hoàn tất, đề tài cài đặt một tiến trình giám sát nền (**Background Monitor Thread**) sử dụng thư viện `psutil`. Luồng giám sát tiến hành lấy mẫu chỉ số bộ nhớ thực tế (**Resident Set Size - RSS**) của tiến trình Python với chu kỳ cực ngắn **1 mili-giây (1 ms)** trong suốt thời gian hàm xử lý đang chạy:
- `baseline_ram_mb`: Mức chiếm dụng RAM tại thời điểm bắt đầu tác vụ.
- `peak_ram_mb`: Mức chiếm dụng RAM cực đại ghi nhận được trong suốt quá trình xử lý.
- `delta_ram_mb`: Chênh lệch tài nguyên phát sinh do tác vụ ($\Delta \text{RAM} = \text{peak\_ram} - \text{baseline\_ram}$).

Mỗi kịch bản được lặp lại 5 lần, ghi nhận thời gian trung vị (`median_ms`), thời gian trung bình (`mean_ms`) và độ lệch chuẩn (`std_ms`).
