# Từ Điển Dữ Liệu Bất Động Sản (Data Dictionary)

> **Dự án:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn.  
> **Phiên bản:** Đối chiếu chính xác theo `sql/schema.sql` và mã nguồn `scripts/feature_engineering.py`.

---

## 1. Schema CSDL PostgreSQL Benchmark (9 Cột Chuẩn Hóa)

Bảng dữ liệu trong PostgreSQL: `public.properties`. Schema này là **bất biến**, được kiểm thử và bảo toàn nguyên trạng để phục vụ các thí nghiệm hiệu năng SQL Q1–Q4.

| Tên Cột (Column Name) | Kiểu Dữ Liệu SQL | Kiểu Dữ Liệu Pandas | Cho Phép NULL? | Ràng Buộc / Constraint SQL | Mô Tả Nghiệp Vụ & Ý Nghĩa Kỹ Thuật | Vai Trò Trong Benchmark |
|---|---|---|:---:|---|---|---|
| `id` | `BIGINT PRIMARY KEY` | `int64` | **Không** | $1 \le id \le N$, Primary Key | Khóa chính định danh duy nhất của từng tin đăng | PostgreSQL tự động tạo chỉ mục B-tree duy nhất (`properties_pkey`); bảng không tự động sắp xếp vật lý (không auto-cluster) |
| `name` | `TEXT` | `string` | **Không** | `NOT NULL`, `CHECK (BTRIM(name) <> '')` | Tiêu đề tin đăng nguyên bản từ nguồn thu thập | Thuộc tính văn bản chứa tên bất động sản |
| `property_type_name` | `TEXT` | `string` | **Không** | `NOT NULL`, `CHECK (BTRIM(property_type_name) <> '')` | Phân loại loại hình bất động sản (Nhà, Đất, Căn hộ chung cư, Biệt thự/Nhà liền kề, Shophouse) | Cột gom nhóm trong bài toán Q4 (Aggregation Control) |
| `province_name` | `TEXT` | `string` | **Không** | `NOT NULL`, `CHECK (BTRIM(province_name) <> '')` | Địa phương cấp tỉnh/thành phố (Hồ Chí Minh, Hà Nội, Đà Nẵng, ...) | Trường lọc chính của bài toán Q1 và điều kiện dẫn đầu trong Q2 |
| `district_name` | `TEXT` | `string` | **Có** | Cho phép NULL | Địa phương cấp quận/huyện | Điều kiện lọc kết hợp trong bài toán Q2 |
| `ward_name` | `TEXT` | `string` | **Có** | Cho phép NULL | Địa phương cấp xã/phường | Thuộc tính địa lý chi tiết |
| `price` | `NUMERIC` | `float64` | **Có** | `CHECK (price > 0)` khi khác NULL | Giá chào bán niêm yết (Đơn vị: VNĐ). NULL thể hiện tin "Giá thỏa thuận" | Trường lọc phạm vi trong Q2 (`price BETWEEN 4100000000 AND 14300000000`) và tính `AVG(price)` trong Q4 |
| `area` | `DOUBLE PRECISION` | `float64` | **Không** | `NOT NULL`, `CHECK (area > 0)` | Diện tích bất động sản niêm yết (Đơn vị: $m^2$) | Thuộc tính số thực dấu phẩy động độ chính xác kép |
| `published_at` | `TIMESTAMP WITHOUT TIME ZONE` | `datetime64[ns]` | **Không** | `NOT NULL` (Định dạng ISO8601) | Mốc thời gian xuất bản tin đăng | Trường lọc ngày trong bài toán Q3 (`WHERE published_at::date = ...` vs Range scan) |

---

## 2. Đặc Trưng Dẫn Xuất Phục Vụ Khoa Học Dữ Liệu (15 Đặc Trưng Mới)

Các đặc trưng này được tạo bởi `scripts/feature_engineering.py` và lưu trữ độc lập tại `results/features/properties_500000_enriched.parquet` nhằm phục vụ phân tích dữ liệu chuyên sâu (EDA), phân nhóm thị trường và đo lường xử lý đa luồng. **Các đặc trưng này hoàn toàn tách biệt, không thêm vào bảng PostgreSQL nhằm bảo toàn row width và I/O block của benchmark.**

| Tên Đặc Trưng | Kiểu Dữ Liệu Parquet | Công Thức / Quy Tắc Xây Dựng | Miền Giá Trị Hợp Lệ | Mô Tả Nghiệp Vụ & Ứng Dụng |
|---|---|---|---|---|
| `price_per_m2` | `float64` | `price / area` (khi `price` khác NULL và `area > 0`) | $0.12$ đ $\rightarrow 3.76$ nghìn tỷ đ/m² | Đơn giá chuẩn hóa trên một mét vuông diện tích; chỉ số đánh giá tương quan giá trị giữa các bất động sản khác quy mô. |
| `published_year` | `Int64` | `published_at.dt.year` | $2024 - 2026$ | Năm đăng tin; phục vụ phân vùng dữ liệu theo năm. |
| `published_month` | `Int64` | `published_at.dt.month` | $1 \le month \le 12$ | Tháng đăng tin; khảo sát chu kỳ theo mùa. |
| `published_day` | `Int64` | `published_at.dt.day` | $1 \le day \le 31$ | Ngày trong tháng. |
| `published_quarter` | `Int64` | `published_at.dt.quarter` | $1, 2, 3, 4$ | Quý đăng tin. |
| `published_day_of_week` | `Int64` | `published_at.dt.dayofweek` | $0$ (Thứ Hai) $\rightarrow 6$ (Chủ Nhật) | Ngày trong tuần (Monday=0). |
| `is_weekend` | `int64` | `1` nếu `dayofweek in [5, 6]` ngược lại `0` | $\{0, 1\}$ | Cờ nhị phân đánh dấu tin đăng vào Thứ Bảy hoặc Chủ Nhật. |
| `area_segment` | `string` | Phân nhóm diện tích theo các ngưỡng $[0, 30, 60, 100, 200, \infty)$ | {`Dưới 30m2`, `30-60m2`, `60-100m2`, `100-200m2`, `Trên 200m2`} | Phân khúc diện tích chuẩn hóa đô thị. |
| `price_segment` | `string` | Phân nhóm giá theo các ngưỡng $[0, 2, 5, 10, 20, \infty)$ tỷ và NULL | {`Thỏa thuận`, `Dưới 2 tỷ`, `2 - 5 tỷ`, `5 - 10 tỷ`, `10 - 20 tỷ`, `Trên 20 tỷ`} | Phân khúc tài chính người mua. |
| `has_district` | `int64` | `1` nếu `district_name is not null` ngược lại `0` | $\{0, 1\}$ | Chỉ báo mức độ đầy đủ thông tin địa lý cấp quận/huyện. |
| `has_ward` | `int64` | `1` nếu `ward_name is not null` ngược lại `0` | $\{0, 1\}$ | Chỉ báo mức độ đầy đủ thông tin địa lý cấp xã/phường. |
| `is_price_outlier` | `int64` | `1` nếu $price > Q_3 + 1.5 \times IQR$ hoặc $price < Q_1 - 1.5 \times IQR$ | $\{0, 1\}$ | Cờ đánh dấu giá trị giá bán vượt ngưỡng IQR. |
| `is_area_outlier` | `int64` | `1` nếu $area > Q_3 + 1.5 \times IQR$ hoặc $area < Q_1 - 1.5 \times IQR$ | $\{0, 1\}$ | Cờ đánh dấu diện tích vượt ngưỡng IQR. |
| `name_length` | `int64` | `len(name)` | $1 \le length \le 1,000$ | Chiều dài tiêu đề tin đăng tính theo ký tự. |
| `name_word_count` | `int64` | Số từ cách nhau bởi khoảng trắng trong `name` | $1 \le word\_count \le 200$ | Số lượng từ trong tiêu đề tin đăng. |

---

## 3. Danh Mục Chỉ Mục Trong Thực Nghiệm PostgreSQL Benchmark

### 3.1. Các chỉ mục thực tế được thiết lập và đo đạc trong bộ thí nghiệm

| Tên Chỉ Mục (Index Name) | Câu Lệnh DDL Thực Tế | Kiểu Index | Mục Đích Thực Nghiệm Trong Bài Toán |
|---|---|---|---|
| `idx_properties_province_name` | `CREATE INDEX idx_properties_province_name ON public.properties USING btree (province_name);` | B-Tree đơn cột | Đo lường hiệu quả lọc địa phương trong bài toán Q1. |
| `idx_properties_location_price` | `CREATE INDEX idx_properties_location_price ON public.properties USING btree (province_name, district_name, price, id);` | B-Tree nhiều cột (Composite) | Đo lường hiệu quả kết hợp lọc điều kiện bình đẳng (`province_name`, `district_name`), lọc phạm vi (`price`) và hỗ trợ thứ tự sắp xếp (`price ASC, id ASC`) kết hợp `LIMIT 20` trong bài toán Q2. |
| `idx_properties_published_at` | `CREATE INDEX idx_properties_published_at ON public.properties USING btree (published_at);` | B-Tree đơn cột | So sánh giữa truy vấn dùng hàm bọc cột (`published_at::date`) và truy vấn sargable viết lại theo khoảng thời gian trong bài toán Q3. |
| `idx_properties_property_type` | `CREATE INDEX idx_properties_property_type ON public.properties USING btree (property_type_name);` | B-Tree đơn cột | Chứng minh trường hợp truy vấn tổng hợp toàn bảng không cải thiện hoặc bị planner bỏ qua trong bài toán Q4. |

### 3.2. Định hướng mở rộng lý thuyết (Chưa triển khai trong benchmark hiện tại)
- **Functional Index (Chỉ mục hàm):** Ví dụ `CREATE INDEX idx_price_m2 ON public.properties (((price / area)));` có thể phục vụ các truy vấn lọc trực tiếp theo đơn giá mỗi mét vuông.
- **BRIN (Block Range Index):** Chỉ mục khối thích hợp cho cột có tương quan vật lý cao với thứ tự nạp dữ liệu (như chuỗi thời gian nạp lũy tiến), giúp tiết kiệm không gian lưu trữ so với B-Tree.
