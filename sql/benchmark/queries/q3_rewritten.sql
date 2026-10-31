SELECT id, name, published_at
FROM public.properties
WHERE published_at >= TIMESTAMP '2025-10-15 00:00:00'
  AND published_at < TIMESTAMP '2025-10-16 00:00:00';
