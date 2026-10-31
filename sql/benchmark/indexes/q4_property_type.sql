CREATE INDEX idx_properties_property_type
ON public.properties USING btree (property_type_name);
