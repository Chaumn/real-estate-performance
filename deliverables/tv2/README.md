# Gói Bàn Giao TV2 — LIVE_MEASURED / PACKAGE_INTEGRITY_VERIFIED / EXPERIMENT_EVIDENCE_VERIFIED_OFFLINE

## 1. Giới thiệu Gói Bàn Giao
Gói bàn giao TV2 chứa toàn bộ kết quả đo thực nghiệm hiệu năng PostgreSQL 18.3 trên cơ sở dữ liệu bất động sản (`real_estate_db`), phục vụ trực tiếp cho TV3 viết Chương 5 của tiểu luận tốt nghiệp môn Tối ưu CSDL (IDS - PTIT).

- **Trạng thái nghiệm thu bàn giao:** `PACKAGE_INTEGRITY_VERIFIED`
- **Trạng thái thực nghiệm:** `EXPERIMENT_EVIDENCE_VERIFIED_OFFLINE` (Phân loại dữ liệu: `LIVE_MEASURED`)
- **Experiment ID:** `62ea434decd44713b3752af152f81de8`
- **Quy mô đo:** 3 quy mô (50.000, 200.000, 500.000 bản ghi) $\times$ 10 cấu hình = 30 cấu hình thực nghiệm.
- **Tổng số lượt chạy:** 90 warm-up runs + 600 official measurement runs.
- **Bằng chứng raw plans:** Toàn bộ 600 official plans và 90 warmups được lưu dưới dạng `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` trong `evidence/benchmark_raw_plans.zip` (600 official plans); 90 warmups ở các file `*_warmup*.json`.

## 2. Hướng Dẫn Sử Dụng Cho TV3
1. **Báo cáo Chương 5:** Tham khảo trực tiếp [`chapter5_handoff.md`](chapter5_handoff.md), đã bao gồm đầy đủ các mục từ 5.1 đến 5.6 với số liệu định lượng, môi trường thực nghiệm và phân tích nguyên nhân.
2. **Bảng số liệu:** Toàn bộ bảng nằm tại thư mục [`tables/`](tables/) với cả hai định dạng `.csv` và `.md`:
   - `benchmark_summary`: Tổng hợp median, IQR, min, max, speedup và scan type.
   - `execution_statistics`: Phân rã Execution Time và Planning Time.
   - `query_comparison`: Đối chiếu chênh lệch thời gian và tỷ lệ cải thiện so với baseline.
   - `scaling_analysis`: Hệ số tăng thời gian so với quy mô dữ liệu 50K.
   - `index_analysis`: Dung lượng index đo từ `pg_relation_size` và scan type thực tế.
   - `q3_factorial_analysis`: Thiết kế giai thừa $2 \times 2$ tách rời tác động của rewriting và indexing.
   - `test_summary`: Kết quả full regression test suite (220 PASS, 0 FAIL, 0 SKIP).
3. **Biểu đồ nghiên cứu:** Thư mục [`figures/`](figures/) chứa FIG01–FIG08 ở cả hai định dạng:
   - PNG 300 DPI: Sẵn sàng chèn trực tiếp vào báo cáo Microsoft Word.
   - SVG vector: Cho phép phóng to, chỉnh sửa định dạng hoặc in ấn học thuật mà không vỡ hình.
4. **Dashboard tương tác (Offline 100%):** Mở [`dashboard/index.html`](dashboard/index.html) trực tiếp trên trình duyệt Chrome / Edge (không yêu cầu web server hay internet). QA được báo cáo trước đây: PASS cho Chrome headless DOM và contact sheet (nhãn tiếng Việt, không thấy clipping), xem evidence/prior_validation.json. Chưa có bằng chứng tái hiện tương tác CDP; CDP interaction: NOT_VERIFIED. Lần này không chạy lại browser, visual QA, PostgreSQL hoặc benchmark.

## 3. Tái Tạo và Kiểm Định
- **Kiểm định gói bàn giao và mã băm SHA-256:**
  ```powershell
  python -m scripts.validate_handoff
  ```
- **Chạy lại toàn bộ test suite kiểm thử hệ thống:**
  ```powershell
  python -m pytest -v --junitxml=deliverables/tv2/evidence/regression_current.xml
  ```

## 4. Giới Hạn Khoa Học Được Ghi Nhận
- Dữ liệu đo là warm-cache (bộ đệm PostgreSQL và OS đã nạp dữ liệu).
- Tập dữ liệu 50K, 200K, 500K có quan hệ tiền tố (prefix-consistent) nhằm đảm bảo tính kế thừa, không phải 3 mẫu ngẫu nhiên độc lập.
- Chưa xác định nguyên nhân độ phân tán IQR ở quy mô lớn; mọi bảng tổng hợp đều trình bày kèm IQR và min/max bên cạnh median.


## Nguồn và phạm vi nghiệm thu

Full regression: 220 PASS, 0 FAIL, 0 SKIP. Trạng thái hiện tại: EXPERIMENT_EVIDENCE_VERIFIED_OFFLINE / PACKAGE_INTEGRITY_VERIFIED. Toàn bộ 220 ca kiểm thử (Unit, Integration và Live PostgreSQL E2E) đạt 100%.

FIG08 lấy từ báo cáo chất lượng/build dataset; không phải phép đo PostgreSQL. Regression mới loại trừ module live để không thay đổi database.

### Regression của bản sửa

- Offline regression: 210 PASS, 0 FAIL, 1 SKIP (`evidence/offline_revision.xml`); loại trừ live PostgreSQL module.
- Kiểm thử packaging cuối cùng: 10 PASS (`evidence/packaging_revision.xml`).
- Integrity: 151 artifact đo/hình/evidence gốc giữ nguyên bytes, bảng giữ nguyên giá trị và dashboard giữ nguyên payload (`evidence/integrity_check.json`). Tái kiểm: `python -m scripts.audit_handoff_integrity`.
- `tables/test_summary` tiếp tục mô tả full regression cũ tại c51b2c2, không phải regression của bản sửa.
