# PHỤ LỤC

## Phụ lục A: Lược đồ DDL và Ràng buộc toàn vẹn cơ sở dữ liệu

Tệp đặc tả cấu trúc bảng quan hệ [`sql/schema.sql`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/sql/schema.sql):

```sql
CREATE TABLE IF NOT EXISTS public.properties (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    property_type_name TEXT NOT NULL,
    province_name TEXT NOT NULL,
    district_name TEXT,
    ward_name TEXT,
    price NUMERIC,
    area DOUBLE PRECISION NOT NULL,
    published_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    CONSTRAINT properties_area_positive CHECK (area > 0),
    CONSTRAINT properties_price_positive CHECK (price IS NULL OR price > 0)
);
```

Tập lệnh khởi tạo các chỉ mục B-tree thực nghiệm trong thư mục `sql/benchmark/indexes/`:

```sql
-- 1. Chỉ mục đơn cột Q1 (q1_province_name.sql)
CREATE INDEX idx_properties_province_name
ON public.properties USING btree (province_name);

-- 2. Chỉ mục tổ hợp đa cột Q2 (q2_location_price.sql)
CREATE INDEX idx_properties_location_price
ON public.properties USING btree (province_name, district_name, price, id);

-- 3. Chỉ mục thời gian Q3 (q3_published_at.sql)
CREATE INDEX idx_properties_published_at
ON public.properties USING btree (published_at);

-- 4. Chỉ mục loại hình bất động sản Q4 (q4_property_type.sql)
CREATE INDEX idx_properties_property_type
ON public.properties USING btree (property_type_name);
```

---

## Phụ lục B: Tập mã nguồn các câu truy vấn Benchmark SQL chuẩn hóa

Đối chiếu trực tiếp với các tệp truy vấn trong thư mục `sql/benchmark/queries/`:

### B.1. Bài toán Q1 (`sql/benchmark/queries/q1.sql`)
```sql
SELECT id, name, price, area
FROM public.properties
WHERE province_name = 'Hải Phòng';
```

### B.2. Bài toán Q2 (`sql/benchmark/queries/q2.sql`)
```sql
SELECT id, name, price, area, published_at
FROM public.properties
WHERE province_name = 'Hà Nội'
  AND district_name = 'Cầu Giấy'
  AND price BETWEEN 4100000000 AND 14300000000
ORDER BY price ASC, id ASC
LIMIT 20;
```

### B.3. Bài toán Q3 Truy vấn gốc (`sql/benchmark/queries/q3_original.sql`)
```sql
SELECT id, name, published_at
FROM public.properties
WHERE published_at::date = DATE '2025-10-15';
```

### B.4. Bài toán Q3 Truy vấn viết lại (`sql/benchmark/queries/q3_rewritten.sql`)
```sql
SELECT id, name, published_at
FROM public.properties
WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00'
  AND published_at <  TIMESTAMP '2025-10-16 00:00:00';
```

### B.5. Bài toán Q4 (`sql/benchmark/queries/q4.sql`)
```sql
SELECT
    property_type_name,
    COUNT(*) AS total,
    ROUND(AVG(price), 0) AS avg_price
FROM public.properties
GROUP BY property_type_name
ORDER BY total DESC;
```

---

## Phụ lục C: Bảng kê mã băm SHA-256 các tệp kế hoạch thực thi thô

Toàn bộ 600 tệp JSON kế hoạch thực thi thô `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` được lưu trữ tại `results/benchmark/raw/{scale}/`. Bảng dưới đây trích dẫn một số mẫu mã băm SHA-256 từ tệp kiểm toán [`results/benchmark/raw_manifest.json`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/benchmark/raw_manifest.json):

| Quy mô | Cấu hình | Lần chạy | Tên tệp kế hoạch JSON | Mã băm toàn vẹn SHA-256 (64 ký tự hex) |
| :---: | :---: | :---: | :--- | :--- |
| 500K | `Q1_baseline` | Run 01 | `500000_Q1_baseline_run01.json` | `7be33f52a78eb04a29a0fef738988a109a0669c3a38ceca9489f61b0c0342217` |
| 500K | `Q1_indexed` | Run 01 | `500000_Q1_indexed_run01.json` | `837e3d162bc58d04269d08e33ea2193b2a0c64c7e54f9810b48455fa2ea2c159` |
| 500K | `Q2_baseline` | Run 01 | `500000_Q2_baseline_run01.json` | `9b3eb16b8ffec64bc81907cb818ba4dbebf25b045353ff7fc9d0124cbf5e2270` |
| 500K | `Q2_indexed` | Run 01 | `500000_Q2_indexed_run01.json` | `ad7be7c7ce1a5e1d4ad3c14a2bf43cf1815b822dc46b6279930f719488aef6a4` |
| 500K | `Q3_A` | Run 01 | `500000_Q3_A_run01.json` | `f6a47a16f6b5b4ce799f8d5f303c73fc7827877ce547e1744b827e8a3ffb1d9c` |
| 500K | `Q3_B` | Run 01 | `500000_Q3_B_run01.json` | `ca0cb5cf920556f8f533a871fe43b9e4a3b836a9a72df91845bb08f3316223e7` |
| 500K | `Q3_C` | Run 01 | `500000_Q3_C_run01.json` | `2e08e8b61cbf7a72bbd8e2840cfad114bf3921074706598501e7415494dcf91f` |
| 500K | `Q3_D` | Run 01 | `500000_Q3_D_run01.json` | `b68078c59918bfdbe9aa48d6dbfa6cb825a0a38b693259e86a032d84ea235552` |
| 500K | `Q4_baseline` | Run 01 | `500000_Q4_baseline_run01.json` | `dbbc3fb4ae3c4078cb18bf332c943ba874aa6794627be71cb87adca246e7f1dc` |
| 500K | `Q4_indexed` | Run 01 | `500000_Q4_indexed_run01.json` | `e2a2bafe4db36829ee168fb99564f9bf35a8f273295c52c938368819c9682701` |

