-- Create firmware releases table
CREATE TABLE IF NOT EXISTS firmware_releases (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    checksum VARCHAR(64),
    platform VARCHAR(50) NOT NULL DEFAULT 'esp32',
    release_notes TEXT,
    released_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for quick version lookups
CREATE INDEX idx_firmware_version ON firmware_releases(version);
CREATE INDEX idx_firmware_platform ON firmware_releases(platform);

-- Create firmware deployment history table
CREATE TABLE IF NOT EXISTS firmware_deployments (
    id SERIAL PRIMARY KEY,
    release_id INTEGER NOT NULL REFERENCES firmware_releases(id),
    device_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, updating, success, failed
    error_message TEXT,
    command_version INTEGER,
    attempted_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- Create index for tracking deployments
CREATE INDEX idx_firmware_deployments_device ON firmware_deployments(device_id);
CREATE INDEX idx_firmware_deployments_status ON firmware_deployments(status);
CREATE INDEX idx_firmware_deployments_release ON firmware_deployments(release_id);
