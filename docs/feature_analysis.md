# Báo Cáo Phân Tích Kỹ Thuật Tạo Đặc Trưng (Feature Analysis Report)

> **Dự án:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn.  
> **Quy mô tập dữ liệu đặc trưng:** 500,000 bản ghi $\times$ 24 cột (`results/features/properties_500000_enriched.parquet`).  
> **Kích thước file Parquet:** 45.22 MB (Tiết kiệm 54% dung lượng so với CSV 98.4 MB).

---

## 1. Mục Đích & Nguyên Tắc Tách Biệt Kiến Trúc (Architecture Separation)

Trong thiết kế hệ thống dữ liệu phục vụ nghiên cứu thực nghiệm, việc duy trì **tính tách biệt rõ ràng giữa Schema cơ sở dữ liệu benchmark** và **Tập đặc trưng phân tích mở rộng** tuân thủ các nguyên tắc sau:
1. **Bảo toàn tính bất biến của Benchmark:** Bảng `public.properties` trong PostgreSQL giữ nguyên 9 cột chuẩn. Nếu bổ sung thêm các cột dẫn xuất (`price_per_m2`, `is_weekend`, `area_segment`) vào bảng cơ sở dữ liệu, kích thước tuple (row width) sẽ tăng lên, làm thay đổi số lượng tuple trên mỗi khối đĩa (disk block), từ đó làm sai lệch các phép đo I/O và Execution Time của các truy vấn nghiệm thu.
2. **Lưu trữ tối ưu với Parquet Snappy:** Toàn bộ 15 đặc trưng phái sinh được lưu trữ dưới định dạng Parquet nén Snappy. Parquet áp dụng cơ chế lưu trữ theo cột (Columnar Storage) cùng các thuật toán nén từ điển (Dictionary Encoding), giúp giảm dung lượng lưu trữ trên đĩa và tối ưu hóa I/O khi nạp vào các công cụ phân tích (Pandas/Polars).

---

## 2. Phân Tích Phân Bố Các Phân Khúc Đặc Trưng

### 2.1. Phân Khúc Diện Tích (`area_segment`)

Phân phối diện tích theo 5 khoảng chuẩn hóa trên 500,000 bản ghi:

| Phân Khúc Diện Tích | Khoảng Giá Trị ($m^2$) | Số Lượng Bản Ghi | Tỷ Trọng (%) | Đặc Trưng Nhóm Dữ Liệu |
|---|---|---:|---:|---|
| **Dưới 30m2** | $[0, 30)$ | 8,649 | 1.73% | Căn hộ diện tích nhỏ, phòng dịch vụ, ki-ốt |
| **30-60m2** | $[30, 60)$ | 131,554 | 26.31% | Nhà phố nhỏ, căn hộ 1-2 phòng ngủ |
| **60-100m2** | $[60, 100)$ | 179,284 | **35.86%** | Phân khúc chiếm tỷ trọng lớn nhất trong tập dữ liệu |
| **100-200m2** | $[100, 200)$ | 118,623 | 23.72% | Nhà phố liền kề, đất nền phân lô |
| **Trên 200m2** | $[200, +\infty)$ | 61,890 | 12.38% | Biệt thự đơn lập, đất diện tích lớn, kho bãi |

> **Nhận xét:** Khoảng $62.17\%$ bất động sản nằm trong khoảng diện tích từ $30\text{ m}^2$ đến $100\text{ m}^2$. Phân khúc diện tích chuẩn hóa này giúp hỗ trợ các phép lọc danh mục thay cho các phép so sánh số thực liên tục.

### 2.2. Phân Khúc Giá Bán Ngân Sách (`price_segment`)

| Phân Khúc Giá | Khoảng Giá Trị (VNĐ) | Số Lượng Bản Ghi | Tỷ Trọng (%) | Mô Tả Phân Khúc |
|---|---|---:|---:|---|
| **Thỏa thuận** | `NULL` | 39,061 | 7.81% | Tin đăng để trống giá chào bán |
| **Dưới 2 tỷ** | $[0, 2 \times 10^9)$ | 40,051 | 8.01% | Phân khúc giá thấp |
| **2 - 5 tỷ** | $[2 \times 10^9, 5 \times 10^9)$ | 106,760 | 21.35% | Phân khúc nhà ở phổ thông |
| **5 - 10 tỷ** | $[5 \times 10^9, 10 \times 10^9)$ | 148,138 | **29.63%** | Phân khúc chiếm tỷ trọng cao nhất |
| **10 - 20 tỷ** | $[10 \times 10^9, 20 \times 10^9)$ | 89,618 | 17.92% | Nhà mặt phố, biệt thự liền kề |
| **Trên 20 tỷ** | $[20 \times 10^9, +\infty)$ | 76,372 | 15.27% | Biệt thự quy mô lớn, tòa nhà thương mại, dự án |

> **Nhận xét:** Trong bài toán benchmark SQL Q2, khoảng giá được chọn để lọc là `price BETWEEN 4100000000 AND 14300000000`, tương ứng chính xác với khoảng tứ phân vị $Q_1 \rightarrow Q_3$ (chiếm 50% số tin có giá), kết hợp với địa bàn Hà Nội, quận Cầu Giấy và sắp xếp theo giá có giới hạn `LIMIT 20`.

---

## 3. Đặc Trưng Thời Gian Đăng Tin

- **Tỷ lệ đăng tin cuối tuần (`is_weekend`):** **18.88%** số lượng tin đăng ghi nhận mốc thời gian vào Thứ Bảy hoặc Chủ Nhật.
- Các ngày trong tuần (Thứ Hai $\rightarrow$ Thứ Sáu) chiếm trung bình $16.22\%$ mỗi ngày, trong khi Thứ Bảy và Chủ Nhật chiếm trung bình $9.44\%$ mỗi ngày.
- Dữ liệu thời gian được phân rã thành các trường `published_year`, `published_month`, `published_quarter`, `published_day_of_week` giúp tăng tốc độ truy xuất khi cần phân tích theo mùa hoặc phân vùng bảng (Partitioning).

---

## 4. Đặc Trưng Chỉ Báo Ngoại Lệ (Outlier Flags)

- **Cờ ngoại lệ giá (`is_price_outlier`):** Có **44,860** bản ghi (~8.97% toàn bộ dataset, tương ứng 9.73% số bản ghi có giá) vượt cận trên IQR ($29.6$ tỷ VNĐ).
- **Cờ ngoại lệ diện tích (`is_area_outlier`):** Có **52,634** bản ghi (~10.53% toàn bộ dataset) vượt cận trên IQR ($216.2\text{ m}^2$).
- **Ghi chú dữ liệu:** Các giá trị ngoại lệ trong dữ liệu thu thập từ web có thể bao gồm các bất động sản thương mại/dự án lớn thực tế, hoặc các lỗi nhập thừa chữ số từ người đăng. Việc gắn cờ nhị phân mà không xóa dòng giúp bảo toàn nguyên vẹn tính phân bố thực tế cho các bài toán đánh giá chỉ mục trong CSDL.

---

## 5. Kết Luận

Tập đặc trưng phân tích được lưu trữ độc lập trong file Parquet nén Snappy đạt hiệu quả nén dung lượng cao và không ảnh hưởng đến cấu trúc bảng chuẩn hóa của cơ sở dữ liệu PostgreSQL.
