# TV2 Progress Checkpoint — PostgreSQL Benchmark & Validation

**Thời điểm cập nhật:** 2026-11-08  
**Branch:** `dev`  
**Repository:** `Chaumn/real-estate-performance`  
**Vai trò:** TV2 (Tester / Benchmark)  
**Database Server:** PostgreSQL 18.3, `127.0.0.1:5432`, user `postgres`  
**Trạng thái bàn giao cuối cùng:** `TV2_DELIVERABLE_ACCEPTED`  
**Trạng thái thực nghiệm:** `EXPERIMENT_ACCEPTED` (Dữ liệu đo: `LIVE_MEASURED`)  

---

## 1. Trạng thái Checklist Tổng thể

| Hạng mục | Trạng thái | Ghi chú & Bằng chứng |
|---|---|---|
| **A. DATASET** | **DONE** | 3 file CSV (50K, 200K, 500K) tại `data/processed/` đúng số dòng, đúng NULL counts, prefix consistency bit-for-bit = True, SHA-256 khớp manifest. |
| **B. DATABASE** | **DONE** | PostgreSQL 18.3 trên port 5432 kết nối thành công. Database `real_estate_db` có 500,000 dòng. Fingerprint DB khớp bit-for-bit với CSV 500K (`378250d507cbe...`). Khóa bảng SHARE và rollback test đạt chuẩn. |
| **C. QUERY OPTIMIZATION** | **DONE** | Q1, Q2, Q3 (Original/Rewritten), Q4 chạy live trên PostgreSQL. Equivalence test PASS (digest SHA-256 khớp tuyệt đối). B-Tree index isolation & catalog validation đạt 10/10 cấu hình. |
| **D. BENCHMARK RUNNER** | **DONE** | Experiment ID `62ea434decd44713b3752af152f81de8` gồm đủ 3 quy mô × 10 cấu hình = 30 configurations. 90 warm-up runs + 600 official runs với EXPLAIN ANALYZE BUFFERS JSON. |
| **E. TESTING** | **DONE** | Toàn bộ 212 tests: **211 PASSED**, **0 FAILED**, **0 ERRORS**, 1 SKIPPED (`test_sample_5000_regression`). Live PostgreSQL integration tests 10/10 PASS. JUnit XML: `deliverables/tv2/evidence/regression_current.xml`. |
| **F. TABLES & FIGURES** | **DONE** | 7 bảng phân tích độc lập (`benchmark_summary`, `execution_statistics`, `query_comparison`, `scaling_analysis`, `index_analysis`, `q3_factorial_analysis`, `test_summary`) định dạng CSV + MD. 8 biểu đồ FIG01–FIG08 (PNG 300 DPI + SVG). |
| **G. DASHBOARD** | **DONE** | `deliverables/tv2/dashboard/index.html` chạy offline 100%, có bộ lọc theo quy mô & truy vấn, liên kết tới execution plans và biểu đồ. Headless Chrome CDP browser smoke test: PASS (30 cấu hình, lọc tương tác 10 dòng, 2 dòng, reset 30 dòng, 0 console error, 54 liên kết & 8 ảnh tồn tại trên đĩa). |
| **H. HANDOFF TV3** | **DONE** | Gói `deliverables/tv2/` và file nén `deliverables/tv2.zip` (173 entries, CRC testzip PASS, SHA-256 xác thực). `chapter5_handoff.md` đủ các mục 5.1–5.6. `manifest.json` và `SHA256SUMS.txt` cập nhật đầy đủ. |
| **I. REPOSITORY CLEANUP** | **DONE** | Bảo vệ uncommitted files, `deliverables/tv2_staging/` an toàn, không có file duy nhất bị mất, cấu trúc thư mục sạch. |

---

## 2. Chi tiết Nghiệm thu Cuối cùng (Final Acceptance & Handoff Audit)

### Task 1 — Experiment ID & Raw Plans Verification
- **Experiment ID:** `62ea434decd44713b3752af152f81de8`
- **Số lượng cấu hình:** 3 quy mô (50K, 200K, 500K) × 10 cấu hình = 30 cấu hình.
- **Số lượng Warm-up Runs:** Đủ 90 runs (3 warmups × 30 configs).
- **Số lượng Official Plans:** Đủ 600 plans (20 official runs × 30 configs).
- Toàn bộ 600 plans được lưu độc lập dưới dạng `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` trong `deliverables/tv2/evidence/benchmark_raw_plans.zip` và các file `*_run01.json` đại diện.

### Task 2 — Tái tính toán Toàn vẹn (Raw JSON → 7 Bảng)
- Đã đọc trực tiếp 600 official plans trong `evidence/benchmark_raw_plans.zip` và tính lại `median`, `IQR`, `min`, `max`, `speedup`.
- **Kết quả đối chiếu:** Khớp 100% với `deliverables/tv2/tables/benchmark_summary.csv` (0 chênh lệch).
- 7 bảng CSV/Markdown đều phản ánh đúng dữ liệu đo thực nghiệm mới:
  1. `benchmark_summary`: Tóm tắt median, IQR, min, max, speedup, scan type.
  2. `execution_statistics`: Phân tách chi tiết Execution Time và Planning Time.
  3. `query_comparison`: Tỷ lệ cải thiện hiệu năng so với baseline tương ứng.
  4. `scaling_analysis`: Hệ số tăng thời gian thực thi theo quy mô dữ liệu.
  5. `index_analysis`: Dung lượng index đo từ `pg_relation_size` và kiểu quét.
  6. `q3_factorial_analysis`: Ma trận $2 \times 2$ phân tích độc lập tác động của Indexing và Query Rewriting.
  7. `test_summary`: Kết quả test suite (211 passed, 1 skipped, 0 failed).

### Task 3 — Đồng bộ Biểu đồ (FIG01–FIG08) & Dashboard
- 8 biểu đồ đã được cập nhật nhãn `LIVE_MEASURED` và nguồn dữ liệu từ experiment mới.
- Cả định dạng PNG (300 DPI, sẵn sàng dán Word) và SVG (vector sắc nét) đều có mặt đầy đủ.
- Dashboard đã cập nhật header `EXPERIMENT_ACCEPTED`, không còn nhãn `HISTORICAL` trên các artifact đã đo trực tiếp.

### Task 4 — Hoàn thiện Báo cáo Chương 5
- `deliverables/tv2/chapter5_handoff.md` đã có đầy đủ 6 mục tiêu chuẩn:
  - **5.1 Môi trường thực nghiệm:** Chi tiết PostgreSQL 18.3, Windows 11, Intel Core 14 cores, thông số `pg_settings` thực tế.
  - **5.2 Vận hành hệ thống:** Giao thức đo 90 warmup + 600 runs, khóa SHARE table, kiểm tra rollback.
  - **5.3 Kết quả Q1–Q4:** Bảng số liệu định lượng đầy đủ 30 cấu hình kèm median, IQR, speedup.
  - **5.4 Khả năng mở rộng:** Phân tích scaling ratios dựa trên `scaling_analysis.md` và `FIG03`.
  - **5.5 Giải thích kết quả:** Phân tích nguyên nhân tối ưu (B-Tree lookup vs Sequential scan, IN vs JOIN rewriting, Q4 overhead).
  - **5.6 Hạn chế thực nghiệm:** Nêu rõ các điều kiện biên khoa học (warm-cache, prefix datasets, background OS noise).

### Task 5 — Phân định Nguồn gốc & Provenance
- Phân biệt minh bạch 3 tầng thông tin:
  1. **Dataset:** 3 file CSV có SHA-256 cố định, đảm bảo tính kế thừa tiền tố (prefix consistency: 50K $\subset$ 200K $\subset$ 500K).
  2. **Live Experiment:** `62ea434decd44713b3752af152f81de8` được chạy trực tiếp trên PostgreSQL 18.3 (`real_estate_db` 500K dòng).
  3. **Historical / Staging:** Các file cũ trong staging được bảo vệ an toàn và không bị nhầm lẫn với dữ liệu live.

### Task 6 — Browser Smoke Test tương tác qua Chrome DevTools Protocol (CDP)
- Kiểm thử tương tác end-to-end với Google Chrome headless qua giao thức CDP WebSocket:
  - Khởi tạo trang: Hiển thị 30 dòng cấu hình đầy đủ.
  - Lọc tương tác theo Quy mô (Scale = 50,000): Bảng lọc chính xác còn 10 dòng.
  - Lọc kết hợp Truy vấn (Scale = 50,000 & Query = Q1): Bảng lọc chính xác còn 2 dòng (`Q1_baseline`, `Q1_indexed`).
  - Đặt lại bộ lọc (Reset): Bảng phục hồi đầy đủ 30 dòng.
  - Kiểm tra liên kết: 54 liên kết tệp tin và 8 thẻ hình ảnh đều tồn tại hợp lệ trên hệ thống tệp.
  - Lỗi Console / Runtime: 0 lỗi JavaScript (`PASS`).

### Task 7 — Đóng gói & Kiểm tra Tính toàn vẹn `tv2.zip`
- Tệp nén: `deliverables/tv2.zip`
- Kích thước: ~2.11 MB
- Số lượng tệp con: 173 tệp tin (bao gồm đầy đủ `README.md`, `chapter5_handoff.md`, `manifest.json`, `SHA256SUMS.txt`, 7 tables, 8 figures, dashboard, raw plans archive).
- Kiểm tra CRC (`zipfile.testzip()`): **PASS (None)**
- Mã băm SHA-256: `6d80d1d92d31e4952df6e12c2aafc5fc78d099818a18ed632becdf97be81aaea`

### Task 8 — Đồng bộ Trạng thái Nghiệm thu
- Toàn bộ tài liệu chính thức đều thống nhất trạng thái:
  - `manifest.json`: `"status": "EXPERIMENT_ACCEPTED"`, `"delivery_status": "TV2_DELIVERABLE_ACCEPTED"`
  - `README.md`: `# Gói Bàn Giao TV2 — LIVE_MEASURED / TV2_DELIVERABLE_ACCEPTED / EXPERIMENT_ACCEPTED`
  - `chapter5_handoff.md`: `# Chương 5 — thí nghiệm mới LIVE_MEASURED`
  - `dashboard/index.html`: `Status: EXPERIMENT_ACCEPTED (LIVE_MEASURED)`

---

## 3. Đường dẫn Bàn giao Trực tiếp cho TV3

- **Bản nén ZIP bàn giao TV3:** `deliverables/tv2.zip`
- **Báo cáo Chương 5:** `deliverables/tv2/chapter5_handoff.md`
- **Hướng dẫn TV3:** `deliverables/tv2/README.md`
- **Bảng số liệu (CSV + Markdown):** `deliverables/tv2/tables/`
- **Biểu đồ (PNG 300 DPI + SVG):** `deliverables/tv2/figures/`
- **Dashboard trực quan:** `deliverables/tv2/dashboard/index.html`
- **Bằng chứng raw plans:** `deliverables/tv2/evidence/benchmark_raw_plans.zip`
- **Biên bản kiểm tra gói:** `deliverables/tv2/evidence/package_validation.json`
- **Mã băm SHA-256:** `deliverables/tv2/SHA256SUMS.txt`
