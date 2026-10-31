
-- Q2: Composite Index Experiment

-- Loai bo Index Q1 de tranh anh huong
DROP INDEX IF EXISTS public.idx_properties_province_name;

-- Cho phep chay lai thi nghiem
DROP INDEX IF EXISTS public.idx_properties_location_price;

ANALYZE public.properties;

-- 1. Baseline Q2
\echo '=== Q2 BASELINE ==='

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, price, area, published_at
FROM public.properties
WHERE province_name = 'Hà Nội'
  AND district_name = 'Cầu Giấy'
  AND price BETWEEN 4100000000 AND 14300000000
ORDER BY price ASC, id ASC
LIMIT 20;

-- 2. Tao Composite Index
CREATE INDEX idx_properties_location_price
ON public.properties
    (province_name, district_name, price, id);

ANALYZE public.properties;

-- 3. Sau toi uu
\echo '=== Q2 OPTIMIZED ==='

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, price, area, published_at
FROM public.properties
WHERE province_name = 'Hà Nội'
  AND district_name = 'Cầu Giấy'
  AND price BETWEEN 4100000000 AND 14300000000
ORDER BY price ASC, id ASC
LIMIT 20;

-- 4. Kiem tra so dong loc
SELECT COUNT(*) AS matching_rows
FROM public.properties
WHERE province_name = 'Hà Nội'
  AND district_name = 'Cầu Giấy'
  AND price BETWEEN 4100000000 AND 14300000000;

-- 5. Dung luong Index
SELECT pg_size_pretty(
    pg_relation_size('public.idx_properties_location_price')
) AS index_size;
