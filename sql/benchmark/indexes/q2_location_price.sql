CREATE INDEX idx_properties_location_price
ON public.properties USING btree (province_name, district_name, price, id);
