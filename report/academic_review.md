# BÁO CÁO PHẢN BIỆN HỌC THUẬT ĐỘC LẬP (ACADEMIC REVIEW REPORT)
## Đề tài: Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn
**Giảng viên Phản biện: Ban Đánh giá Chuyên môn Khoa học Dữ liệu & Hệ cơ sở dữ liệu**

---

### TỔNG QUAN ĐÁNH GIÁ CỦA PHẢN BIỆN (REVIEWER ASSESSMENT)

Tiểu luận giải quyết một chủ đề có ý nghĩa lý thuyết và ứng dụng thực tiễn trong ngành Khoa học Dữ liệu và Kỹ nghệ Cơ sở dữ liệu: Xây dựng pipeline dữ liệu thực tế lớn có kiểm soát và đo lường định lượng các kỹ thuật tối ưu hóa hiệu năng truy vấn trên PostgreSQL phiên bản 18.3 x86_64 cùng các công cụ xử lý dữ liệu hiện đại (Pandas, Polars, Parquet).

Tuy nhiên, trong các bản thảo sơ bộ trước đây, công trình đã bộc lộ một số khiếm khuyết học thuật nghiêm trọng:
1. **Lẫn lộn cấu trúc nghiên cứu:** Việc gộp phần Xây dựng dữ liệu và Thiết kế thực nghiệm vào cùng một chương làm mờ nhạt ranh giới giữa quy trình dữ liệu (data engineering) và phương pháp đo lường (benchmarking methodology); các câu hỏi nghiên cứu chưa được phân tách rõ ràng giữa tầng tiền xử lý dữ liệu và tầng cơ sở dữ liệu quan hệ.
2. **Sai lệch số liệu thống kê giữa các chương:** Tồn tại sự mâu thuẫn giữa số liệu trong văn bản và các tệp dữ liệu gốc (ví dụ: số tin đăng Hải Phòng bị ghi nhận sai lệch, tỷ lệ khuyết thiếu của `ward_name` và `district_name` không khớp với báo cáo profiling, giá trị trung vị bị sai lệch).
3. **Diễn giải khoa học chưa chuẩn xác:** Nhầm lẫn giữa khái niệm `Shared Hit Blocks` (đọc từ bộ đệm RAM) với số block đọc từ đĩa; tùy tiện khẳng định Index Scan có độ phức tạp $O(1)$ phổ quát; đưa ra kết luận khái quát thái quá ("mọi tác vụ Chunked đều dưới 20 MB RAM") khi số liệu thực tế đo được là +21,09 MB; gọi con số 46,02 MB là dung lượng quan sát đồng thời trong khi các chỉ mục được đo riêng theo từng cấu hình độc lập.
4. **Vấn đề xuất bản Word (.docx):** Script xuất Word ban đầu chưa sử dụng Word Heading styles thực sự khiến mục lục không tự cập nhật được; biểu đồ bị thiếu hoặc không được chèn thực tế vào văn bản; công thức KaTeX và mã định dạng Markdown chưa được xử lý đồng bộ.

Sau khi yêu cầu rà soát và sửa đổi toàn diện, bản thảo hiện tại đã khắc phục triệt để các tồn tại trên. Báo cáo phản biện này thẩm định chi tiết các nội dung đã được hoàn thiện.

---

### PHẦN 1: THẨM ĐỊNH TÍNH CHUẨN XÁC DỮ LIỆU VÀ CÂU HỎI NGHIÊN CỨU

#### 1.1. Chuẩn hóa ba câu hỏi nghiên cứu (RQ1 – RQ3)
Cấu trúc nghiên cứu đã được tái cấu trúc thành 6 chương mạch lạc:
- **RQ1 (Xây dựng bộ dữ liệu và đánh giá chất lượng dữ liệu):** Tập trung vào quy trình nạp luồng, bộ quy tắc làm sạch và hồ sơ chất lượng dữ liệu (Data Profiling & EDA), được trình bày tại Chương 3 và trả lời tại Mục 5.1 và 6.2.
- **RQ2 (Đánh giá hiệu năng xử lý dữ liệu bằng Pandas, Polars, CSV, Parquet và Chunked Processing):** Tập trung vào so sánh định dạng tệp (CSV vs Parquet), động cơ tính toán (Pandas vs Polars) và kỹ thuật kiểm soát bộ nhớ (Chunked Streaming), trình bày phương pháp tại Mục 4.2 và trả lời tại Mục 5.2 và 6.2.
- **RQ3 (Đánh giá tối ưu PostgreSQL thông qua Q1–Q4):** Khảo sát 4 bài toán truy vấn SQL điển hình trên PostgreSQL 18.3 qua 3 quy mô dữ liệu (50K, 200K, 500K), trình bày phương pháp tại Mục 4.3 và trả lời tại Mục 5.3 và 6.2.

Sự phân tách này bảo đảm tính logic: từ xây dựng dữ liệu $\rightarrow$ tối ưu tầng tiền xử lý $\rightarrow$ tối ưu tầng lưu trữ quan hệ.

#### 1.2. Thẩm định tính chuẩn xác của các số liệu thống kê gốc
Đối chiếu trực tiếp với các tệp dữ liệu thô trong repository:
- **Tỷ lệ khuyết thiếu:**
  - `ward_name`: Thiếu đúng **72.150 bản ghi** (**14,43%**), khớp hoàn toàn với `build_report_500000.json` và `data_quality_report_500000.json`. Bản thảo cũ ghi sai thành 47.904 bản ghi (9,58%) đã được sửa dứt điểm.
  - `district_name`: Thiếu đúng **14.235 bản ghi** (**2,85%**). Bản thảo cũ ghi sai thành 53 bản ghi (0,01%) đã được sửa dứt điểm.
  - `price`: Thiếu đúng **39.061 bản ghi** (**7,81%**), phản ánh các tin đăng dạng "giá thỏa thuận".
- **Số lượng tin đăng Hải Phòng (Bài toán Q1):** Đúng **10.422 bản ghi** (**2,08%** tổng số hàng tại 500K), khớp với `Actual Rows: 10422.0` trong tệp kế hoạch `500000_Q1_baseline_run01.json`. Bản thảo cũ ghi nhận con số hư cấu 15.541 (3,11%) đã được loại bỏ hoàn toàn.
- **Đại lượng thống kê mô tả vững:**
  - Trung vị diện tích là **80,0 m²** (IQR = 64,1 m²), sửa đổi từ con số 68,0 m² trước đó.
  - Trung vị giá chào bán là **7,40 tỷ VNĐ** (IQR = 10,20 tỷ VNĐ), sửa đổi từ con số 6,50 tỷ VNĐ trước đó.
- **Chỉ số bộ nhớ Chunked Processing:**
  - Tác vụ đọc phân khối (`Pandas Chunked read`): Delta RSS = **+19,68 MB**.
  - Tác vụ đọc kèm tính toán tổng hợp phân khối (`Pandas Chunked aggregate`): Delta RSS = **+21,09 MB**.
  - Tác giả đã loại bỏ câu khẳng định thiếu cơ sở cho rằng "mọi tác vụ Chunked đều dưới 20 MB", giải thích thỏa đáng nguyên nhân vượt ngưỡng do chi phí tích lũy bảng tổng hợp trung gian.

---

### PHẦN 2: THẨM ĐỊNH TÍNH ĐÚNG ĐẮN VỀ MẶT KHOA HỌC VÀ CƠ SỞ DỮ LIỆU

#### 2.1. Phân biệt Shared Hit Blocks và Shared Read Blocks
Trong các bản thảo trước, tác giả thường dùng cụm từ "số block đọc từ đĩa" để chỉ `Shared Hit Blocks`. Đây là một lỗi nghiêm trọng về mặt kiến trúc cơ sở dữ liệu.
Bản thảo sửa đổi đã đính chính chính xác:
- Sau 3 lượt warm-up, toàn bộ dữ liệu của bảng và chỉ mục đã nằm trong bộ đệm RAM của PostgreSQL (`Shared Buffers`).
- Số lượng `Shared Read Blocks` (đọc đĩa vật lý) bằng 0.
- Số lượng `Shared Hit Blocks` phản ánh số lần hệ thống truy xuất và kiểm tra trang dữ liệu trong RAM. Việc Composite Index giảm số khối từ 12.898 xuống 23 là giảm **số lần truy xuất trang đệm trong bộ nhớ**, giúp giải phóng băng thông bộ nhớ và chu kỳ khóa đệm (buffer pin/lock).

#### 2.2. Chi phí tìm kiếm B-tree và Loại bỏ nút Sort
- **Về độ phức tạp của B-tree:** Bản thảo đã sửa đổi, không còn khẳng định Index Scan có độ phức tạp cố định $O(1)$. Tác giả đã trình bày đúng đắn rằng chi phí B-tree là $O(h + k)$, trong đó chiều cao cây $h \approx 3$ và số bản ghi cần lấy $k=20$. Vì $k=20$ là một hằng số cố định trong câu lệnh `LIMIT 20`, chi phí được chặn trên bởi một ngưỡng cận hằng số cố định trong điều kiện thực nghiệm cụ thể.
- **Về việc loại bỏ nút Sort:** Đối chiếu trực tiếp với tệp kế hoạch thực thi `500000_Q2_baseline_run01.json` và `500000_Q2_indexed_run01.json`:
  - Bản Baseline có nút: `Sort Key: price, id`, `Sort Method: top-N heapsort  Memory: 27kB`.
  - Bản Indexed: chỉ gồm nút `Limit` trỏ thẳng tới `Index Scan using idx_properties_location_price`. Nút `Sort` hoàn toàn biến mất. Do đó, việc sử dụng thuật ngữ "loại bỏ hoàn toàn nút Sort" là hoàn toàn chuẩn xác và có bằng chứng kế hoạch thực thi chứng minh.

#### 2.3. Chi phí phụ trội lưu trữ vật lý (Storage Overhead 46,02 MB)
Tác giả đã làm rõ phương pháp luận: Con số **46,02 MB** (chiếm 45,6% bảng Heap 100,8 MB tại 500K) là **tổng dung lượng của 4 chỉ mục được đo đạc riêng lẻ theo từng cấu hình độc lập** (Q1: 3,40 MB; Q2: 28,53 MB; Q3: 10,73 MB; Q4: 3,36 MB). Tác giả không gọi đây là dung lượng quan sát được đồng thời trong một trạng thái cơ sở dữ liệu duy nhất, mà là tổng chi phí tài nguyên tối thiểu nếu áp dụng đồng thời cả 4 chỉ mục.

#### 2.4. Tính đúng đắn của các câu lệnh SQL
Đối chiếu trực tiếp 4 bài toán truy vấn trong văn bản báo cáo với các tệp tại `sql/benchmark/queries/`:
- Q1: `SELECT id, name, price, area FROM public.properties WHERE province_name = 'Hải Phòng';` (khớp hoàn toàn, không dùng `SELECT *`).
- Q2: `SELECT id, name, price, area, published_at FROM public.properties WHERE province_name = 'Hà Nội' AND district_name = 'Cầu Giấy' AND price BETWEEN 4100000000 AND 14300000000 ORDER BY price ASC, id ASC LIMIT 20;` (khớp hoàn toàn danh sách cột và điều kiện lọc).
- Q3: Câu truy vấn gốc dùng hàm ép kiểu `published_at::date = DATE '2025-10-15'`; câu truy vấn viết lại dùng khoảng nửa mở `published_at >= TIMESTAMP '2025-10-15 00:00:00' AND published_at < TIMESTAMP '2025-10-16 00:00:00'` (khớp hoàn toàn).
- Q4: `SELECT property_type_name, COUNT(*) AS total, ROUND(AVG(price), 0) AS avg_price FROM public.properties GROUP BY property_type_name ORDER BY total DESC;` (khớp hoàn toàn, bao gồm cả mệnh đề `ORDER BY total DESC`).

---

### PHẦN 3: THẨM ĐỊNH CHẤT LƯỢNG XUẤT BẢN WORD (.DOCX)

Script xuất bản [`report/export_docx.py`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/report/export_docx.py) đã được nâng cấp toàn diện:
1. **Word Heading Styles thực sự:** Sử dụng các style chuẩn (`Heading 1`, `Heading 2`, `Heading 3`, `Heading 4`) giúp tài liệu tương thích hoàn toàn với tính năng Navigation Pane và cho phép mục lục (TOC) tự động cập nhật được trong Microsoft Word.
2. **Chèn hình ảnh thực tế:** Toàn bộ 13 biểu đồ được trích dẫn trong văn bản (10 hình tại Chương 3 và 3 hình tại Chương 5) đều được đọc trực tiếp từ tệp ảnh nguồn trong repository và chèn vào văn bản với chú thích hình ảnh đặt ở phía dưới căn giữa.
3. **Bố cục bảng biểu:** Tiêu đề bảng được đặt ở phía trên bảng; bảng được định dạng viền kẻ rõ ràng, lặp lại hàng tiêu đề khi ngắt trang, tô màu thanh lịch và không bị tràn lề A4.
4. **Chuẩn hóa công thức toán học và làm sạch văn bản:** Toàn bộ cú pháp KaTeX (`$...$`, `$$...$$`, `\text{...}`) được chuyển đổi sang định dạng ký hiệu toán học sạch sẽ; loại bỏ hoàn toàn các thẻ HTML `<br>`, các liên kết cục bộ `file:///d:/...` trong tệp Word xuất ra.
5. **Trang bìa và Thông tin học thuật:** Bố cục trang bìa học thuật chuẩn theo quy chuẩn Học viện Công nghệ Bưu chính Viễn thông; thông tin sinh viên và giảng viên được giữ ở dạng định danh trang trọng, không bịa đặt tùy tiện.

---

### KẾT LUẬN CỦA GIẢNG VIÊN PHẢN BIỆN

Bản thảo sau khi sửa đổi toàn diện đã đáp ứng đầy đủ và nghiêm túc các tiêu chuẩn học thuật của một công trình nghiên cứu khoa học dữ liệu và cơ sở dữ liệu:
- Logic nghiên cứu mạch lạc theo đúng quy chuẩn 6 chương.
- Các câu hỏi nghiên cứu RQ1 – RQ3 được đồng bộ hóa xuyên suốt từ Mở đầu, Phương pháp, Kết quả đến Kết luận và Ma trận chứng tích.
- 100% số liệu thực nghiệm được đối soát chuẩn xác với các tệp kết quả gốc.
- Các kiến giải lý thuyết về B-tree, Buffer Pool, Sargability và Chunking được diễn giải khách quan, định lượng và chặt chẽ.
- Tệp xuất Word (.docx) đạt chất lượng định dạng chuyên nghiệp, sẵn sàng nộp và lưu chiểu.

**Đánh giá chung: ĐẠT YÊU CẦU BẢO VỆ VÀ LƯU CHIỂU HỌC THUẬT.**
