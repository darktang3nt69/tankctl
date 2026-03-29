-- Persistent warning acknowledgements keyed by device + warning code.
CREATE TABLE IF NOT EXISTS warning_acknowledgements (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    warning_code VARCHAR(100) NOT NULL,
    acknowledged_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (device_id, warning_code)
);

CREATE INDEX IF NOT EXISTS idx_warning_ack_device ON warning_acknowledgements (device_id);
CREATE INDEX IF NOT EXISTS idx_warning_ack_code ON warning_acknowledgements (warning_code);
