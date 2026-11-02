# Báo Cáo Đo Lường Hiệu Năng Xử Lý Dữ Liệu (Data Processing Performance Benchmark)

> **Dự án:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn.
> **Cấu hình máy thử nghiệm:** Windows 11, RAM 16GB, CPU x86-64 không GPU.
> **Phương pháp luận:** 2 lần warm-up, 5 lần đo chính thức. Thời gian ghi nhận Median Execution Time (ms) ± Std. Bộ nhớ đo qua luồng giám sát thời gian thực: Baseline RSS (MB trước chạy), Peak RSS (Đỉnh RAM đạt tới trong khi chạy), và Delta RSS (Mức tăng bộ nhớ tối đa).

---

## 1. Bảng Tổng Hợp Kết Quả Đo Lường Thực Tế

| Quy Mô | Nhóm Thao Tác | Kỹ Thuật / Thư Viện | Định Dạng File | Thời Gian Median (ms) | Độ Lệch Chuẩn (std) | Baseline RSS (MB) | Peak RSS (MB) | Delta RSS (MB) |
|---:|---|---|:---:|---:|---:|---:|---:|---:|
| 50,000 | File Ingestion (CSV) | Pandas read_csv | CSV | 168.04 ms | ±3.96 ms | 127.07 MB | 153.37 MB | +26.60 MB |
| 50,000 | File Ingestion (CSV) | Polars read_csv | CSV | 5.19 ms | ±1.65 ms | 167.94 MB | 178.53 MB | +10.85 MB |
| 50,000 | File Ingestion (Parquet) | Pandas read_parquet | Parquet | 9.91 ms | ±1.75 ms | 254.49 MB | 261.17 MB | +7.43 MB |
| 50,000 | File Ingestion (Parquet) | Polars read_parquet | Parquet | 10.75 ms | ±1.55 ms | 300.62 MB | 317.53 MB | +9.20 MB |
| 50,000 | Memory-bounded Ingestion | Pandas Chunked read_csv (10k) | CSV | 300.30 ms | ±37.00 ms | 296.73 MB | 310.82 MB | +13.82 MB |
| 50,000 | Memory-bounded Ingestion | Pandas Chunked aggregate (10k) | CSV | 367.81 ms | ±56.03 ms | 291.83 MB | 306.58 MB | +14.75 MB |
| 50,000 | In-Memory Analytics | Pandas Filter + GroupBy | In-Memory | 7.66 ms | ±3.75 ms | 292.80 MB | 292.83 MB | +0.02 MB |
| 50,000 | In-Memory Analytics | Polars Filter + GroupBy | In-Memory | 5.27 ms | ±0.43 ms | 307.09 MB | 308.06 MB | +1.00 MB |
| 200,000 | File Ingestion (CSV) | Pandas read_csv | CSV | 1,148.26 ms | ±44.73 ms | 336.68 MB | 436.40 MB | +99.45 MB |
| 200,000 | File Ingestion (CSV) | Polars read_csv | CSV | 24.48 ms | ±3.54 ms | 418.50 MB | 457.64 MB | +41.24 MB |
| 200,000 | File Ingestion (Parquet) | Pandas read_parquet | Parquet | 51.08 ms | ±12.35 ms | 506.24 MB | 523.25 MB | +21.37 MB |
| 200,000 | File Ingestion (Parquet) | Polars read_parquet | Parquet | 47.65 ms | ±4.79 ms | 523.86 MB | 542.14 MB | +17.14 MB |
| 200,000 | Memory-bounded Ingestion | Pandas Chunked read_csv (10k) | CSV | 1,156.66 ms | ±582.00 ms | 400.83 MB | 416.86 MB | +15.97 MB |
| 200,000 | Memory-bounded Ingestion | Pandas Chunked aggregate (10k) | CSV | 2,125.68 ms | ±274.82 ms | 337.58 MB | 354.29 MB | +16.88 MB |
| 200,000 | In-Memory Analytics | Pandas Filter + GroupBy | In-Memory | 19.08 ms | ±3.73 ms | 451.30 MB | 454.18 MB | +2.88 MB |
| 200,000 | In-Memory Analytics | Polars Filter + GroupBy | In-Memory | 6.89 ms | ±1.36 ms | 476.55 MB | 478.06 MB | +1.78 MB |
| 500,000 | File Ingestion (CSV) | Pandas read_csv | CSV | 3,038.53 ms | ±224.52 ms | 540.27 MB | 781.70 MB | +241.37 MB |
| 500,000 | File Ingestion (CSV) | Polars read_csv | CSV | 75.27 ms | ±5.52 ms | 692.36 MB | 801.52 MB | +105.62 MB |
| 500,000 | File Ingestion (Parquet) | Pandas read_parquet | Parquet | 127.00 ms | ±23.68 ms | 827.64 MB | 931.18 MB | +47.95 MB |
| 500,000 | File Ingestion (Parquet) | Polars read_parquet | Parquet | 202.25 ms | ±28.95 ms | 769.00 MB | 811.37 MB | +44.95 MB |
| 500,000 | Memory-bounded Ingestion | Pandas Chunked read_csv (10k) | CSV | 3,723.10 ms | ±394.53 ms | 417.73 MB | 437.41 MB | +19.68 MB |
| 500,000 | Memory-bounded Ingestion | Pandas Chunked aggregate (10k) | CSV | 3,835.01 ms | ±424.43 ms | 417.45 MB | 438.54 MB | +21.09 MB |
| 500,000 | In-Memory Analytics | Pandas Filter + GroupBy | In-Memory | 55.17 ms | ±13.38 ms | 722.53 MB | 726.17 MB | +5.98 MB |
| 500,000 | In-Memory Analytics | Polars Filter + GroupBy | In-Memory | 13.88 ms | ±7.21 ms | 769.50 MB | 775.43 MB | +4.44 MB |

---

## 2. Phân Tích Chuyên Sâu Các Phương Pháp Tối Ưu Xử Lý

### 2.1. So Sánh Hiệu Năng: Pandas vs. Polars

- **Tốc độ nạp CSV (500,000 dòng):** Pandas mất `3,038.53 ms`, Polars hoàn thành trong `75.27 ms` $\rightarrow$ **Polars nhanh hơn 40.37x**.
- **Tốc độ Lọc & Gom Nhóm In-Memory (Filter + GroupBy trên tập 'Hà Nội'):** Pandas xử lý trong `55.17 ms`, Polars hoàn thành trong `13.88 ms` $\rightarrow$ **Polars nhanh hơn 3.97x**.
- **Cơ sở kỹ thuật:**
  1. Polars được xây dựng trên Rust với mô hình dữ liệu Apache Arrow nguyên bản, hỗ trợ zero-copy và vectorized SIMD execution.
  2. Polars tự động khai thác tính toán song song đa luồng CPU (Multi-threaded Rayon execution) trong khi Pandas bị giới hạn bởi GIL trên các tác vụ Python đơn luồng.

### 2.2. So Sánh Định Dạng Lưu Trữ: CSV vs. Parquet

- **Dung lượng lưu trữ:** CSV 500,000 chiếm `93.88 MB`, Parquet Snappy chỉ chiếm `41.42 MB` $\rightarrow$ **Mức nén đạt 2.27x**.
- **Tốc độ nạp vào Pandas:** Đọc Parquet mất `127.00 ms` so với CSV `3,038.53 ms` $\rightarrow$ **Tăng tốc 23.93x**.
- **Lợi thế:** Parquet lưu trữ metadata kiểu dữ liệu nhị phân chuẩn xác, không phải phân tích chuỗi văn bản (string parsing) qua từng dòng như CSV.

### 2.3. Kiểm Soát Bộ Nhớ Với Kỹ Thuật Đọc Theo Khối (Chunked Streaming)

- **Hiện tượng:** Khi nạp toàn bộ file CSV 500K dòng vào RAM một lần bằng `pd.read_csv`, tiến trình ghi nhận Delta RSS tăng đáng kể để chứa toàn bộ DataFrame.
- **Kiểm soát bằng Chunked Streaming:** Khi áp dụng `chunksize=10,000`, dữ liệu được nạp và giải phóng tuần tự theo từng khối. Mặc dù tổng thời gian thực thi có thể tăng do chi phí vòng lặp I/O lặp lại, mức tăng bộ nhớ (Delta RSS) được giữ trong phạm vi một khối (~10–35 MB), ngăn ngừa tình trạng cạn kiệt bộ nhớ (OOM) khi xử lý các tập dữ liệu có quy mô lớn hơn dung lượng RAM vật lý.

---

## 3. Khuyến Nghị Thực Tiễn Cho Pipeline Kỹ Thuật Dữ Liệu

1. **Tầng Lưu Trữ (Analytical Storage):** Định dạng **Parquet Snappy** mang lại ưu thế vượt trội về kích thước file và tốc độ nạp dữ liệu.
2. **Tầng Xử Lý Phân Tích (Ingestion & ETL):** **Polars** đem lại hiệu năng xử lý đa luồng cao cho các tác vụ tính toán lớn.
3. **Tầng Phục Vụ Truy Vấn Trực Tuyến (Online Serving):** Sử dụng **PostgreSQL** kết hợp các cấu hình chỉ mục B-tree (đơn cột, composite) phục vụ các truy vấn tra cứu điểm, lọc phạm vi kết hợp phân trang Top-N trong thời gian mili-giây.