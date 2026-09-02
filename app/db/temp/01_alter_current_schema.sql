-- =====================================================================
-- 요구사항 1: 현재 운영 DB(checkinmate) 스키마를 아래 상태로 맞추기 위한 ALTER 쿼리
--
-- 적용 전 상태 (2026-08-14 조사 기준):
--   - Member.org_id     : FK 없음 (migration/003에는 fk_member_org가 정의돼 있었으나 실제 DB에는 미반영)
--   - AttendanceLog.org_id : NULL 허용, FK 없음, 813건 중 551건이 NULL
--   - Device.id         : AUTO_INCREMENT 아님, org FK 없음
--   - AttendanceLog     : device_id 컬럼 자체가 없음 (재실 인증 기기 추적 불가)
--
-- 순서대로 실행할 것 (뒷 단계가 앞 단계 결과에 의존함).
-- 원본 app/db/migration/ 은 건드리지 않음 (temp에서 먼저 검증 후 적용).
-- =====================================================================

-- ---------------------------------------------------------------
-- 1) Member.org_id  ->  Org(id) FK 추가
--    (기존 데이터 4건 전부 org_id=1로 채워져 있어 바로 추가 가능)
-- ---------------------------------------------------------------
ALTER TABLE Member
    ADD CONSTRAINT fk_member_org
        FOREIGN KEY (org_id) REFERENCES Org(id);


-- ---------------------------------------------------------------
-- 2) AttendanceLog.org_id  NULL 백필 + NOT NULL 전환 + FK 추가
--    Member.org_id 기준으로 채움 (member_id로 조인)
-- ---------------------------------------------------------------
UPDATE AttendanceLog al
JOIN Member m ON m.id = al.member_id
SET al.org_id = m.org_id
WHERE al.org_id IS NULL;

-- 백필 후에도 NULL이 남는지 확인용 (있으면 안 됨 — 있다면 위 UPDATE 전에 원인 파악 필요)
-- SELECT COUNT(*) FROM AttendanceLog WHERE org_id IS NULL;

ALTER TABLE AttendanceLog
    MODIFY COLUMN org_id INT(11) NOT NULL;

ALTER TABLE AttendanceLog
    ADD CONSTRAINT fk_log_org
        FOREIGN KEY (org_id) REFERENCES Org(id);


-- ---------------------------------------------------------------
-- 3) Device.id  AUTO_INCREMENT 전환 + org FK 추가
--    (현재 Device 테이블 row 0건이라 안전하게 변경 가능)
-- ---------------------------------------------------------------
ALTER TABLE Device
    MODIFY COLUMN id INT(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE Device
    ADD CONSTRAINT fk_device_org
        FOREIGN KEY (org_id) REFERENCES Org(id);


-- ---------------------------------------------------------------
-- 4) AttendanceLog.device_id  신설
--    - 구성원이 재실 인증을 찍은 실제 기기를 기록하기 위한 컬럼
--    - 기존 source(VARCHAR) 자유텍스트와는 별개 (source: 채널 구분 / device_id: 실제 기기 식별)
--    - 기존 813건은 device 연결 정보가 없으므로 NULL 허용
-- ---------------------------------------------------------------
ALTER TABLE AttendanceLog
    ADD COLUMN device_id INT(11) NULL AFTER member_id,
    ADD KEY idx_log_device (device_id),
    ADD CONSTRAINT fk_log_device
        FOREIGN KEY (device_id) REFERENCES Device(id);


-- ---------------------------------------------------------------
-- 검증용 쿼리 (실행 결과만 확인, 스키마 변경 없음)
-- ---------------------------------------------------------------
-- SHOW CREATE TABLE Member;
-- SHOW CREATE TABLE AttendanceLog;
-- SHOW CREATE TABLE Device;
-- SELECT COUNT(*) AS null_org_left FROM AttendanceLog WHERE org_id IS NULL;
