CREATE TABLE AttendanceSession (
    id BIGINT(20) NOT NULL AUTO_INCREMENT,
    member_id BIGINT(20) NOT NULL,
    open_key VARCHAR(1) NULL,
    is_open INT(11) NOT NULL DEFAULT 1,
    start_at DATETIME(6) NOT NULL,
    last_ping_at DATETIME(6) NOT NULL,
    end_at DATETIME(6) NULL,
    close_reason VARCHAR(16) NULL,
    duration_seconds INT(11) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY idx_session_member_id (member_id),
    KEY idx_session_is_open (is_open),
    CONSTRAINT fk_session_member
        FOREIGN KEY (member_id) REFERENCES Member(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
