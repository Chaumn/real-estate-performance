# HỒ SƠ GIAO NỘP TIỂU LUẬN KHOA HỌC (ACADEMIC SUBMISSION PACKAGE)

---

## 1. THÔNG TIN ĐỀ TÀI VÀ HỒ SƠ TÁC GIẢ

- **Tên đề tài:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn
- **Môn học:** Nhập môn Khoa học Dữ liệu / Hệ thống Quản trị Cơ sở Dữ liệu
- **Cơ sở đào tạo:** Học viện Công nghệ Bưu chính Viễn thông (PTIT)
- **Sinh viên thực hiện:** `[Cần điền: Họ và tên sinh viên thực hiện]`
- **Mã sinh viên:** `[Cần điền: Mã sinh viên / Lớp chuyên ngành]`
- **Chuyên ngành:** Khoa học Dữ liệu & Hệ thống Thông tin
- **Giảng viên hướng dẫn:** `[Cần điền: Học hàm, học vị và Họ tên Giảng viên hướng dẫn]`
- **Thời gian nghiệm thu:** Tháng 11 / Năm 2026
- **Kho mã nguồn Git (Git Repository):** `https://github.com/Chaumn/real-estate-performance` (Branch: `dev`)

---

## 2. CẤU TRÚC THƯ MỤC NỘP BÀI (`submission/`)

```text
submission/
├── TieuLuan_BatDongSan.docx         # Bản thảo báo cáo Word OpenXML (Times New Roman, Heading 1-4, TOC động)
├── TieuLuan_BatDongSan.pdf          # Báo cáo chuẩn xuất bản PDF/A-1b (63 trang, nhúng phông Unicode TrueType)
├── README_SUBMISSION.md             # Tài liệu thuyết minh hồ sơ giao nộp và hướng dẫn tái lập (Tệp này)
└── evidence/                        # Thư mục chứng tích dữ liệu và bằng chứng thực nghiệm độc lập
    ├── dataset_manifest.json        # Bản kê kiểm toán SHA-256, kích thước byte và thuộc tính của 3 tập dữ liệu
    ├── benchmark_manifest.json      # Bản kê kiểm toán SHA-256 của 600 kế hoạch thực thi EXPLAIN ANALYZE
    └── benchmark_raw_plans.zip      # Gói nén chứa toàn bộ 600 tệp JSON kế hoạch thực thi thô (3 scale x 10 config x 20 runs)
```

---

## 3. BẢNG ĐỐI CHIẾU MÃ BĂM TOÀN VẸN (SHA-256 CHECKSUMS)

Tất cả các tệp trong gói giao nộp đều được tính toán mã băm SHA-256 xác thực độc lập. Người chấm có thể sử dụng PowerShell (`Get-FileHash -Algorithm SHA256 <file>`) hoặc lệnh `sha256sum` trên Linux để kiểm tra tính toàn vẹn:

| Tệp bàn giao (Artifact) | Dung lượng (Bytes) | Dung lượng (MB) | Mã băm SHA-256 (Checksum) |
| :--- | :---: | :---: | :--- |
| `submission/TieuLuan_BatDongSan.docx` | 2.943.576 | 2,81 MB | `750fb5a347b580977648694fb302be60ba665811f16532f6d5d35aadb90b507b` |
| `submission/TieuLuan_BatDongSan.pdf` | 6.222.013 | 5,93 MB | `baab85fefc175d2e50b913ec05b57e754d70f3470b25373aee5861c297c3883d` |
| `submission/evidence/dataset_manifest.json` | 3.529 | 0,003 MB | `5bcea1bfa797edd804dba4c533d4a8861ce6eaaa0ac1b74bc9f167a7824f3ec4` |
| `submission/evidence/benchmark_manifest.json` | 94.180 | 0,09 MB | `b6f032cfb82af0216f08b6b85dedc341c903b3e00b372ba7c7f54a279570c63b` |
| `submission/evidence/benchmark_raw_plans.zip` | 504.366 | 0,48 MB | `262ed49431c0a4c758ad638dd253726273119acf27a23ca20997cec477677753` |

### Bảng đối chiếu mã băm ba tập dữ liệu chuẩn hóa cục bộ (`data/processed/`):
*(Lưu ý: Các tệp CSV được loại trừ khỏi kho Git theo `.gitignore` nhằm tránh vượt ngưỡng dung lượng kho mã nguồn).*

| Tập dữ liệu (Processed Dataset) | Số dòng (Rows) | Số cột | Dung lượng (Bytes) | Mã băm SHA-256 (Checksum) |
| :--- | :---: | :---: | :---: | :--- |
| `properties_50000.csv` | 50.000 | 9 | 9.803.441 | `11bc4fe13aafbcbb8be177b94dbba221199a4fe9963f2766dc8257ee7a89849b` |
| `properties_200000.csv` | 200.000 | 9 | 39.311.466 | `84eabf931d8d87d00fef07e60fa0d6a2f8c5b3c59cf6b8f52fe6305a41755106` |
| `properties_500000.csv` | 500.000 | 9 | 98.442.479 | `9ba1afe8ce7edbf6f6df615822be88dd33fca401a4e1564aa6a56e0767e3a89e` |

---

## 4. HƯỚNG DẪN TÁI LẬP THỰC NGHIỆM TỪ ĐẦU (REPRODUCIBILITY GUIDE)

### 4.1. Yêu cầu môi trường và Phiên bản công cụ
- **Hệ điều hành:** Windows 10/11 x86_64 (hoặc Linux Ubuntu 22.04 LTS).
- **Python:** Phiên bản 3.11+ (Môi trường phát triển: Python 3.13.7).
- **PostgreSQL:** Phiên bản 18.3 x86_64 (Port cục bộ được cấu hình: `5433`, đường dẫn cluster: `.pgdata`).
- **Thư viện Python cốt lõi:**
  ```text
  pandas>=2.2.0
  polars>=1.0.0
  psutil>=5.9.0
  psycopg2-binary>=2.9.9
  python-docx>=1.1.0
  matplotlib>=3.8.0
  seaborn>=0.13.0
  pytest>=8.0.0
  ```

### 4.2. Quy trình thiết lập môi trường
```powershell
# 1. Khởi tạo môi trường ảo Python
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Cài đặt các gói phụ thuộc
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4.3. Thứ tự thực thi quy trình nghiên cứu (Execution Pipeline)

#### Bước 1: Tái lập tập dữ liệu chuẩn hóa (RQ1)
Script sẽ kết nối luồng trực tiếp từ Hugging Face (`Phuscca/vietnam-real-estates`), áp dụng bộ quy tắc làm sạch 6 trường bắt buộc, xử lý giá thỏa thuận và xuất ra ba tập dữ liệu chuẩn hóa:
```powershell
python scripts/build_large_dataset.py
```
*Kết quả:* Tạo ra `data/processed/properties_50000.csv`, `properties_200000.csv`, `properties_500000.csv` và `results/build_report_500000.json`.

#### Bước 2: Chạy kiểm toán chất lượng dữ liệu và trực quan hóa EDA (RQ1)
```powershell
python scripts/run_eda.py
```
*Kết quả:* Tạo ra 10 biểu đồ PNG chất lượng cao tại `results/eda/` và tệp báo cáo `results/data_quality_report_500000.json`.

#### Bước 3: Benchmark hiệu năng xử lý Ingestion & In-Memory (RQ2)
Khảo sát so sánh Pandas, Polars, CSV, Parquet và Chunked Streaming:
```powershell
python scripts/benchmark_processing.py
```
*Kết quả:* Lưu trữ số liệu chi tiết tại `results/processing_benchmark/processing_benchmark.csv`.

#### Bước 4: Khởi tạo cơ sở dữ liệu PostgreSQL và nạp dữ liệu (RQ3)
```powershell
# Khởi động cụm PostgreSQL (Port 5433)
pg_ctl -D .pgdata start

# Khởi tạo lược đồ bảng và nạp 500K dòng
python scripts/import_csv.py
```

#### Bước 5: Chạy Benchmark truy vấn SQL và ghi nhận 600 kế hoạch thực thi (RQ3)
```powershell
python scripts/benchmark_runner.py
```
*Kết quả:* Thực thi 3 quy mô $\times$ 10 cấu hình $\times$ 20 lần chạy; ghi nhận 600 tệp JSON thô tại `results/benchmark/raw/` và bảng tổng hợp `results/benchmark/benchmark_results.csv`.

#### Bước 6: Chạy toàn bộ 189 kiểm thử tự động (Automated Test Suite)
```powershell
python -m pytest
```
*Kết quả kỳ vọng:* 188 passed, 1 skipped (bài kiểm tra kết nối mạng bên ngoài Hugging Face ở chế độ offline).

#### Bước 7: Xuất bản tài liệu Word và chuyển đổi PDF/A-1b
```powershell
# Xuất bản Word OpenXML (.docx)
python report/export_docx.py

# Cập nhật mục lục động và xuất bản PDF/A-1b chuẩn
powershell -ExecutionPolicy Bypass -File scripts/save_as_pdf.ps1
```

---

## 5. CẢNH BÁO GIỚI HẠN VÀ TÍNH PHỤ THUỘC MÔI TRƯỜNG

1. **Giới hạn Dataset Revision của Hugging Face:**  
   Kho dữ liệu upstream `Phuscca/vietnam-real-estates` trên Hugging Face được nạp ở chế độ luồng (Streaming API) với `revision: null` (commit mặc định). Mặc dù các tham số tạo dữ liệu được cố định tuyệt đối (`seed = 42`, `buffer_size = 10,000`, `batch_size = 2,000`), nếu tác giả kho nguồn thực hiện ghi đè hoặc chỉnh sửa lịch sử commit trên Hugging Face, dữ liệu luồng nạp về có thể có sai khác. Để khắc phục triệt để, người thẩm định có thể sử dụng trực tiếp các mã băm SHA-256 trong `submission/evidence/dataset_manifest.json` để kiểm chứng toàn vẹn.
2. **Cấu hình Cổng kết nối PostgreSQL (Port Dependency):**  
   Môi trường thực nghiệm được chạy trên cổng `port = 5433` với thư mục cụm dữ liệu cục bộ `.pgdata`. Nếu người thẩm định sử dụng dịch vụ PostgreSQL hệ thống chạy ở cổng mặc định `5432`, cần cập nhật lại biến môi trường `PGPORT=5432` hoặc tùy chỉnh tham số kết nối trong `scripts/benchmark_runner.py`.
3. **Độ dao động thời gian thực thi (Hardware & OS Variance):**  
   Thời gian thực thi truy vấn (Execution Time) và độ lệch chuẩn ($\pm \sigma$) phụ thuộc vào xung nhịp vi xử lý (CPU Single-thread Turbo), tốc độ đọc bộ nhớ RAM (Memory Bandwidth) và cơ chế bộ đệm trang đĩa (OS Page Cache) của máy chủ thực nghiệm. Do đó, con số mili-giây tuyệt đối trên máy của người chấm có thể chênh lệch nhẹ so với báo cáo, nhưng **tỷ lệ tăng tốc tương đối (Speedup Ratio)**, **số lượng khối đệm Shared Hit Blocks**, và **cấu trúc cây kế hoạch thực thi (Query Execution Plan)** được đảm bảo nhất quán 100%.
4. **Giới hạn của phép đo RAM RSS bằng cơ chế lấy mẫu 1 ms:**  
   Chỉ số đo lường mức tăng bộ nhớ đỉnh $\Delta RSS$ được giám sát bằng luồng nền trong cùng tiến trình (in-process thread) với tần số lấy mẫu 1 ms. Phương pháp này có độ trễ vật lý và chịu sự chi phối của bộ cấp phát bộ nhớ Python (pymalloc & arenas fragmentation). Vì vậy, mức $\Delta RSS$ phản ánh xu hướng sử dụng bộ nhớ tương đối của các giải pháp, không đại diện cho mức tiêu thụ tuyệt đối của hệ điều hành.

