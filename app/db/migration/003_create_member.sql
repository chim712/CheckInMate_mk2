CREATE TABLE Member (
    id BIGINT(20) NOT NULL AUTO_INCREMENT,
    org_id INT(11) NULL,
    kiosk_id BIGINT(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'INACTIVE',
    role VARCHAR(16) NOT NULL DEFAULT 'USER',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    deleted_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_member_kiosk_id (kiosk_id),
    KEY idx_member_org_id (org_id),
    CONSTRAINT fk_member_org
        FOREIGN KEY (org_id) REFERENCES Org(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
