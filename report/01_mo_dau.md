# CHƯƠNG 1: MỞ ĐẦU

## 1.1. Bối cảnh và Đặt vấn đề

Trong kỷ nguyên kinh tế số và bùng nổ dữ liệu, thị trường bất động sản là một trong những lĩnh vực có tốc độ sinh dữ liệu giao dịch, niêm yết và biến động giá cả nhanh nhất. Các sàn thương mại điện tử bất động sản, hệ thống quản lý danh mục tài sản và cổng phân tích thị trường phải tiếp nhận và xử lý hàng triệu tin đăng bất động sản với đặc thù đa chiều: vừa chứa dữ liệu định lượng có biên độ phân tán lớn (diện tích, giá bán từ vài chục triệu đến hàng trăm tỷ đồng), vừa chứa dữ liệu phân cấp địa lý hành chính (tỉnh/thành phố, quận/huyện, phường/xã), vừa chứa dữ liệu chuỗi thời gian liên tục (`published_at`).

Khi quy mô dữ liệu trong bảng tăng vọt từ hàng chục nghìn lên hàng trăm nghìn và hàng triệu dòng, các truy vấn phục vụ người dùng cuối (như lọc nhà đất theo khu vực, tìm kiếm khoảng giá, sắp xếp theo giá tăng dần hoặc tổng hợp báo cáo thị trường) bắt đầu bộc lộ các vấn đề nghẽn cổ chai hiệu năng nghiêm trọng:
1. **Chi phí I/O quét toàn bảng (Sequential Scan Overhead):** Khi không có cơ chế chỉ mục phù hợp, hệ quản trị cơ sở dữ liệu buộc phải đọc tuần tự toàn bộ các trang dữ liệu từ đĩa hoặc bộ nhớ đệm. Thời gian phản hồi của hệ thống tăng tuyến tính theo kích thước bảng, gây suy giảm trải nghiệm người dùng và làm tê liệt máy chủ trong các khung giờ cao điểm.
2. **Chi phí sắp xếp trong bộ nhớ (In-memory Sorting Overhead):** Với các câu truy vấn có mệnh đề `ORDER BY ... LIMIT K`, nếu hệ thống không thể tận dụng cấu trúc chỉ mục để đọc dữ liệu theo thứ tự đã sắp xếp sẵn, nó phải tải toàn bộ tập kết quả lọc vào RAM và thực thi các giải thuật sắp xếp tốn kém (như Top-N Heapsort hoặc QuickSort), tiêu tốn chu kỳ CPU và dung lượng vùng nhớ tạm thời (`work_mem`).
3. **Hiểu nhầm phổ biến về Đánh chỉ mục:** Trong thực tế phát triển phần mềm, tồn tại một quan niệm sai lầm phổ biến trong giới lập trình viên: *"Cứ thấy truy vấn chậm là tạo thêm chỉ mục B-tree trên các cột trong mệnh đề WHERE"*. Cách tiếp cận cảm tính này bỏ qua các nguyên lý nền tảng của bộ tối ưu hóa chi phí (Cost-based Optimizer), không phân biệt được vị từ khả chỉ mục (sargable) với vị từ không khả chỉ mục (non-sargable), và lờ đi thực tế rằng việc đánh chỉ mục là một sự đánh đổi khắt khe giữa tốc độ đọc với dung lượng lưu trữ (Storage Overhead) và độ trễ ghi dữ liệu (Write Penalty).
4. **Nghẽn cổ chai ở tầng tiền xử lý dữ liệu (Data Preprocessing Pipeline):** Trước khi dữ liệu đến được cơ sở dữ liệu quan hệ, các nhà khoa học dữ liệu và kỹ sư dữ liệu thường phải đối mặt với bài toán tràn bộ nhớ (Out-Of-Memory - OOM) khi nạp các tệp dữ liệu lớn bằng các thư viện phân tích truyền thống như Pandas trên các máy trạm có tài nguyên hữu hạn (ví dụ: máy tính cá nhân 16 GB RAM).

Xuất phát từ những thách thức lý thuyết và thực tiễn nêu trên, đề tài **“Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn”** được lựa chọn nhằm xây dựng một mô hình thực nghiệm chặt chẽ, định lượng hóa một cách khoa học ảnh hưởng của các kỹ thuật tối ưu hóa trong hệ quản trị cơ sở dữ liệu PostgreSQL 18.3.

---

## 1.2. Mục tiêu nghiên cứu

Đề tài hướng tới ba mục tiêu tổng quát:
1. **Xây dựng quy trình xử lý dữ liệu chuẩn tắc (Data Engineering Pipeline):** Thu thập dòng dữ liệu từ nguồn thực tế Hugging Face, áp dụng các quy tắc làm sạch chuẩn hóa nghiêm ngặt, trích xuất 9 thuộc tính cốt lõi và xây dựng ba tập dữ liệu chuẩn ở các quy mô 50.000, 200.000 và 500.000 bản ghi, đảm bảo khả năng tái lập 100%.
2. **Thiết kế khung thực nghiệm tối ưu hóa cơ sở dữ liệu có kiểm soát (Benchmarking Framework):** Xây dựng bộ công cụ benchmark tự động trên PostgreSQL 18.3, tuân thủ các chuẩn mực đo lường khoa học (cô lập trạng thái bộ đệm với 3 lượt warm-up, 20 lượt đo chính thức, sử dụng trung vị và khoảng tứ phân vị IQR, trích xuất toàn bộ kế hoạch thực thi chi tiết `EXPLAIN (ANALYZE, BUFFERS)`).
3. **Chứng minh quy luật và giới hạn của các kỹ thuật tối ưu hóa:** Đánh giá định lượng hiệu năng của B-tree đơn cột, Composite Index bao phủ sắp xếp/cắt ngọn, kỹ thuật viết lại truy vấn (Query Rewriting / Sargability), và làm rõ các trường hợp chỉ mục không mang lại hiệu quả (Negative Control) cùng sự đánh đổi về dung lượng lưu trữ vật lý.

---

## 1.3. Đối tượng và Phạm vi nghiên cứu

- **Đối tượng nghiên cứu:**
  - Bộ dữ liệu bất động sản Việt Nam (`vietnam-real-estates`) chứa thông tin địa lý, đặc tính tài sản, giá cả và thời gian đăng tin.
  - Các kỹ thuật tối ưu hóa cơ sở dữ liệu: Single-column Index, Composite Index, Query Rewriting (Sargability), Aggregation Control.
  - Các cơ chế nội tại của PostgreSQL: Quản lý bộ đệm (Shared Buffers), các kiểu quét dữ liệu (Seq Scan, Index Scan, Bitmap Scan), giải thuật sắp xếp (Top-N Heapsort).
  - Kiến trúc xử lý dữ liệu tiền kỳ: DataFrame hướng dòng (Pandas trên định dạng CSV) đối chiếu với DataFrame vector hóa hướng cột (Polars trên định dạng Parquet).
- **Phạm vi nghiên cứu:**
  - Quy mô dữ liệu: Cố định ở 3 ngưỡng thực nghiệm: 50.000, 200.000 và 500.000 bản ghi.
  - Hệ quản trị cơ sở dữ liệu: PostgreSQL 18.3 chạy trên hệ điều hành Windows x86_64, cấu hình máy trạm 16 GB RAM, ổ cứng SSD.
  - Giới hạn tải: Đo lường hiệu năng truy vấn đơn luồng có kiểm soát (Single-client benchmarking) trong trạng thái hệ thống ổn định, tập trung vào thời gian lập kế hoạch (`Planning Time`), thời gian thực thi (`Execution Time`) và số lượng khối đệm truy xuất (`Shared Buffer Blocks`).

---

## 1.4. Các câu hỏi nghiên cứu (Research Questions: RQ1 – RQ3)

Để định hướng toàn bộ quá trình thiết kế thực nghiệm và phân tích dữ liệu, đề tài xây dựng ba câu hỏi nghiên cứu trọng tâm:

### Câu hỏi nghiên cứu 1 (RQ1): Hiệu quả của Cấu trúc Chỉ mục B-tree Đơn Cột và Đa Cột
> **RQ1:** Khi quy mô dữ liệu bất động sản tăng từ 50.000 đến 500.000 bản ghi, việc sử dụng Chỉ mục B-tree đơn cột (Single-column Index) và Chỉ mục B-tree đa cột (Composite Index) bao phủ đồng thời mệnh đề lọc, sắp xếp (`ORDER BY`) và cắt ngọn (`LIMIT`) làm thay đổi thời gian thực thi truy vấn và số lượng khối dữ liệu nạp vào bộ đệm (Buffer Shared Hits/Reads) như thế nào so với phương thức Quét tuần tự (Sequential Scan)?

### Câu hỏi nghiên cứu 2 (RQ2): Tác động Độc lập và Tương hỗ giữa Viết lại Truy vấn và Đánh chỉ mục
> **RQ2:** Giữa kỹ thuật Viết lại truy vấn (Query Rewriting) nhằm chuyển đổi vị từ tìm kiếm sang dạng khả chỉ mục (Sargable Predicate) và kỹ thuật Đánh chỉ mục (Indexing), yếu tố nào đóng vai trò quyết định, và cơ chế tương tác giữa chúng diễn ra như thế nào trong bộ tối ưu hóa chi phí (Query Planner) của PostgreSQL?

### Câu hỏi nghiên cứu 3 (RQ3): Giới hạn của Chỉ mục B-tree, Chi phí Đánh đổi Lưu trữ và Hiệu năng Tầng Tiền xử lý
> **RQ3:** Đâu là giới hạn mà tại đó chỉ mục B-tree không còn mang lại lợi ích hiệu năng (hoặc gây lãng phí/suy giảm) trong các truy vấn tổng hợp toàn bảng (`GROUP BY` không WHERE), chi phí đánh đổi về không gian lưu trữ vật lý (Storage Overhead) của các chỉ mục là bao nhiêu, và trong giai đoạn tiền xử lý dữ liệu, kiến trúc DataFrame hướng cột (Polars Parquet) cùng kỹ thuật nạp phân khối (Chunked Streaming) cải thiện thời gian và kiểm soát đỉnh RAM (Peak RSS) như thế nào so với kiến trúc truyền thống (Pandas CSV)?

---

## 1.5. Ý nghĩa khoa học và thực tiễn của đề tài

- **Ý nghĩa khoa học:**
  - Cung cấp một bộ bằng chứng thực nghiệm đầy đủ (600 tệp JSON kế hoạch thực thi chi tiết) chứng minh rõ ràng quy luật hoạt động của bộ tối ưu hóa chi phí trong hệ quản trị cơ sở dữ liệu hiện đại (PostgreSQL 18.3).
  - Phân rã độc lập các biến số ảnh hưởng (Sargability vs Indexing; Equality Filter vs Range Filter vs Sort Order) thay vì đưa ra các kết luận gộp chung thiếu căn cứ.
  - Thiết lập ma trận truy vết chứng tích khoa học (Evidence Matrix) kết nối chặt chẽ từ giả thuyết đến kết quả định lượng.
- **Ý nghĩa thực tiễn:**
  - Đưa ra khuyến nghị thiết kế chỉ mục chuẩn mực cho các kỹ sư dữ liệu: thứ tự đặt cột trong Composite Index, cách viết câu lệnh SQL tránh bẫy vô hiệu hóa index do ép kiểu, và cách thiết kế bảng tổng hợp (Materialized Views) thay thế cho việc đánh chỉ mục B-tree vô ích trên truy vấn aggregate.
  - Cung cấp giải pháp nạp và xử lý dữ liệu theo lô (Chunking Pipeline) giúp xử lý các tập dữ liệu lớn trên máy tính có tài nguyên RAM hạn chế mà không bị tràn bộ nhớ.
  - Toàn bộ mã nguồn, dữ liệu và công cụ web dashboard tương tác được đóng gói hoàn chỉnh, có thể ứng dụng trực tiếp vào giảng dạy và thực hành chuyên sâu môn Khoa học Dữ liệu và Cơ sở dữ liệu.

---

## 1.6. Bố cục của tiểu luận

Bản thảo tiểu luận được cấu trúc thành 5 chương chính:
- **Chương 1: Mở đầu** — Giới thiệu bối cảnh, mục tiêu, đối tượng, phạm vi và ba câu hỏi nghiên cứu cốt lõi (RQ1–RQ3).
- **Chương 2: Cơ sở lý thuyết và Tổng quan tài liệu** — Trình bày nền tảng lý thuyết về kiến trúc bảng Heap, cơ chế Buffer Pool, cấu trúc cây B-tree, mô hình chi phí của bộ lập lịch PostgreSQL, khái niệm Sargability và kiến trúc lưu trữ hướng cột.
- **Chương 3: Xây dựng bộ dữ liệu và Thiết kế phương pháp thực nghiệm** — Trình bày quy trình streaming data từ Hugging Face, bộ quy tắc làm sạch dữ liệu, phân tích khám phá dữ liệu (EDA), cùng thiết kế chi tiết 10 cấu hình thực nghiệm PostgreSQL và kịch bản đo đạc hiệu năng tiền xử lý.
- **Chương 4: Kết quả thực nghiệm và Thảo luận khoa học** — Trình bày toàn bộ số liệu đo đạc thực tế, phân tích kế hoạch thực thi (EXPLAIN plan), buffer I/O, hệ số tăng tốc (Speedup) nhằm trả lời dứt khoát ba câu hỏi nghiên cứu RQ1, RQ2 và RQ3.
- **Chương 5: Kết luận và Khuyến nghị** — Tổng kết các phát hiện khoa học, đưa ra khuyến nghị thực tiễn cho kỹ sư hệ thống, nêu rõ các hạn chế và định hướng phát triển tiếp theo của đề tài.
- **Tài liệu tham khảo & Phụ lục** — Liệt kê các tài liệu khoa học trích dẫn, lược đồ DDL, mã truy vấn benchmark và bảng kê chứng tích thực nghiệm SHA-256.
