# CHƯƠNG 6: KẾT LUẬN VÀ KHUYẾN NGHỊ

## 6.1. Tổng kết các đóng góp chính của đề tài

Đề tài **“Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn”** đã hoàn thành các mục tiêu nghiên cứu với những đóng góp học thuật và thực tiễn cụ thể:

1. **Xây dựng quy trình xử lý dữ liệu chuẩn tắc:**
   - Xây dựng thành công quy trình nạp luồng kết hợp bộ đệm xáo trộn cố định (`seed = 42`, `buffer_size = 10,000`, `batch_size = 2,000`) từ nguồn `Phuscca/vietnam-real-estates`, xuất ra 500.000 bản ghi chuẩn hóa theo hợp đồng 9 thuộc tính qua ba quy mô thực nghiệm (50.000, 200.000 và 500.000 bản ghi).
   - Thiết lập bộ quy tắc làm sạch khách quan, bảo toàn 39.061 tin đăng dạng "giá thỏa thuận" (`price IS NULL`) mà không làm biến dạng phân phối thực tế của thị trường.
2. **Khảo sát hiệu năng tầng tiền xử lý dữ liệu:**
   - Định lượng hóa ưu thế của định dạng cột Parquet (tiết kiệm 55,9% dung lượng đĩa so với CSV) và động cơ Polars (đọc CSV nhanh hơn 40,3 lần và phân tích trong bộ nhớ nhanh hơn 4,0 lần so với Pandas).
   - Đánh giá năng lực kiểm soát bộ nhớ của kỹ thuật nạp phân khối (Chunked Streaming) thông qua luồng giám sát RAM thực thời (lấy mẫu RSS 1 ms).
3. **Thiết lập khung thực nghiệm tối ưu hóa có kiểm soát trên PostgreSQL 18.3:**
   - Xây dựng bộ công cụ benchmark tự động tuân thủ các chuẩn mực thực nghiệm khắt khe: cách ly chỉ mục, cập nhật catalog thống kê, 3 lượt warm-up kiểm soát bộ đệm và 20 lượt đo chính thức lấy trung vị và khoảng tứ phân vị IQR.
   - Thu thập đầy đủ 600 tệp JSON kế hoạch thực thi thô được kiểm toán mã băm SHA-256, đồng thời thiết lập thủ tục kiểm chứng tương đương ngữ nghĩa truy vấn (`EXCEPT ALL`).
4. **Phân tích thực nghiệm đa diện và làm rõ các cơ chế nội tại:**
   - Định lượng hiệu quả của chỉ mục đơn cột Q1 (giảm 43,5% số khối đệm nạp, tăng tốc 4,04 lần tại 500K).
   - Làm sáng tỏ cơ chế Early Termination và triệt tiêu hoàn toàn nút `Sort` của Composite Index trong bài toán Q2, đạt mức tăng tốc 942,37 lần tại 500K.
   - Khảo sát thực nghiệm quy luật Sargability qua ma trận $2 \times 2$ (Q3), chứng minh chỉ mục B-tree bị vô hiệu hóa hoàn toàn khi vị từ chứa hàm ép kiểu, và hiệu năng chỉ xuất hiện khi kết hợp vị từ sargable với chỉ mục tương ứng (tăng tốc 17,97 lần).
   - Thiết lập bài toán đối chứng âm Q4 chứng minh chỉ mục B-tree không đem lại lợi ích cho truy vấn tổng hợp toàn bảng, đồng thời đo lường tổng chi phí lưu trữ của 4 chỉ mục đo riêng lẻ theo cấu hình là 46,02 MB (~45,6% kích thước bảng Heap).

---

## 6.2. Câu trả lời tường minh cho ba câu hỏi nghiên cứu (RQ1 – RQ3)

Dựa trên toàn bộ kết quả thực nghiệm định lượng, đề tài đưa ra câu trả lời cho ba câu hỏi nghiên cứu:

### Trả lời Câu hỏi nghiên cứu 1 (RQ1)
> **Kết luận RQ1:**
> - Quy trình nạp luồng kết hợp bộ đệm shuffle cho phép thu thập và chuẩn hóa thành công 500.000 bản ghi bất động sản từ nguồn Hugging Face với tỷ lệ lỗi vi phạm toàn vẹn bị loại bỏ rất thấp (203 bản ghi, chiếm 0,04%).
> - Hồ sơ chất lượng dữ liệu phản ánh trung thực đặc trưng thị trường: độ đầy đủ đạt 100% trên 6 trường bắt buộc; tỷ lệ khuyết thiếu có tính phân tầng hành chính rõ rệt: trường `ward_name` khuyết 14,43% (72.150 bản ghi), trường `district_name` khuyết 2,85% (14.235 bản ghi), và trường `price` khuyết 7,81% (39.061 bản ghi dạng giá thỏa thuận).
> - Phân bố không gian tập trung cao độ tại TP. Hồ Chí Minh (37,34%), Hà Nội (34,03%) và Hải Phòng (2,08%). Phân bố loại hình tập trung ở Nhà riêng (46,08%) và Đất (24,12%). Do dữ liệu định lượng có phân phối lệch phải mạnh với nhiều ngoại lệ siêu giá trị, các đại lượng thống kê mô tả vững được xác lập với **trung vị diện tích là 80,0 m²** ($IQR = 64,1$ m²) và **trung vị giá chào bán là 7,40 tỷ VNĐ** ($IQR = 10,20$ tỷ VNĐ).

### Trả lời Câu hỏi nghiên cứu 2 (RQ2)
> **Kết luận RQ2:**
> - Ở tầng tiền xử lý dữ liệu, định dạng Parquet (41,42 MB) giúp tiết kiệm 55,9% dung lượng lưu trữ trên đĩa so với CSV (93,88 MB) và giảm mức tăng RAM khi nạp vào Pandas từ +241,37 MB xuống +47,95 MB.
> - Động cơ Polars thể hiện ưu thế vượt trội: đọc tệp CSV 500K dòng chỉ trong 75,27 ms (nhanh gấp 40,3 lần Pandas read_csv: 3.038,53 ms) và hoàn thành tác vụ lọc kết hợp tổng hợp trong 13,88 ms (nhanh gấp 4,0 lần Pandas: 55,17 ms).
> - Kỹ thuật nạp phân khối (Chunked Streaming với kích thước 10.000 dòng) giúp khống chế mức tăng bộ nhớ thực tế: thao tác nạp phân khối chỉ tăng +19,68 MB RAM; thao tác nạp kèm tính toán tổng hợp (Chunked Aggregate) có mức tăng RAM là +21,09 MB (do chi phí tích lũy bảng tổng hợp trung gian). Mặc dù không phải mọi tác vụ Chunked đều có mức tăng dưới 20 MB, kỹ thuật này giúp duy trì dấu chân bộ nhớ ổn định ở ngưỡng ~20-21 MB, thấp hơn 11,4 lần so với nạp toàn bộ tệp, đổi lại thời gian thực thi dài hơn do chi phí vòng lặp.

### Trả lời Câu hỏi nghiên cứu 3 (RQ3)
> **Kết luận RQ3:**
> - Trong PostgreSQL 18.3, đối với truy vấn lọc đơn cột có độ chọn lọc vừa phải (Q1 - Hải Phòng 2,08%), chỉ mục B-tree chuyển đổi phương thức quét từ `Seq Scan` sang `Bitmap Index Scan + Bitmap Heap Scan`, giảm số khối đệm từ 12.808 xuống 7.236 Shared Hit Blocks, đạt mức tăng tốc từ 4,04 lần (500K) đến 8,21 lần (50K).
> - Đối với truy vấn lọc khoảng kết hợp sắp xếp và cắt ngọn (Q2), Composite Index bao phủ đúng thứ tự `(province_name, district_name, price, id)` kích hoạt cơ chế Early Termination, dừng duyệt ngay khi đủ 20 dòng, loại bỏ hoàn toàn nút `Sort` trong kế hoạch thực thi, giảm số khối truy cập bộ đệm từ 12.898 xuống đúng 23 Shared Hit Blocks (giữ cố định qua mọi quy mô dữ liệu), đạt mức tăng tốc 942,37 lần tại 500K. Chi phí thực thi trong trường hợp này bị chặn trên bởi một ngưỡng cận hằng số nhờ $k=20$ cố định và dữ liệu nằm liên tục trên các nút lá B-tree.
> - Đối với truy vấn thời gian (Q3), vị từ non-sargable (`published_at::date`) khiến chỉ mục B-tree bị vô hiệu hóa hoàn toàn (tỷ lệ sử dụng 0,00%, Speedup = 0,95x). Chỉ khi viết lại truy vấn sang khoảng thời gian nửa mở sargable kết hợp chỉ mục B-tree, hệ thống mới kích hoạt được Bitmap Index Scan và đạt mức tăng tốc 17,97 lần tại 500K.
> - Trong truy vấn tổng hợp toàn bảng (Q4), chỉ mục B-tree không đem lại lợi ích (Speedup = 0,95x) và bộ lập lịch giữ nguyên `Seq Scan + HashAggregate` do chi phí Random I/O qua chỉ mục lớn hơn quét tuần tự. Tổng dung lượng của 4 chỉ mục đo riêng lẻ theo cấu hình tại 500K là 46,02 MB (chiếm 45,6% dung lượng bảng Heap 100,8 MB), trong đó Composite Index chiếm 62,0% tổng dung lượng chỉ mục.

---

## 6.3. Khuyến nghị kỹ thuật thực tiễn cho kỹ sư dữ liệu và DBA

Từ các kết quả nghiên cứu định lượng, nhóm nghiên cứu đề xuất các nguyên tắc kiến trúc và thực hành kỹ thuật:

1. **Nguyên tắc thiết kế Composite Index bao phủ truy vấn tìm kiếm phân trang:**
   - Khi thiết kế chỉ mục cho các chức năng tra cứu danh sách có sắp xếp và phân trang (`LIMIT K`), các cột phải được sắp xếp theo thứ tự nghiêm ngặt:
     $$\text{Index Order} = (\text{Cột lọc đẳng thức =}, \text{Cột lọc khoảng BETWEEN}, \text{Cột ORDER BY}, \text{Khóa phá vỡ trùng lặp PK})$$
   - Thứ tự này cho phép hệ thống loại bỏ hoàn toàn nút `Sort` trong bộ nhớ và kích hoạt cơ chế Early Termination, giúp truy vấn đạt thời gian đáp ứng dưới 1 mili-giây.
2. **Tuân thủ tính Sargability trong mã SQL tầng ứng dụng:**
   - Tránh bao bọc cột dữ liệu trong các hàm số học, hàm chuỗi hoặc toán tử ép kiểu trong mệnh đề `WHERE` (như `WHERE col::date = ...` hoặc `WHERE UPPER(name) = ...`).
   - Luôn viết lại vị từ dưới dạng so sánh khoảng nửa mở $[T_1, T_2)$ để bộ lập lịch có thể tận dụng chỉ mục B-tree tiêu chuẩn. Trường hợp bắt buộc phải lọc theo biểu thức, cần tạo **Functional Index (Chỉ mục hàm)** chuyên biệt.
3. **Tránh tạo chỉ mục B-tree trên các cột chỉ phục vụ tổng hợp toàn bảng:**
   - Đối với các bài toán báo cáo dashboard tổng hợp dữ liệu trên toàn bảng thiếu điều kiện lọc chọn lọc, việc tạo chỉ mục B-tree đơn thuần không đem lại hiệu quả và gây lãng phí lưu trữ.
   - Giải pháp thay thế phù hợp là sử dụng **Materialized Views** được làm mới định kỳ, hoặc thiết kế các bảng tổng hợp tiền kỳ (Aggregate Tables) trong kiến trúc kho dữ liệu.
4. **Hiện đại hóa tầng tiền xử lý dữ liệu:**
   - Ưu tiên lưu trữ dữ liệu phân tích ở định dạng Parquet để tiết kiệm không gian lưu trữ và tăng tốc độ đọc tệp.
   - Sử dụng Polars hoặc kỹ thuật Chunked Streaming trong Pandas để kiểm soát đỉnh bộ nhớ RAM, tránh lỗi OOM trong các đường ống ETL/ELT.

---

## 6.4. Hạn chế của nghiên cứu

Mặc dù đã thực hiện quy trình thực nghiệm chặt chẽ, nghiên cứu còn tồn tại một số hạn chế khách quan:
1. **Môi trường đo lường đơn luồng:** Thực nghiệm được tiến hành trên một nút máy chủ cục bộ với mô hình một tiến trình truy vấn tuần tự. Kết quả đo chưa phản ánh các hiện tượng tranh chấp tài nguyên bộ đệm (Buffer Contention), xung đột khóa giao dịch (Lock Contention) và độ trễ mạng trong môi trường phân tán đa người dùng đồng thời.
2. **Chưa định lượng trực tiếp độ trễ ghi dữ liệu (Write Penalty):** Nghiên cứu đã đo đạc chi phí phụ trội lưu trữ vật lý của các chỉ mục (~45,6% bảng Heap), nhưng chưa tiến hành đo đạc thực nghiệm về độ suy giảm thông lượng của các thao tác ghi dữ liệu (`INSERT`, `UPDATE`, `DELETE`) khi duy trì đồng thời các chỉ mục này.
3. **Phạm vi quy mô dữ liệu và giới hạn tài nguyên RAM:** Quy mô dữ liệu tối đa trong thực nghiệm là 500.000 bản ghi (~94 MB CSV), nằm hoàn toàn trong dung lượng RAM vật lý 16 GB của máy trạm. Do đó, nghiên cứu chưa có thực nghiệm chứng minh hành vi của hệ thống khi khối lượng dữ liệu vượt quá dung lượng RAM vật lý (hiện tượng tráo đổi bộ nhớ đệm Disk Swapping / Buffer Eviction liên tục).
4. **Giới hạn của phép lấy mẫu RSS 1 ms:** Phép đo RSS phản ánh bộ nhớ tiến trình do hệ điều hành cấp phát, chịu ảnh hưởng bởi cơ chế quản lý khối trễ của Python runtime và hiện tượng phân mảnh bộ nhớ, do đó chỉ mang tính chất định lượng tương đối.
5. **Tính tái lập phụ thuộc vào Dataset Revision nguồn:** Do nạp theo chế độ streaming từ repository Hugging Face với `revision: null`, tính tái lập tuyệt đối của dữ liệu phụ thuộc vào việc kho lưu trữ upstream không thay đổi nội dung các tệp dữ liệu nguồn.

---

## 6.5. Định hướng phát triển tiếp theo

Trong các giai đoạn nghiên cứu tiếp theo, đề tài có thể được mở rộng theo các hướng:
1. **Khảo sát Chỉ mục BRIN cho dữ liệu chuỗi thời gian:** Cột `published_at` có tính chất tăng dần theo thời gian vật lý. Việc áp dụng chỉ mục BRIN (Block Range Index) có thể mang lại khả năng nén kích thước chỉ mục xuống vài kilobyte mà vẫn duy trì hiệu năng tìm kiếm khoảng tốt.
2. **Phân vùng dữ liệu (Table Partitioning):** Mở rộng quy mô dữ liệu lên hàng triệu bản ghi và áp dụng kỹ thuật phân vùng bảng theo thời gian hoặc theo địa bàn hành chính, kết hợp kỹ thuật cắt tỉa phân vùng (Partition Pruning).
3. **Kiểm thử tải đa người dùng đồng thời:** Sử dụng công cụ `pgbench` để mô phỏng tải truy vấn đồng thời từ hàng trăm kết nối, khảo sát thông lượng giao dịch (TPS) và độ trễ ở các phân vị cao ($P_{95}$, $P_{99}$).

