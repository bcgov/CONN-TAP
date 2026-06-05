-- Example fact table backing the `isp-spending` dataset module.
CREATE TABLE IF NOT EXISTS analytics.isp_spending (
    id         BIGSERIAL PRIMARY KEY,
    region     TEXT        NOT NULL,
    year       INTEGER     NOT NULL,
    provider   TEXT        NOT NULL,
    amount     NUMERIC(18,2) NOT NULL,
    loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS isp_spending_region_year_idx
    ON analytics.isp_spending (region, year);

INSERT INTO analytics.isp_spending (region, year, provider, amount) VALUES
    ('BC', 2025, 'Telus',   125000.00),
    ('BC', 2025, 'Rogers',   84000.00),
    ('BC', 2024, 'Telus',   110000.00),
    ('AB', 2025, 'Telus',    72000.00),
    ('ON', 2025, 'Rogers',  210000.00),
    ('ON', 2024, 'Bell',    180000.00)
ON CONFLICT DO NOTHING;
