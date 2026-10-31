# Bàn giao benchmark độc lập cho TV2

## Phạm vi và đầu vào

TV2 thực hiện benchmark trên PostgreSQL 17, database `real_estate_db`,
bảng `public.properties`. Bộ bàn giao chỉ có SQL và hướng dẫn, không có
runner benchmark Python. Các lệnh trong tài liệu chưa được chạy trên
database thật trong bước bàn giao.

- Nguồn: `Phuscca/vietnam-real-estates`, split `train`.
- Dataset source revision: `68bae25c3fa65a8e694973efe80bd6e237de11f5`.
- Seed: `42`; shuffle_buffer: `10000`; batch_size: `2000`.
- CSV: `data/processed/properties_50000.csv`, `properties_200000.csv`,
  `properties_500000.csv`. Các file nhỏ là prefix của file lớn, cùng ID.
- Ghi SHA-256 từng CSV và giữ report tương ứng; mỗi lần chỉ nạp một dataset.
- Giữ nguyên schema 9 cột, importer, cleaning và CSV đã nghiệm thu.

`sql/baseline_queries.sql` và `sql/optimizations/` được giữ nguyên làm
tài liệu nghiệm thu. Các script cũ ghép DDL/ANALYZE/EXPLAIN và có bước
dọn Index phụ thuộc thứ tự chạy. TV2 dùng `sql/benchmark/` để chạy độc
lập, không chạy xen các script thực nghiệm cũ vào lượt đo.

“Không Index” nghĩa là không có bốn Index tối ưu bổ sung; **Primary Key
trên id luôn được giữ lại** ở mọi cấu hình.

## Cấu hình môi trường

Chạy từ thư mục gốc project. Dùng cùng PostgreSQL 17.x, phần cứng và cấu
hình cho ba quy mô. Ghi CPU, RAM, loại ổ lưu trữ, OS, phiên bản Python/
Psycopg, tải máy và các session hoạt động khác. Database và bảng theo
`sql/schema.sql` phải tồn tại trước.

Importer dùng `.env` đã có. Không đặt mật khẩu trên dòng lệnh, trong log
hoặc report chia sẻ. **psql không tự đọc .env**: dùng cùng host, port và
user với importer. Ví dụ sau dùng localhost:5432 và postgres; thay bằng
cấu hình của TV2 nếu khác và nhập mật khẩu tại prompt:

```powershell
$env:PGCLIENTENCODING = "UTF8"
psql -X -W -h localhost -p 5432 -U postgres -d real_estate_db -v ON_ERROR_STOP=1
```

`-X` bỏ cấu hình psqlrc cá nhân. Xác nhận và lưu metadata:

```sql
SELECT version(), current_database(), current_user;
SHOW server_version_num;
SHOW client_encoding;
SHOW TimeZone;
SELECT datcollate, datctype
FROM pg_database WHERE datname = current_database();

SELECT name, setting, unit, source
FROM pg_settings
WHERE name IN (
    'shared_buffers', 'effective_cache_size', 'work_mem', 'maintenance_work_mem',
    'random_page_cost', 'seq_page_cost', 'effective_io_concurrency',
    'max_parallel_workers', 'max_parallel_workers_per_gather',
    'jit', 'default_statistics_target', 'track_io_timing',
    'enable_seqscan', 'enable_indexscan', 'enable_indexonlyscan', 'enable_bitmapscan'
)
ORDER BY name;
```

Không ép `enable_seqscan=off` hay ép scan type để có kết quả có lợi cho
Index. Mọi setting phải nhất quán; thay đổi cấu hình là thí nghiệm khác
và phải ghi nhận. Khi `track_io_timing=off`, vẫn ghi buffers nhưng không
diễn giải thời gian I/O không được thu thập.

## Nạp lần lượt 50K, 200K, 500K

Trước mỗi lần nạp, trong psql:

```psql
\i sql/benchmark/reset_indexes.sql
```

Chạy **từng lệnh riêng** ở terminal. Hoàn tất benchmark của quy mô hiện
tại rồi mới chuyển sang dataset tiếp theo:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.import_csv --file data/processed/properties_50000.csv --replace
```

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.import_csv --file data/processed/properties_200000.csv --replace
```

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.import_csv --file data/processed/properties_500000.csv --replace
```

`--replace` chủ động thay toàn bộ dữ liệu, không nối ba dataset. Có thể
bỏ cờ nếu bảng chắc chắn rỗng. Importer xác nhận số bản ghi, ID và NULL
trước commit. Nếu import lỗi, dừng; không đo dữ liệu của lượt trước còn
lại sau rollback. Sau mỗi lần nạp, trong psql:

```sql
ANALYZE public.properties;
SELECT COUNT(*) AS rows, MIN(id) AS min_id, MAX(id) AS max_id
FROM public.properties;
```

Số dòng phải đúng 50000/200000/500000, ID 1..N đã được importer xác nhận.
ANALYZE cập nhật thống kê planner
([PostgreSQL 17](https://www.postgresql.org/docs/17/sql-analyze.html)).
Chạy lại khi dữ liệu/thống kê thay đổi hoặc theo chính sách nhất quán
đã chọn trước mỗi cấu hình. Nếu ANALYZE lại sau tạo Index, làm trước
warm-up và ghi nhận; không ANALYZE giữa các lượt đo. Thời gian nạp,
reset, tạo Index và ANALYZE không thuộc Execution Time của query.

## Ma trận cấu hình độc lập

**Trước MỖI hàng dưới đây, luôn chạy reset_indexes.sql**, kể cả vừa chạy
một hàng tương tự. Sau reset, chỉ tạo Index ghi ở hàng đó nếu có.
Không cần chạy Q1 trước Q2 hay Q3 trước Q4.
Nếu reset, CREATE INDEX, ANALYZE hoặc một lượt đo báo lỗi, dừng và xử lý,
không tiếp tục coi cấu hình đó là hợp lệ.

| Cấu hình | File trong sql/benchmark/queries/ | File trong sql/benchmark/indexes/ |
| --- | --- | --- |
| Q1 baseline | q1.sql | Không |
| Q1 indexed | q1.sql | q1_province_name.sql |
| Q2 baseline | q2.sql | Không |
| Q2 indexed | q2.sql | q2_location_price.sql |
| Q3 A: original, không Index | q3_original.sql | Không |
| Q3 B: rewritten, không Index | q3_rewritten.sql | Không |
| Q3 C: original, có Index | q3_original.sql | q3_published_at.sql |
| Q3 D: rewritten, có Index | q3_rewritten.sql | q3_published_at.sql |
| Q4 baseline, đối chứng | q4.sql | Không |
| Q4 indexed, đối chứng | q4.sql | q4_property_type.sql |

Các Index B-tree giữ đúng tên và thứ tự cột nghiệm thu:

| Query | Tên Index | Cột |
| --- | --- | --- |
| Q1 | idx_properties_province_name | (province_name) |
| Q2 | idx_properties_location_price | (province_name, district_name, price, id) |
| Q3 | idx_properties_published_at | (published_at) |
| Q4 | idx_properties_property_type | (property_type_name) |

Ví dụ Q2 baseline trong psql:

```psql
\i sql/benchmark/reset_indexes.sql
```

Q2 indexed, dù cấu hình trước là Q1/Q3/Q4:

```psql
\i sql/benchmark/reset_indexes.sql
\i sql/benchmark/indexes/q2_location_price.sql
```

Q3 A/B reset rồi không tạo Index; C/D đều reset rồi tạo
`q3_published_at.sql` riêng cho mỗi cấu hình, chỉ khác file query.
Q4 cũng reset trước mỗi trạng thái không/có `q4_property_type.sql`.
Các file Index chỉ chứa CREATE INDEX, không ẩn reset/ANALYZE/EXPLAIN.
Không dùng IF NOT EXISTS để tránh âm thầm dùng định nghĩa Index cũ.

Reset chỉ DROP đúng bốn Index bổ sung, có schema public, không CASCADE,
không xóa Primary Key, bảng hoặc dữ liệu. Sau chuẩn bị mỗi cấu hình,
kiểm tra Index thực tế và ghi dung lượng:

```sql
SELECT
    indexrelid::regclass AS index_name,
    indisprimary, indisvalid,
    pg_get_indexdef(indexrelid) AS index_definition,
    pg_relation_size(indexrelid) AS index_bytes
FROM pg_index
WHERE indrelid = 'public.properties'::regclass
ORDER BY indexrelid::regclass::text;
```

Baseline phải chỉ còn Primary Key; indexed có Primary Key và đúng một
Index bổ sung. Nếu có Index lạ, dừng và làm rõ, không tự DROP hàng loạt:
reset cố ý không đụng Index ngoài danh sách. Lưu kích thước từng Index
bằng byte, tách Primary Key; baseline không có Index bổ sung (size = 0).
`pg_relation_size(indexrelid)` đo relation của chính Index
([hàm dung lượng PostgreSQL](https://www.postgresql.org/docs/17/functions-admin.html#FUNCTIONS-ADMIN-DBSIZE)).

## EXPLAIN JSON và quy trình đo

Mỗi file `queries/` chỉ có một SELECT. TV2 giữ nguyên file, thêm tiền tố:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
-- Dán nguyên SELECT từ file query của cấu hình ngay bên dưới.
```

Không EXPLAIN một script chứa DDL, không dùng COUNT thay cho Q1/Q2/Q3,
không sửa LIMIT hoặc ORDER BY. EXPLAIN ANALYZE thực sự thực thi query,
có overhead đo và không trả dữ liệu SELECT để kiểm tra tương đương
([EXPLAIN PostgreSQL 17](https://www.postgresql.org/docs/17/sql-explain.html)).
Dùng cùng tùy chọn cho tất cả cấu hình.

Ví dụ PowerShell tạo SQL đo **một lượt Q2** từ nguyên file query và lưu
JSON. Đây là ví dụ thao tác, không phải runner benchmark:

```powershell
$utf8 = [System.Text.UTF8Encoding]::new($false)
$env:PGCLIENTENCODING = "UTF8"
New-Item -ItemType Directory -Force -Path results/benchmark | Out-Null
$query = Get-Content -LiteralPath sql/benchmark/queries/q2.sql -Raw -Encoding utf8
$explainPath = Join-Path $PWD "results/benchmark/q2_explain.sql"
[System.IO.File]::WriteAllText($explainPath, "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)" + [Environment]::NewLine + $query, $utf8)
psql -X -W -q -A -t -v ON_ERROR_STOP=1 -h localhost -p 5432 -U postgres -d real_estate_db -f $explainPath -o results/benchmark/50000_q2_indexed_run01.json
if ($LASTEXITCODE -ne 0) { throw "Lượt đo thất bại; không dùng JSON đầu ra" }
```

Chỉ đo sau khi chuẩn bị đúng cấu hình. Đặt tên output theo dataset,
cấu hình, lượt chạy, không ghi đè lượt trước. Nếu dùng session mới như
ví dụ, giữ cùng setting giữa session; nếu TV2 dùng connection liên tục
cho mỗi cấu hình, giữ chính sách đó nhất quán. Không trộn stderr/prompt/
thông tin kết nối vào JSON.

Với mỗi dataset × cấu hình:

1. Reset, tạo đúng Index nếu có, ANALYZE khi cần, kiểm tra Index và kết quả.
2. Warm-up **3 lần** bằng cùng EXPLAIN JSON, bỏ ba số đo này.
3. Đo chính thức **20 lần** tuần tự, giữ nguyên JSON từng lượt.
4. Không import/reset/tạo Index/ANALYZE xen giữa 3+20 lượt. Không chạy
   cấu hình song song; ghi nhận autovacuum, I/O và tải nền nếu xuất hiện.
5. Dùng **median của 20 Execution Time**, không chọn số nhỏ nhất. Median
   là trung bình giá trị thứ 10 và 11 sau khi sắp tăng; giữ toàn bộ số
   đo thô, nên báo thêm min/max hoặc IQR.

Đây là phép đo sau warm-up, không phải cold-cache benchmark. DDL/ANALYZE
cũng ảnh hưởng cache; warm-up phải nhất quán. Không giả định mọi dữ liệu
đều vừa RAM hay mọi block đều cache hit. Lưu thứ tự cấu hình; có thể lặp
các vòng với thứ tự đổi/cân bằng để đánh giá ảnh hưởng chạy trước/sau.

Mỗi lượt đo tối thiểu ghi:

| Trường | Cách lấy / ý nghĩa |
| --- | --- |
| dataset_rows, revision, seed, shuffle_buffer, CSV SHA-256 | Metadata dữ liệu |
| query_id, configuration, run_number | Ví dụ 500K / Q3 D / run 01 |
| Execution Time (ms) | Trường cấp ngoài ở phần tử đầu mảng JSON, không dùng wall-clock client |
| Planning Time (ms) | Ghi riêng, không cộng vào Execution Time |
| scan type, Index Name, Actual Rows, Actual Loops | Duyệt Plan kể cả node con Bitmap/parallel, không chỉ đọc Limit/Aggregate ở gốc |
| buffers | Shared Hit/Read/Dirtied/Written Blocks; Temp Read/Written Blocks nếu có |
| index_bytes | Catalog query ngoài lượt đo; tách Index tối ưu và Primary Key |
| full_plan_json, settings, notes | Giữ kế hoạch đầy đủ, JIT/workers, tải nền và ngoại lệ |

Buffers tại một node bao gồm node con: ghi tổng tại gốc và chi tiết
cần thiết, không cộng toàn bộ cây gây đếm trùng. Shared Read chưa chứng
minh có I/O ổ đĩa vật lý vì còn cache OS. Nếu scan type thay đổi giữa
20 lượt, giữ từng plan và giải thích.

## Xác nhận kết quả tương đương ngoài phần đo

Giữ dataset không đổi giữa các cấu hình. Chạy SELECT thuần và lưu kết
quả baseline/indexed để đối chiếu, không tính bước này vào 20 lượt:

- **Q1:** tập hàng id/name/price/area ở **Hải Phòng**. Không ORDER BY
  nên không so thứ tự hàng; chuẩn hóa theo id ở bước kiểm tra ngoài đo.
- **Q2:** tối đa 20 hàng đúng thứ tự price ASC, id ASC; **Hà Nội**,
  **Cầu Giấy**, BETWEEN **4100000000 AND 14300000000**, gồm cả hai biên.
  Không đổi điều kiện, cận giá hoặc LIMIT. id phân giải các giá bằng nhau.
- **Q3:** A/C là original, B/D là rewritten. Với TIMESTAMP WITHOUT TIME
  ZONE, ngày **2025-10-15** tương đương khoảng nửa mở
  **[2025-10-15 00:00:00, 2025-10-16 00:00:00)**. Không dùng BETWEEN
  cho khoảng này vì sẽ gồm nửa đêm ngày hôm sau.
- **Q4:** cùng ánh xạ property_type_name -> (total, avg_price).
  Giữ COUNT(*), ROUND(AVG(price), 0), GROUP BY property_type_name và
  ORDER BY total DESC. AVG bỏ NULL, COUNT(*) tính mọi dòng; không đổi
  NULL thành 0. Nhóm có total bằng nhau có thể đổi thứ tự; so theo khóa
  nhóm bên ngoài phần đo, không thêm ORDER BY vào query nghiệm thu.

Q3 cần so toàn bộ hàng, không chỉ so COUNT. Chạy hai chiều EXCEPT ALL
trên từng dataset ở trạng thái không/có Index; kết quả phải là 0:

```sql
WITH original AS (
    SELECT id, name, published_at
    FROM public.properties
    WHERE published_at::date = DATE '2025-10-15'
), rewritten AS (
    SELECT id, name, published_at
    FROM public.properties
    WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00'
      AND published_at < TIMESTAMP '2025-10-16 00:00:00'
)
SELECT COUNT(*) AS differing_rows
FROM (
    (SELECT * FROM original EXCEPT ALL SELECT * FROM rewritten)
    UNION ALL
    (SELECT * FROM rewritten EXCEPT ALL SELECT * FROM original)
) AS differences;
```

Q3 A/B/C/D tách hai yếu tố: so A-B khi không Index, C-D khi có Index;
A-C giữ original, B-D giữ rewritten. Chênh lệch A-D gồm cả viết lại
query lẫn Index, không được gán toàn bộ cho query rewriting.

**Q4 là trường hợp đối chứng:** không mặc định Index phải giúp nhanh
hơn. Query tổng hợp toàn bảng có thể vẫn Seq Scan hoặc có kế hoạch
tương tự; báo đúng plan và median dù không cải thiện hay chậm hơn.
Index tồn tại cũng không bắt buộc planner chọn Index Scan ở Q1/Q2/Q3.

## Tiêu chí bàn giao và giới hạn

- 3 dataset × 10 cấu hình, mỗi cấu hình 3 warm-up + 20 lượt chính thức.
- Có metadata, Index đúng, kiểm tra tương đương, JSON thô, median
  Execution Time, buffers, scan type và index size.
- **Số đo đơn lẻ của các thực nghiệm trước không phải benchmark chính
  thức**, không đưa chúng vào bảng median 20 lượt.
- Unit test offline bảo vệ SELECT, định nghĩa Index và phạm vi reset
  so với SQL nghiệm thu; không chứng minh plan, tốc độ, quyền DDL,
  khóa hoặc kết quả thực tế trên PostgreSQL 17. TV2 phải xác nhận.

Chạy unit tests không kết nối database:

```powershell
$pytestRunRoot = Join-Path $env:TEMP ("real-estate-handoff-tests-" + [guid]::NewGuid().ToString("N"))
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp $pytestRunRoot
```
