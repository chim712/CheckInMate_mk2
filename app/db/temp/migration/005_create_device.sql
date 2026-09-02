-- 변경점 (기존 006_create_device.sql 대비):
--   - id: 수기 채번 -> AUTO_INCREMENT로 전환 (AttendanceLog.device_id가 이 값을 FK로 참조하므로 채번 방식 확정 필요)
--   - fk_device_org 신설: org FK가 누락되어 있었음
--   - 파일 번호를 006 -> 005로 당김: AttendanceLog(현 006)가 device_id로 이 테이블을 FK 참조하므로
--     Device 테이블이 먼저 생성되어야 함 (원본 순서 그대로면 FK 생성 시 에러 발생)
CREATE TABLE Device (
    id            INT(11)       NOT NULL AUTO_INCREMENT COMMENT 'Device ID',
    org_id        INT(11)       NOT NULL COMMENT '소속 기관 ID',
    name          VARCHAR(50)   NOT NULL COMMENT '기기 이름 (예: 본사, 2층 사무실)',
    token_hash    CHAR(64)      NOT NULL COMMENT 'Device token SHA-256 hash',
    created_by    CHAR(36)      NULL COMMENT '등록한 Admin/Master 계정 ID',
    revoked_at    DATETIME      NULL COMMENT '철회 시각',
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록 시각',
    last_seen_at  DATETIME      NULL COMMENT '마지막 접속 시각',

    PRIMARY KEY (id),
    UNIQUE KEY uk_device_token_hash (token_hash),
    KEY idx_device_org (org_id),
    KEY idx_device_last_seen (last_seen_at),
    CONSTRAINT fk_device_org
        FOREIGN KEY (org_id) REFERENCES Org(id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COMMENT='키오스크 디바이스 정보';
