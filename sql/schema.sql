
-- Real Estate Performance
-- Schema for property listings

CREATE TABLE IF NOT EXISTS public.properties (
    id BIGINT PRIMARY KEY,

    name TEXT NOT NULL,
    property_type_name TEXT NOT NULL,
    province_name TEXT NOT NULL,

    district_name TEXT,
    ward_name TEXT,

    price NUMERIC,
    area DOUBLE PRECISION NOT NULL,

    published_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,

    CONSTRAINT chk_price_positive
        CHECK (price > 0),

    CONSTRAINT chk_area_positive
        CHECK (area > 0),

    CONSTRAINT chk_name_not_empty
        CHECK (BTRIM(name) <> ''),

    CONSTRAINT chk_property_type_not_empty
        CHECK (BTRIM(property_type_name) <> ''),

    CONSTRAINT chk_province_not_empty
        CHECK (BTRIM(province_name) <> '')
);
