# CHƯƠNG 5: KẾT LUẬN VÀ KHUYẾN NGHỊ

## 5.1. Tổng kết các đóng góp chính của đề tài

Đề tài **“Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn”** đã hoàn thành trọn vẹn các mục tiêu đề ra với những đóng góp học thuật và thực tiễn nổi bật:
1. **Xây dựng Pipeline Thu thập và Chuẩn hóa Dữ liệu Bất động sản có Khả năng Tái lập:**
   - Xây dựng thành công quy trình xử lý dữ liệu dòng (Streaming Pipeline) kết hợp bộ đệm shuffle cố định (`seed=42`, `buffer_size=10,000`) từ nguồn Hugging Face, đảm bảo dữ liệu sinh ra hoàn toàn có thể tái lập ở cả 3 quy mô: 50.000, 200.000 và 500.000 bản ghi.
   - Thiết lập bộ quy tắc làm sạch dữ liệu khoa học, bảo toàn nguyên vẹn 100% các bản ghi có giá trị thị trường thực tế (bao gồm các tin đăng khuyết giá hoặc giá thỏa thuận) mà không làm biến dạng phân phối xác suất của thị trường.
2. **Thiết lập Khung Benchmark Tự động và Kiểm chứng Khoa học trên PostgreSQL 18.3:**
   - Xây dựng bộ công cụ `scripts/benchmark_runner.py` vận hành theo tiêu chuẩn đo lường thực nghiệm khắt khe: cách ly chỉ mục, cập nhật thống kê bộ lập lịch, 3 lượt warm-up kiểm soát bộ đệm và 20 lượt đo chính thức lấy trung vị (Median) và khoảng tứ phân vị (IQR).
   - Thiết lập cơ chế kiểm chứng tương đương ngữ nghĩa truy vấn (Equivalence Verification với `EXCEPT ALL`) và thu thập đầy đủ 600 tệp JSON kế hoạch thực thi thô được kiểm toán mã băm SHA-256.
3. **Phân tích Thực nghiệm Đa diện và Chuyên sâu:**
   - Đánh giá định lượng hiệu năng của các loại chỉ mục B-tree (đơn cột, đa cột bao phủ), làm sáng tỏ hiện tượng tăng tốc cực đại 942 lần do cơ chế Early Termination và triệt tiêu nút Sort trong RAM.
   - Chứng minh thực nghiệm quy luật Sargability: làm rõ cơ chế vô hiệu hóa chỉ mục khi áp dụng hàm trên cột và chứng minh sức mạnh cộng hưởng giữa câu truy vấn viết lại và chỉ mục.
   - Thiết lập bài toán đối chứng âm (Negative Control) chứng minh giới hạn của chỉ mục B-tree trong truy vấn tổng hợp toàn bảng, đồng thời đo lường chính xác chi phí đánh đổi không gian lưu trữ vật lý (Storage Overhead chiếm ~45.6% bảng Heap).
   - Đo lường thực thời tài nguyên RAM (1ms sampling) trên tầng tiền xử lý, chứng minh ưu thế của định dạng Parquet kết hợp Polars và giải pháp nạp phân khối (Chunked Streaming).

---

## 5.2. Câu trả lời tường minh cho ba câu hỏi nghiên cứu (RQ1 – RQ3)

Dựa trên toàn bộ kết quả thực nghiệm định lượng, đề tài đưa ra câu trả lời dứt khoát cho ba câu hỏi nghiên cứu:

### Trả lời Câu hỏi nghiên cứu 1 (RQ1)
> **Kết luận RQ1:** 
> - Đối với chỉ mục đơn cột (Single-column Index - Q1), chỉ mục giúp giảm số lượng khối đệm đọc từ đĩa khoảng **43.5%** thông qua việc chuyển đổi từ `Seq Scan` sang `Bitmap Index Scan + Bitmap Heap Scan`, mang lại hệ số tăng tốc từ **8.21 lần** (ở 50K) đến **4.04 lần** (ở 500K). Hệ số tăng tốc có xu hướng giảm nhẹ khi dữ liệu mở rộng do các bản ghi phân tán trên nhiều trang Heap.
> - Đối với chỉ mục tổ hợp đa cột (Composite Index - Q2) được sắp xếp đúng thứ tự lọc, sắp xếp và cắt ngọn: chỉ mục tạo ra một bước nhảy vọt về hiệu năng, đạt hệ số tăng tốc **170.81 lần** (50K), **718.35 lần** (200K) và đạt đỉnh **942.37 lần** (500K). Cơ chế tạo nên sự bùng nổ này là: cây B-tree cho phép bộ lập lịch duyệt theo đúng thứ tự sắp xếp, dừng quét ngay khi gom đủ 20 dòng (**Early Termination**), triệt tiêu hoàn toàn nút sắp xếp (`Sort: Top-N heapsort`) trong bộ nhớ RAM, và giảm số lượng khối đệm cần truy cập từ 12.898 trang xuống còn đúng **23 trang** (giảm 560 lần). Kỹ thuật này biến một truy vấn $O(N)$ phụ thuộc kích thước bảng thành truy vấn cận hằng số $O(1)$.

### Trả lời Câu hỏi nghiên cứu 2 (RQ2)
> **Kết luận RQ2:**
> - Viết lại truy vấn sang dạng sargable nhưng không có chỉ mục (Cấu hình B) không làm thay đổi đáng kể thời gian thực thi (Speedup = 1.04x tại 500K) vì hệ thống vẫn bắt buộc phải quét tuần tự toàn bảng.
> - Ngược lại, tạo chỉ mục B-tree nhưng giữ nguyên vị từ non-sargable chứa hàm ép kiểu `published_at::date` (Cấu hình C) khiến bộ lập lịch **hoàn toàn vô hiệu hóa chỉ mục** (tỷ lệ sử dụng index = 0.00%, Speedup = 0.95x), gây lãng phí 10.73 MB dung lượng lưu trữ trên đĩa.
> - Hiệu năng chỉ được kích hoạt khi có sự **kết hợp đồng thời** giữa vị từ sargable dạng khoảng nửa mở $[T_1, T_2)$ và chỉ mục B-tree tương ứng (Cấu hình D), giúp bộ lập lịch kích hoạt `Bitmap Index Scan`, giảm 79.2% lưu lượng I/O và tăng tốc độ truy vấn **17.97 lần** tại 500K (và 29.31 lần tại 50K).

### Trả lời Câu hỏi nghiên cứu 3 (RQ3)
> **Kết luận RQ3:**
> - Trong các truy vấn tổng hợp toàn bảng (`GROUP BY` không WHERE - Q4), chỉ mục B-tree đơn cột **hoàn toàn không mang lại lợi ích hiệu năng** (Speedup = 0.95x - 1.01x). Bộ tối ưu hóa chi phí (CBO) của PostgreSQL quyết định giữ nguyên phương thức `Seq Scan` kết hợp `HashAggregate`, bởi vì chi phí truy cập ngẫu nhiên (Random I/O) qua con trỏ lá B-tree để đọc cột tính toán (`price`) tốn kém hơn nhiều so với việc quét tuần tự liên tục toàn bộ bảng.
> - Chỉ mục gây ra chi phí phụ trội lưu trữ (Storage Overhead) rất lớn: 4 chỉ mục B-tree tại quy mô 500.000 dòng chiếm **46.02 MB**, tương đương **45.6%** dung lượng của toàn bộ bảng dữ liệu gốc, trong đó Composite Index chiếm tới 62.0% tổng dung lượng chỉ mục.
> - Ở tầng tiền xử lý, định dạng Parquet kết hợp Polars cho tốc độ nạp tệp nhanh hơn **21 đến 40 lần** so với Pandas CSV và tiết kiệm 55.9% dung lượng đĩa. Đồng thời, kỹ thuật Nạp phân khối (Chunked Streaming) giúp khống chế mức tăng RAM ở mức chỉ **+19.68 MB**, tạo điều kiện tiên quyết để xử lý các tệp dữ liệu lớn trên máy trạm 16 GB RAM mà không gặp lỗi OOM.

---

## 5.3. Khuyến nghị thực tiễn cho kỹ sư dữ liệu và thiết kế hệ thống

Từ các kết luận khoa học vững chắc của đề tài, nhóm nghiên cứu đề xuất một bộ quy tắc kiến trúc và thực hành kỹ thuật dành cho các kỹ sư dữ liệu (Data Engineers) và chuyên viên quản trị cơ sở dữ liệu (DBAs):

1. **Nguyên tắc vàng khi thiết kế Composite Index:**
   - Khi thiết kế chỉ mục cho các màn hình tra cứu, tìm kiếm danh sách có phân trang (`LIMIT ... OFFSET` hoặc `LIMIT K`), phải sắp xếp các cột trong chỉ mục theo thứ tự nghiêm ngặt:
     $$\text{Index Order} = (\text{Cột lọc đẳng thức =}, \text{Cột lọc khoảng BETWEEN/RANGE}, \text{Cột ORDER BY})$$
   - Chỉ mục bao phủ đúng thứ tự sẽ loại bỏ hoàn toàn chi phí sắp xếp trong RAM/Disk và kích hoạt cơ chế Early Termination, giúp hệ thống phục vụ hàng nghìn truy vấn đồng thời với độ trễ dưới 1 mili-giây.
2. **Tuyệt đối tuân thủ tính Sargability trong mã SQL ứng dụng:**
   - Tránh việc áp dụng các hàm toán học, hàm chuỗi, hoặc ép kiểu trực tiếp trên cột dữ liệu trong mệnh đề `WHERE` (ví dụ: `WHERE DATE(created_at) = '...'`, `WHERE UPPER(name) = '...'`, `WHERE col + 1 = 10`).
   - Luôn viết lại vị từ dưới dạng khoảng nửa mở hoặc biểu thức so sánh đơn thuần để bộ lập lịch có thể sử dụng chỉ mục B-tree tiêu chuẩn. Trường hợp bắt buộc phải lọc theo biểu thức cố định, cần cân nhắc sử dụng **Chỉ mục hàm (Expression / Functional Index)** thay vì chỉ mục B-tree thông thường.
3. **Không lạm dụng chỉ mục trên các cột phục vụ truy vấn tổng hợp:**
   - Đối với các bài toán báo cáo dashboard phân tích thị trường (như tính trung bình, tổng, đếm theo phân loại trên toàn bảng), không nên tạo chỉ mục B-tree đơn thuần.
   - Giải pháp chuẩn mực là sử dụng **Bảng tổng hợp động (Materialized Views)** được làm mới định kỳ (`REFRESH MATERIALIZED VIEW`), hoặc xây dựng các bảng dữ liệu tổng hợp tiền kỳ (Aggregate Tables) trong kiến trúc Data Warehouse / Data Lakehouse.
4. **Kiến trúc tiền xử lý dữ liệu hiện đại:**
   - Trong các pipeline xử lý dữ liệu lớn (ETL / ELT), nên chuyển đổi định dạng tệp thô từ CSV sang Parquet càng sớm càng tốt để tận dụng khả năng nén cột (tiết kiệm hơn 50% đĩa) và tốc độ nạp nhị phân.
   - Ưu tiên sử dụng Polars hoặc kỹ thuật Chunked Streaming trong Pandas để bảo đảm tiến trình không bao giờ bị dừng đột ngột do cạn kiệt tài nguyên RAM.

---

## 5.4. Hạn chế của nghiên cứu và Hướng phát triển tương lai

### 5.4.1. Các hạn chế của đề tài
Mặc dù đã đạt được những kết quả thực nghiệm chuẩn xác và có giá trị cao, nghiên cứu còn tồn tại một số hạn chế nhất định do điều kiện hạ tầng:
1. **Môi trường đo lường đơn luồng:** Thực nghiệm được tiến hành trên một nút máy chủ cục bộ (Single-node Windows x86_64) với mô hình một tiến trình truy vấn tuần tự. Kết quả đo chưa phản ánh đầy đủ tác động của tranh chấp khóa (Lock Contention), tắc nghẽn bộ đệm đồng thời (Concurrent Buffer Contention) và độ trễ mạng trong môi trường phân tán.
2. **Chưa định lượng trực tiếp độ trễ ghi (Write Penalty):** Nghiên cứu đã đo đạc chính xác chi phí lưu trữ vật lý (Storage Overhead), nhưng chưa đo lường định lượng thời gian chậm đi của các thao tác `INSERT`, `UPDATE`, `DELETE` khi bảng có 4 chỉ mục phụ trợ so với bảng không có chỉ mục.
3. **Phạm vi loại hình chỉ mục:** Nghiên cứu tập trung chuyên sâu vào cấu trúc cây B-tree tiêu chuẩn (loại chỉ mục phổ biến nhất), chưa mở rộng khảo sát các cấu trúc chỉ mục chuyên biệt khác của PostgreSQL như BRIN (Block Range Index), GiST, GIN hoặc Hash Index.

### 5.4.2. Hướng phát triển tiếp theo
Trong các giai đoạn nghiên cứu tiếp theo, đề tài có thể được mở rộng theo các hướng:
1. **Khảo sát Chỉ mục BRIN cho Dữ liệu Chuỗi thời gian:** Cột `published_at` có tính chất tăng dần theo thời gian vật lý. Việc áp dụng chỉ mục BRIN (Block Range Index) có thể mang lại khả năng nén dung lượng chỉ mục từ hàng chục megabyte xuống vài kilobyte mà vẫn duy trì hiệu năng tìm kiếm khoảng xuất sắc.
2. **Phân vùng Dữ liệu (Table Partitioning):** Mở rộng quy mô bảng lên hàng triệu đến chục triệu bản ghi và áp dụng kỹ thuật Phân vùng bảng (Partitioning) theo thời gian (theo tháng/năm) hoặc theo khu vực địa lý (Miền Bắc, Miền Trung, Miền Nam), kết hợp với kỹ thuật Cắt tỉa phân vùng (Partition Pruning).
3. **Đánh giá Hiệu năng Đa luồng và Kiểm thử Tải (Stress Testing):** Sử dụng các công cụ kiểm thử tải chuyên nghiệp như `pgbench` để mô phỏng hàng trăm người dùng truy cập đồng thời, khảo sát thông lượng giao dịch (Transactions Per Second - TPS) và độ trễ ở phân vị 95% ($P_{95}$) và 99% ($P_{99}$).
