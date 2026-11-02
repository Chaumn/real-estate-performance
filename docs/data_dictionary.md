# Từ Điển Dữ Liệu Bất Động Sản (Data Dictionary)

> **Dự án:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn.  
> **Phiên bản:** 2.0 (Bao gồm 9 cột schema cơ sở dữ liệu benchmark và 15 đặc trưng dẫn xuất phân tích).

---

## 1. Schema CSDL PostgreSQL Benchmark (9 Cột Cốt Lõi)

Bảng dữ liệu trong PostgreSQL: `public.properties`. Schema này là **bất biến**, được kiểm thử và bảo toàn tuyệt đối để đảm bảo khả năng tái lập và đối sánh của các thí nghiệm hiệu năng Q1–Q4.

| Tên Cột (Column Name) | Kiểu Dữ Liệu SQL | Kiểu Dữ Liệu Pandas | Cho Phép NULL? | Ràng Buộc / Ranh Giới Hợp Lệ | Mô Tả Nghiệp Vụ & Ý Nghĩa Kỹ Thuật | Vai Trò Trong Benchmark |
|---|---|---|:---:|---|---|---|
| `id` | `BIGINT PRIMARY KEY` | `int64` | **Không** | $1 \le id \le N$, Đơn điệu tăng | Mã định danh duy nhất của từng bản ghi tin đăng | Khóa chính, clustered B-tree index mặc định |
| `name` | `TEXT` | `string` | **Không** | Chuỗi không rỗng, giữ dấu tiếng Việt | Tiêu đề tin đăng nguyên bản từ sàn giao dịch | Đối tượng so khớp hoặc quét chuỗi |
| `property_type_name` | `VARCHAR(100)` | `string` | **Không** | {Nhà, Đất, Căn hộ chung cư, Biệt thự/Nhà liền kề, Shophouse, ...} | Phân loại phân khúc hình thức bất động sản | Dùng trong kiểm thử Q4 (Aggregation Control) |
| `province_name` | `VARCHAR(100)` | `string` | **Không** | 63 tỉnh/thành phố chuẩn hóa của Việt Nam | Địa phương cấp tỉnh/thành phố | Trường lọc chính của bài toán Q1 và Q2 |
| `district_name` | `VARCHAR(100)` | `string` | **Có** | Tên quận/huyện hợp lệ hoặc NULL | Địa phương cấp quận/huyện | Thuộc tính lọc thứ cấp |
| `ward_name` | `VARCHAR(100)` | `string` | **Có** | Tên phường/xã hợp lệ hoặc NULL | Địa phương cấp phường/xã | Thuộc tính lọc chi tiết |
| `price` | `NUMERIC(15, 2)` | `float64` | **Có** | $price > 0$ hoặc `NULL` (tin thỏa thuận) | Giá chào bán niêm yết (Đơn vị: VNĐ) | Trường lọc phạm vi (Range Filter) trong Q2 |
| `area` | `NUMERIC(10, 2)` | `float64` | **Không** | $area > 0$ m², không vô hạn | Diện tích bất động sản niêm yết (Đơn vị: m²) | Điều kiện lọc phạm vi trong Q3 |
| `published_at` | `TIMESTAMP` | `datetime64[ns]` | **Không** | ISO8601 (`YYYY-MM-DD HH:MM:SS.ffffff`) | Mốc thời gian xuất bản tin đăng lên hệ thống | Trường sắp xếp `ORDER BY ... DESC` trong Q2 |

---

## 2. Đặc Trưng Dẫn Xuất Phục Vụ Khoa Học Dữ Liệu (15 Feature Mới)

Các đặc trưng này được lưu trữ độc lập tại `results/features/properties_500000_enriched.parquet` nhằm phục vụ phân tích dữ liệu chuyên sâu (EDA), phân nhóm thị trường (Market Segmentation) và kỹ thuật tính toán song song, **hoàn toàn không làm biến đổi cấu trúc bảng 9 cột của cơ sở dữ liệu**.

| Tên Đặc Trưng | Kiểu Dữ Liệu | Công Thức / Quy Tắc Xây Dựng | Miền Giá Trị Hợp Lệ | Mô Tả Nghiệp Vụ & Ứng Dụng |
|---|---|---|---|---|
| `price_per_m2` | `float64` | `price / area` (nếu price not null) | $0.12$ đ $\rightarrow 3.76$ nghìn tỷ đ/m² | Đơn giá chuẩn hóa trên một mét vuông diện tích; chỉ số so sánh giá trị tương đối giữa các bất động sản khác quy mô. |
| `published_year` | `Int64` | `published_at.dt.year` | $2024 - 2026$ | Năm đăng tin; phục vụ phân vùng dữ liệu theo năm (Yearly Partitioning). |
| `published_month` | `Int64` | `published_at.dt.month` | $1 \le month \le 12$ | Tháng đăng tin; khảo sát tính chu kỳ mùa vụ bất động sản. |
| `published_day` | `Int64` | `published_at.dt.day` | $1 \le day \le 31$ | Ngày trong tháng. |
| `published_quarter` | `Int64` | `published_at.dt.quarter` | $1, 2, 3, 4$ | Quý tài chính đăng tin. |
| `published_day_of_week` | `Int64` | `published_at.dt.dayofweek` | $0$ (Thứ Hai) $\rightarrow 6$ (Chủ Nhật) | Ngày trong tuần; phục vụ phân tích hành vi người dùng. |
| `is_weekend` | `int64` | `1` nếu `dayofweek in [5, 6]` ngược lại `0` | $\{0, 1\}$ | Cờ nhị phân đánh dấu tin đăng vào cuối tuần (Thứ 7 / CN). |
| `area_segment` | `string` | Chia nhóm diện tích theo tiêu chuẩn quy hoạch đô thị | {`Dưới 30m2`, `30-60m2`, `60-100m2`, `100-200m2`, `Trên 200m2`} | Phân khúc diện tích chuẩn hóa, thay thế cho các phép so sánh số học tốn kém. |
| `price_segment` | `string` | Phân nhóm khoảng giá ngân sách | {`Thỏa thuận`, `Dưới 2 tỷ`, `2 - 5 tỷ`, `5 - 10 tỷ`, `10 - 20 tỷ`, `Trên 20 tỷ`} | Phân khúc tài chính khách hàng, hỗ trợ phân loại nhanh trên giao diện tìm kiếm. |
| `has_district` | `int64` | `1` nếu `district_name is not null` ngược lại `0` | $\{0, 1\}$ | Chỉ báo mức độ hoàn chỉnh thông tin địa lý cấp quận. |
| `has_ward` | `int64` | `1` nếu `ward_name is not null` ngược lại `0` | $\{0, 1\}$ | Chỉ báo mức độ hoàn chỉnh thông tin địa lý cấp xã/phường. |
| `is_price_outlier` | `int64` | `1` nếu $price > Q_3 + 1.5 \times IQR$ hoặc $price < Q_1 - 1.5 \times IQR$ | $\{0, 1\}$ | Cờ đánh dấu tin đăng có mức giá cực trị (biệt thự siêu sang hoặc lỗi niêm yết). |
| `is_area_outlier` | `int64` | `1` nếu $area > Q_3 + 1.5 \times IQR$ hoặc $area < Q_1 - 1.5 \times IQR$ | $\{0, 1\}$ | Cờ đánh dấu bất động sản diện tích cực lớn (đất nông nghiệp/dự án). |
| `name_length` | `int64` | `len(name)` | $1 \le length \le 1,000$ | Chiều dài tiêu đề tin đăng (tính theo số ký tự). |
| `name_word_count` | `int64` | Số từ cách nhau bởi khoảng trắng trong `name` | $1 \le word\_count \le 200$ | Số lượng từ trong tiêu đề; đánh giá độ chi tiết của tiêu đề. |

---

## 3. Khuyến Nghị Đánh Chỉ Mục (Indexing Suitability Matrix)

Dựa trên tần suất truy vấn và tính chất phân bố thống kê:

| Thuộc Tính / Đặc Trưng | Loại Chỉ Mục Khuyến Nghị | Ghi Chú Kỹ Thuật |
|---|---|---|
| `province_name` | `B-Tree` | Hiệu quả cao khi độ chọn lọc (selectivity) $< 15\%$; chuyển Bitmap Scan khi dữ liệu lớn. |
| `(province_name, price, published_at)` | `Composite B-Tree` | Tối ưu toàn diện cho Q2: Index Filter + Index Order (không tốn chi phí Sort). |
| `area` | `B-Tree` | Hỗ trợ tìm kiếm theo khoảng diện tích trong Q3. |
| `published_at` | `BRIN` (Block Range Index) | Cực kỳ hiệu quả nếu dữ liệu nhập theo trình tự thời gian (append-only), dung lượng chỉ mục chỉ chiếm $< 1\%$ B-Tree. |
| `price_per_m2` | `B-Tree (Functional Index)` | Có thể tạo `CREATE INDEX idx_price_m2 ON properties ((price / area))` nếu có truy vấn lọc theo đơn giá. |

