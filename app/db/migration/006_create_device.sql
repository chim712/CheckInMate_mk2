CREATE TABLE Device (
    id            INT(11)       NOT NULL COMMENT 'Device UUID',
    org_id        INT(11)      NOT NULL COMMENT '소속 기관 ID',
    name          VARCHAR(50)   NOT NULL COMMENT '기기 이름 (예: 본사, 2층 사무실)',
    token_hash    CHAR(64)      NOT NULL COMMENT 'Device token SHA-256 hash',
    created_by    CHAR(36)      NULL COMMENT '등록한 Admin/Master 계정 ID',
    revoked_at    DATETIME      NULL COMMENT '철회 시각',
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록 시각',
    last_seen_at  DATETIME      NULL COMMENT '마지막 접속 시각',

    PRIMARY KEY (id),
    UNIQUE KEY uk_device_token_hash (token_hash),
    KEY idx_device_org (org_id),
    KEY idx_device_last_seen (last_seen_at)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COMMENT='키오스크 디바이스 정보';
