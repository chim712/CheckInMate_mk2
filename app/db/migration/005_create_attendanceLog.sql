CREATE TABLE AttendanceLog (
    id BIGINT(20) NOT NULL AUTO_INCREMENT,
    org_id INT(11) NULL,
    member_id BIGINT(20) NOT NULL,
    event_time DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    event_type VARCHAR(16) NOT NULL,
    source VARCHAR(32) NULL,
    meta TEXT NULL,
    PRIMARY KEY (id),
    KEY idx_log_member_id (member_id),
    KEY idx_log_org_id (org_id),
    CONSTRAINT fk_log_member
        FOREIGN KEY (member_id) REFERENCES Member(id),
    CONSTRAINT fk_log_org
        FOREIGN KEY (org_id) REFERENCES Org(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
