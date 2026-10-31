
-- Q3: Query Rewriting + Date Index
-- Dataset: 500K

-- Loai bo cac Index toi uu truoc do
DROP INDEX IF EXISTS public.idx_properties_location_price;
DROP INDEX IF EXISTS public.idx_properties_published_at;

ANALYZE public.properties;

-- A. Original Query - No Index
\echo '=== Q3 A: ORIGINAL - NO INDEX ==='

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, published_at
FROM public.properties
WHERE published_at::date = DATE '2025-10-15';


-- B. Rewritten Query - No Index
\echo '=== Q3 B: REWRITTEN - NO INDEX ==='

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, published_at
FROM public.properties
WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00'
  AND published_at < TIMESTAMP '2025-10-16 00:00:00';


-- Tao B-tree Index tren published_at
CREATE INDEX idx_properties_published_at
ON public.properties (published_at);

ANALYZE public.properties;


-- C. Original Query - With Index
\echo '=== Q3 C: ORIGINAL - WITH INDEX ==='

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, published_at
FROM public.properties
WHERE published_at::date = DATE '2025-10-15';


-- D. Rewritten Query - With Index
\echo '=== Q3 D: REWRITTEN - WITH INDEX ==='

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name, published_at
FROM public.properties
WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00'
  AND published_at < TIMESTAMP '2025-10-16 00:00:00';


-- Kiem tra so ban ghi hai truy van
SELECT
    COUNT(*) FILTER (
        WHERE published_at::date = DATE '2025-10-15'
    ) AS original_rows,

    COUNT(*) FILTER (
        WHERE published_at >= TIMESTAMP '2025-10-15'
          AND published_at < TIMESTAMP '2025-10-16'
    ) AS rewritten_rows
FROM public.properties;


-- Kiem tra dung luong Index
SELECT
    pg_size_pretty(
        pg_relation_size('public.idx_properties_published_at')
    ) AS index_size;
