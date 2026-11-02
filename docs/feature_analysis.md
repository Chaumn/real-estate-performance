# Báo Cáo Phân Tích Kỹ Thuật Tạo Đặc Trưng (Feature Analysis Report)

> **Đề tài:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn.  
> **Quy mô tập dữ liệu đặc trưng:** 500,000 bản ghi $\times$ 24 cột (`results/features/properties_500000_enriched.parquet`).  
> **Kích thước file Parquet:** 45.22 MB (Tiết kiệm 54% dung lượng so với CSV 98.4 MB).

---

## 1. Mục Đích & Nguyên Tắc Tách Biệt Kiến Trúc (Architecture Separation)

Trong các bài toán hệ thống dữ liệu lớn, việc duy trì **tính tách biệt rõ ràng giữa Schema chuẩn hóa của CSDL giao dịch/thực nghiệm** và **Bộ đặc trưng phân tích mở rộng** là nguyên tắc kiến trúc tối thượng:
1. **Bảo toàn tính bất biến của Benchmark:** Bảng `public.properties` trong PostgreSQL giữ nguyên 9 cột chuẩn. Nếu bổ sung thêm các cột dẫn xuất (`price_per_m2`, `is_weekend`, `area_segment`) vào bảng cơ sở dữ liệu, kích thước tuple (row width) sẽ tăng lên, làm thay đổi số lượng tuple trên mỗi khối dữ liệu đĩa (disk block), từ đó làm sai lệch các phép đo I/O và Execution Time so với baseline.
2. **Lưu trữ tối ưu với Parquet Snappy:** Toàn bộ 15 đặc trưng phái sinh được lưu trữ dưới định dạng Parquet nén Snappy. Parquet áp dụng cơ chế lưu trữ theo cột (Columnar Storage) cùng các thuật toán nén từ điển (Dictionary Encoding) và mã hóa độ dài chạy (RLE), giúp giảm đáng kể dung lượng bộ nhớ và tăng tốc độ đọc của các thư viện phân tích như Pandas hay Polars lên 5–10 lần.

---

## 2. Phân Tích Phân Bố Các Phân Khúc Đặc Trưng

### 2.1. Phân Khúc Diện Tích (`area_segment`)

Phân phối diện tích theo 5 khoảng chuẩn hóa đô thị trên 500,000 bản ghi:

| Phân Khúc Diện Tích | Khoảng Giá Trị ($m^2$) | Số Lượng Bản Ghi | Tỷ Trọng (%) | Đặc Trưng Thị Trường |
|---|---|---:|---:|---|
| **Dưới 30m2** | $[0, 30)$ | 8,649 | 1.73% | Căn hộ mini, phòng trọ, ki-ốt phố cổ |
| **30-60m2** | $[30, 60)$ | 131,554 | 26.31% | Nhà phố nhỏ, căn hộ 1-2 phòng ngủ |
| **60-100m2** | $[60, 100)$ | 179,284 | **35.86%** | Phân khúc phổ biến nhất (Căn hộ gia đình, nhà chia lô) |
| **100-200m2** | $[100, 200)$ | 118,623 | 23.72% | Nhà phố lớn, biệt thự liền kề, đất nền đô thị |
| **Trên 200m2** | $[200, +\infty)$ | 61,890 | 12.38% | Biệt thự đơn lập, đất trang trại, kho xưởng |

> **Nhận xét:** Hơn **62%** bất động sản trên thị trường nằm trong khoảng diện tích vàng từ $30\text{ m}^2$ đến $100\text{ m}^2$. Đây chính là căn cứ thực tế để bài toán Q3 thiết lập điều kiện lọc diện tích `area BETWEEN 50 AND 100`, đảm bảo truy vấn chạm vào tập dữ liệu có mật độ cao nhất.

### 2.2. Phân Khúc Giá Bán Ngân Sách (`price_segment`)

| Phân Khúc Giá | Khoảng Giá Trị (VNĐ) | Số Lượng Bản Ghi | Tỷ Trọng (%) | Nhóm Khách Hàng Mục Tiêu |
|---|---|---:|---:|---|
| **Thỏa thuận** | `NULL` | 39,061 | 7.81% | Bất động sản giá trị cao hoặc chủ muốn thương lượng |
| **Dưới 2 tỷ** | $[0, 2 \times 10^9)$ | 40,051 | 8.01% | Phân khúc bình dân, nhà vùng ven, căn hộ nhỏ |
| **2 - 5 tỷ** | $[2 \times 10^9, 5 \times 10^9)$ | 106,760 | 21.35% | Phân khúc nhà ở đại chúng, căn hộ trung cấp |
| **5 - 10 tỷ** | $[5 \times 10^9, 10 \times 10^9)$ | 148,138 | **29.63%** | Phân khúc nhà phố trung tâm, căn hộ cao cấp |
| **10 - 20 tỷ** | $[10 \times 10^9, 20 \times 10^9)$ | 89,618 | 17.92% | Nhà mặt phố kinh doanh, biệt thự liền kề |
| **Trên 20 tỷ** | $[20 \times 10^9, +\infty)$ | 76,372 | 15.27% | Biệt thự sang trọng, tòa nhà văn phòng, đất dự án |

> **Nhận xét:** Khoảng giá 2 - 5 tỷ và 5 - 10 tỷ chiếm hơn 50% thị trường. Bài toán Q2 tập trung vào điều kiện `price BETWEEN 2000000000 AND 5000000000`, qua đó kiểm chứng chính xác hiệu năng của Composite Index trong phân khúc giao dịch sôi động nhất.

---

## 3. Phân Tích Hành Vi Người Dùng Qua Đặc Trưng Thời Gian

- **Tỷ lệ đăng tin cuối tuần (`is_weekend`):** **18.88%** số lượng tin đăng được tạo vào Thứ Bảy và Chủ Nhật.
  - Trung bình một ngày trong tuần (Thứ Hai $\rightarrow$ Thứ Sáu) chiếm khoảng $16.2\%$ lượng tin đăng mỗi ngày.
  - Trong khi đó, mỗi ngày cuối tuần chỉ chiếm khoảng $9.4\%$.
  - Điều này chỉ ra rằng phần lớn tin đăng bất động sản được thực hiện bởi các sàn giao dịch hoặc môi giới chuyên nghiệp trong giờ làm việc hành chính, thay vì người bán cá nhân đăng vào dịp cuối tuần.

---

## 4. Đánh Giá Độ Nhạy Của Các Chỉ Báo Ngoại Lệ (Outlier Flags)

- **Cờ ngoại lệ giá (`is_price_outlier`):** Chiếm **44,860** bản ghi (~8.97% toàn bộ tập dữ liệu, hoặc 9.73% số bản ghi có giá). Ngưỡng trên theo IQR là $29.6$ tỷ VNĐ.
- **Cờ ngoại lệ diện tích (`is_area_outlier`):** Chiếm **52,634** bản ghi (~10.53% toàn bộ tập dữ liệu). Ngưỡng trên theo IQR là $216.2\text{ m}^2$.
- **Lợi ích kỹ thuật:** Việc bổ sung cột cờ nhị phân `is_price_outlier` và `is_area_outlier` trong tập đặc trưng phân tích giúp các mô hình hồi quy (ví dụ Gradient Boosting hoặc Ridge Regression) có thể nhanh chóng lọc bỏ hoặc gắn trọng số riêng cho các bất động sản siêu dự án mà không cần phải tính toán lại ngưỡng quantile phức tạp trên toàn bộ 500,000 dòng.

---

## 5. Kết Luận

Hệ thống đặc trưng được tạo ra hoàn toàn khép kín, minh bạch về mặt công thức số học và kiểm định đơn vị đạt 100%. Định dạng lưu trữ Parquet mang lại hiệu năng vượt trội, sẵn sàng cung cấp đầu vào cho bài toán so sánh hiệu năng xử lý dữ liệu ở Phase 5.

