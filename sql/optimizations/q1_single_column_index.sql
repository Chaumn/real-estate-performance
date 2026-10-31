
-- Q1: Single-column B-tree Index

-- 1. Tao index
CREATE INDEX IF NOT EXISTS idx_properties_province_name
ON public.properties USING BTREE (province_name);

-- 2. Cap nhat thong ke
ANALYZE public.properties;

-- 3. Kiem tra ke hoach thuc thi
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, price, area
FROM public.properties
WHERE province_name = 'Hải Phòng';

-- 4. Xac nhan so ban ghi
SELECT COUNT(*) AS matching_rows
FROM public.properties
WHERE province_name = 'Hải Phòng';

-- 5. Kiem tra dung luong index
SELECT
    pg_size_pretty(
        pg_relation_size('idx_properties_province_name')
    ) AS index_size;
