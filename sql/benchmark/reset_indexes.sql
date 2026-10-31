-- Reset only the four supplemental indexes used by Q1-Q4.
-- Keep the properties primary key, table and data.
DROP INDEX IF EXISTS public.idx_properties_province_name;
DROP INDEX IF EXISTS public.idx_properties_location_price;
DROP INDEX IF EXISTS public.idx_properties_published_at;
DROP INDEX IF EXISTS public.idx_properties_property_type;
