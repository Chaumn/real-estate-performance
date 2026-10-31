
-- DATA PROFILING - 500K DATASET
-- Read-only queries, except updating planner statistics

-- 1. Cap nhat thong ke PostgreSQL
ANALYZE public.properties;

-- 2. Thong tin tong quan
SELECT
    COUNT(*) AS total_rows,
    COUNT(price) AS rows_with_price,
    MIN(published_at)::date AS earliest_date,
    MAX(published_at)::date AS latest_date
FROM public.properties;

-- 3. Top 10 tinh/thanh pho
SELECT province_name, COUNT(*) AS total
FROM public.properties
GROUP BY province_name
ORDER BY total DESC
LIMIT 10;

-- 4. Top 10 cap tinh/thanh - quan/huyen
SELECT
    province_name,
    district_name,
    COUNT(*) AS total
FROM public.properties
WHERE district_name IS NOT NULL
GROUP BY province_name, district_name
ORDER BY total DESC
LIMIT 10;

-- 5. Phan bo loai bat dong san
SELECT
    property_type_name,
    COUNT(*) AS total
FROM public.properties
GROUP BY property_type_name
ORDER BY total DESC;

-- 6. Phan vi gia (don vi VND)
SELECT
    percentile_disc(0.25)
        WITHIN GROUP (ORDER BY price) AS price_p25,
    percentile_disc(0.50)
        WITHIN GROUP (ORDER BY price) AS price_median,
    percentile_disc(0.75)
        WITHIN GROUP (ORDER BY price) AS price_p75
FROM public.properties
WHERE price IS NOT NULL;

-- 7. Top 10 thang co nhieu tin dang
SELECT
    DATE_TRUNC('month', published_at)::date AS month,
    COUNT(*) AS total
FROM public.properties
GROUP BY 1
ORDER BY total DESC
LIMIT 10;
