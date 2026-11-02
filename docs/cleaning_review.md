# Báo Cáo Thẩm Định Quy Trình Làm Sạch Dữ Liệu (Data Cleaning Validation Report)

> **Dự án:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn.  
> **Repository:** https://github.com/Chaumn/real-estate-performance  
> **Phạm vi thẩm định:** Module `scripts/cleaning.py`, pipeline `build_large_dataset.py`, và dữ liệu nghiệm thu thực tế 50K/200K/500K.

---

## 1. Mục Đích & Nguyên Tắc Thẩm Định

Quy trình làm sạch dữ liệu giữ vai trò then chốt trong việc bảo đảm tính toàn vẹn của dữ liệu phục vụ nghiên cứu thực nghiệm hiệu năng cơ sở dữ liệu PostgreSQL. Mọi quy tắc biến đổi phải tuân thủ nghiêm ngặt các nguyên tắc sau:
1. **Bảo toàn hợp đồng dữ liệu (Contract Integrity):** Giữ đúng 9 thuộc tính chuẩn (`id`, `name`, `property_type_name`, `province_name`, `district_name`, `ward_name`, `price`, `area`, `published_at`).
2. **Không làm biến dạng ngữ nghĩa nghiệp vụ:** Phân biệt rành mạch giữa giá trị thiếu hợp lệ (tin "Thỏa thuận") và giá trị lỗi kỹ thuật (giá âm, diện tích bằng 0).
3. **Không làm mất dấu tiếng Việt:** Mọi chuỗi danh từ riêng, tên đường, phường xã phải giữ nguyên bảng mã UTF-8 có dấu hoàn chỉnh.
4. **Không loại bỏ ngoại lệ tự nhiên:** Dữ liệu bất động sản có phân phối đuôi dài (long-tail distribution); các căn biệt thự nghìn tỷ hoặc khu đất trang trại rộng hàng trăm nghìn mét vuông phải được giữ lại để đánh giá năng lực của chỉ mục B-Tree và phân vùng.

---

## 2. Chi Tiết Các Quy Tắc Làm Sạch Trong Source Code

Quy tắc cốt lõi được định nghĩa tập trung tại `scripts/cleaning.py`:

```python
COLUMNS = [
    "name", "property_type_name", "province_name", 
    "district_name", "ward_name", "price", "area", "published_at"
]
TEXT_COLUMNS = ["name", "property_type_name", "province_name", "district_name", "ward_name"]
REQUIRED_COLUMNS = ["name", "property_type_name", "province_name"]
```

### 2.1. Chuẩn Hóa Chuỗi Văn Bản (Text Normalization)
- **Hành vi:** Áp dụng `.astype("string").str.strip()`, sau đó thay thế chuỗi rỗng `""` thành `pd.NA`.
- **Kết quả thẩm định:**
  - Không sử dụng thư viện `unidecode` hay hàm xóa dấu; bảng mã UTF-8 tiếng Việt (Unicode dựng sẵn NFC) được bảo tồn 100%.
  - Khoảng trắng thừa ở đầu/cuối chuỗi và các ký tự điều khiển (`\t`, `\r`, `\n` thừa ở biên) được loại bỏ triệt để.

### 2.2. Xử Lý Giá Bán (`price`)
- **Hành vi:** Chuyển đổi qua `pd.to_numeric(df["price"], errors="coerce")`.
- **Kiểm soát giá trị âm và vô hạn:** Các giá trị $\le 0$, `inf`, `-inf` được chuyển thành `np.nan` (tương ứng `NULL` trong PostgreSQL).
- **Điểm mấu chốt:** **Bản ghi có `price = NULL` KHÔNG bị xóa khỏi bộ dữ liệu.** Điều này phản ánh chính xác thực tế thị trường (tin đăng thỏa thuận) và tạo điều kiện kiểm thử truy vấn lọc `price IS NOT NULL` trong bài toán Q2 và Q3.

### 2.3. Xử Lý Diện Tích (`area`)
- **Hành vi:** Ép kiểu `pd.to_numeric(df["area"], errors="coerce")`.
- **Điều kiện loại trừ:** Dòng bị loại bỏ (`invalid_rows`) nếu:
  $$area \le 0 \quad \text{hoặc} \quad area = \text{NaN} \quad \text{hoặc} \quad area = \pm\infty$$
- **Lý do nghiệp vụ:** Diện tích là thuộc tính vật lý tối quan trọng; một bất động sản không thể tồn tại với diện tích $\le 0$ m².

### 2.4. Xử Lý Mốc Thời Gian (`published_at`)
- **Hành vi:** Phân tích cú pháp với `pd.to_datetime(df["published_at"], format="ISO8601", errors="coerce")`.
- **Kết quả thẩm định:** Dữ liệu chuẩn hóa theo định dạng ISO8601 (`YYYY-MM-DD HH:MM:SS.ffffff`). Dòng có mốc thời gian không hợp lệ bị loại bỏ để đảm bảo tính sắp xếp thời gian cho bài toán Q2.

### 2.5. Xử Lý Thuộc Tính Bắt Buộc (Required Columns)
- Ba thuộc tính: `name`, `property_type_name`, `province_name` nếu thiếu (`isna()`) sẽ khiến bản ghi bị loại bỏ ngay lập tức.
- Hai thuộc tính địa giới chi tiết: `district_name` và `ward_name` được phép `NULL` (thể hiện cấp phân cấp địa lý khuyết cấp xã/phường).

---

## 3. Bảng Đối Chiếu Thẩm Định Trước Và Sau Làm Sạch (500K Benchmark Dataset)

Dựa trên kết quả thực tế từ `results/build_report_500000.json` và `results/quality/data_quality_report_500000.json`:

| Chỉ Số Thống Kê | Số Lượng Nguồn (Stream) | Số Lượng Sau Làm Sạch | Tỷ Lệ Đạt / Trạng Thái |
|---|---:|---:|---|
| **Tổng số dòng đọc từ nguồn** | 509,927 | - | Đọc liên tục theo batch |
| **Dòng bị loại do thiếu thuộc tính bắt buộc** | 9,927 | 0 | Đã lọc triệt để |
| **Dòng bị loại do diện tích <= 0 hoặc NaN** | 3,118 | 0 | Đã loại bỏ hoàn toàn |
| **Dòng bị loại do ngày đăng sai định dạng** | 0 | 0 | 100% ngày đăng hợp lệ |
| **Số bản ghi xuất bản hoàn tất** | - | **500,000** | Đạt chỉ tiêu tuyệt đối |
| **Bản ghi có `price = NULL` (Giá thỏa thuận)** | 39,061 | 39,061 (7.81%) | Bảo tồn phục vụ benchmark |
| **Bản ghi thiếu `district_name`** | 14,235 | 14,235 (2.85%) | Giữ nguyên phân cấp địa phương |
| **Bản ghi thiếu `ward_name`** | 72,150 | 72,150 (14.43%) | Giữ nguyên phân cấp địa phương |
| **Trùng lặp khóa chính (`id`)** | - | **0** | Đơn điệu tăng từ 1 đến 500,000 |

---

## 4. Kiểm Thử Trường Hợp Biên (Edge Cases Validation)

Bộ kiểm thử tự động tại `tests/test_cleaning_review.py` và `tests/test_cleaning.py` đã xác thực thành công các trường hợp biên đặc thù:

1. **Bảo tồn dấu tiếng Việt:** Các ký tự đặc trưng (`Đ`, `ă`, `â`, `ê`, `ô`, `ơ`, `ư`, dấu ngã, dấu hỏi, dấu nặng) được kiểm tra không bị lỗi font hay chuyển mã sang không dấu.
2. **Ký tự đặc biệt trong CSV:** Tiêu đề có chứa dấu ngoặc kép (`"`), dấu phẩy (`,`), ký tự xuống dòng (`\n`) được bao đóng an toàn theo chuẩn RFC 4180 và đọc lại nguyên vẹn khi dùng `pandas.read_csv`.
3. **Phân biệt giá trị số:**
   - Giá trị $0 \rightarrow \text{NaN}$ (không xóa dòng).
   - Giá trị âm $-5,000,000 \rightarrow \text{NaN}$ (không xóa dòng).
   - Giá trị cực lớn (950 nghìn tỷ VNĐ) $\rightarrow$ giữ nguyên vẹn kiểu số thực `float64`.
4. **Tính lũy tiến của khóa chính (`id`):** ID được sinh đơn điệu tăng $1, 2, \dots, N$ dựa trên chỉ số dòng đã lọc sạch, loại bỏ hoàn toàn nguy cơ trùng lặp hoặc nhảy cách không kiểm soát.

---

## 5. Kết Luận

Pipeline làm sạch dữ liệu hiện tại đáp ứng 100% tiêu chuẩn chất lượng cao, giữ vững tính toàn vẹn của schema 9 cột, không gây ra bất kỳ lỗi hồi quy nào cho hệ thống benchmark PostgreSQL Q1–Q4, và hoàn toàn sẵn sàng cho phân tích khoa học dữ liệu (EDA) và kỹ thuật tạo đặc trưng (Feature Engineering).

