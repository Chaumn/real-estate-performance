
-- Q4: Aggregation Control Experiment
-- Dataset: 500K

-- Loai bo Date Index cua Q3
DROP INDEX IF EXISTS public.idx_properties_published_at;

-- Dam bao Q4 co the chay lai
DROP INDEX IF EXISTS public.idx_properties_property_type;

ANALYZE public.properties;

-- A. Baseline without additional Index
\echo '=== Q4 BASELINE ==='

EXPLAIN (ANALYZE, BUFFERS)
SELECT
    property_type_name,
    COUNT(*) AS total,
    ROUND(AVG(price), 0) AS avg_price
FROM public.properties
GROUP BY property_type_name
ORDER BY total DESC;

-- B. Create Index on property_type_name
CREATE INDEX idx_properties_property_type
ON public.properties (property_type_name);

ANALYZE public.properties;

-- C. Run the same query with Index
\echo '=== Q4 WITH INDEX ==='

EXPLAIN (ANALYZE, BUFFERS)
SELECT
    property_type_name,
    COUNT(*) AS total,
    ROUND(AVG(price), 0) AS avg_price
FROM public.properties
GROUP BY property_type_name
ORDER BY total DESC;

-- D. Validate dataset
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT property_type_name) AS type_count
FROM public.properties;

-- E. Index size
SELECT pg_size_pretty(
    pg_relation_size('public.idx_properties_property_type')
) AS index_size;
