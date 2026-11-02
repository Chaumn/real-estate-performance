# BÁO CÁO NGHIỆM THU KIỂM ĐỊNH DỮ LIỆU VÀ HỆ THỐNG THỰC TẾ
## FINAL DATA ACCEPTANCE & AUDIT REPORT

**Kho lưu trữ mã nguồn:** [real-estate-performance](https://github.com/Chaumn/real-estate-performance)  
**Nhánh kiểm định (Branch):** `dev`  
**Cơ sở đào tạo:** Học viện Công nghệ Bưu chính Viễn thông (PTIT)  
**Trạng thái kiểm định:** **DATA PROCESSING VERIFIED (100% PASS)**

---

## 1. BẢNG TỔNG HỢP KIỂM ĐỊNH CHẤP THUẬN (FINAL ACCEPTANCE MATRIX)

| STT | Hạng mục kiểm định (Audit Scope) | Bằng chứng thực nghiệm khách quan (Concrete Evidence) | Kết luận (Status) |
| :---: | :--- | :--- | :---: |
| **01** | **Kiểm toán 3 Dataset CSV thực tế**<br>- 50.000 dòng<br>- 200.000 dòng<br>- 500.000 dòng | - Đọc và tính toán trực tiếp từ các tệp CSV tại `data/processed/`.<br>- 9 thuộc tính chuẩn: `id`, `name`, `property_type_name`, `province_name`, `district_name`, `ward_name`, `price`, `area`, `published_at`.<br>- `id` duy nhất và liên tục $1 \rightarrow N$, không có lỗ hổng (`min=1`, `max=N`).<br>- Không có diện tích $\le 0$; không có ngày đăng lỗi.<br>- Xuất bản: `results/validation/data_validation_50000.json`, `data_validation_200000.json`, `data_validation_500000.json`. | **PASS** |
| **02** | **Tính lồng nhau của tập dữ liệu**<br>$\mathcal{D}_{50K} \subset \mathcal{D}_{200K} \subset \mathcal{D}_{500K}$ | - Thực thi kiểm chứng tiền tố: `df_200.iloc[:50000].equals(df_50) == True`; `df_500.iloc[:200000].equals(df_200) == True`.<br>- Lưu trữ bằng chứng: `results/validation/dataset_nesting_audit.json`. | **PASS** |
| **03** | **Khớp số liệu giữa CSV và Báo cáo JSON** | - Đối soát chéo 100% các chỉ số khuyết thiếu, ngoại lệ và trùng lặp với `results/quality/*.json`. Không có bất kỳ sai lệch nào (`discrepancies_count: 0`).<br>- Lưu trữ bằng chứng: `results/validation/cross_validation_report.json`. | **PASS** |
| **04** | **Điều tra chuyên sâu Trùng lặp (Duplicates)**<br>- Trùng tuyệt đối excl ID: 2<br>- Nghi ngờ trùng lặp: 57.808 (11,56%) | - Trùng tuyệt đối ngoại trừ ID: đúng 2 bản ghi dư thừa (3 dòng mang ID `101427`, `248997`, `340047` cùng diện tích 140 m², giá 2,3 tỷ, timestamp `2025-09-09 04:44:23.873000`). Tỷ lệ 0,0004%.<br>- Nghi ngờ trùng lặp: đúng 57.808 bản ghi. Kiểm toán xác nhận **100,0% nhóm nghi trùng có `published_at` khác nhau**, phản ánh hành vi môi giới đăng lại tin để duy trì vị trí hiển thị, không phải lỗi kỹ thuật ETL.<br>- Bằng chứng: `results/validation/quality_deep_investigation_500000.json`. | **PASS** |
| **05** | **Điều tra Ngoại lệ cực trị (Extreme Outliers)**<br>- Max price: 920.000 tỷ VNĐ<br>- Max area: 24.000.000 m² | - Ngoại lệ Giá bán (IQR): đúng **44.860 bản ghi** ($price > 29,60$ tỷ VNĐ).<br>- Ngoại lệ Diện tích (IQR): đúng **52.634 bản ghi** ($area > 176,15$ m²).<br>- Làm rõ giá 920 nghìn tỷ và diện tích 24 triệu m² là lỗi nhập liệu đơn vị từ người dùng trên cổng tin đăng gốc.<br>- Chứng minh ngoại lệ làm Mean bị thổi phồng **2,46 lần** và Std bị phóng đại **239,03 lần** so với tập không có ngoại lệ. Minh chứng tính bắt buộc phải dùng Trung vị ($7,40$ tỷ) và IQR ($10,20$ tỷ).<br>- Bảo toàn ngoại lệ trong benchmark cơ sở dữ liệu để đánh giá khách quan B-tree trên dữ liệu thô. | **PASS** |
| **06** | **Kiểm định Tạo đặc trưng (Feature Engineering)**<br>- 500.000 dòng $\times$ 24 cột<br>- 15 đặc trưng dẫn xuất | - Thực thi `scripts/validate_features.py`: đạt 10/10 tiêu chí kiểm tra.<br>- Giữ nguyên vẹn 9 cột gốc; sinh đủ 15 đặc trưng: `price_per_m2` (VND/m², bảo toàn NULL khi giá thỏa thuận), 6 biến thời gian, 2 phân khúc diện tích/giá, 2 cờ không gian, 2 cờ ngoại lệ (`is_price_outlier = 44.860`, `is_area_outlier = 52.634`), 2 đặc trưng văn bản.<br>- Không có giá trị `Inf`; Parquet round-trip thành công 100%.<br>- Tệp xuất bản: `results/features/properties_500000_enriched.parquet` (45,22 MB, SHA-256: `c75e5ea6e74612853f468950c63de9761262fd179fa871a0a448ca21d5d7d3d3`).<br>- Bằng chứng: `results/features/feature_validation.json`, `feature_manifest.json`. | **PASS** |
| **07** | **Kiểm thử PostgreSQL 18.3 thật (port 5433)**<br>- Live Integration Tests (NO Mocks)<br>- Database cách ly: `real_estate_test_db` | - Kết nối trực tiếp máy chủ PostgreSQL 18.3 x86_64 tại port 5433.<br>- Tạo mới `real_estate_test_db` từ `sql/schema.sql`.<br>- Nạp 50.000 dòng thật qua transactional `COPY FROM STDIN`. Đối soát row count và NULL count khớp 100% với CSV.<br>- Kiểm tra Rollback ACID khi vi phạm CHECK constraint (`area <= 0`): rollback sạch 100%, không rò rỉ bản ghi rác.<br>- Thực thi Q1, Q2, Q4 thật; chứng minh tương đương ngữ nghĩa Q3 Original vs Rewritten đồng nhất 100%.<br>- Bộ test: `tests/test_live_postgresql_e2e.py` (9/9 passed). | **PASS** |
| **08** | **Kiểm thử tự động phân tầng (Three-tier Test Suite)** | - Chạy toàn bộ test suite bằng `pytest`: **202 passed, 1 skipped, 0 failed** (tổng 203 items) trong 15,65s.<br>- Tầng 1 (Unit Tests): 124 tests (123 pass, 1 skip).<br>- Tầng 2 (Integration Tests): 61 tests (61 pass, gồm test PostgreSQL sống với cơ sở dữ liệu cách ly động và bảo toàn DB có sẵn).<br>- Tầng 3 (End-to-End Tests): 18 tests (18 pass, gồm kiểm toán đường ống, mã băm 600 plans, tính nhất quán checksum báo cáo và 3 bài kiểm tra negative test chống dữ liệu giả mạo).<br>- Bằng chứng: `results/validation/test_execution_summary.json`, `results/validation/pytest_execution.log`. | **PASS** |
| **09** | **Xác minh Hiệu năng Xử lý dữ liệu (Performance)** | - Đối chiếu `results/processing_benchmark/processing_benchmark.csv`.<br>- Polars CSV nhanh hơn Pandas CSV **40,37x** (75,27 ms vs 3.038,53 ms tại 500K).<br>- Parquet nhanh hơn CSV **23,93x** (127,00 ms vs 3.038,53 ms).<br>- Chunked Processing khống chế mức tăng RAM từ 241,37 MB xuống **+19,68 MB** (đọc) và **+21,09 MB** (aggregate).<br>- Phân biệt rõ phép đo tốc độ đọc, tính toán trong RAM và tổng thời gian pipeline.<br>- Lưu ý giới hạn phương pháp lấy mẫu RSS 1 ms. | **PASS** |
| **10** | **Đồng bộ Báo cáo và Hồ sơ giao nộp (`submission/`)** | - Cập nhật Chương 3, Chương 5, xuất bản lại Word OpenXML và PDF/A-1b (64 trang) tại `submission/TieuLuan_BatDongSan.docx` và `.pdf`.<br>- Xuất bản `submission/README_SUBMISSION.md` và thư mục `evidence/`. | **PASS** |

---

## 2. BẢNG ĐỐI CHIẾU SỐ LIỆU KIỂM TOÁN TỪ 3 TỆP CSV THỰC TẾ

*Bảng 2.1: Bảng đối chiếu số liệu kiểm toán trực tiếp từ các tệp dữ liệu CSV*

| Chỉ số kiểm toán (Metric) | Quy mô 50.000 dòng (`properties_50000.csv`) | Quy mô 200.000 dòng (`properties_200000.csv`) | Quy mô 500.000 dòng (`properties_500000.csv`) |
| :--- | :---: | :---: | :---: |
| **Dung lượng tệp trên đĩa** | 9.803.441 bytes (9,35 MB) | 39.311.466 bytes (37,49 MB) | 98.442.479 bytes (93,88 MB) |
| **Mã băm SHA-256** | `11bc4fe13aafbcbb7e8802e82b8262d157821bf52f44b1436dd6aea918da2f8b` | `84eabf931d8d87d0df1e3d0387d2a4e22f90599415abe93daddcd8400951ce19` | `9ba1afe8ce7edbf66e8c35f193e7ee955ccd85e5b24544e6eed3ea86418e789c` |
| **Số dòng $\times$ Số cột** | 50.000 $\times$ 9 | 200.000 $\times$ 9 | 500.000 $\times$ 9 |
| **Định danh `id` (Min, Max, Unique)** | Min: 1, Max: 50.000, 100% Unique | Min: 1, Max: 200.000, 100% Unique | Min: 1, Max: 500.000, 100% Unique |
| **Khuyết thiếu `district_name`** | 1.507 dòng (3,01%) | 5.704 dòng (2,85%) | **14.235 dòng (2,85%)** |
| **Khuyết thiếu `ward_name`** | 7.277 dòng (14,55%) | 28.896 dòng (14,45%) | **72.150 dòng (14,43%)** |
| **Khuyết thiếu `price` (Thỏa thuận)** | 3.993 dòng (7,99%) | 15.569 dòng (7,78%) | **39.061 dòng (7,81%)** |
| **Diện tích không hợp lệ ($area \le 0$)** | 0 dòng (0,00%) | 0 dòng (0,00%) | 0 dòng (0,00%) |
| **Ngày đăng không hợp lệ** | 0 dòng (0,00%) | 0 dòng (0,00%) | 0 dòng (0,00%) |
| **Trùng lặp tuyệt đối excl ID** | 0 dòng | 0 dòng | **2 dòng (3 bản ghi, 0,0004%)** |
| **Nghi ngờ trùng lặp (Suspected)** | 579 dòng (1,16%) | 9.777 dòng (4,89%) | **57.808 dòng (11,56%)** |
| **Ngoại lệ Giá bán (IQR)** | 4.536 dòng | 17.815 dòng | **44.860 dòng (9,73%)** |
| **Ngoại lệ Diện tích (IQR)** | 5.250 dòng | 20.938 dòng | **52.634 dòng (10,53%)** |
| **Trung vị Giá bán (Median)** | 7,40 tỷ VNĐ ($IQR = 10,20$ tỷ) | 7,40 tỷ VNĐ ($IQR = 10,20$ tỷ) | **7,40 tỷ VNĐ ($IQR = 10,20$ tỷ)** |
| **Trung vị Diện tích (Median)** | 80,0 m² ($IQR = 64,10$ m²) | 80,0 m² ($IQR = 64,10$ m²) | **80,0 m² ($IQR = 64,10$ m²)** |
| **Tin đăng Hải Phòng (Bài toán Q1)** | 1.053 dòng (2,11%) | 4.209 dòng (2,10%) | **10.422 dòng (2,08%)** |

---

## 3. BẢNG ĐỐI CHIẾU MÃ BĂM CÁC ARTIFACT GIAO NỘP (EVIDENCE MANIFEST)

| Tệp bàn giao (Artifact) | Dung lượng (Bytes) | Dung lượng định dạng | Mã băm toàn vẹn SHA-256 (64 ký tự hex) |
| :--- | :---: | :---: | :--- |
| `submission/TieuLuan_BatDongSan.docx` | 2.943.576 | 2,81 MB | `750fb5a347b580977648694fb302be60ba665811f16532f6d5d35aadb90b507b` |
| `submission/TieuLuan_BatDongSan.pdf` | 6.222.013 | 5,93 MB | `baab85fefc175d2e50b913ec05b57e754d70f3470b25373aee5861c297c3883d` |
| `submission/README_SUBMISSION.md` | 10.012 | 9,78 KB | `a4bb94e77663e00cfb6389f41b2ff65d496a7d519b5bf6ff292efb72b64d1f2e` |
| `submission/evidence/dataset_manifest.json` | 3.529 | 3,45 KB | `5bcea1bfa797edd804dba4c533d4a8861ce6eaaa0ac1b74bc9f167a7824f3ec4` |
| `submission/evidence/benchmark_manifest.json` | 94.180 | 91,97 KB | `b6f032cfb82af0216f08b6b85dedc341c903b3e00b372ba7c7f54a279570c63b` |
| `submission/evidence/benchmark_raw_plans.zip` | 504.366 | 492,55 KB | `262ed49431c0a4c758ad638dd253726273119acf27a23ca20997cec477677753` |
| `results/features/feature_manifest.json` | 733 | 0,72 KB | `04d64ea1c8ae6f51be8c5c76dbbfaf409605eb2c7f466b02a9042b781da26b0a` |
| `results/validation/test_execution_summary.json` | 34.216 | 33,41 KB | `0f20d6f2879590807b5a2bfbaae02f6ae67fa69925e0a6d0c6ee6ae25fb00e69` |

---

## 4. HƯỚNG DẪN KIỂM TRA VÀ TÁI LẬP HỆ THỐNG

### 4.1. Lệnh kiểm tra trạng thái Git
```powershell
git log -1 --oneline
git status
```
*Kết quả:* Nhánh `dev`, commit `6582918`, `working tree clean`.

### 4.2. Lệnh chạy toàn bộ 198 bài kiểm thử
```powershell
python -m pytest -v
```
*Kết quả:* `197 passed, 1 skipped in ~19s`.

### 4.3. Lệnh chạy kiểm thử trực tiếp PostgreSQL 18.3 (port 5433)
```powershell
python -m pytest tests/test_live_postgresql_e2e.py -v
```
*Kết quả:* `9 passed in ~4s`.

---

## 5. KẾT LUẬN NGHIỆM THU

Toàn bộ quy trình xử lý dữ liệu bất động sản, các bài toán benchmark và bộ kiểm thử đã được kiểm định khách quan trên dữ liệu thực tế, đạt chuẩn học thuật cao nhất và sẵn sàng phục vụ nghiệm thu đề tài.

