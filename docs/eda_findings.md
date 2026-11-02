# Báo Cáo Khám Phá Dữ Liệu Bất Động Sản (Exploratory Data Analysis - EDA Report)

> **Đề tài:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn.  
> **Quy mô tập dữ liệu phân tích:** 500,000 bản ghi thực tế đã làm sạch (`data/processed/properties_500000.csv`).  
> **Thư viện triển khai:** Python 3.13, Pandas, NumPy, Matplotlib, Seaborn (`scripts/run_eda.py`).

---

## 1. Tổng Quan & Cấu Trúc Khuyết Thiếu

Bộ dữ liệu chứa 500,000 bản ghi tin đăng bất động sản tại Việt Nam với 9 trường thông tin:

| Thuộc Tính | Số Bản Ghi Đầy Đủ | Số Lượng Thiếu | Tỷ Lệ Thiếu (%) | Nhận Định Dữ Liệu Thực Tế |
|---|---:|---:|---:|---|
| `id` | 500,000 | 0 | 0.00% | Mã định danh đơn điệu tăng từ 1 đến 500,000 |
| `name` | 500,000 | 0 | 0.00% | Tiêu đề tin đăng nguyên bản, bảo toàn byte tiếng Việt |
| `property_type_name` | 500,000 | 0 | 0.00% | 5 loại hình: Nhà, Đất, Căn hộ chung cư, Biệt thự/Nhà liền kề, Shophouse |
| `province_name` | 500,000 | 0 | 0.00% | Địa phương cấp tỉnh/thành phố, 100% bản ghi có giá trị |
| `district_name` | 485,765 | 14,235 | 2.85% | Khuyết thiếu do một số tin đăng chỉ ghi nhận địa giới cấp tỉnh |
| `ward_name` | 427,850 | 72,150 | 14.43% | Tỷ lệ khuyết thiếu tự nhiên ở khu vực ngoại thành hoặc chưa phân định |
| `price` | 460,939 | 39,061 | 7.81% | Giá niêm yết (asking price); bản ghi thiếu tương ứng tin đăng "Giá thỏa thuận" |
| `area` | 500,000 | 0 | 0.00% | Diện tích bắt buộc dương ($> 0\text{ m}^2$) |
| `published_at` | 500,000 | 0 | 0.00% | Mốc thời gian ISO8601 chuẩn xác |

![Biểu đồ tỷ lệ dữ liệu khuyết thiếu](../results/eda/missing_values_bar.png)

> [!NOTE]
> Giá trị cột `price` phản ánh **giá chào bán niêm yết** của người đăng tin, không đồng nhất với giá trị giao dịch thực tế đã công chứng. Khoảng 7.81% tin đăng để trống giá (thỏa thuận) được giữ nguyên dạng `NULL` để phục vụ các truy vấn kiểm tra điều kiện lọc.

---

## 2. Phân Tích Đơn Biến (Univariate Analysis)

### 2.1. Phân Bố Giá Chào Bán (`price`)
- **Tứ phân vị & Trung vị:** $Q_1 = 4.10$ tỷ VNĐ, Trung vị ($P_{50}$) = $7.40$ tỷ VNĐ, $Q_3 = 14.30$ tỷ VNĐ.
- **Khoảng tứ phân vị ($IQR$):** $IQR = Q_3 - Q_1 = 10.20$ tỷ VNĐ.
- **Giá trị ngoại vi:** $P_{95} = 47.00$ tỷ VNĐ, $P_{99} = 130.00$ tỷ VNĐ. Giá trị trung bình đạt $20.78$ tỷ VNĐ.
- **Hình dạng phân phối:** Phân phối lệch phải rõ rệt (Right-skewed). Khoảng cách giữa Trung vị ($7.4$ tỷ) và Trung bình ($20.78$ tỷ) phản ánh sự xuất hiện của các bất động sản giá trị cao (tòa nhà văn phòng, biệt thự dự án lớn, lô đất quy mô lớn) kéo dài về phía đuôi phải.
- Biểu đồ thang đo $\log_{10}(\text{price})$ thể hiện hình thái tiệm cận phân phối chuẩn log-normal.

![Phân bố giá bán](../results/eda/price_distribution.png)

### 2.2. Phân Bố Diện Tích (`area`)
- **Tứ phân vị & Trung vị:** $Q_1 = 55.90\text{ m}^2$, Trung vị ($P_{50}$) = $80.00\text{ m}^2$, $Q_3 = 120.00\text{ m}^2$.
- **Khoảng tứ phân vị ($IQR$):** $IQR = 64.10\text{ m}^2$.
- **Giá trị ngoại vi:** $P_{95} = 388.00\text{ m}^2$, $P_{99} = 2,229.01\text{ m}^2$.
- **Hình dạng phân phối:** Mật độ tập trung cao nhất nằm trong khoảng $40 - 120\text{ m}^2$ (phù hợp với quy mô nhà ở dân dụng phổ thông). Các diện tích lớn ($> 1,000\text{ m}^2$) chủ yếu là đất trang trại hoặc đất dự án.

![Phân bố diện tích](../results/eda/area_distribution.png)

### 2.3. Cơ Cấu Phân Loại Bất Động Sản (`property_type_name`)
Tổng thể 500,000 bản ghi gồm 5 nhóm loại hình:

| Loại Bất Động Sản | Tổng Số Tin Đăng | Tỷ Trọng (%) | Số Tin Có Giá Cụ Thể | Số Tin Giá Thỏa Thuận (NULL) |
|---|---:|---:|---:|---:|
| **Nhà** | 230,412 | 46.08% | 218,063 | 12,349 |
| **Đất** | 120,576 | 24.12% | 109,624 | 10,952 |
| **Căn hộ chung cư** | 104,107 | 20.82% | 92,971 | 11,136 |
| **Biệt thự/Nhà liền kề** | 36,611 | 7.32% | 33,056 | 3,555 |
| **Shophouse** | 8,294 | 1.66% | 7,225 | 1,069 |
| **Tổng cộng** | **500,000** | **100.00%** | **460,939** | **39,061** |

![Cơ cấu loại bất động sản](../results/eda/property_type_count.png)

### 2.4. Phân Bố Địa Bàn Hành Chính (`province_name`)
- Hai địa phương chiếm khối lượng tin đăng lớn nhất:
  1. **Hồ Chí Minh:** 186,698 tin đăng (37.34%).
  2. **Hà Nội:** 170,167 tin đăng (34.03%).
  3. Các địa phương tiếp theo: Đà Nẵng (25,772 tin), Bình Dương (21,399 tin), Khánh Hòa (13,893 tin), Hải Phòng (10,422 tin - chiếm 2.08%).
- **Ý nghĩa với Benchmark SQL:** Lọc `province_name = 'Hải Phòng'` trong bài toán Q1 có độ chọn lọc $\approx 2.08\%$, là tỷ lệ chọn lọc thấp điển hình nơi B-tree đơn cột thể hiện rõ ưu thế so với quét toàn bảng (Sequential Scan).

![Top 15 tỉnh thành](../results/eda/province_distribution.png)

### 2.5. Xu Hướng Tin Đăng Theo Thời Gian (`published_at`)
- Chuỗi thời gian đăng tin trải đều qua các tháng thu thập với dữ liệu chuẩn định dạng ISO8601.
- Mốc thời gian này được sử dụng trực tiếp trong bài toán Q3 để đánh giá ảnh hưởng của việc viết lại truy vấn lọc ngày sargable.

![Xu hướng tin đăng theo tháng](../results/eda/monthly_listings_trend.png)

---

## 3. Phân Tích Hai Biến & Đa Biến (Bivariate & Multivariate Analysis)

### 3.1. Mối Quan Hệ Giữa Diện Tích và Giá Chào Bán
- Biểu đồ mật độ Hexbin thể hiện cụm tập trung dày đặc nhất ở khu vực diện tích $40 - 120\text{ m}^2$ với giá từ $3 - 15$ tỷ VNĐ.
- Xu hướng tương quan đồng biến: bất động sản có diện tích lớn hơn nhìn chung có giá chào bán cao hơn, tuy nhiên độ phân tán tăng dần ở các quy mô diện tích lớn do vị trí địa lý khác nhau.

![Mối quan hệ diện tích và giá](../results/eda/price_vs_area_scatter.png)

### 3.2. Mức Giá Theo Từng Loại Hình Bất Động Sản
Dựa trên 460,939 bản ghi có giá cụ thể:
- **Biệt thự/Nhà liền kề:** Trung vị giá cao nhất (~19.5 tỷ VNĐ), biên độ dao động rộng.
- **Shophouse:** Trung vị ~9.5 tỷ VNĐ.
- **Nhà:** Trung vị ~8.9 tỷ VNĐ.
- **Căn hộ chung cư:** Trung vị ~4.85 tỷ VNĐ, phân bố tập trung tương đối ổn định.
- **Đất:** Trung vị ~4.45 tỷ VNĐ, độ trải IQR lớn giữa đất đô thị và đất ngoại thành.

![Boxplot giá theo loại bất động sản](../results/eda/price_by_property_type_boxplot.png)

### 3.3. Trung Vị Đơn Giá (Triệu VNĐ/m²) Theo Tỉnh Thành
- **Hà Nội & Hồ Chí Minh:** Giữ mức trung vị đơn giá trên mỗi mét vuông cao nhất trong nhóm khảo sát.
- **Đà Nẵng & Khánh Hòa:** Giữ vị trí tiếp theo trong nhóm các tỉnh thành đô thị - du lịch ven biển.
- **Bình Dương & Đồng Nai:** Phân khúc đô thị vệ tinh - công nghiệp với đơn giá bình quân phù hợp mức thu nhập lao động.

![Đơn giá trung vị theo tỉnh thành](../results/eda/price_per_m2_by_province.png)

### 3.4. Ma Trận Tương Quan Thứ Hạng Spearman
- Sử dụng hệ số tương quan thứ hạng Spearman nhằm hạn chế ảnh hưởng của giá trị cực trị:
  - $\text{corr}(\text{area}, \text{price}) = +0.58$: Tương quan thuận ở mức vừa phải (không khẳng định quan hệ nhân quả duy nhất).
  - $\text{corr}(\text{area}, \text{price\_per\_m2}) = -0.32$: Tương quan nghịch nhẹ (các bất động sản diện tích rất lớn như trang trại thường có đơn giá mỗi mét vuông thấp hơn đất nhà phố nội đô).
  - Tương quan giữa giá và các thành phần thời gian (`published_month`, `published_year`) tiệm cận 0.

![Ma trận tương quan Spearman](../results/eda/numeric_correlation_heatmap.png)

---

## 4. Đối Chiếu Kết Quả EDA Với Thiết Kế Benchmark SQL

Bảng đối chiếu giữa hiện trạng phân bố dữ liệu và cấu hình thực tế của 4 bài toán benchmark:

| Bài Toán | Truy Vấn SQL Nghiệm Thu Thực Tế | Chỉ Mục Tương Ứng | Đối Chiếu Với Phân Bố Dữ Liệu |
|---|---|---|---|
| **Q1 — Single-column Index** | `WHERE province_name = 'Hải Phòng'` | `ON properties USING btree (province_name)` | Hải Phòng có 10,422 dòng (selectivity 2.08%). B-Tree index giúp PostgreSQL quét trực tiếp 2.08% dữ liệu thay vì Sequential Scan toàn bảng 500K dòng. |
| **Q2 — Composite Index** | `WHERE province_name = 'Hà Nội' AND district_name = 'Cầu Giấy' AND price BETWEEN 4100000000 AND 14300000000 ORDER BY price ASC, id ASC LIMIT 20` | `ON properties USING btree (province_name, district_name, price, id)` | Khoảng giá 4.1 – 14.3 tỷ đúng bằng $Q_1 \rightarrow Q_3$ (50% dữ liệu có giá). Index composite khớp thứ tự sắp xếp và bộ lọc, cho phép cơ chế **Early-stopping với LIMIT 20** mà không cần qua bước Top-N Heap Sort. |
| **Q3 — Query Rewriting + Index** | So sánh `WHERE published_at::date = DATE '2025-10-15'` (A & C) với `WHERE published_at >= TIMESTAMP '...' AND published_at < TIMESTAMP '...'` (B & D) | `ON properties USING btree (published_at)` | Hàm bọc cột `::date` vô hiệu hóa chỉ mục B-tree thông thường (buộc quét toàn bảng). Khi viết lại thành khoảng giá trị sargable, PostgreSQL khai thác được B-tree index để tìm kiếm phạm vi thời gian. |
| **Q4 — Aggregation Control** | `SELECT property_type_name, COUNT(*), ROUND(AVG(price), 0) FROM properties GROUP BY property_type_name ORDER BY total DESC` | `ON properties USING btree (property_type_name)` | Phép tổng hợp cần duyệt qua toàn bộ dữ liệu bảng để gom nhóm và tính trung bình. Bộ lập lịch PostgreSQL ưu tiên `Parallel Seq Scan` vì chi phí đọc ngẫu nhiên qua Index Scan trên 100% dòng dữ liệu không mang lại cải thiện. |
