CREATE TABLE Account (
    id BIGINT(20) NOT NULL AUTO_INCREMENT,
    org_id INT(11) NOT NULL,
    login_id VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('MASTER','ADMIN') NOT NULL,
    failed_login_count INT(11) NOT NULL DEFAULT 0,
    last_login_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    deleted_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    KEY idx_account_org_id (org_id),
    KEY idx_account_deleted_at (deleted_at),
    CONSTRAINT fk_account_org
        FOREIGN KEY (org_id) REFERENCES Org(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
