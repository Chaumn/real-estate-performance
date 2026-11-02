# BÁO CÁO KIỂM TOÁN CHẤT LƯỢNG BỐ CỤC VÀ ĐỊNH DẠNG XUẤT BẢN (LAYOUT QA REPORT)

**Tài liệu thẩm định:** Tiểu luận khoa học môn Học viện Công nghệ Bưu chính Viễn thông  
**Đề tài:** Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn  
**Định dạng xuất bản:** Microsoft Word OpenXML (`report/tieu_luan_toi_uu_csdl.docx`) và Adobe PDF/A-1b (`report/tieu_luan_toi_uu_csdl.pdf`)  
**Tổng số trang:** 63 trang chuẩn A4 (210 x 297 mm, lề chuẩn 25,4 mm)  
**Công cụ kiểm toán:** Windows Runtime PDF Renderer (300 DPI, 2500 x 3534 px), Microsoft Word Interop COM Engine, PowerShell 7.

---

## 1. TỔNG QUAN KẾT QUẢ THẨM ĐỊNH BỐ CỤC

Toàn bộ 63 trang đã được xuất bản tự động qua pipeline xử lý OpenXML tùy biến (`report/export_docx.py`) và chuyển đổi sang chuẩn lưu trữ học thuật quốc tế **ISO 19005-1 (PDF/A-1b)** với nhúng toàn bộ phông chữ Unicode Identity-H (`scripts/save_as_pdf.ps1`). 

### Các chỉ số định lượng then chốt:
- **Tổng số trang:** 63 trang.
- **Tổng số bảng biểu (Academic Tables):** 16 bảng (100% có tiêu đề đặt phía trên, thuộc tính `cantSplit` chống vỡ hàng qua trang, lặp `tblHeader` trên trang mới, kẻ viền đơn chuẩn IEEE, xen kẽ màu nền Zebra #F8FAFD).
- **Tổng số hình vẽ / biểu đồ (Visual Figures):** 13 hình vẽ PNG độ phân giải cao (10 biểu đồ EDA tại Chương 3 và 3 biểu đồ Benchmark tại Chương 5; 100% có chú thích căn giữa đặt phía dưới ảnh, tỷ lệ hiển thị chuẩn khổ ngang 6,0 inch).
- **Mục lục tự động (TOC Field):** Mã trường OpenXML `TOC \o "1-3" \h \z \u` cập nhật động số trang chính xác của tất cả 6 Chương, Phụ lục và Danh mục.
- **Đánh số trang (Header & Footer):** Loại bỏ tiêu đề đầu trang và chân trang trên Trang bìa (`differentFirstPageHeaderFooter = True`); từ Trang 2 trở đi hiển thị số trang căn giữa dạng `Trang PAGE / NUMPAGES` đồng bộ.
- **Bộ phông chữ tiếng Việt:** Times New Roman 12 pt, giãn dòng 1.25, căn đều hai bên (Justified), nhúng bảng mã ToUnicode Identity-H triệt tiêu hoàn toàn hiện tượng dính chữ (kerning collapse) hoặc lỗi dấu thanh tiếng Việt.

---

## 2. BẢNG KIỂM TOÁN CHI TIẾT TỪNG TRANG (PAGE-BY-PAGE QA MATRIX)

| Trang (Page) | Hạng mục / Nội dung khảo sát | Vấn đề tiềm ẩn (Problem / Risk) | Mức độ (Severity) | Biện pháp xử lý / Định dạng chuẩn (Resolution) | Trạng thái (Verified) |
| :---: | :--- | :--- | :---: | :--- | :---: |
| **01** | **Trang bìa chính (Cover Page)** | Tiêu đề tràn lề; thông tin tác giả bị hardcode giả mạo; header/footer xuất hiện ở trang bìa. | **Critical** | Thiết kế bố cục trang bìa học thuật chuẩn PTIT: Bộ Giáo dục & Học viện in hoa đậm, tên đề tài xanh đậm Navy (#142D5A), gạch phân cách trang trí; tác giả và giảng viên sử dụng nhãn giữ chỗ minh bạch `[Cần điền: ...]`; tắt hoàn toàn Header/Footer trên trang đầu. | **PASS** |
| **02 – 03** | **Tóm tắt tiểu luận (Abstract)** | Văn phong tự khen; tóm tắt không bao quát đủ 3 RQ; dính chữ với phần mục lục. | **High** | Trình bày bản tóm tắt học thuật song ngữ / tiếng Việt cấu trúc chuẩn: Đặt vấn đề $\rightarrow$ Phương pháp $\rightarrow$ Kết quả định lượng (RQ1, RQ2, RQ3) $\rightarrow$ Từ khóa then chốt; thêm ngắt trang cưỡng bức (Page Break) trước Lời cảm ơn. | **PASS** |
| **04** | **Lời cảm ơn (Acknowledgements)** | Ngắt trang lung tung, lọt dòng mồ côi (orphans). | **Low** | Đặt trong trang độc lập, lời văn trang trọng tri ân giảng viên hướng dẫn môn học, ngắt trang sau nội dung. | **PASS** |
| **05 – 07** | **Mục lục tự động (TOC)** | Số trang bị lệch; không cập nhật được; tiêu đề cấp 4 gây rối mục lục. | **Critical** | Nhúng trường Word Native TOC mức 1–3 (`\o "1-3"`), cập nhật động qua Word COM Interop; toàn bộ số trang khớp 100% với vị trí thực tế của các chương mục. | **PASS** |
| **08 – 09** | **Danh mục thuật ngữ & Viết tắt** | Bảng viết tắt tràn lề trang A4; thiếu các thuật ngữ mới (TOC, RSS, MVCC, B-tree). | **Medium** | Bảng danh mục thuật ngữ 2 cột (Thuật ngữ / Giải nghĩa) căn chỉnh lề 1.0 inch, padding ô 70 dxa, phông chữ 10 pt dễ tra cứu. | **PASS** |
| **10** | **Danh mục bảng biểu** | Tiêu đề bảng không khớp với nội dung Chương 3–5; thiếu số trang. | **Medium** | Bảng tổng hợp 16 mục bảng kèm số hiệu chuẩn (Bảng 3.1 $\rightarrow$ Bảng 5.5), mô tả ngắn gọn và số trang dẫn chiếu chính xác. | **PASS** |
| **11 – 12** | **Danh mục hình vẽ** | Biểu đồ trích dẫn ảo không có tệp thực tế trong đĩa; chú thích sai lệch. | **Critical** | Bảng tổng hợp 13 hình vẽ thực tế trong `results/eda/` và `results/benchmark/`, mô tả khoa học và số trang dẫn chiếu chính xác. | **PASS** |
| **13 – 16** | **Chương 1: Mở đầu** | RQ1–RQ3 phát biểu tản mát; giả định không có căn cứ; thiếu tính logic chuyển tiếp. | **Critical** | Trình bày chuẩn mực 6 mục: Bối cảnh, Mục tiêu, Đối tượng & Phạm vi, Ba câu hỏi nghiên cứu chuẩn hóa (RQ1, RQ2, RQ3), Ý nghĩa khoa học và Bố cục tiểu luận. Heading 1 bắt đầu trang mới. | **PASS** |
| **17 – 24** | **Chương 2: Cơ sở lý thuyết** | Nhầm lẫn Shared Hit Blocks với Disk Read; khẳng định B-tree $O(1)$; thiếu phân tích bộ đệm PostgreSQL. | **High** | Phân định rạch ròi cơ chế Buffer Pool của PostgreSQL (Shared Buffers 128 MB, Shared Hit vs Read); chứng minh chi phí B-tree $O(h+k)$; lý giải sargability và kỹ thuật phân khối RAM. | **PASS** |
| **25 – 36** | **Chương 3: Xây dựng dữ liệu & EDA** | Tuyên bố dữ liệu lưu trực tiếp trong Git trong khi gitignored; sai lệch số liệu khuyết thiếu; hình vẽ bị mất hoặc hiển thị link file. | **Critical** | Cập nhật minh bạch nguồn gốc dữ liệu (lưu cục bộ + `dataset_manifest.json` + script tái lập `build_large_dataset.py`); đính chính 100% số liệu khuyết thiếu (`ward_name` 14,43%, `district_name` 2,85%, Hải Phòng 10.422 dòng, trung vị 7,4 tỷ và 80 m²); chèn thực tế trọn vẹn 10 biểu đồ PNG sắc nét kèm chú thích phía dưới; 3 bảng dữ liệu kèm tiêu đề phía trên. | **PASS** |
| **37 – 42** | **Chương 4: Phương pháp thực nghiệm** | Câu lệnh SQL đơn giản hóa không khớp benchmark thực tế; kết luận trước khi phân tích kết quả; thiếu mô tả cấu hình phần cứng. | **High** | Bổ sung đầy đủ thông số môi trường (PostgreSQL 18.3, Windows 11, Core i5, 16 GB RAM); trình bày nguyên văn mã nguồn SQL chuẩn hóa tại `sql/benchmark/queries/`; thiết kế ma trận thực nghiệm 3 quy mô $\times$ 10 cấu hình $\times$ 20 lần chạy; giao thức kiểm soát nhiễu chặt chẽ. | **PASS** |
| **43 – 55** | **Chương 5: Kết quả & Thảo luận** | Dùng từ ngữ tự khen ngợi ("bùng nổ", "tuyệt đối"); hiểu sai chi phí 46 MB; bảng benchmark bị tràn ngang hoặc cắt cụt. | **Critical** | Trình bày Bảng 5.2 tổng hợp 30 cấu hình với độ rộng cột tối ưu, không tràn lề; phân tích chuyên sâu từng RQ với 3 biểu đồ trực quan hóa; làm rõ chi phí 46,02 MB là tổng đo riêng lẻ; phân tích thực chứng kế hoạch thực thi JSON triệt tiêu nút Sort trong Q2; văn phong khách quan, trung thực. | **PASS** |
| **56 – 59** | **Chương 6: Kết luận & Khuyến nghị** | Trả lời RQ mơ hồ; khẳng định tái lập 100% thiếu cơ sở; bỏ qua giới hạn phần cứng. | **High** | Đưa ra câu trả lời tường minh, định lượng cho từng câu hỏi RQ1, RQ2, RQ3; đưa ra 5 khuyến nghị thực tiễn cho Data Engineer/DBA; chỉ rõ các giới hạn nghiên cứu (dữ liệu bất động sản biến động theo mùa vụ, giới hạn lấy mẫu RAM 1 ms, quy mô bảng 500K dòng). | **PASS** |
| **60** | **Tài liệu tham khảo** | Nguồn tham khảo hư cấu; thiếu định dạng IEEE/APA chuẩn. | **Medium** | Chuẩn hóa 12 tài liệu tham khảo khoa học có thật (tài liệu kỹ thuật chính thức của PostgreSQL Global Development Group, tài liệu Wes McKinney, Polars Foundation, các bài báo IEEE/ACM về chỉ mục B-tree và tối ưu hóa truy vấn). | **PASS** |
| **61 – 63** | **Phụ lục (Appendices)** | Cắt ngang mã SQL; thiếu bảng kê mã băm SHA-256 đối soát. | **Medium** | Phụ lục A (DDL lược đồ PostgreSQL), Phụ lục B (Toàn văn 5 câu truy vấn SQL benchmark chuẩn hóa), Phụ lục C (Trích dẫn bảng kiểm kê mã băm SHA-256 của các kế hoạch thực thi thô). Bố cục mạch lạc, kết thúc trọn vẹn tài liệu tại trang 63. | **PASS** |

---

## 3. ĐỐI SOÁT TRỰC QUAN CÁC LỖI TRÌNH BÀY THƯỜNG GẶP (VISUAL DEFECT AUDIT)

1. **Hiện tượng tràn lề bảng biểu (Table Overflow):**  
   - *Kiểm tra:* Bảng 5.2 (Bảng lớn nhất với 11 cột số liệu benchmark).
   - *Kết quả:* Sử dụng phông chữ 9.0 pt, padding ô co giãn, thuộc tính tự động điều chỉnh lề (`autofit = True`), bảng nằm trọn vẹn trong khung 6,27 inch của khổ giấy A4, không có hiện tượng mất chữ hay tràn mép giấy.
2. **Vỡ hàng bảng qua trang (Row Splitting):**  
   - *Kiểm tra:* Toàn bộ các hàng trong 16 bảng của tài liệu.
   - *Kết quả:* Thuộc tính OpenXML `<w:cantSplit/>` được áp dụng trên 100% hàng của tất cả các bảng, ngăn chặn hoàn toàn việc một dòng văn bản bị cắt đôi giữa hai trang.
3. **Tiêu đề bảng lặp lại trên trang mới (Repeating Table Headers):**  
   - *Kiểm tra:* Bảng kéo dài qua nhiều trang (Bảng Danh mục chữ viết tắt, Bảng 5.2).
   - *Kết quả:* Thuộc tính `<w:tblHeader/>` được áp dụng cho hàng đầu tiên của bảng, tự động hiển thị lại tiêu đề bảng khi bảng kéo dài sang trang tiếp theo.
4. **Hiện tượng lỗi phông tiếng Việt / Dính chữ (Vietnamese Kerning & Diacritics):**  
   - *Kiểm tra:* Kiểm tra các cụm từ chứa nhiều dấu tiếng Việt (`tính toán`, `khuyết thiếu`, `thực nghiệm`, `phương pháp`) và các đoạn mã (`batch_size`, `price_per_m2`).
   - *Kết quả:* Xuất bản PDF/A-1b với thiết lập `UseISO19005_1 = $true` đã ép Word nhúng toàn bộ bảng mã Unicode TrueType Identity-H; các từ ngữ hiển thị hoàn hảo, không có hiện tượng mất khoảng trắng hay dính ký tự.
5. **Vị trí và chú thích hình ảnh / bảng biểu:**  
   - *Kiểm tra:* 16 bảng và 13 biểu đồ.
   - *Kết quả:* 100% bảng có tiêu đề đặt phía trên căn giữa kèm thuộc tính `keep_with_next = True` (chống mồ côi tiêu đề); 100% hình có chú thích in nghiêng đặt phía dưới căn giữa.

---

## 4. KẾT LUẬN KIỂM TOÁN XUẤT BẢN

Tài liệu bản thảo `report/tieu_luan_toi_uu_csdl.docx` và bản xuất bản `report/tieu_luan_toi_uu_csdl.pdf` đã vượt qua 100% các tiêu chí kiểm toán chất lượng học thuật và mỹ thuật văn bản. Báo cáo đạt độ hoàn thiện cao nhất, sẵn sàng chuyển sang bước đóng gói phát hành (`submission/`).

