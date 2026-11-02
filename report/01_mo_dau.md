# CHƯƠNG 1: MỞ ĐẦU

## 1.1. Bối cảnh và Đặt vấn đề

Trong kỷ nguyên kinh tế số, thị trường bất động sản là một trong những lĩnh vực có tốc độ tích lũy và luân chuyển dữ liệu nhanh nhất. Các cổng thông tin niêm yết thương mại điện tử, hệ thống thẩm định giá tự động và ứng dụng quản lý danh mục tài sản phải tiếp nhận hàng triệu tin đăng bất động sản với đặc thù đa chiều phức tạp: vừa chứa dữ liệu văn bản phi cấu trúc (tiêu đề, mô tả), dữ liệu phân cấp hành chính (tỉnh/thành phố, quận/huyện, phường/xã), vừa chứa dữ liệu định lượng có biên độ biến động rất rộng (diện tích, giá bán từ vài triệu đến hàng trăm tỷ đồng) và chuỗi dấu thời gian liên tục (`published_at`).

Khi quy mô bảng dữ liệu gia tăng từ hàng chục nghìn lên hàng trăm nghìn và hàng triệu dòng, các truy vấn phục vụ người dùng cuối (như lọc bất động sản theo địa phương, tìm kiếm trong khoảng giá, sắp xếp theo giá tăng dần hoặc tổng hợp báo cáo thị trường theo phân khúc) bộc lộ các vấn đề nghẽn cổ chai hiệu năng nghiêm trọng:

1. **Chi phí I/O quét toàn bộ bảng (Sequential Scan Overhead):** Khi không có cơ chế chỉ mục phù hợp, hệ quản trị cơ sở dữ liệu buộc phải quét tuần tự toàn bộ các trang dữ liệu trong bảng Heap. Thời gian phản hồi của hệ thống tăng theo quy mô kích thước bảng, gây suy giảm năng lực phục vụ của máy chủ trong các khung giờ cao điểm.
2. **Chi phí sắp xếp trong bộ nhớ (In-memory Sorting Overhead):** Với các câu truy vấn có mệnh đề sắp xếp và cắt ngọn (`ORDER BY ... LIMIT K`), nếu hệ thống không thể tận dụng cấu trúc chỉ mục để đọc dữ liệu theo thứ tự đã được sắp sẵn, nó phải nạp toàn bộ tập kết quả thỏa mãn điều kiện lọc vào RAM và thực thi các giải thuật sắp xếp (như Top-N Heapsort hoặc External Merge Sort), tiêu tốn chu kỳ CPU và dung lượng vùng nhớ tạm thời (`work_mem`).
3. **Hiểu nhầm phổ biến về Đánh chỉ mục (Indexing Misconceptions):** Trong thực tế phát triển phần mềm, tồn tại xu hướng tiếp cận cảm tính: *"Cứ thấy truy vấn chậm là tạo thêm chỉ mục B-tree trên các cột trong mệnh đề WHERE"*. Cách tiếp cận này bỏ qua nguyên lý hoạt động của bộ tối ưu hóa chi phí (Cost-Based Optimizer), không phân biệt được vị từ khả chỉ mục (sargable) với vị từ không khả chỉ mục (non-sargable), và không lường trước được chi phí phụ trội lưu trữ vật lý (Storage Overhead) cũng như độ trễ bảo trì chỉ mục khi ghi dữ liệu (Write Penalty).
4. **Nghẽn cổ chai ở tầng tiền xử lý dữ liệu (Data Preprocessing Pipeline):** Trước khi dữ liệu được nạp vào cơ sở dữ liệu quan hệ, các tác vụ trích xuất, làm sạch và tổng hợp dữ liệu thường gặp hiện tượng tràn bộ nhớ (Out-Of-Memory - OOM) khi nạp các tệp dữ liệu văn bản lớn bằng các thư viện phân tích truyền thống như Pandas trên các môi trường máy trạm có tài nguyên bộ nhớ hữu hạn.

Xuất phát từ những thách thức lý thuyết và thực tiễn nêu trên, đề tài **“Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn”** được triển khai nhằm xây dựng một mô hình thực nghiệm chặt chẽ, định lượng hóa một cách khách quan ảnh hưởng của các kỹ thuật tối ưu hóa trong hệ quản trị cơ sở dữ liệu PostgreSQL (phiên bản 18.3 x86_64) và các công cụ xử lý dữ liệu hiện đại.

---

## 1.2. Mục tiêu nghiên cứu

Đề tài hướng tới ba mục tiêu cụ thể:
1. **Xây dựng quy trình xử lý dữ liệu chuẩn tắc (Data Engineering Pipeline):** Thu thập luồng dữ liệu từ nguồn thực tế Hugging Face, áp dụng các quy tắc làm sạch chuẩn hóa, trích xuất hợp đồng 9 thuộc tính cốt lõi và xây dựng ba tập dữ liệu ở các quy mô 50.000, 200.000 và 500.000 bản ghi với các tham số kiểm soát xác định.
2. **Đánh giá hiệu năng xử lý dữ liệu tiền kỳ (In-memory & File Processing):** Khảo sát định lượng ảnh hưởng của định dạng lưu trữ (CSV vs Parquet), động cơ tính toán (Pandas vs Polars) và kỹ thuật nạp phân khối (Chunked Streaming) đến thời gian xử lý và mức chiếm dụng tài nguyên bộ nhớ thực tế (Resident Set Size - RSS).
3. **Đánh giá thực nghiệm các kỹ thuật tối ưu hóa trong PostgreSQL (Relational Optimization):** Thiết kế khung thực nghiệm có kiểm soát (cô lập trạng thái bộ đệm với 3 lượt warm-up, 20 lượt đo chính thức lấy trung vị và khoảng tứ phân vị IQR, trích xuất toàn bộ kế hoạch thực thi chi tiết `EXPLAIN (ANALYZE, BUFFERS)`) để làm rõ hiệu quả và giới hạn của chỉ mục B-tree đơn cột, Composite Index bao phủ sắp xếp/cắt ngọn, kỹ thuật viết lại truy vấn (Query Rewriting / Sargability), bài toán đối chứng âm (Negative Control) và chi phí lưu trữ phụ trội.

---

## 1.3. Đối tượng và Phạm vi nghiên cứu

- **Đối tượng nghiên cứu:**
  - Bộ dữ liệu bất động sản Việt Nam (`Phuscca/vietnam-real-estates`) chứa thông tin địa lý, phân loại tài sản, giá cả và thời gian đăng tin.
  - Các kỹ thuật tối ưu hóa cơ sở dữ liệu: Single-column Index, Composite Index, Query Rewriting (Sargability), Aggregation Control.
  - Các cơ chế nội tại của PostgreSQL: Quản lý bộ đệm (Shared Buffers), các kiểu quét dữ liệu (Seq Scan, Index Scan, Bitmap Index Scan, Bitmap Heap Scan), giải thuật sắp xếp (Top-N Heapsort).
  - Kiến trúc xử lý dữ liệu tiền kỳ: Định dạng tệp CSV và Parquet; Thư viện phân tích Pandas và Polars; Kỹ thuật nạp phân khối (Chunked Streaming).
- **Phạm vi nghiên cứu:**
  - Quy mô dữ liệu: Khảo sát tại 3 ngưỡng thực nghiệm: 50.000, 200.000 và 500.000 bản ghi.
  - Hệ quản trị cơ sở dữ liệu: PostgreSQL 18.3 chạy trên hệ điều hành Windows x86_64, cấu hình máy trạm 16 GB RAM, ổ cứng SSD NVMe.
  - Điều kiện đo đạc: Đo lường hiệu năng truy vấn đơn tiến trình (Single-client benchmarking) trong trạng thái hệ thống ổn định, tập trung vào thời gian lập kế hoạch (`Planning Time`), thời gian thực thi (`Execution Time`), số khối bộ đệm truy xuất (`Shared Hit Blocks`) và mức chiếm dụng bộ nhớ RAM tiến trình (`Delta RSS`).

---

## 1.4. Các câu hỏi nghiên cứu chuẩn hóa (RQ1 – RQ3)

Để định hướng toàn bộ quá trình thiết kế thực nghiệm và phân tích dữ liệu, đề tài xây dựng ba câu hỏi nghiên cứu chuẩn hóa:

### Câu hỏi nghiên cứu 1 (RQ1): Xây dựng bộ dữ liệu và đánh giá chất lượng dữ liệu
> **RQ1:** Làm thế nào để xây dựng một quy trình nạp luồng và làm sạch dữ liệu lớn có thể kiểm soát được từ nguồn bất động sản thực tế, và đặc trưng chất lượng dữ liệu (tỷ lệ khuyết thiếu, phân bố không gian, ngoại lệ định lượng và độ tin cậy) của tập dữ liệu này thể hiện như thế nào ở các quy mô từ 50.000 đến 500.000 bản ghi?

### Câu hỏi nghiên cứu 2 (RQ2): Đánh giá hiệu năng xử lý dữ liệu bằng Pandas, Polars, CSV, Parquet và Chunked Processing
> **RQ2:** Ở tầng tiền xử lý dữ liệu, sự kết hợp giữa định dạng lưu trữ (CSV vs Parquet) và động cơ xử lý (Pandas vs Polars) tác động như thế nào đến tốc độ nạp tệp, hiệu năng tính toán phân tích và mức chiếm dụng tài nguyên bộ nhớ thực tế (Delta RSS); đồng thời kỹ thuật nạp phân khối (Chunked Streaming) đóng vai trò gì trong việc kiểm soát đỉnh bộ nhớ?

### Câu hỏi nghiên cứu 3 (RQ3): Đánh giá tối ưu PostgreSQL thông qua Q1–Q4
> **RQ3:** Khi quy mô dữ liệu mở rộng đến 500.000 bản ghi trong PostgreSQL, các kỹ thuật tối ưu hóa cơ sở dữ liệu quan hệ (Chỉ mục B-tree đơn cột trong Q1, Composite Index bao phủ lọc/sắp xếp/cắt ngọn trong Q2, Viết lại truy vấn sargable trong Q3) mang lại hiệu quả tăng tốc và thay đổi cơ chế truy cập bộ đệm (Shared Hit Blocks) như thế nào, đâu là giới hạn của B-tree trong bài toán đối chứng âm Q4, và chi phí phụ trội lưu trữ vật lý của các chỉ mục là bao nhiêu?

---

## 1.5. Ý nghĩa khoa học và thực tiễn của đề tài

- **Ý nghĩa khoa học:**
  - Cung cấp một bộ dữ liệu thực nghiệm có kiểm chứng (600 tệp JSON kế hoạch thực thi chi tiết) minh chứng cho quy luật hoạt động của bộ tối ưu hóa chi phí trong hệ quản trị cơ sở dữ liệu hiện đại (PostgreSQL 18.3).
  - Phân tách độc lập các biến số ảnh hưởng (Sargability đối chiếu Indexing; Lọc đẳng thức đối chiếu Lọc khoảng và Thứ tự sắp xếp; Lưu trữ hàng đối chiếu Lưu trữ cột) thông qua thiết kế thực nghiệm có kiểm soát.
  - Thiết lập ma trận truy vết chứng tích khoa học (Evidence Matrix) kết nối chặt chẽ từ câu hỏi nghiên cứu, giả thuyết đến kết quả đo đạc định lượng cụ thể.
- **Ý nghĩa thực tiễn:**
  - Đưa ra khuyến nghị thiết kế chỉ mục thực tế cho kỹ sư dữ liệu: thứ tự đặt cột trong Composite Index để triệt tiêu nút Sort, cách chuẩn hóa vị từ SQL tránh vô hiệu hóa index do ép kiểu, và giải pháp thay thế cho việc đánh chỉ mục trên truy vấn tổng hợp toàn bảng.
  - Cung cấp quy trình xử lý dữ liệu theo lô (Chunking Pipeline) và khuyến nghị ứng dụng định dạng Parquet kết hợp Polars để tối ưu hóa thời gian và tài nguyên bộ nhớ trong các đường ống kỹ nghệ dữ liệu (Data Pipelines).
  - Toàn bộ mã nguồn, dữ liệu thực nghiệm và công cụ trực quan hóa được lưu trữ minh bạch, phục vụ học tập và nghiên cứu thực nghiệm trong các môn học Khoa học Dữ liệu và Cơ sở dữ liệu.

---

## 1.6. Bố cục của tiểu luận

Tiểu luận được cấu trúc thành 6 chương chính theo mạch nghiên cứu khoa học:
- **Chương 1: Mở đầu** — Giới thiệu bối cảnh, mục tiêu, đối tượng, phạm vi, ba câu hỏi nghiên cứu chuẩn hóa (RQ1 – RQ3), ý nghĩa khoa học và thực tiễn của đề tài.
- **Chương 2: Cơ sở lý thuyết và Tổng quan tài liệu** — Trình bày nền tảng lý thuyết về kiến trúc bảng Heap, cơ chế Shared Buffers, cấu trúc chỉ mục B-tree, mô hình chi phí của bộ lập lịch truy vấn, nguyên lý Sargability và kiến trúc lưu trữ hướng cột.
- **Chương 3: Xây dựng bộ dữ liệu và Đánh giá chất lượng dữ liệu** — Trình bày quy trình thu thập dữ liệu dòng từ Hugging Face, bộ quy tắc làm sạch, lược đồ quan hệ PostgreSQL và kết quả hồ sơ chất lượng dữ liệu (Data Profiling & EDA), trực tiếp trả lời RQ1.
- **Chương 4: Phương pháp thực nghiệm** — Mô tả môi trường thực nghiệm, thiết kế kịch bản benchmark tiền xử lý cho RQ2 và thiết kế 10 cấu hình benchmark PostgreSQL (Q1 – Q4) cho RQ3, giao thức đo lường kiểm soát nhiễu và kiểm chứng tính tương đương ngữ nghĩa.
- **Chương 5: Kết quả thực nghiệm và Thảo luận khoa học** — Trình bày toàn bộ số liệu đo đạc thực tế, phân tích kế hoạch thực thi (EXPLAIN plan), phân tích buffer I/O, thời gian và tài nguyên RAM, trả lời dứt khoát RQ2 và RQ3.
- **Chương 6: Kết luận và Khuyến nghị** — Tổng kết các phát hiện khoa học, đưa ra khuyến nghị thực tiễn cho kỹ sư hệ thống, nêu rõ các hạn chế và định hướng phát triển tiếp theo của đề tài.
- **Tài liệu tham khảo & Phụ lục** — Liệt kê các tài liệu khoa học trích dẫn, lược đồ DDL, mã truy vấn benchmark và bảng kê chứng tích thực nghiệm SHA-256.
