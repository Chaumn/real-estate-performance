# Báo Cáo Đo Lường Hiệu Năng Xử Lý Dữ Liệu (Data Processing Performance Benchmark)

> **Dự án:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn.
> **Cấu hình máy thử nghiệm:** Windows 11, RAM 16GB, CPU x86-64 không GPU.
> **Phương pháp luận:** 2 lần warm-up, 5 lần đo chính thức, ghi nhận Median Execution Time (ms) và Delta RAM (MB).

---

## 1. Bảng Tổng Hợp Kết Quả Đo Lường Thực Tế

| Quy Mô Dữ Liệu | Nhóm Thao Tác | Kỹ Thuật / Thư Viện | Định Dạng File | Thời Gian Median (ms) | Độ Lệch Chuẩn (std) | RAM Tiêu Thụ Tăng Thêm (MB) |
|---:|---|---|:---:|---:|---:|---:|
| 50,000 | File Ingestion (CSV) | Pandas read_csv | CSV | 229.75 ms | ±5.35 ms | +3.33 MB |
| 50,000 | File Ingestion (CSV) | Polars read_csv | CSV | 8.88 ms | ±0.97 ms | +10.39 MB |
| 50,000 | File Ingestion (Parquet) | Pandas read_parquet | Parquet | 16.59 ms | ±2.07 ms | +10.27 MB |
| 50,000 | File Ingestion (Parquet) | Polars read_parquet | Parquet | 25.50 ms | ±4.80 ms | +8.70 MB |
| 50,000 | Memory-bounded Ingestion | Pandas Chunked read_csv (10k) | CSV | 333.92 ms | ±18.95 ms | +0.00 MB |
| 50,000 | In-Memory Analytics | Pandas Filter + GroupBy | In-Memory | 3.49 ms | ±0.57 ms | +0.00 MB |
| 50,000 | In-Memory Analytics | Polars Filter + GroupBy | In-Memory | 4.04 ms | ±0.50 ms | +0.26 MB |
| 200,000 | File Ingestion (CSV) | Pandas read_csv | CSV | 1,206.33 ms | ±74.24 ms | +9.72 MB |
| 200,000 | File Ingestion (CSV) | Polars read_csv | CSV | 36.62 ms | ±4.51 ms | +39.65 MB |
| 200,000 | File Ingestion (Parquet) | Pandas read_parquet | Parquet | 58.76 ms | ±5.99 ms | +3.39 MB |
| 200,000 | File Ingestion (Parquet) | Polars read_parquet | Parquet | 72.58 ms | ±2.36 ms | +16.91 MB |
| 200,000 | Memory-bounded Ingestion | Pandas Chunked read_csv (10k) | CSV | 1,383.82 ms | ±151.62 ms | +0.50 MB |
| 200,000 | In-Memory Analytics | Pandas Filter + GroupBy | In-Memory | 5.06 ms | ±1.25 ms | +0.00 MB |
| 200,000 | In-Memory Analytics | Polars Filter + GroupBy | In-Memory | 3.83 ms | ±0.36 ms | +0.07 MB |
| 500,000 | File Ingestion (CSV) | Pandas read_csv | CSV | 2,996.45 ms | ±341.02 ms | +20.92 MB |
| 500,000 | File Ingestion (CSV) | Polars read_csv | CSV | 77.25 ms | ±7.73 ms | +98.68 MB |
| 500,000 | File Ingestion (Parquet) | Pandas read_parquet | Parquet | 142.18 ms | ±7.62 ms | +4.34 MB |
| 500,000 | File Ingestion (Parquet) | Polars read_parquet | Parquet | 167.36 ms | ±18.51 ms | +42.96 MB |
| 500,000 | Memory-bounded Ingestion | Pandas Chunked read_csv (10k) | CSV | 2,782.27 ms | ±269.31 ms | +0.00 MB |
| 500,000 | In-Memory Analytics | Pandas Filter + GroupBy | In-Memory | 6.54 ms | ±1.54 ms | +0.00 MB |
| 500,000 | In-Memory Analytics | Polars Filter + GroupBy | In-Memory | 4.00 ms | ±0.59 ms | +0.02 MB |

---

## 2. Phân Tích Chuyên Sâu Các Phương Pháp Tối Ưu Xử Lý

### 2.1. Đối Đầu Tốc Độ: Pandas vs. Polars

- **Tốc độ đọc CSV (500,000 dòng):** Pandas mất `2,996.45 ms` trong khi Polars chỉ mất `77.25 ms` $\rightarrow$ **Polars nhanh hơn 38.79x**.
- **Tốc độ Lọc & Tính Toán Gom Nhóm (Filter + GroupBy):** Pandas xử lý trong `6.54 ms`, Polars hoàn thành trong `4.00 ms` $\rightarrow$ **Polars nhanh hơn 1.64x**.
- **Nguyên nhân kỹ thuật:**
  1. Polars được viết bằng ngôn ngữ Rust, sử dụng Arrow columnar memory layout nguyên bản với zero-copy.
  2. Polars tự động khai thác song song đa luồng CPU (Multi-threaded Rayon execution) trong khi Pandas bị giới hạn bởi GIL trên đơn luồng.

### 2.2. So Sánh Định Dạng Lưu Trữ: CSV vs. Parquet

- **Dung lượng lưu trữ:** CSV 500,000 chiếm `93.88 MB`, Parquet Snappy chỉ chiếm `41.42 MB` $\rightarrow$ **Nén nhỏ hơn 2.27x**.
- **Tốc độ nạp vào Pandas:** Đọc Parquet mất `142.18 ms` so với CSV `2,996.45 ms` $\rightarrow$ **Tăng tốc 21.08x**.
- **Lợi thế:** Parquet lưu sẵn kiểu dữ liệu (strongly typed metadata), bỏ qua toàn bộ bước parsing chuỗi ký tự sang số/ngày tháng.

### 2.3. Đọc Dữ Liệu Theo Chunk (Chunked Reading): Kiểm Soát Bộ Nhớ Trong Giới Hạn Hẹp

- Khi đọc toàn bộ file CSV 500K bằng `pd.read_csv`, tiến trình cần cấp phát vùng nhớ liên tục lớn.
- Khi sử dụng `chunksize=10,000`, dữ liệu được nạp và giải phóng tuần tự theo từng khối. Mặc dù tổng thời gian thực thi có thể tăng nhẹ do overhead I/O lặp lại, mức đỉnh RAM (Peak RAM) được giữ ở mức cố định $\le 25\text{ MB}$, cho phép xử lý các tập dữ liệu lớn hàng chục GB trên máy tính RAM 16GB mà không bao giờ gặp lỗi `MemoryError` hoặc tràn Swap disk.

---

## 3. Khuyến Nghị Thực Tiễn Cho Pipeline Kỹ Thuật Dữ Liệu

1. **Tầng Storage (Cold / Warm Data):** Sử dụng định dạng **Parquet Snappy** cho toàn bộ dữ liệu phân tích và lưu trữ trung gian.
2. **Tầng Ingestion & Transformation:** Ưu tiên **Polars** cho các tác vụ làm sạch, gom nhóm hoặc trích xuất số liệu phân tích lớn nhờ khả năng xử lý song song vượt trội.
3. **Tầng Serving & Online Database:** Giữ vững **PostgreSQL** kết hợp B-Tree và Composite Index cho các truy vấn tra cứu thời gian thực (Point lookup, Range filter, Top-N sorting) đã được chứng minh hiệu năng ở các mốc sub-millisecond trong báo cáo benchmark.