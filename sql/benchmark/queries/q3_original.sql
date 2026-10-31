SELECT id, name, published_at
FROM public.properties
WHERE published_at::date = DATE '2025-10-15';
