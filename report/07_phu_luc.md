# PHỤ LỤC

## Phụ lục A: Lược đồ bảng `public.properties` và Ràng buộc toàn vẹn

Đoạn mã DDL chuẩn hóa khởi tạo bảng và các ràng buộc dữ liệu tại tệp [`sql/schema.sql`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/sql/schema.sql):

```sql
-- DDL Schema for real-estate-performance project
-- Compatible with PostgreSQL 17/18+

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

COMMENT ON TABLE public.properties IS 'Stores cleaned real estate listings with 9 standardized attributes';
COMMENT ON COLUMN public.properties.id IS 'Sequential unique identifier (PK)';
COMMENT ON COLUMN public.properties.price IS 'Asking price in VND (NULL if negotiable)';
COMMENT ON COLUMN public.properties.area IS 'Usable or land area in square meters (> 0)';
```

---

## Phụ lục B: Bộ mã truy vấn Benchmark SQL nghiệm thu

### B.1. Bài toán Q1: Single-column Index
- **Truy vấn:**
  ```sql
  SELECT * FROM public.properties WHERE province_name = 'Hải Phòng';
  ```
- **Chỉ mục:**
  ```sql
  CREATE INDEX idx_properties_province_name ON public.properties (province_name);
  ```

### B.2. Bài toán Q2: Composite Index
- **Truy vấn:**
  ```sql
  SELECT id, name, price, area, district_name 
  FROM public.properties 
  WHERE province_name = 'Hà Nội' 
    AND district_name = 'Cầu Giấy' 
    AND price BETWEEN 4100000000 AND 14300000000 
  ORDER BY price ASC, id ASC 
  LIMIT 20;
  ```
- **Chỉ mục:**
  ```sql
  CREATE INDEX idx_properties_location_price 
  ON public.properties (province_name, district_name, price, id);
  ```

### B.3. Bài toán Q3: Query Rewriting và Sargability
- **Cấu hình A & C (Truy vấn gốc non-sargable):**
  ```sql
  SELECT * FROM public.properties WHERE published_at::date = DATE '2025-10-15';
  ```
- **Cấu hình B & D (Truy vấn viết lại sargable):**
  ```sql
  SELECT * FROM public.properties 
  WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00' 
    AND published_at <  TIMESTAMP '2025-10-16 00:00:00';
  ```
- **Chỉ mục (Cấu hình C và D):**
  ```sql
  CREATE INDEX idx_properties_published_at ON public.properties (published_at);
  ```

### B.4. Bài toán Q4: Aggregation Control
- **Truy vấn:**
  ```sql
  SELECT property_type_name, COUNT(*), ROUND(AVG(price), 0) 
  FROM public.properties 
  GROUP BY property_type_name;
  ```
- **Chỉ mục:**
  ```sql
  CREATE INDEX idx_properties_property_type ON public.properties (property_type_name);
  ```

---

## Phụ lục C: Bảng kê khai bằng chứng thực nghiệm và Mã băm toàn vẹn SHA-256

Bảng dưới đây trích xuất một phần đại diện từ tệp [`results/benchmark/raw_manifest.json`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/benchmark/raw_manifest.json) (dung lượng 217.5 KB, quản lý toàn bộ 600 tệp JSON kế hoạch thực thi thô):

| Quy mô | Cấu hình | Lần chạy | Mã băm SHA-256 tệp JSON thô | Thời gian chạy (ms) | Kiểu quét ghi nhận |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 500.000 | `Q1_baseline` | 01 | `4f38e68e4fb7f0f6cbe16c35c36e4f3a7ea55b41295b2ceecbc4cbb0521e05a8` | 36.621 ms | Seq Scan |
| 500.000 | `Q1_indexed` | 01 | `9d55a40b196ee1b1c67ca8d81084b6f1784c568f18dbe154378f5fef91bb1640` | 9.102 ms | Bitmap Scan |
| 500.000 | `Q2_baseline` | 01 | `d121df4f661b6238b991ef23640b8a4f9103c80fbdfba9bc2d7870a0004ad2ba` | 47.982 ms | Seq Scan |
| 500.000 | `Q2_indexed` | 01 | `a61b6f00be0fb244465eb2b9a7c36d22ef14aa1796cbe48aa90666bbdb7eb57f` | **0.048 ms** | Index Scan |
| 500.000 | `Q3_A` | 01 | `2f9f8bf8e66a3fb96e8e0404a3e79cf44c01ff55b768404aeb53c15d482b61f8` | 39.851 ms | Seq Scan |
| 500.000 | `Q3_B` | 01 | `1a8fa066e2c39e083ea4279f649bf55d9d4f0aa289ab37ecb571168fca8b7891` | 38.419 ms | Seq Scan |
| 500.000 | `Q3_C` | 01 | `7b7cf7a8a25c15e8da39b4b0fa0e729a4ebdb20a32502cfa1ef1fdb8ba509b55` | 42.105 ms | Seq Scan |
| 500.000 | `Q3_D` | 01 | `c37ff290f9ea771413bd2a433f52aa81dc89b1424b94fcf138eb159ef4a84e62` | **2.215 ms** | Bitmap Scan |
| 500.000 | `Q4_baseline` | 01 | `ee29c99fa140e6c5bb5d2cf57b8535b91b5c213bb10476483486c99c855aa801` | 63.110 ms | Seq Scan |
| 500.000 | `Q4_indexed` | 01 | `59be61543883a48e7ea519c72cbf4258c73d9d30070ea83b38c22bb4696c6a49` | 66.241 ms | Seq Scan |

---

## Phụ lục D: Thông số môi trường phần cứng và Hệ quản trị CSDL

Trích xuất từ tệp siêu dữ liệu môi trường [`results/benchmark/environment_info.json`](file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/results/benchmark/environment_info.json):

```json
{
  "os_name": "Windows",
  "os_release": "11",
  "os_version": "10.0.26100",
  "os_platform": "win32",
  "processor": "Intel64 Family 6 Model 154 Stepping 3, GenuineIntel",
  "cpu_count_physical": 14,
  "cpu_count_logical": 20,
  "total_ram_gb": 15.69,
  "python_version": "3.13.7",
  "psycopg_version": "3.2.3",
  "postgres_server_version": "PostgreSQL 18.3 on x86_64-windows, compiled by msvc-19.44.35225, 64-bit",
  "postgres_port": 5433,
  "postgres_shared_buffers": "128MB",
  "postgres_work_mem": "4MB",
  "postgres_random_page_cost": 4.0,
  "postgres_seq_page_cost": 1.0
}
```
