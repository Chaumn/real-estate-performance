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

**Sinh viên thực hiện:** Daniel Chau & Nhóm nghiên cứu  
**Mã sinh viên:** B21DCDT...  
**Chuyên ngành:** Khoa học Dữ liệu & Hệ thống Thông tin  
**Giảng viên hướng dẫn:** TS. Giảng viên phụ trách môn học  

<br><br><br>

**Hà Nội – 2026**

---

## TÓM TẮT TIỂU LUẬN (ABSTRACT)

Khi khối lượng dữ liệu giao dịch và thông tin bất động sản gia tăng nhanh chóng từ hàng chục nghìn đến hàng triệu bản ghi, các hệ thống cơ sở dữ liệu quan hệ truyền thống phải đối mặt với thách thức nghiêm trọng về độ trễ truy vấn, nghẽn cổ chai I/O đĩa và cạn kiệt bộ nhớ đệm. Đề tài này tập trung giải quyết trọn vẹn hai vấn đề cốt lõi: (1) Xây dựng một quy trình (pipeline) tự động, có khả năng tái lập để thu thập, làm sạch và chuẩn hóa bộ dữ liệu bất động sản Việt Nam ở ba thang đo thực nghiệm 50.000, 200.000 và 500.000 bản ghi; (2) Thiết kế một khung thực nghiệm khoa học có kiểm soát nhằm đánh giá định lượng ảnh hưởng của các kỹ thuật tối ưu hóa hiệu năng trong hệ quản trị cơ sở dữ liệu PostgreSQL (phiên bản 18.3 x86_64).

Nghiên cứu tập trung giải quyết ba câu hỏi nghiên cứu cốt lõi (**RQ1–RQ3**):
- **RQ1:** Đánh giá hiệu quả của cấu trúc chỉ mục B-tree đơn cột và đa cột (Composite Index). Kết quả thực nghiệm chứng minh Composite Index bao phủ đúng thứ tự lọc, sắp xếp và cắt ngọn (`(province_name, district_name, price, id)`) giúp giảm số lượng khối đệm I/O từ 12.898 trang xuống còn đúng **23 trang** (giảm 560 lần), loại bỏ hoàn toàn nút Top-N Heapsort trong bộ nhớ, đem lại mức tăng tốc kỷ lục **942.37 lần** trên tập dữ liệu 500.000 bản ghi.
- **RQ2:** Phân tách độc lập hiệu ứng của kỹ thuật Viết lại truy vấn (Query Rewriting / Sargability) và Đánh chỉ mục (Indexing) qua ma trận thực nghiệm trực giao $2 \times 2$. Kết quả khẳng định chỉ mục B-tree hoàn toàn bị vô hiệu hóa khi câu truy vấn chứa vị từ non-sargable (`published_at::date`), và việc viết lại truy vấn sang khoảng thời gian nửa mở $[T_1, T_2)$ kết hợp với chỉ mục tương ứng giúp tăng tốc độ thực thi tới **17.97 lần**.
- **RQ3:** Xác lập giới hạn của chỉ mục B-tree thông qua bài toán đối chứng âm (Negative Control) với truy vấn tổng hợp toàn bảng (`GROUP BY` không WHERE), chứng minh bộ lập lịch giữ nguyên `Seq Scan` và việc đánh chỉ mục không đem lại lợi ích trong khi tiêu tốn **45.6% dung lượng lưu trữ phụ trội** (46.02 MB index so với 100.8 MB bảng Heap tại 500K). Đồng thời, ở tầng tiền xử lý, kiến trúc hướng cột vector hóa của Polars Parquet cho tốc độ nạp tệp nhanh hơn **21 lần** so với Pandas CSV, và kỹ thuật nạp phân khối (Chunked Streaming) giúp giữ mức tăng RAM ổn định dưới **20 MB**.

Toàn bộ 600 kế hoạch thực thi thô (raw EXPLAIN plans) được bảo vệ bằng mã băm SHA-256 trong tệp kê khai dữ liệu, cùng 182 kiểm thử tự động offline đảm bảo tính minh bạch và khả năng tái lập 100% của công trình.

---

## LỜI CẢM ƠN (ACKNOWLEDGEMENTS)

Nhóm nghiên cứu xin bày tỏ lòng biết ơn sâu sắc đến các Thầy/Cô bộ môn Khoa học Dữ liệu và Hệ thống Thông tin, Học viện Công nghệ Bưu chính Viễn thông đã truyền thụ những kiến thức nền tảng vững chắc về cấu trúc dữ liệu, giải thuật, nguyên lý hệ quản trị cơ sở dữ liệu và phương pháp nghiên cứu khoa học.

Xin chân thành cảm ơn tác giả bộ dữ liệu nguồn `Phuscca/vietnam-real-estates` trên Hugging Face đã cung cấp dữ liệu thực tế phục vụ học tập và nghiên cứu. Mặc dù đã nỗ lực hết mình để hoàn thiện đề tài với tính khoa học và thực nghiệm cao nhất, tiểu luận không thể tránh khỏi những thiếu sót nhất định. Nhóm rất mong nhận được những ý kiến đóng góp quý báu từ quý Thầy/Cô và Hội đồng đánh giá.

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
  - 1.4. Các câu hỏi nghiên cứu (Research Questions: RQ1 – RQ3)
  - 1.5. Ý nghĩa khoa học và thực tiễn của đề tài
  - 1.6. Bố cục của tiểu luận
- **CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ TỔNG QUAN TÀI LIỆU**
  - 2.1. Kiến trúc lưu trữ và Quản lý bộ đệm trong PostgreSQL
    - 2.1.1. Cấu trúc bảng Heap và Định dạng Page 8 KB
    - 2.1.2. Cơ chế Buffer Pool và Chính sách Đọc/Ghi đệm
  - 2.2. Cấu trúc dữ liệu và Cơ chế hoạt động của Chỉ mục B-tree
    - 2.2.1. Cây B-tree đa nhánh và Thứ tự khóa (Key Ordering)
    - 2.2.2. Composite Index và Quy tắc tiền tố ngoài cùng bên trái (Leftmost Prefix Rule)
  - 2.3. Bộ lập lịch truy vấn (Query Optimizer) và Mô hình chi phí (Cost Model)
    - 2.3.1. Các phương thức quét bảng: Sequential Scan, Index Scan, Bitmap Heap Scan
    - 2.3.2. Thuật toán sắp xếp trong bộ nhớ (Top-N Heapsort vs External Merge Sort)
  - 2.4. Tính khả chỉ mục của vị từ truy vấn (Sargability)
    - 2.4.1. Khái niệm Sargable Predicate
    - 2.4.2. Tác động của hàm ép kiểu và biểu thức trên cột chỉ mục
  - 2.5. Lý thuyết xử lý dữ liệu lớn ở tầng tiền kỳ (In-memory Data Ingestion)
    - 2.5.1. Định dạng hàng (CSV) đối chiếu định dạng cột nhị phân (Parquet)
    - 2.5.2. Kỹ thuật nạp phân khối (Chunked Streaming) kiểm soát giới hạn RAM
- **CHƯƠNG 3: XÂY DỰNG BỘ DỮ LIỆU VÀ THIẾT KẾ PHƯƠNG PHÁP THỰC NGHIỆM**
  - 3.1. Quy trình thu thập và chuẩn hóa dữ liệu lớn từ Hugging Face
    - 3.1.1. Nguồn dữ liệu và Cơ chế Streaming Shuffle Buffer
    - 3.1.2. Bộ quy tắc làm sạch dữ liệu và Hợp đồng 9 thuộc tính
    - 3.1.3. Lược đồ cơ sở dữ liệu quan hệ chuẩn hóa trên PostgreSQL
  - 3.2. Hồ sơ chất lượng dữ liệu và Phân tích khám phá (Data Profiling & EDA)
    - 3.2.1. Thống kê mô tả và Phân tích giá trị khuyết thiếu
    - 3.2.2. Phân tích ngoại lệ theo phương pháp Khoảng tứ phân vị (IQR)
    - 3.2.3. Mối tương quan phi tuyến giữa diện tích, vị trí và giá chào bán
  - 3.3. Thiết kế khung thực nghiệm tối ưu hiệu năng cơ sở dữ liệu
    - 3.3.1. Ba quy mô dữ liệu thực nghiệm: 50.000, 200.000 và 500.000 bản ghi
    - 3.3.2. Thiết kế 10 cấu hình thực nghiệm độc lập cho 4 bài toán truy vấn
    - 3.3.3. Thiết kế kiểm thử tính tương đương kết quả (Equivalence Verification)
    - 3.3.4. Giao thức đo lường kiểm soát nhiễu: 3 Warm-up + 20 Official Runs
  - 3.4. Thiết kế thực nghiệm so sánh hiệu năng tiền xử lý (Processing Benchmark)
- **CHƯƠNG 4: KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN KHOA HỌC**
  - 4.1. Kết quả thực nghiệm trả lời RQ1: Hiệu quả của cấu trúc Index B-tree đơn và đa cột
    - 4.1.1. Phân tích bài toán Q1 (Single-column Index trên `province_name`)
    - 4.1.2. Phân tích đột phá hiệu năng bài toán Q2 (Composite Index và Early Termination)
    - 4.1.3. Cơ chế triệt tiêu nút sắp xếp (Top-N Heapsort) và chuyển đổi Buffer I/O
  - 4.2. Kết quả thực nghiệm trả lời RQ2: Tương tác giữa Viết lại truy vấn và Đánh chỉ mục
    - 4.2.1. Phân tích trực giao $2 \times 2$ của bài toán Q3 (Cấu hình A, B, C, D)
    - 4.2.2. Hiện tượng vô hiệu hóa Index do vị từ Non-sargable (Cấu hình C)
    - 4.2.3. Sức mạnh cộng hưởng của Sargable Range Query và Index (Cấu hình D)
  - 4.3. Kết quả thực nghiệm trả lời RQ3: Giới hạn của Index, Đánh đổi lưu trữ và Hiệu năng tiền xử lý
    - 4.3.1. Bài toán đối chứng âm Q4: Vì sao Index không cải thiện truy vấn tổng hợp?
    - 4.3.2. Định lượng chi phí phụ trội lưu trữ vật lý của B-tree Index (Storage Overhead)
    - 4.3.3. Đánh giá hiệu năng Ingestion và Thao tác bộ nhớ: Pandas vs Polars, CSV vs Parquet
  - 4.4. Đánh giá tính toàn vẹn của bằng chứng thực nghiệm và Độ tin cậy khoa học
- **CHƯƠNG 5: KẾT LUẬN VÀ KHUYẾN NGHỊ**
  - 5.1. Tổng kết các đóng góp chính của đề tài
  - 5.2. Câu trả lời tường minh cho ba câu hỏi nghiên cứu (RQ1 – RQ3)
  - 5.3. Khuyến nghị thực tiễn cho kỹ sư dữ liệu và thiết kế hệ thống
  - 5.4. Hạn chế của nghiên cứu và Hướng phát triển tương lai
- **TÀI LIỆU THAM KHẢO**
- **PHỤ LỤC**
  - Phụ lục A: Lược đồ bảng `public.properties` và Ràng buộc kiểm tra
  - Phụ lục B: Bộ mã truy vấn Benchmark SQL nghiệm thu
  - Phụ lục C: Bảng kê khai bằng chứng thực nghiệm và Mã băm toàn vẹn SHA-256
  - Phụ lục D: Thông số môi trường phần cứng và Hệ quản trị CSDL

---

## DANH MỤC THUẬT NGỮ VÀ VIẾT TẮT

| Viết tắt | Thuật ngữ Tiếng Anh | Ý nghĩa Tiếng Việt |
| :--- | :--- | :--- |
| **B-tree** | Balanced Tree | Cây cân bằng, cấu trúc chỉ mục mặc định phổ biến trong RDBMS |
| **BOM** | Byte Order Mark | Ký tự đánh dấu thứ tự byte đầu tệp văn bản mã hóa UTF-8/UTF-16 |
| **CSV** | Comma-Separated Values | Định dạng tệp văn bản thuần phân tách bằng dấu phẩy |
| **CTE** | Common Table Expression | Mệnh đề bảng tạm thời trong câu lệnh SQL (`WITH ... AS`) |
| **DBMS / RDBMS** | (Relational) Database Management System | Hệ quản trị cơ sở dữ liệu (quan hệ) |
| **DDL** | Data Definition Language | Ngôn ngữ định nghĩa dữ liệu (CREATE, ALTER, DROP) |
| **DML** | Data Manipulation Language | Ngôn ngữ thao tác dữ liệu (SELECT, INSERT, UPDATE, DELETE) |
| **EDA** | Exploratory Data Analysis | Phân tích khám phá dữ liệu |
| **FIFO** | First In, First Out | Nguyên lý vào trước ra trước |
| **I/O** | Input / Output | Thao tác nhập/xuất dữ liệu giữa bộ nhớ trong và thiết bị lưu trữ |
| **IQR** | Interquartile Range | Khoảng tứ phân vị ($IQR = Q_3 - Q_1$) |
| **LRU** | Least Recently Used | Thuật toán giải phóng trang đệm ít được sử dụng nhất gần đây |
| **NFC** | Normalization Form C | Chuẩn chuẩn hóa ký tự Unicode tổ hợp kết hợp dựng sẵn |
| **Parquet** | Apache Parquet | Định dạng tệp lưu trữ dữ liệu dạng cột nén nhị phân mã nguồn mở |
| **PK** | Primary Key | Khóa chính của bảng cơ sở dữ liệu quan hệ |
| **RAM** | Random Access Memory | Bộ nhớ truy xuất ngẫu nhiên (bộ nhớ trong) |
| **RDBMS** | Relational Database Management System | Hệ quản trị cơ sở dữ liệu quan hệ |
| **RQ** | Research Question | Câu hỏi nghiên cứu khoa học |
| **RSS** | Resident Set Size | Dung lượng bộ nhớ RAM thực tế đang chiếm dụng bởi tiến trình |
| **Sargable** | Search Argument Able | Khả năng tận dụng chỉ mục của vị từ tìm kiếm trong truy vấn SQL |
| **Seq Scan** | Sequential Scan | Quét tuần tự toàn bộ các trang dữ liệu của bảng từ đầu đến cuối |
| **TID** | Tuple Identifier | Định danh con trỏ vật lý trỏ trực tiếp đến hàng dữ liệu trong Heap Page |
