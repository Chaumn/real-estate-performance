
-- BASELINE QUERIES
-- Project: Real Estate Performance
-- Dataset: 500,000 records
-- Chua tao Index toi uu bo sung

-- ==================================================
-- Q1: Tim BDS theo tinh/thanh pho
-- Huong toi uu: Single-column Index
-- ==================================================

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, price, area
FROM public.properties
WHERE province_name = 'Hải Phòng';

-- Kiem tra so dong thoa dieu kien
SELECT COUNT(*) AS q1_matching_rows
FROM public.properties
WHERE province_name = 'Hải Phòng';


-- ==================================================
-- Q2: Tim BDS theo vi tri, gia va sap xep
-- Huong toi uu: Composite Index
-- ==================================================

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, price, area, published_at
FROM public.properties
WHERE province_name = 'Hà Nội'
  AND district_name = 'Cầu Giấy'
  AND price BETWEEN 4100000000 AND 14300000000
ORDER BY price ASC, id ASC
LIMIT 20;

-- Kiem tra so dong thoa dieu kien loc
SELECT COUNT(*) AS q2_matching_rows
FROM public.properties
WHERE province_name = 'Hà Nội'
  AND district_name = 'Cầu Giấy'
  AND price BETWEEN 4100000000 AND 14300000000;


-- ==================================================
-- Q3: Tim BDS theo ngay dang
-- Huong toi uu: Query Rewriting + Date Index
-- ==================================================

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, published_at
FROM public.properties
WHERE published_at::date = DATE '2025-10-15';

-- Kiem tra so dong thoa dieu kien
SELECT COUNT(*) AS q3_matching_rows
FROM public.properties
WHERE published_at::date = DATE '2025-10-15';


-- ==================================================
-- Q4: Thong ke theo loai bat dong san
-- Vai tro: Truy van doi chung
-- ==================================================

EXPLAIN (ANALYZE, BUFFERS)
SELECT
    property_type_name,
    COUNT(*) AS total,
    ROUND(AVG(price), 0) AS avg_price
FROM public.properties
GROUP BY property_type_name
ORDER BY total DESC;

-- Kiem tra ket qua thong ke
SELECT
    property_type_name,
    COUNT(*) AS total,
    ROUND(AVG(price), 0) AS avg_price
FROM public.properties
GROUP BY property_type_name
ORDER BY total DESC;
