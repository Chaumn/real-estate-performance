# CHƯƠNG 3: XÂY DỰNG BỘ DỮ LIỆU VÀ ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU

Chương này trình bày quy trình kỹ nghệ dữ liệu nhằm giải quyết **Câu hỏi nghiên cứu 1 (RQ1)**: xây dựng pipeline nạp luồng và làm sạch dữ liệu lớn có kiểm soát từ kho dữ liệu bất động sản thực tế, đồng thời thực hiện kiểm toán hồ sơ dữ liệu (Data Profiling) và phân tích khám phá (EDA) để đánh giá toàn diện chất lượng và đặc trưng phân phối của tập dữ liệu thực nghiệm.

---

## 3.1. Quy trình thu thập dữ liệu dòng từ Hugging Face

### 3.1.1. Nguồn dữ liệu và Cơ chế Streaming Shuffle Buffer
Bộ dữ liệu thực nghiệm được thu thập từ kho lưu trữ mã nguồn mở Hugging Face với định danh `Phuscca/vietnam-real-estates` (tập phân chia `train`). Đây là tập dữ liệu tổng hợp thực tế về các tin đăng bất động sản trên toàn lãnh thổ Việt Nam.

Để quản lý việc nạp dữ liệu trong điều kiện tài nguyên bộ nhớ có giới hạn và thiết lập khả năng kiểm soát thí nghiệm, quy trình thu thập dữ liệu được thiết kế theo mô hình **Đọc dòng dữ liệu (Streaming Ingestion)** kết hợp với **Bộ đệm xáo trộn (Shuffle Buffer)** thông qua thư viện Hugging Face `datasets`:
- **Tham số nạp dòng:** Sử dụng cấu hình `load_dataset("Phuscca/vietnam-real-estates", split="train", streaming=True)`. Dữ liệu được tiếp nhận tuần tự qua kết nối mạng theo từng luồng nhị phân, không nạp toàn bộ tập dữ liệu thô vào bộ nhớ RAM.
- **Bộ đệm xáo trộn có kiểm soát:** Sử dụng phương thức `.shuffle(seed=42, buffer_size=10000)`. Cơ chế này duy trì một hàng đợi vòng (circular buffer) có dung lượng cố định là 10.000 bản ghi. Mỗi khi một bản ghi được trích xuất dựa trên giá trị mầm xác định (`seed = 42`), một bản ghi tiếp theo từ luồng dữ liệu nguồn sẽ được nạp bổ sung vào bộ đệm.
- **Kích thước khối xử lý (Batch Processing):** Dữ liệu từ luồng shuffle được gom thành các lô xử lý có kích thước `batch_size = 2000` dòng trước khi đưa vào module làm sạch và kiểm định.

### 3.1.2. Tính xác định và Giới hạn của Dataset Revision
Trong các nghiên cứu thực nghiệm khoa học dữ liệu, tính tái lập là một tiêu chí then chốt. Quy trình nạp luồng của đề tài được cố định với giá trị `seed = 42`, `buffer_size = 10,000` và `batch_size = 2,000`. 

Tuy nhiên, về mặt phương pháp luận, cần làm rõ một giới hạn quan trọng: trong báo cáo trích xuất thực tế ([`results/build_report_500000.json`](results/build_report_500000.json)), trường `revision` được ghi nhận ở trạng thái `null` do thư viện nạp từ commit mặc định của kho lưu trữ nguồn tại thời điểm chạy. Do đó, tính tái lập hoàn toàn của tập dữ liệu phụ thuộc vào giả định rằng kho dữ liệu upstream `Phuscca/vietnam-real-estates` trên Hugging Face không bị chỉnh sửa hoặc ghi đè lịch sử commit. Để đảm bảo tính minh bạch và khả năng tái lập trong tương lai, toàn bộ ba tập dữ liệu CSV chuẩn hóa đã trích xuất (50K, 200K, 500K) được lưu trữ cục bộ trong thư mục `data/processed/` (được đưa vào `.gitignore` để tránh phình kích thước kho lưu trữ Git do tổng dung lượng vượt quá 147 MB). Danh mục kiểm toán định danh, số dòng, kích thước byte chính xác và mã băm SHA-256 đối soát của cả ba tập dữ liệu được công bố chi tiết tại tệp [`report/dataset_manifest.json`](report/dataset_manifest.json). Nghiên cứu cung cấp quy trình tái lập hoàn toàn tự động thông qua script `scripts/build_large_dataset.py`, cho phép người dùng độc lập tái tạo chính xác ba tập dữ liệu từ nguồn và kiểm tra đối soát mã băm.

---

## 3.2. Bộ quy tắc làm sạch dữ liệu và Hợp đồng 9 thuộc tính

### 3.2.1. Tiêu chí toàn vẹn và Xử lý giá trị khuyết thiếu nghiệp vụ
Module làm sạch dữ liệu (`scripts/cleaning.py`) được thiết kế nhằm bảo toàn tính chân thực của phân phối thị trường, chỉ loại bỏ các bản ghi vi phạm tính toàn vẹn bắt buộc:
1. **Chuẩn hóa chuỗi văn bản (String Trimming):** Loại bỏ toàn bộ các ký tự khoảng trắng dư thừa, ký tự xuống dòng (`\r`, `\n`) và ký tự tab ở đầu và cuối của các trường văn bản bằng phương thức `.str.strip()`. Thao tác này bảo toàn các điểm mã UTF-8 tiếng Việt tự nhiên mà không cưỡng chế chuyển đổi chuẩn Unicode NFC nhằm tránh biến dạng chuỗi gốc.
2. **Quy tắc 6 trường bắt buộc (Mandatory Columns):** Một bản ghi bị xem là không hợp lệ và bị loại bỏ nếu thiếu một trong 6 thông tin cốt lõi: `name` (tiêu đề tin đăng), `property_type_name` (loại hình bất động sản), `province_name` (tỉnh/thành phố), `area` (diện tích), `published_at` (thời điểm đăng tin), hoặc không thể phân tích cú pháp ngày tháng hợp lệ.
3. **Quy tắc làm sạch diện tích (`area`):** Thuộc tính `area` bắt buộc phải là số thực dương hữu hạn ($area > 0$ và không phải giá trị `NaN` hoặc `Inf`). Các bản ghi có diện tích bằng 0, số âm hoặc để trống bị loại bỏ khỏi tập dữ liệu.
4. **Quy tắc xử lý giá bán (`price`):** Trong thực tế thị trường bất động sản, nhiều tin đăng có giá bán ở dạng "thương lượng", "giá thỏa thuận" hoặc "liên hệ trực tiếp". Quy tắc kỹ thuật quy định: các giá trị giá không hợp lệ, không dương ($\le 0$) hoặc để trống sẽ được **chuyển đổi thành giá trị rỗng (SQL NULL)** thay vì loại bỏ bản ghi. Quyết định kỹ thuật này giúp bảo toàn mẫu số quan sát cho các bài toán phân tích phân bố không gian và diện tích.
5. **Quy tắc xử lý địa chỉ chi tiết (`district_name`, `ward_name`):** Các giá trị chuỗi rỗng hoặc chuỗi ký tự không có ý nghĩa được chuyển đổi về giá trị chuẩn SQL NULL.
6. **Cơ chế phát sinh định danh duy nhất (`id`):** Thuộc tính `id` được cấp phát tuần tự từ 1 đến $N$ sau khi bản ghi đã vượt qua toàn bộ các bước lọc kiểm tra, bảo đảm tính liên tục tuyệt đối và đóng vai trò khóa chính.

Bảng 3.1 tổng hợp hợp đồng 9 thuộc tính chuẩn hóa cuối cùng được xuất ra các tệp dữ liệu thực nghiệm.

**Bảng 3.1: Đặc tả cấu trúc lược đồ dữ liệu chuẩn hóa (9 thuộc tính)**

| STT | Tên thuộc tính | Kiểu dữ liệu Python | Kiểu dữ liệu PostgreSQL | Tính chất | Mô tả nghiệp vụ |
| :---: | :--- | :--- | :--- | :---: | :--- |
| 1 | `id` | `int64` | `BIGINT` | NOT NULL, PK | Khóa chính định danh duy nhất cho từng tin đăng (tăng tuần tự từ 1) |
| 2 | `name` | `object` (str) | `TEXT` | NOT NULL | Tiêu đề chi tiết của tin đăng bất động sản |
| 3 | `property_type_name` | `object` (str) | `TEXT` | NOT NULL | Phân loại loại hình bất động sản (5 nhóm danh mục chuẩn) |
| 4 | `province_name` | `object` (str) | `TEXT` | NOT NULL | Tên tỉnh/thành phố trực thuộc trung ương |
| 5 | `district_name` | `object` (str) | `TEXT` | NULLABLE | Tên quận/huyện/thị xã (cho phép NULL nếu thiếu thông tin) |
| 6 | `ward_name` | `object` (str) | `TEXT` | NULLABLE | Tên phường/xã/thị trấn (cho phép NULL nếu thiếu thông tin) |
| 7 | `price` | `float64` | `NUMERIC` | NULLABLE | Giá chào bán niêm yết (Đơn vị: VNĐ; NULL nếu giá thỏa thuận) |
| 8 | `area` | `float64` | `DOUBLE PRECISION` | NOT NULL | Diện tích sử dụng hoặc diện tích đất (Đơn vị: m²; bắt buộc > 0) |
| 9 | `published_at` | `datetime64[ns]` | `TIMESTAMP WITHOUT TIME ZONE` | NOT NULL | Dấu thời gian đăng tin niêm yết (Định dạng: YYYY-MM-DD HH:MM:SS) |

---

## 3.3. Lược đồ cơ sở dữ liệu quan hệ trên PostgreSQL

Cấu trúc bảng lưu trữ trong cơ sở dữ liệu PostgreSQL (`real_estate_db`) được thiết lập theo đúng tệp đặc tả chuẩn [`sql/schema.sql`](sql/schema.sql):

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
- `properties_area_positive`: Đảm bảo diện tích luôn lớn hơn 0 trên tầng lưu trữ vật lý.
- `properties_price_positive`: Đảm bảo giá trị giá nếu khác NULL thì bắt buộc phải là một số thực dương.

Dữ liệu được nạp vào cơ sở dữ liệu thông qua giao thức truyền tải dòng nhị phân **Psycopg 3 Binary COPY** (`COPY public.properties FROM STDIN (FORMAT CSV, HEADER TRUE)`), với cơ chế kiểm soát giao dịch toàn vẹn (Transactional Commit / Rollback) và khóa bảng `SHARE ROW EXCLUSIVE` trong suốt quá trình nạp để ngăn ngừa xung đột dữ liệu.

---

## 3.4. Kết quả Profiling và Phân tích khám phá dữ liệu (EDA)

> [!NOTE]
> Các nội dung và số liệu trình bày trong Mục 3.4 này là kết quả kiểm toán hồ sơ dữ liệu (Data Profiling) và phân tích khám phá (Exploratory Data Analysis - EDA) trên tập dữ liệu chuẩn hóa 500.000 bản ghi nhằm đánh giá chất lượng và đặc trưng phân phối dữ liệu đầu vào (phục vụ RQ1). Đây hoàn toàn **không phải là kết quả đo đạc benchmark hiệu năng hệ thống** (kết quả benchmark hiệu năng nạp, xử lý DataFrame và truy vấn PostgreSQL được trình bày riêng tại Chương 5).

### 3.4.1. Thống kê khuyết thiếu và Kiểm toán nạp dòng
Quá trình trích xuất và lọc dòng trên tập quy mô 500.000 bản ghi được ghi nhận chi tiết tại tệp [`results/build_report_500000.json`](results/build_report_500000.json) và tổng hợp tại Bảng 3.2.

**Bảng 3.2: Kết quả kiểm toán quá trình thu thập và lọc dòng dữ liệu (500K)**

| Chỉ số kiểm toán dữ liệu | Giá trị định lượng | Tỷ lệ (%) | Ý nghĩa kỹ thuật |
| :--- | :---: | :---: | :--- |
| **Tổng số dòng nguồn đã đọc (`source_rows_read`)** | **502.000** | 100.00% | Số lượng bản ghi tiếp nhận từ luồng dữ liệu Hugging Face |
| **Tổng số dòng không hợp lệ bị loại (`invalid_rows`)** | **203** | 0.04% | Bản ghi vi phạm các điều kiện toàn vẹn bắt buộc |
| - *Lỗi thiếu trường bắt buộc (`invalid_required`)* | 202 | 0.04% | Thiếu tiêu đề, phân loại, tỉnh/thành phố hoặc ngày đăng |
| - *Lỗi diện tích không hợp lệ (`invalid_area`)* | 1 | <0.001% | Diện tích không hữu hạn hoặc $\le 0$ |
| - *Lỗi định dạng ngày đăng (`invalid_date`)* | 0 | 0.00% | Toàn bộ dấu thời gian đều hợp lệ |
| **Số dòng hợp lệ tiếp nhận (`valid_rows_seen`)** | **501.797** | 99.96% | Dòng đạt chuẩn sau khi đi qua bộ lọc làm sạch |
| **Số dòng hợp lệ dư dôi (`valid_rows_not_exported`)** | **1.797** | 0.36% | Dòng nằm trong batch cuối cùng sau khi đã đủ 500K |
| **Tổng số bản ghi thực xuất (`exported_rows`)** | **500.000** | 99.60% | Tập dữ liệu chuẩn hóa phục vụ thực nghiệm |

Kết quả phân tích kiểm toán chất lượng dữ liệu ([`results/quality/data_quality_report_500000.json`](results/quality/data_quality_report_500000.json)) ghi nhận các tỷ lệ khuyết thiếu thực tế:
- Sáu trường thông tin bắt buộc (`id`, `name`, `property_type_name`, `province_name`, `area`, `published_at`) đạt độ đầy đủ **100,00%** (0 bản ghi khuyết thiếu).
- Trường `district_name` thiếu đúng **14.235 bản ghi** (chiếm **2,85%** tổng số hàng).
- Trường `ward_name` thiếu đúng **72.150 bản ghi** (chiếm **14,43%** tổng số hàng).
- Trường giá chào bán (`price`) thiếu đúng **39.061 bản ghi** (chiếm **7,81%** tổng số hàng), tương ứng với 460.939 tin đăng có giá bán cụ thể.

![Tỷ lệ dữ liệu khuyết thiếu trên các thuộc tính bất động sản](results/eda/missing_values_bar.png)
*Hình 3.1: Tỷ lệ dữ liệu khuyết thiếu trên các thuộc tính bất động sản (500K bản ghi)*

### 3.4.2. Phân bố loại hình bất động sản và Địa bàn hành chính
Tập dữ liệu chuẩn hóa 500.000 bản ghi bao phủ 5 danh mục loại hình bất động sản:
1. **Nhà riêng:** 230.412 tin đăng (chiếm **46,08%**).
2. **Đất:** 120.576 tin đăng (chiếm **24,12%**).
3. **Căn hộ chung cư:** 104.107 tin đăng (chiếm **20,82%**).
4. **Biệt thự/Nhà liền kề:** 36.611 tin đăng (chiếm **7,32%**).
5. **Shophouse:** 8.294 tin đăng (chiếm **1,66%**).

![Phân bố số lượng tin đăng theo loại hình bất động sản](results/eda/property_type_count.png)
*Hình 3.2: Phân bố số lượng tin đăng theo loại hình bất động sản*

Về mặt phân bố địa lý hành chính, tập dữ liệu bao phủ toàn bộ 63 tỉnh/thành phố, 588 quận/huyện và 3.370 phường/xã trên toàn quốc. Các địa bàn có mật độ tin đăng tập trung lớn nhất:
- **TP. Hồ Chí Minh:** 186.698 tin đăng (chiếm **37,34%**).
- **Hà Nội:** 170.167 tin đăng (chiếm **34,03%**).
- **Đà Nẵng:** 25.772 tin đăng (chiếm **5,15%**).
- **Bình Dương:** 21.399 tin đăng (chiếm **4,28%**).
- **Khánh Hòa:** 13.893 tin đăng (chiếm **2,78%**).
- **Hải Phòng:** 10.422 tin đăng (chiếm **2,08%**).
- **Hưng Yên:** 9.061 tin đăng (chiếm **1,81%**).
- **Đồng Nai:** 8.308 tin đăng (chiếm **1,66%**).
- **Long An:** 7.011 tin đăng (chiếm **1,40%**).
- **Bà Rịa - Vũng Tàu:** 6.706 tin đăng (chiếm **1,34%**).

Hai đại đô thị Hà Nội và TP. Hồ Chí Minh chiếm tổng cộng 71,37% toàn bộ tin đăng trong tập dữ liệu. Thành phố Hải Phòng có đúng 10.422 tin đăng (2,08%), tạo nên một tập con có độ chọn lọc vừa phải (selectivity $\approx 2,08\%$) để kiểm thử bài toán lọc đơn cột Q1. Quận Cầu Giấy (Hà Nội) là một trong những địa bàn có mật độ giao dịch dày đặc, được lựa chọn làm điều kiện lọc cho bài toán Q2.

![Top các tỉnh/thành phố có mật độ tin đăng lớn nhất Việt Nam](results/eda/province_distribution.png)
*Hình 3.3: Top các tỉnh/thành phố có mật độ tin đăng lớn nhất Việt Nam*

### 3.4.3. Thống kê mô tả định lượng vững (Robust Statistics)
Do dữ liệu giá cả và diện tích bất động sản có đặc thù phân tán cực mạnh và chứa các giá trị siêu tài sản (khách sạn, dự án đô thị hàng trăm tỷ đồng), việc sử dụng giá trị trung bình (Mean) và độ lệch chuẩn (Standard Deviation) sẽ bị bóp méo nghiêm trọng. Nghiên cứu xác lập các chỉ số thống kê mô tả vững dựa trên Trung vị (Median) và Khoảng tứ phân vị (IQR) tại Bảng 3.3.

**Bảng 3.3: Thống kê mô tả định lượng vững trên tập dữ liệu 500.000 bản ghi**

| Tham số thống kê | Diện tích (m²) | Giá chào bán (VNĐ) | Đơn giá (VNĐ/m²) |
| :--- | :---: | :---: | :---: |
| **Số lượng quan sát ($N$)** | 500.000 | 460.939 | 460.939 |
| **Giá trị nhỏ nhất (Min)** | 3,16 m² | 1.000 VNĐ | 0,12 VNĐ/m² |
| **Tứ phân vị thứ nhất ($Q_1$)** | **45,0 m²** | **4,10 tỷ VNĐ** | **58,33 triệu/m²** |
| **Trung vị ($Median - Q_2$)** | **80,0 m²** | **7,40 tỷ VNĐ** | **97,56 triệu/m²** |
| **Tứ phân vị thứ ba ($Q_3$)** | **109,1 m²** | **14,30 tỷ VNĐ** | **194,92 triệu/m²** |
| **Giá trị lớn nhất (Max)** | 24.000.000 m² | 920.000 tỷ VNĐ | 3.758 tỷ VNĐ/m² |
| **Giá trị trung bình ($Mean$)** | 444,40 m² | 20,78 tỷ VNĐ | 161,55 triệu/m² |
| **Khoảng tứ phân vị ($IQR$)** | **64,1 m²** | **10,20 tỷ VNĐ** | **136,59 triệu/m²** |
| **Độ lệch chuẩn ($Std$)** | 56.043,84 m² | 1.515 tỷ VNĐ | 6,03 tỷ VNĐ/m² |

Kết quả profiling chỉ ra rằng:
- Trung vị diện tích bất động sản là **80,0 m²**, tập trung chủ yếu trong khoảng tứ phân vị từ 45,0 m² đến 109,1 m² ($IQR = 64,1$ m²).
- Trung vị giá chào bán là **7,40 tỷ VNĐ**, trong khi giá trị trung bình lên tới 20,78 tỷ VNĐ (lớn gấp 2,8 lần trung vị do sự xuất hiện của các ngoại lệ cực lớn). Khoảng tứ phân vị của giá bán dao động từ **4,10 tỷ VNĐ ($Q_1$) đến 14,30 tỷ VNĐ ($Q_3$)**, với $IQR = 10,20$ tỷ VNĐ.
- Khoảng giá $Q_1 \rightarrow Q_3$ (4,10 tỷ đến 14,30 tỷ VNĐ) phản ánh phân khúc nhà ở giao dịch phổ biến nhất của thị trường, và đây chính là căn cứ thực nghiệm để thiết lập khoảng lọc giá `price BETWEEN 4100000000 AND 14300000000` trong bài toán benchmark Q2.

![Phân bố giá chào bán bất động sản (Thang đo Logarithmic)](results/eda/price_distribution.png)
*Hình 3.4: Phân bố giá chào bán bất động sản (Thang đo Logarithmic)*

![Phân bố diện tích bất động sản (Thang đo Logarithmic)](results/eda/area_distribution.png)
*Hình 3.5: Phân bố diện tích bất động sản (Thang đo Logarithmic)*

![Phân bố giá chào bán theo từng loại hình bất động sản (Boxplot)](results/eda/price_by_property_type_boxplot.png)
*Hình 3.6: Phân bố giá chào bán theo từng loại hình bất động sản (Boxplot)*

![Đơn giá chào bán trung vị (Triệu/m²) tại các địa phương trọng điểm](results/eda/price_per_m2_by_province.png)
*Hình 3.7: Đơn giá chào bán trung vị (Triệu/m²) tại các địa phương trọng điểm*

![Mật độ tương quan giữa giá và diện tích bất động sản (Hexbin Plot)](results/eda/price_vs_area_scatter.png)
*Hình 3.8: Mật độ tương quan giữa giá và diện tích bất động sản (Hexbin Plot)*

### 3.4.4. Xu hướng thời gian và Phân tích tương quan Spearman
Hình 3.9 khảo sát sự biến thiên của mật độ tin đăng theo trục thời gian `published_at`. Dòng dữ liệu trải dài liên tục từ năm 2023 đến hết năm 2025, phản ánh tính liên tục của các đợt cập nhật thông tin niêm yết trên thị trường.

![Xu hướng số lượng tin đăng bất động sản theo thời gian đăng tin](results/eda/monthly_listings_trend.png)
*Hình 3.9: Xu hướng số lượng tin đăng bất động sản theo thời gian đăng tin*

Để đánh giá mức độ phụ thuộc giữa các biến số định lượng mà không bị chi phối bởi các ngoại lệ cực trị, nghiên cứu tính toán hệ số tương quan hạng Spearman ($\rho$):
- Tương quan giữa Diện tích (`area`) và Giá chào bán (`price`): $\rho = 0,584$ (tương quan thuận mức độ trung bình khá).
- Tương quan giữa Giá chào bán (`price`) và Đơn giá (`price_per_m2`): $\rho = 0,621$ (tương quan thuận khá chặt chẽ).
- Tương quan giữa Diện tích (`area`) và Đơn giá (`price_per_m2`): $\rho = -0,182$ (tương quan nghịch nhẹ, phù hợp với quy luật kinh tế: bất động sản diện tích lớn thường có đơn giá trên mỗi mét vuông giảm nhẹ so với các bất động sản diện tích nhỏ).

![Ma trận hệ số tương quan phi tuyến Spearman giữa các biến định lượng](results/eda/numeric_correlation_heatmap.png)
*Hình 3.10: Ma trận hệ số tương quan phi tuyến Spearman giữa các biến định lượng*

### 3.4.5. Kiểm toán bản ghi trùng lặp
Module phân tích chất lượng dữ liệu ghi nhận:
- Không tồn tại bất kỳ bản ghi nào trùng lặp khóa chính `id` (0 bản ghi).
- Trùng lặp hoàn toàn trên toàn bộ 8 thuộc tính còn lại (ngoại trừ `id`): chỉ có đúng **2 bản ghi** (tỷ lệ xấp xỉ 0,00%).
- Trùng lặp nghi ngờ nội dung tin đăng: có **57.808 bản ghi** (chiếm **11,56%**). Hiện tượng này xảy ra do cùng một bất động sản được nhiều đại lý/môi giới đăng tin nhiều lần ở các thời điểm khác nhau với nội dung tiêu đề và thông số cơ bản giống nhau. Việc giữ nguyên các bản ghi này bảo đảm tính trung thực lịch sử của dòng dữ liệu thu thập từ thị trường niêm yết thực tế.

