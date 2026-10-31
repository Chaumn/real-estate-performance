CREATE INDEX idx_properties_published_at
ON public.properties USING btree (published_at);
