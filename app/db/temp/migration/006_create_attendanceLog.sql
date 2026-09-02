-- 변경점 (기존 005_create_attendanceLog.sql 대비):
--   - org_id: NULL -> NOT NULL (fk_log_org는 기존에도 정의돼 있었음, 실 DB엔 미반영이었던 것)
--   - device_id 컬럼 신설: 재실 인증에 사용된 실제 기기(Device)를 식별하기 위함
--     * source(VARCHAR)는 채널 구분용으로 유지, device_id는 실제 기기 FK로 역할 분리
--     * 기존 로그에는 기기 연결 정보가 없으므로 NULL 허용
--   - 파일 번호를 005 -> 006으로 미룸: device_id가 Device 테이블을 FK 참조하므로 Device(005) 이후에 생성
CREATE TABLE AttendanceLog (
    id BIGINT(20) NOT NULL AUTO_INCREMENT,
    org_id INT(11) NOT NULL,
    member_id BIGINT(20) NOT NULL,
    device_id INT(11) NULL,
    event_time DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    event_type VARCHAR(16) NOT NULL,
    source VARCHAR(32) NULL,
    meta TEXT NULL,
    PRIMARY KEY (id),
    KEY idx_log_member_id (member_id),
    KEY idx_log_org_id (org_id),
    KEY idx_log_device (device_id),
    CONSTRAINT fk_log_member
        FOREIGN KEY (member_id) REFERENCES Member(id),
    CONSTRAINT fk_log_org
        FOREIGN KEY (org_id) REFERENCES Org(id),
    CONSTRAINT fk_log_device
        FOREIGN KEY (device_id) REFERENCES Device(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
