# Báo Cáo Thẩm Định Quy Trình Làm Sạch Dữ Liệu (Data Cleaning Validation Report)

> **Dự án:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn.  
> **Repository:** https://github.com/Chaumn/real-estate-performance  
> **Phạm vi thẩm định:** Module `scripts/cleaning.py`, pipeline `build_large_dataset.py`, và dữ liệu nghiệm thu thực tế 50K/200K/500K.

---

## 1. Mục Đích & Nguyên Tắc Thẩm Định

Quy trình làm sạch dữ liệu giữ vai trò thiết lập tính toàn vẹn của dữ liệu phục vụ nghiên cứu thực nghiệm hiệu năng cơ sở dữ liệu PostgreSQL. Các quy tắc biến đổi tuân thủ các nguyên tắc sau:
1. **Bảo toàn hợp đồng dữ liệu (Contract Integrity):** Giữ đúng 9 thuộc tính chuẩn (`id`, `name`, `property_type_name`, `province_name`, `district_name`, `ward_name`, `price`, `area`, `published_at`).
2. **Bảo tồn ngữ nghĩa nghiệp vụ:** Phân biệt rành mạch giữa giá trị thiếu hợp lệ (tin "Thỏa thuận") và giá trị lỗi kỹ thuật (giá âm, diện tích không hợp lệ).
3. **Bảo toàn chuỗi tiếng Việt:** Mọi chuỗi danh từ riêng, tên đường, phường xã giữ nguyên bảng mã UTF-8 và dấu tiếng Việt của nguồn, không dùng các hàm chuyển đổi làm mất dấu (như `unidecode`). Lưu ý rằng pipeline chỉ áp dụng loại bỏ khoảng trắng thừa (`.str.strip()`), không áp dụng chuẩn hóa dạng thức Unicode dựng sẵn (NFC/NFD).
4. **Không tùy tiện loại bỏ ngoại lệ:** Dữ liệu bất động sản có phân phối lệch phải và đuôi dài; các bất động sản giá trị cao hoặc diện tích lớn được giữ lại để đánh giá năng lực của chỉ mục B-Tree và phân vùng trong điều kiện tải dữ liệu thực tế.

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
  - Không sử dụng thư viện `unidecode` hay hàm xóa dấu; chuỗi UTF-8 tiếng Việt được bảo tồn nguyên trạng ký tự.
  - Khoảng trắng thừa ở đầu/cuối chuỗi được loại bỏ. Hàm không thực hiện biến đổi bảng mã dạng thức Unicode dựng sẵn (NFC).

### 2.2. Xử Lý Giá Bán (`price`)
- **Hành vi:** Chuyển đổi qua `pd.to_numeric(df["price"], errors="coerce")`.
- **Kiểm soát giá trị âm và vô hạn:** Các giá trị $\le 0$, `inf`, `-inf` được chuyển thành `np.nan` (tương ứng `NULL` trong PostgreSQL).
- **Điểm mấu chốt:** **Bản ghi có `price = NULL` KHÔNG bị xóa khỏi bộ dữ liệu.** Điều này phản ánh thực tế tin đăng "Giá thỏa thuận" và cung cấp dữ liệu cho các truy vấn có điều kiện lọc `price IS NOT NULL` trong bài toán Q2.

### 2.3. Xử Lý Diện Tích (`area`)
- **Hành vi:** Ép kiểu `pd.to_numeric(df["area"], errors="coerce")`.
- **Điều kiện loại trừ:** Dòng bị loại bỏ (`invalid_rows`) nếu:
  $$area \le 0 \quad \text{hoặc} \quad area = \text{NaN} \quad \text{hoặc} \quad area = \pm\infty$$
- **Cơ sở:** Diện tích là thuộc tính vật lý bắt buộc; một bất động sản không thể có diện tích $\le 0$ m².

### 2.4. Xử Lý Mốc Thời Gian (`published_at`)
- **Hành vi:** Phân tích cú pháp với `pd.to_datetime(df["published_at"], format="ISO8601", errors="coerce")`.
- **Kết quả thẩm định:** Dữ liệu chuẩn hóa theo định dạng ISO8601 (`YYYY-MM-DD HH:MM:SS.ffffff`). Dòng có mốc thời gian không hợp lệ bị loại bỏ.

### 2.5. Xử Lý Thuộc Tính Bắt Buộc (Required Columns)
- Ba thuộc tính: `name`, `property_type_name`, `province_name` nếu thiếu (`isna()`) sẽ khiến bản ghi bị loại bỏ.
- Hai thuộc tính địa giới chi tiết: `district_name` và `ward_name` được phép `NULL`.

---

## 3. Bảng Đối Chiếu Thẩm Định Thực Tế (500K Benchmark Dataset)

Dựa trên kết quả thực tế được ghi nhận chính xác tại `results/build_report_500000.json`:

| Chỉ Số Thống Kê | Số Lượng Thực Tế | Ghi Chú Kỹ Thuật |
|---|---:|---|
| **Tổng số dòng đọc từ nguồn stream (`source_rows_read`)** | 502,000 | Đọc 251 batch, mỗi batch 2,000 dòng từ stream đã shuffle |
| **Tổng số dòng không hợp lệ bị loại (`invalid_rows`)** | 203 | Tỷ lệ loại bỏ: 0.04% tổng số dòng nguồn đã đọc |
| ↳ *Dòng thiếu thuộc tính bắt buộc (`invalid_required`)* | 202 | Thiếu ít nhất một trong 3 trường `name`, `property_type_name`, `province_name` |
| ↳ *Dòng diện tích không hợp lệ (`invalid_area`)* | 1 | Diện tích $\le 0$ hoặc không phân tích được thành số |
| ↳ *Dòng ngày đăng sai định dạng (`invalid_date`)* | 0 | 100% dòng có trường thời gian phân tích được theo ISO8601 |
| ↳ *Dòng có giá không hợp lệ (`invalid_price_values`)* | 0 | Không có giá âm hay vô hạn; giá không phân tích được chuyển thành NULL |
| **Tổng số dòng hợp lệ ghi nhận (`valid_rows_seen`)** | 501,797 | $502,000 - 203 = 501,797$ |
| **Số dòng hợp lệ không xuất (`valid_rows_not_exported`)** | 1,797 | Dư ở batch thứ 251 khi đã đạt target 500,000 |
| **Số dòng thực tế xuất ra dataset (`exported_rows`)** | **500,000** | Đạt chính xác target 500,000 bản ghi |
| **Bản ghi có `price = NULL` (Giá thỏa thuận)** | 39,061 | Chiếm 7.81% tổng dataset 500K |
| **Bản ghi thiếu `district_name`** | 14,235 | Chiếm 2.85% tổng dataset 500K |
| **Bản ghi thiếu `ward_name`** | 72,150 | Chiếm 14.43% tổng dataset 500K |
| **Trùng lặp khóa chính (`id`)** | **0** | Khóa chính sinh đơn điệu tăng $1 \rightarrow 500,000$ |

---

## 4. Kiểm Thử Trường Hợp Biên (Edge Cases Validation)

Bộ kiểm thử tự động tại `tests/test_cleaning_review.py` và `tests/test_cleaning.py` xác thực các trường hợp biên:

1. **Bảo tồn ký tự tiếng Việt:** Ký tự tiếng Việt (`Đ`, `ă`, `â`, `ê`, `ô`, `ơ`, `ư`, thanh điệu) được lưu giữ đúng byte UTF-8.
2. **Ký tự đặc biệt trong CSV:** Tiêu đề có chứa dấu ngoặc kép (`"`), dấu phẩy (`,`), ký tự xuống dòng (`\n`) được bao đóng an toàn theo chuẩn RFC 4180 và đọc lại nguyên vẹn khi dùng `pandas.read_csv`.
3. **Phân biệt giá trị số:**
   - Giá trị $0 \rightarrow \text{NaN}$ (không xóa dòng).
   - Giá trị âm $-5,000,000 \rightarrow \text{NaN}$ (không xóa dòng).
   - Giá trị cực lớn (950 nghìn tỷ VNĐ) $\rightarrow$ giữ nguyên vẹn kiểu số thực `float64`.
4. **Tính lũy tiến của khóa chính (`id`):** ID được sinh đơn điệu tăng $1, 2, \dots, N$ dựa trên chỉ số dòng đã lọc sạch, không có khoảng trống hoặc trùng lặp trong dataset hoàn thiện.

---

## 5. Kết Luận

Pipeline làm sạch dữ liệu hoạt động nhất quán với hợp đồng schema 9 cột, duy trì đầy đủ tính đúng đắn cho các bài toán benchmark SQL Q1–Q4 trên PostgreSQL. Mọi số liệu trong báo cáo này hoàn toàn đồng bộ với tệp báo cáo `results/build_report_500000.json`.
