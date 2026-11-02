# BÁO CÁO PHẢN BIỆN HỌC THUẬT ĐỘC LẬP (ACADEMIC REVIEW REPORT)
## Đề tài: Xây dựng bộ dữ liệu về bất động sản, thực hiện các phương pháp tối ưu hiệu năng cho hệ thống khi dữ liệu quá lớn
**Hội đồng Đánh giá / Phản biện Khoa học: Chuyên ban Hệ cơ sở dữ liệu và Kỹ nghệ Dữ liệu**

---

### TÓM TẮT ĐÁNH GIÁ CHUNG CỦA PHẢN BIỆN (EXECUTIVE SUMMARY)

Đề tài giải quyết một bài toán mang tính thực tiễn và học thuật rất cao trong kỹ nghệ dữ liệu: Xây dựng một quy trình thu thập - làm sạch dòng dữ liệu lớn có thể tái lập, đồng thời thiết kế hệ thống thực nghiệm khoa học có đối chứng nhằm đánh giá tường minh các kỹ thuật tối ưu hóa hiệu năng truy vấn trên hệ quản trị cơ sở dữ liệu PostgreSQL khi dữ liệu mở rộng từ 50.000 đến 500.000 bản ghi.

Khác với các báo cáo thực tập hoặc đồ án tốt nghiệp thông thường mang tính sao chép mã nguồn và kết luận cảm tính (“Index luôn làm tăng tốc truy vấn”), công trình này thể hiện tính chặt chẽ vượt trội về mặt phương pháp luận thực nghiệm:
1. **Có đối chứng âm (Negative Control):** Đưa vào bài toán Q4 để chứng minh trường hợp chỉ mục B-tree hoàn toàn không mang lại lợi ích cho truy vấn tổng hợp toàn bảng.
2. **Thiết kế phân rã trực giao (Factorial Orthogonal Design):** Phân tách độc lập hiệu ứng của kỹ thuật Viết lại truy vấn (Query Rewriting / Sargability) và Đánh chỉ mục (Indexing) qua mô hình $2 \times 2$ (Q3 A/B/C/D).
3. **Bằng chứng thực nghiệm nguyên bản (Raw Evidence Provenance):** Lưu giữ đầy đủ 600 tệp JSON kế hoạch thực thi `EXPLAIN (ANALYZE, BUFFERS)` có mã băm SHA-256 đối soát.
4. **Phương pháp đo lường có kiểm soát nhiễu:** Sử dụng chính sách 3 warm-up + 20 runs, loại bỏ nhiễu biên bằng trung vị (Median) và khoảng tứ phân vị (IQR).

---

### PHẦN 1: THẨM ĐỊNH TÍNH ĐÚNG ĐẮN VỀ PHƯƠNG PHÁP LUẬN (METHODOLOGY AUDIT)

#### 1.1. Thẩm định Pipeline Tiền xử lý và Làm sạch Dữ liệu
- **Tính tái lập (Reproducibility):** Pipeline sử dụng cơ chế streaming với seed cố định (`seed=42`), kích thước bộ đệm shuffle xác định (`buffer_size=10,000`) và batch xử lý cố định (`batch_size=2,000`). Điểm này bảo đảm rằng việc tái chạy script từ nguồn Hugging Face sẽ sinh ra tập dữ liệu có cùng thứ tự bản ghi và ID liên tục từ 1 đến $N$.
- **Tính nhất quán dữ liệu:** Việc chỉ lọc bỏ các bản ghi vi phạm tính toàn vẹn bắt buộc (thiếu tên, loại hình, tỉnh/thành phố, diện tích $\le 0$, hoặc ngày đăng sai định dạng) và **bảo toàn các bản ghi khuyết giá (`price IS NULL`)** là một quyết định kỹ thuật chính xác. Trong thị trường bất động sản thực tế, tin đăng "giá thỏa thuận" chiếm tỷ trọng đáng kể (~7.81%); việc tùy tiện điền giá trung bình (imputation) hoặc xóa bỏ sẽ làm biến dạng phân phối thực tế của thị trường.
- **Lưu ý phản biện:** Tác giả đã đính chính chính xác việc không tự nhận "chuẩn hóa Unicode NFC" khi mã nguồn thực tế chỉ dùng `.str.strip()`. Đây là thái độ trung thực khoa học đáng khen ngợi.

#### 1.2. Thẩm định Thiết kế Thực nghiệm Benchmark PostgreSQL
- **Chính sách kiểm soát bộ nhớ đệm (Buffer Cache Control):**
  - Trong thực tế, các truy vấn chạy lặp lại nhiều lần có nguy cơ đo đạc tốc độ đọc từ RAM (Shared Buffers) thay vì từ đĩa (Disk I/O).
  - Tác giả đã giải quyết thỏa đáng vấn đề này bằng cách:
    - Thực hiện **3 lần warm-up** để đưa hệ thống về trạng thái ổn định (steady-state).
    - Đo đạc chính xác cả hai đại lượng: `shared_hit_blocks` (số khối trúng cache) và `shared_read_blocks` (số khối đọc vật lý).
    - Thể hiện sự chuyển đổi buffer I/O rõ rệt: ở Q2, việc có Composite Index đã giảm số block cần duyệt từ **12.898 blocks** xuống còn vỏn vẹn **23 blocks** (giảm 560 lần lượng trang dữ liệu phải nạp).
- **Kiểm định tính tương đương ngữ nghĩa (Equivalence Check):**
  - Tác giả đã thiết lập quy trình kiểm tra tự động trước khi đo: kết quả của truy vấn Baseline và Optimized phải trả về cùng số hàng và cùng dữ liệu (đối với Q3 sử dụng toán tử tập hợp hai chiều `EXCEPT ALL` để chứng minh tập kết quả trả về của cấu hình A và cấu hình D là đồng nhất 100%).

---

### PHẦN 2: THẨM ĐỊNH CÁC KẾT LUẬN KHOA HỌC (SCIENTIFIC CLAIMS AUDIT)

#### 2.1. Về hiện tượng tăng tốc cực đại 942.37x tại Q2 (Composite Index)
- *Câu hỏi phản biện:* Tại sao một chỉ mục B-tree lại có thể tăng tốc độ truy vấn tới gần 1.000 lần (từ 48.06 ms xuống 0.051 ms trên tập 500K)? Con số này có bị thổi phồng hoặc do lỗi đo đạc không?
- *Phân tích thẩm định:*
  - Bằng chứng JSON thô (`results/benchmark/raw/500000/Q2_indexed_run_*.json`) cho thấy rõ cơ chế nội tại của bộ lập lịch PostgreSQL 18.3:
    1. Câu truy vấn Q2 có mệnh đề: `ORDER BY price ASC, id ASC LIMIT 20`.
    2. Trong cấu hình Baseline (`Seq Scan`), PostgreSQL buộc phải quét toàn bộ 500.000 dòng, lọc ra hàng nghìn bản ghi thỏa mãn điều kiện `BETWEEN`, sau đó thực hiện thuật toán **Top-N Heapsort** trong bộ nhớ để tìm ra 20 dòng nhỏ nhất. Toàn bộ 12.898 trang dữ liệu của bảng phải được duyệt qua.
    3. Trong cấu hình Indexed, chỉ mục được tạo trên 4 cột: `(province_name, district_name, price, id)`. Cây B-tree đã lưu trữ các con trỏ dòng theo đúng thứ tự sắp xếp tăng dần của `price` và `id`. Do đó, bộ tối ưu chỉ cần tìm đến nút lá đầu tiên thỏa mãn `province_name = 'Hà Nội'` và `district_name = 'Cầu Giấy'`, sau đó duyệt xuôi theo liên kết lá của B-tree và **dừng quét ngay lập tức khi lấy đủ 20 bản ghi** (`early termination`).
    4. Số lượng block truy cập giảm từ 12.898 xuống đúng 23 block. Thuật toán phân loại (Sort node) bị loại bỏ hoàn toàn.
  - *Kết luận phản biện:* Mức tăng tốc 942x là **hoàn toàn có cơ sở lý thuyết và bằng chứng thực nghiệm vững chắc**, phản ánh đúng bản chất sức mạnh của Composite Index khi kết hợp với `ORDER BY ... LIMIT`.

#### 2.2. Về tính khả chỉ mục (Sargability) tại Q3
- *Phân tích thẩm định:*
  - Cấu hình C (giữ nguyên hàm `published_at::date = '2025-10-15'`, có tạo index `idx_properties_published_at`) đạt tốc độ 42.26 ms so với Baseline A là 40.06 ms (Speedup = 0.95x). Chỉ mục hoàn toàn không được đụng tới (Tỷ lệ sử dụng index = 0.0%).
  - Cấu hình D (viết lại sang `published_at >= '2025-10-15 00:00:00' AND published_at < '2025-10-16 00:00:00'`) giúp bộ lập lịch nhận diện đây là khoảng nửa mở (sargable range predicate), kích hoạt `Bitmap Index Scan`, giảm thời gian xuống 2.23 ms (Speedup = 17.97x).
  - *Kết luận phản biện:* Kết quả thực nghiệm đã chứng minh một cách mẫu mực quy luật: **"Chỉ mục B-tree vô dụng trước các biểu thức không khả chỉ mục (Non-sargable expressions)"**.

#### 2.3. Về trường hợp đối chứng Q4 (Aggregation Control)
- *Phân tích thẩm định:*
  - Truy vấn `SELECT property_type_name, COUNT(*), ROUND(AVG(price), 0) FROM properties GROUP BY property_type_name` tại 500K dòng mất 63.28 ms ở Baseline và 66.48 ms ở cấu hình có Index (Speedup = 0.95x).
  - Cả hai cấu hình đều sử dụng `Seq Scan` + `HashAggregate`. Kế hoạch thực thi chứng minh rằng bộ tối ưu hóa chi phí (Cost-based Optimizer) của PostgreSQL đã tính toán chính xác: nếu sử dụng Index Scan, chi phí nạp từng khối Heap ngẫu nhiên (Random I/O) để lấy cột `price` sẽ tốn kém hơn nhiều so với việc quét tuần tự liên tục (Sequential Read) toàn bộ bảng vào bộ đệm băm.
  - *Kết luận phản biện:* Đề tài đã phá vỡ ngộ nhận phổ biến cho rằng "cứ tạo index là hệ thống sẽ chạy nhanh hơn".

---

### PHẦN 3: ĐÁNH GIÁ CÁC GIỚI HẠN VÀ ĐỀ XUẤT CHO BẢN THẢO (LIMITATIONS & RECOMMENDATIONS)

Mặc dù hệ thống thực nghiệm đạt chất lượng xuất sắc, tác giả cần lưu ý các điểm sau trong bản thảo tiểu luận:
1. **Phạm vi môi trường đơn luồng/cục bộ:** Thực nghiệm được tiến hành trên môi trường máy trạm cục bộ (Windows, 16GB RAM, ổ cứng SSD, PostgreSQL 18.3). Tác giả cần nêu rõ đây là môi trường kiểm thử cô lập, tránh việc suy diễn nguyên văn các con số thời gian tuyệt đối (milliseconds) sang môi trường Cloud đa người dùng với độ trễ mạng và tranh chấp khóa (lock contention).
2. **Phạm vi phân tích ghi (Write Overhead):** Đề tài đã định lượng chi phí lưu trữ (Storage Overhead) của Index rất chi tiết (chiếm ~45.6% dung lượng bảng), nhưng chưa đo lường trực tiếp độ trễ khi thực hiện các thao tác `INSERT / UPDATE / DELETE` (DML write penalty). Cần đưa điểm này vào phần "Hạn chế của nghiên cứu và Hướng phát triển".
3. **Phân biệt rạch ròi:** Chương 3 phải tập trung hoàn toàn vào **Phương pháp thiết kế** (cách xây dựng bộ dữ liệu, nguyên lý các câu hỏi RQ, công thức toán học, thiết kế kịch bản đo); tuyệt đối không đưa trước số liệu đo đạc vào Chương 3. Toàn bộ số đo, bảng biểu kết quả và bình luận sâu phải nằm tập trung ở **Chương 4 (Kết quả và Thảo luận)**.

### KẾT LUẬN CỦA PHẢN BIỆN
Bản thảo đáp ứng đầy đủ các tiêu chuẩn khắt khe của một công trình nghiên cứu thực nghiệm cấp đại học/cao học. Hệ thống chứng tích đầy đủ, mã nguồn có kiểm thử tự động, cấu trúc báo cáo logic và thuyết phục. Đề nghị tác giả triển khai bản thảo chi tiết theo đúng cấu trúc đã phê duyệt.
