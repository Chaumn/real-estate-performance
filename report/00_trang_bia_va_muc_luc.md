# BỘ GIÁO DỤC VÀ ĐÀO TẠO
# HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG
**KHOA CÔNG NGHỆ THÔNG TIN**
***

<br><br><br>

## TIỂU LUẬN MÔN HỌC
### NHẬP MÔN KHOA HỌC DỮ LIỆU & HỆ QUẢN TRỊ CƠ SỞ DỮ LIỆU

<br>

# ĐỀ TÀI:
# XÂY DỰNG BỘ DỮ LIỆU VỀ BẤT ĐỘNG SẢN, THỰC HIỆN CÁC PHƯƠNG PHÁP TỐI ƯU HIỆU NĂNG CHO HỆ THỐNG KHI DỮ LIỆU QUÁ LỚN

<br><br><br>

**Sinh viên thực hiện:** [Cần điền: Họ và tên sinh viên thực hiện]  
**Mã sinh viên:** [Cần điền: Mã sinh viên / Lớp chuyên ngành]  
**Chuyên ngành:** Khoa học Dữ liệu & Hệ thống Thông tin  
**Giảng viên hướng dẫn:** [Cần điền: Học hàm, học vị và Họ tên Giảng viên hướng dẫn]  

<br><br><br>

**Hà Nội – 2026**

---

## TÓM TẮT TIỂU LUẬN (ABSTRACT)

Khi khối lượng dữ liệu giao dịch và thông tin bất động sản gia tăng nhanh chóng từ hàng chục nghìn đến hàng trăm nghìn và hàng triệu bản ghi, các hệ thống cơ sở dữ liệu quan hệ truyền thống và đường ống tiền xử lý dữ liệu phải đối mặt với thách thức nghiêm trọng về độ trễ truy vấn, nghẽn cổ chai I/O và áp lực bộ nhớ. Tiểu luận này thực hiện một nghiên cứu thực nghiệm có kiểm soát nhằm giải quyết đồng bộ ba bài toán: xây dựng bộ dữ liệu bất động sản thực tế chuẩn hóa, tối ưu hóa tầng nạp và xử lý dữ liệu tiền kỳ trong bộ nhớ, và đánh giá định lượng các kỹ thuật tối ưu hóa truy vấn trong hệ quản trị cơ sở dữ liệu quan hệ PostgreSQL (phiên bản 18.3 x86_64).

Nội dung nghiên cứu được tổ chức chặt chẽ xoay quanh ba câu hỏi nghiên cứu cốt lõi (**RQ1 – RQ3**):

1. **RQ1 (Xây dựng bộ dữ liệu và đánh giá chất lượng dữ liệu):** Nghiên cứu thiết kế quy trình nạp luồng (streaming ingestion) kết hợp bộ đệm xáo trộn có kiểm soát (`seed = 42`, `buffer_size = 10,000`, `batch_size = 2,000`) từ kho dữ liệu Hugging Face (`Phuscca/vietnam-real-estates`) để trích xuất 500.000 bản ghi theo hợp đồng 9 thuộc tính chuẩn hóa. Kết quả kiểm toán và phân tích chất lượng dữ liệu (Data Profiling) ghi nhận: 6 trường thông tin bắt buộc đạt độ đầy đủ 100%; trường `district_name` thiếu đúng 14.235 bản ghi (2,85%); trường `ward_name` thiếu đúng 72.150 bản ghi (14,43%); trường giá chào bán (`price`) thiếu đúng 39.061 bản ghi (7,81%), phản ánh trung thực các tin đăng dạng giá thỏa thuận trên thị trường và được giữ nguyên giá trị SQL NULL. Phân bố địa phương tập trung chủ yếu tại TP. Hồ Chí Minh (186.698 tin, chiếm 37,34%), Hà Nội (170.167 tin, chiếm 34,03%) và Hải Phòng (10.422 tin, chiếm 2,08%). Do phân bố giá và diện tích lệch phải mạnh (skewed), nghiên cứu xác lập các đại lượng thống kê vững: trung vị diện tích là **80 m²** (khoảng tứ phân vị IQR = 64,1 m²) và trung vị giá chào bán là **7,4 tỷ VNĐ** (IQR = 10,2 tỷ VNĐ).

2. **RQ2 (Đánh giá hiệu năng xử lý dữ liệu bằng Pandas, Polars, CSV, Parquet và Chunked Processing):** Ở tầng tiền xử lý dữ liệu, thực nghiệm so sánh định dạng lưu trữ (CSV vs Parquet) và động cơ tính toán (Pandas vs Polars) kết hợp luồng giám sát tài nguyên RAM thực thời (lấy mẫu RSS 1 ms). Định dạng Parquet nhị phân nén hướng cột (dung lượng 41,42 MB) giúp tiết kiệm 55,9% không gian đĩa so với CSV (93,88 MB). Động cơ Polars đọc tệp CSV 500.000 dòng trong **75,27 ms**, nhanh gấp **40,3 lần** so với Pandas read_csv (**3.038,53 ms**). Trong tác vụ lọc và tính toán tổng hợp nội bộ (In-Memory Analytics), Polars hoàn thành trong **13,88 ms**, nhanh gấp 4,0 lần Pandas (55,17 ms). Đối với bài toán kiểm soát bộ nhớ, kỹ thuật nạp phân khối (Chunked Streaming với kích thước 10.000 dòng) giữ mức tăng bộ nhớ thực tế (Delta RSS) ở ngưỡng ổn định: thao tác nạp phân khối chỉ tăng **+19,68 MB** RAM (so với +241,37 MB khi nạp toàn bộ qua Pandas read_csv), và thao tác nạp kèm tổng hợp phân khối (Chunked Aggregate) có Delta RSS là **+21,09 MB**.

3. **RQ3 (Đánh giá tối ưu PostgreSQL thông qua Q1–Q4):** Trên hệ quản trị PostgreSQL 18.3, nghiên cứu thực hiện 600 lượt đo chính thức (3 quy mô 50K, 200K, 500K $\times$ 10 cấu hình $\times$ 20 lần chạy sau 3 lượt warm-up):
   - *Với bài toán lọc đẳng thức đơn cột (Q1 - Hải Phòng, 10.422 bản ghi tại 500K):* Chỉ mục B-tree `idx_properties_province_name` chuyển đổi kế hoạch từ `Seq Scan` sang `Bitmap Index Scan + Bitmap Heap Scan`, giảm số khối bộ đệm từ 12.808 xuống 7.236 Shared Hit Blocks, đạt hệ số tăng tốc **4,04 lần** tại 500K (và 8,21 lần tại 50K).
   - *Với bài toán lọc khoảng, sắp xếp và cắt ngọn (Q2 - Cầu Giấy, Top 20 giá thấp nhất):* Chỉ mục tổ hợp Composite Index `(province_name, district_name, price, id)` kích hoạt cơ chế Early Termination, dừng duyệt ngay khi đủ 20 bản ghi, loại bỏ hoàn toàn nút `Sort` (Top-N Heapsort) trong kế hoạch thực thi, giảm số khối truy cập bộ đệm từ 12.898 xuống đúng **23 Shared Hit Blocks** (giảm 560 lần), đem lại mức tăng tốc **942,37 lần** tại 500K (từ 48,06 ms xuống 0,051 ms).
   - *Với bài toán thời gian và tính khả chỉ mục (Q3 - ma trận trực giao $2 \times 2$):* Thực nghiệm chứng minh chỉ mục B-tree bị vô hiệu hóa hoàn toàn khi vị từ chứa hàm ép kiểu `published_at::date` (tỷ lệ sử dụng index là 0,00%, Speedup = 0,95x, lãng phí 10,73 MB index). Ngược lại, viết lại vị từ sang khoảng sargable kết hợp chỉ mục B-tree giúp chuyển sang Bitmap Index Scan, giảm 79,2% số khối đệm và tăng tốc **17,97 lần** tại 500K.
   - *Với bài toán đối chứng âm và chi phí lưu trữ (Q4):* Truy vấn tổng hợp toàn bảng (`GROUP BY` không WHERE) duy trì kế hoạch `Seq Scan + HashAggregate` bất kể có chỉ mục hay không (Speedup = 0,95x), chứng minh giới hạn của B-tree khi phải đọc toàn bộ bảng. Tổng dung lượng của 4 chỉ mục đo riêng lẻ theo cấu hình tại quy mô 500K là **46,02 MB** (chiếm 45,6% dung lượng bảng Heap 100,8 MB).

Toàn bộ kế hoạch thực thi chi tiết được lưu trữ trong 600 tệp JSON kiểm toán bằng mã băm SHA-256, cùng bộ kiểm thử tự động xác nhận tính toàn vẹn và khả năng tái lập của nghiên cứu.

---

## LỜI CẢM ƠN (ACKNOWLEDGEMENTS)

Nhóm nghiên cứu xin bày tỏ lòng biết ơn sâu sắc đến các Thầy/Cô bộ môn Khoa học Dữ liệu và Hệ thống Thông tin, Khoa Công nghệ Thông tin - Học viện Công nghệ Bưu chính Viễn thông đã tận tình truyền thụ nền tảng lý thuyết vững chắc về giải thuật, cấu trúc dữ liệu, nguyên lý hệ quản trị cơ sở dữ liệu và phương pháp luận nghiên cứu khoa học.

Nhóm nghiên cứu chân thành cảm ơn cộng đồng mã nguồn mở Hugging Face và tác giả bộ dữ liệu `Phuscca/vietnam-real-estates` đã cung cấp nguồn tài nguyên dữ liệu phong phú phục vụ quá trình học tập và nghiên cứu thực nghiệm.

Mặc dù nhóm nghiên cứu đã nỗ lực hết mình với tinh thần làm việc nghiêm túc, khoa học và cầu thị, tiểu luận khó tránh khỏi những giới hạn nhất định. Nhóm rất mong nhận được những nhận xét, góp ý và chỉ dẫn quý báu từ quý Thầy/Cô trong Hội đồng phản biện để tiếp tục hoàn thiện đề tài trong các giai đoạn phát triển tiếp theo.

---

## MỤC LỤC (TABLE OF CONTENTS)

- **TÓM TẮT TIỂU LUẬN (ABSTRACT)**
- **LỜI CẢM ƠN (ACKNOWLEDGEMENTS)**
- **DANH MỤC THUẬT NGỮ VÀ VIẾT TẮT**
- **DANH MỤC BẢNG BIỂU**
- **DANH MỤC HÌNH VẼ**
- **CHƯƠNG 1: MỞ ĐẦU**
  - 1.1. Bối cảnh và Đặt vấn đề
  - 1.2. Mục tiêu nghiên cứu
  - 1.3. Đối tượng và Phạm vi nghiên cứu
  - 1.4. Các câu hỏi nghiên cứu chuẩn hóa (RQ1 – RQ3)
  - 1.5. Ý nghĩa khoa học và thực tiễn của đề tài
  - 1.6. Bố cục của tiểu luận
- **CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ TỔNG QUAN TÀI LIỆU**
  - 2.1. Kiến trúc lưu trữ bảng Heap và Quản lý bộ đệm trong PostgreSQL
    - 2.1.1. Cấu trúc trang dữ liệu (Page 8 KB) và Bảng Heap
    - 2.1.2. Cơ chế Shared Buffers và Phân biệt Shared Hit Blocks với Shared Read Blocks
  - 2.2. Cấu trúc dữ liệu và Cơ chế hoạt động của Chỉ mục B-tree
    - 2.2.1. Cây B-tree đa nhánh và Phân tích chi phí tìm kiếm
    - 2.2.2. Composite Index và Quy tắc tiền tố ngoài cùng bên trái (Leftmost Prefix Rule)
  - 2.3. Bộ lập lịch truy vấn (Query Optimizer) và Các phương thức quét dữ liệu
    - 2.3.1. Các phương thức quét: Sequential Scan, Index Scan, Bitmap Index Scan
    - 2.3.2. Thuật toán sắp xếp trong bộ nhớ (Top-N Heapsort vs External Sort)
  - 2.4. Tính khả chỉ mục của vị từ truy vấn (Sargability)
    - 2.4.1. Khái niệm vị từ Sargable
    - 2.4.2. Tác động của hàm ép kiểu và biểu thức biến đổi trên cột chỉ mục
  - 2.5. Lý thuyết xử lý dữ liệu lớn ở tầng tiền xử lý (In-memory Data Ingestion)
    - 2.5.1. Định dạng hàng (CSV) đối chiếu định dạng cột nhị phân (Parquet)
    - 2.5.2. Kỹ thuật nạp phân khối (Chunked Streaming) và Giới hạn đo lường RAM RSS
- **CHƯƠNG 3: XÂY DỰNG BỘ DỮ LIỆU VÀ ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU**
  - 3.1. Quy trình thu thập dữ liệu dòng từ Hugging Face
    - 3.1.1. Nguồn dữ liệu và Cơ chế Streaming Shuffle Buffer
    - 3.1.2. Tính xác định và Giới hạn của Dataset Revision
  - 3.2. Bộ quy tắc làm sạch dữ liệu và Hợp đồng 9 thuộc tính
    - 3.2.1. Tiêu chí toàn vẹn và Xử lý giá trị khuyết thiếu nghiệp vụ
    - 3.2.2. Đặc tả cấu trúc lược đồ 9 thuộc tính chuẩn hóa
  - 3.3. Lược đồ cơ sở dữ liệu quan hệ trên PostgreSQL
  - 3.4. Kết quả Profiling và Phân tích khám phá dữ liệu (EDA)
    - 3.4.1. Thống kê khuyết thiếu và Kiểm toán nạp dòng
    - 3.4.2. Phân bố loại hình bất động sản và Địa bàn hành chính
    - 3.4.3. Thống kê mô tả định lượng vững (Robust Statistics)
    - 3.4.4. Phân tích phân vị và Ngoại lệ theo phương pháp IQR
    - 3.4.5. Phân tích tương quan phi tham số Spearman
    - 3.4.6. Kiểm toán bản ghi trùng lặp
- **CHƯƠNG 4: PHƯƠNG PHÁP THỰC NGHIỆM**
  - 4.1. Môi trường thực nghiệm phần cứng và phần mềm
  - 4.2. Thiết kế thực nghiệm RQ2: Đánh giá hiệu năng xử lý dữ liệu tiền kỳ
    - 4.2.1. Kịch bản thực nghiệm Ingestion và Phân tích nội bộ
    - 4.2.2. Phương pháp giám sát bộ nhớ thực thời và Giới hạn phép lấy mẫu RSS 1 ms
  - 4.3. Thiết kế thực nghiệm RQ3: Tối ưu hóa truy vấn PostgreSQL
    - 4.3.1. Ba quy mô dữ liệu thực nghiệm: 50.000, 200.000 và 500.000 bản ghi
    - 4.3.2. Bốn bài toán truy vấn SQL thực nghiệm (Q1 – Q4)
    - 4.3.3. Phân rã 10 cấu hình thực nghiệm Benchmark PostgreSQL
  - 4.4. Giao thức đo lường kiểm soát nhiễu thực nghiệm
    - 4.4.1. Cách ly cấu hình chỉ mục và Cập nhật thống kê bộ lập lịch
    - 4.4.2. Quy trình 3 Warm-up + 20 Official Runs và Thu thập kế hoạch JSON
  - 4.5. Thiết kế kiểm thử tính tương đương ngữ nghĩa truy vấn (Equivalence Verification)
- **CHƯƠNG 5: KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN KHOA HỌC**
  - 5.1. Đánh giá chất lượng và Tính đại diện của bộ dữ liệu (Trả lời RQ1)
  - 5.2. Hiệu năng xử lý dữ liệu với Pandas, Polars, CSV, Parquet và Chunked Processing (Trả lời RQ2)
    - 5.2.1. Tốc độ nạp tệp: Ưu thế vượt trội của Polars CSV và Định dạng Parquet
    - 5.2.2. Phân tích kỹ thuật nạp phân khối Chunked Streaming và Mức tăng RAM
    - 5.2.3. Hiệu năng lọc và Tổng hợp dữ liệu trong bộ nhớ
  - 5.3. Đánh giá tối ưu hóa truy vấn PostgreSQL thông qua Q1 – Q4 (Trả lời RQ3)
    - 5.3.1. Tổng quan bảng số liệu Benchmark qua 3 quy mô dữ liệu
    - 5.3.2. Bài toán Q1: Hiệu quả của chỉ mục đơn cột và Chuyển đổi Bitmap Scan
    - 5.3.3. Bài toán Q2: Đột phá hiệu năng Composite Index, Early Termination và Triệt tiêu nút Sort
    - 5.3.4. Bài toán Q3: Phân tích trực giao 2x2, Vô hiệu hóa Index và Cộng hưởng Sargable
    - 5.3.5. Bài toán Q4: Đối chứng âm Aggregation Control và Giới hạn của B-tree
    - 5.3.6. Chi phí phụ trội lưu trữ vật lý của các chỉ mục B-tree (46,02 MB tại 500K)
  - 5.4. Tổng hợp đối chiếu và Ma trận chứng tích thực nghiệm
- **CHƯƠNG 6: KẾT LUẬN VÀ KHUYẾN NGHỊ**
  - 6.1. Tổng kết các đóng góp chính của đề tài
  - 6.2. Câu trả lời tường minh cho ba câu hỏi nghiên cứu (RQ1 – RQ3)
  - 6.3. Khuyến nghị kỹ thuật thực tiễn cho kỹ sư dữ liệu và DBA
  - 6.4. Hạn chế của nghiên cứu
  - 6.5. Định hướng phát triển tiếp theo
- **TÀI LIỆU THAM KHẢO**
- **PHỤ LỤC**
  - Phụ lục A: Lược đồ DDL và Ràng buộc toàn vẹn cơ sở dữ liệu
  - Phụ lục B: Tập mã nguồn các câu truy vấn Benchmark SQL chuẩn hóa
  - Phụ lục C: Bảng kê mã băm SHA-256 các tệp kế hoạch thực thi thô

---

## DANH MỤC THUẬT NGỮ VÀ VIẾT TẮT

| Viết tắt / Thuật ngữ | Tiếng Anh đầy đủ | Giải thích ngữ nghĩa |
| :--- | :--- | :--- |
| **CBO** | Cost-Based Optimizer | Bộ tối ưu hóa truy vấn dựa trên mô hình chi phí ước tính |
| **CSV** | Comma-Separated Values | Định dạng tệp văn bản thuần lưu trữ bản ghi theo từng dòng |
| **CTE** | Common Table Expression | Mệnh đề WITH định nghĩa bảng tạm thời trong câu truy vấn SQL |
| **DDL** | Data Definition Language | Tập lệnh định nghĩa cấu trúc cơ sở dữ liệu (CREATE, ALTER, DROP) |
| **DML** | Data Manipulation Language | Tập lệnh thao tác dữ liệu (INSERT, UPDATE, DELETE) |
| **EDA** | Exploratory Data Analysis | Quá trình phân tích khám phá cấu trúc và đặc trưng của dữ liệu |
| **IQR** | Interquartile Range | Khoảng tứ phân vị ($IQR = Q_3 - Q_1$), thước đo độ phân tán vững |
| **OOM** | Out Of Memory | Lỗi tiến trình bị hệ điều hành cưỡng chế dừng do cạn kiệt RAM |
| **Parquet** | Apache Parquet | Định dạng tệp lưu trữ nhị phân hướng cột có nén và siêu dữ liệu |
| **PK** | Primary Key | Khóa chính định danh duy nhất cho từng bản ghi trong bảng |
| **Q1 – Q4** | Query 1 to Query 4 | Bốn bài toán truy vấn SQL điển hình được thiết kế cho thực nghiệm |
| **RQ1 – RQ3** | Research Questions 1 to 3 | Ba câu hỏi nghiên cứu chuẩn hóa định hướng đề tài |
| **RSS** | Resident Set Size | Dung lượng bộ nhớ RAM vật lý thực tế của một tiến trình hệ thống |
| **Sargable** | Search Argument Able | Tính chất của vị từ cho phép tận dụng cây chỉ mục B-tree |
| **Seq Scan** | Sequential Scan | Phương thức quét tuần tự toàn bộ các trang dữ liệu trong bảng Heap |
| **Shared Buffers** | PostgreSQL Shared Buffers | Vùng bộ đệm RAM chia sẻ của PostgreSQL lưu trữ các trang 8 KB |
| **TID** | Tuple Identifier | Con trỏ vật lý trỏ trực tiếp đến vị trí hàng trong bảng (Block, Offset) |

---

## DANH MỤC BẢNG BIỂU

| Số hiệu | Tên bảng biểu | Vị trí |
| :---: | :--- | :---: |
| **Bảng 2.1** | Ma trận tiêu chí lựa chọn phương thức quét bảng của Bộ tối ưu hóa chi phí (CBO) | Chương 2 |
| **Bảng 3.1** | Đặc tả cấu trúc lược đồ dữ liệu chuẩn hóa (9 thuộc tính) | Chương 3 |
| **Bảng 3.2** | Kết quả kiểm toán quá trình thu thập và lọc dòng dữ liệu (500K) | Chương 3 |
| **Bảng 3.3** | Thống kê mô tả định lượng vững trên tập dữ liệu 500.000 bản ghi | Chương 3 |
| **Bảng 4.1** | Đặc tả 10 cấu hình thực nghiệm Benchmark PostgreSQL | Chương 4 |
| **Bảng 5.1** | Kết quả đo lường hiệu năng nạp và xử lý dữ liệu tiền kỳ (500.000 bản ghi) | Chương 5 |
| **Bảng 5.2** | Tổng hợp kết quả đo đạc Benchmark PostgreSQL trên 3 quy mô dữ liệu | Chương 5 |
| **Bảng 5.3** | Diễn biến hiệu năng của bài toán Q1 qua 3 thang đo dữ liệu | Chương 5 |
| **Bảng 5.4** | So sánh chi tiết hiệu năng bài toán Q2 và Cơ chế Early Termination | Chương 5 |
| **Bảng 5.5** | Bảng phân rã trực giao 2x2 hiệu năng bài toán Q3 qua 3 thang đo | Chương 5 |
| **Bảng 5.6** | Kết quả thực nghiệm bài toán đối chứng âm Q4 qua 3 thang đo | Chương 5 |
| **Bảng 5.7** | Chi phí phụ trội lưu trữ vật lý của các chỉ mục B-tree qua các thang đo | Chương 5 |

---

## DANH MỤC HÌNH VẼ

| Số hiệu | Tên hình vẽ | Vị trí | Tệp ảnh nguồn |
| :---: | :--- | :---: | :--- |
| **Hình 3.1** | Tỷ lệ dữ liệu khuyết thiếu trên các thuộc tính bất động sản | Chương 3 | `results/eda/missing_values_bar.png` |
| **Hình 3.2** | Phân bố số lượng tin đăng theo loại hình bất động sản | Chương 3 | `results/eda/property_type_count.png` |
| **Hình 3.3** | Top các tỉnh/thành phố có mật độ tin đăng lớn nhất Việt Nam | Chương 3 | `results/eda/province_distribution.png` |
| **Hình 3.4** | Phân bố giá chào bán bất động sản (Thang đo Logarithmic) | Chương 3 | `results/eda/price_distribution.png` |
| **Hình 3.5** | Phân bố diện tích bất động sản (Thang đo Logarithmic) | Chương 3 | `results/eda/area_distribution.png` |
| **Hình 3.6** | Phân bố giá chào bán theo từng loại hình bất động sản (Boxplot) | Chương 3 | `results/eda/price_by_property_type_boxplot.png` |
| **Hình 3.7** | Đơn giá chào bán trung vị (Triệu/m²) tại các địa phương trọng điểm | Chương 3 | `results/eda/price_per_m2_by_province.png` |
| **Hình 3.8** | Mật độ tương quan giữa giá và diện tích bất động sản (Hexbin Plot) | Chương 3 | `results/eda/price_vs_area_scatter.png` |
| **Hình 3.9** | Xu hướng số lượng tin đăng bất động sản theo thời gian đăng tin | Chương 3 | `results/eda/monthly_listings_trend.png` |
| **Hình 3.10** | Ma trận hệ số tương quan phi tuyến Spearman giữa các biến định lượng | Chương 3 | `results/eda/numeric_correlation_heatmap.png` |
| **Hình 5.1** | Thời gian thực thi trung vị theo quy mô dữ liệu của 4 bài toán truy vấn | Chương 5 | `results/benchmark/analysis/execution_time_by_scale.png` |
| **Hình 5.2** | So sánh hệ số tăng tốc (Speedup Factor) của các phương pháp tối ưu | Chương 5 | `results/benchmark/analysis/speedup_comparison.png` |
| **Hình 5.3** | Chi phí phụ trội lưu trữ (Storage Overhead) của các chỉ mục B-tree | Chương 5 | `results/benchmark/analysis/index_storage_overhead.png` |
