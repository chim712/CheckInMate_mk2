-- 변경점 (기존 003_create_member.sql 대비):
--   - org_id: BIGINT NULL -> INT(11) NOT NULL
--     (Org.id 타입과 맞춤 + 구성원은 소속 기관이 항상 있어야 하므로 NOT NULL로 전환)
--   - fk_member_org 는 기존에도 정의돼 있었음 (실 DB엔 미반영이었던 것 -> temp/01_alter_current_schema.sql에서 보정)
CREATE TABLE Member (
    id BIGINT(20) NOT NULL AUTO_INCREMENT,
    org_id INT(11) NOT NULL,
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
