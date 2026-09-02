-- 변경 없음 (기존 001_create_org.sql과 동일)
CREATE TABLE Org (
    id INT(11) NOT NULL AUTO_INCREMENT,
    org_code VARCHAR(4) NOT NULL,
    org_name VARCHAR(100) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    deleted_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_org_code (org_code),
    KEY idx_org_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
