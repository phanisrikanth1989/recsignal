-- ==============================================================================
-- RecSignal — Oracle DDL for UAT
-- ==============================================================================
-- Run as: sqlplus recsignal_owner/<password>@<host>:1521/<service>
-- Or via SQL Developer connected to the recsignal schema.
--
-- Execution order matters — parent tables first, FK-dependent tables after.
-- ==============================================================================

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  1. HOSTS (no FK dependencies)                                             ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_hosts (
    id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hostname        VARCHAR2(255)   NOT NULL,
    ip_address      VARCHAR2(45),
    environment     VARCHAR2(64),
    support_group   VARCHAR2(128),
    is_active       NUMBER(1)       DEFAULT 1 NOT NULL,
    last_seen_at    TIMESTAMP,
    created_at      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_uq_hosts_hostname UNIQUE (hostname)
);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  2. ALERT RULES (no FK dependencies)                                       ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_alert_rules (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rule_name         VARCHAR2(128)   NOT NULL,
    metric_name       VARCHAR2(64)    NOT NULL,
    operator          VARCHAR2(4)     DEFAULT '>' NOT NULL,
    threshold_value   NUMBER(10,2)    NOT NULL,
    severity          VARCHAR2(20)    NOT NULL,
    duration_minutes  NUMBER(10)      DEFAULT 0 NOT NULL,
    is_active         NUMBER(1)       DEFAULT 1 NOT NULL,
    created_at        TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at        TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL
);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  3. NOTIFICATION TARGETS (no FK dependencies)                              ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_notification_targets (
    id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    support_group   VARCHAR2(128)   NOT NULL,
    email_to        VARCHAR2(512)   NOT NULL,
    is_active       NUMBER(1)       DEFAULT 1 NOT NULL,
    created_at      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL
);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  4. METRICS LATEST (FK → hosts)  — One row per host (latest snapshot)      ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_metrics_latest (
    id                   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id              NUMBER          NOT NULL,
    cpu_percent          NUMBER(5,2),
    memory_percent       NUMBER(5,2),
    swap_percent         NUMBER(5,2),
    disk_percent_total   NUMBER(5,2),
    load_avg_1m          NUMBER(8,4),
    disk_read_bytes_sec  NUMBER(14,2),
    disk_write_bytes_sec NUMBER(14,2),
    disk_read_iops       NUMBER(10,2),
    disk_write_iops      NUMBER(10,2),
    net_bytes_sent_sec   NUMBER(14,2),
    net_bytes_recv_sec   NUMBER(14,2),
    open_fds             NUMBER(10),
    max_fds              NUMBER(10),
    process_count        NUMBER(10),
    zombie_count         NUMBER(10),
    boot_time            TIMESTAMP,
    status               VARCHAR2(20)    DEFAULT 'unknown' NOT NULL,
    last_heartbeat_at    TIMESTAMP,
    collected_at         TIMESTAMP,
    created_at           TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at           TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_uq_ml_host   UNIQUE (host_id),
    CONSTRAINT recsignal_fk_ml_host   FOREIGN KEY (host_id)
        REFERENCES recsignal_hosts (id)
);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  5. METRICS HISTORY (FK → hosts)  — Time-series, one row per collection    ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_metrics_history (
    id                   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id              NUMBER          NOT NULL,
    cpu_percent          NUMBER(5,2),
    memory_percent       NUMBER(5,2),
    swap_percent         NUMBER(5,2),
    disk_percent_total   NUMBER(5,2),
    load_avg_1m          NUMBER(8,4),
    disk_read_bytes_sec  NUMBER(14,2),
    disk_write_bytes_sec NUMBER(14,2),
    disk_read_iops       NUMBER(10,2),
    disk_write_iops      NUMBER(10,2),
    net_bytes_sent_sec   NUMBER(14,2),
    net_bytes_recv_sec   NUMBER(14,2),
    open_fds             NUMBER(10),
    max_fds              NUMBER(10),
    process_count        NUMBER(10),
    zombie_count         NUMBER(10),
    boot_time            TIMESTAMP,
    collected_at         TIMESTAMP       NOT NULL,
    created_at           TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_fk_mh_host   FOREIGN KEY (host_id)
        REFERENCES recsignal_hosts (id)
);

CREATE INDEX recsignal_idx_mh_host_time ON recsignal_metrics_history (host_id, collected_at DESC);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  6. MOUNT METRICS (FK → hosts)                                             ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_mount_metrics (
    id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id         NUMBER          NOT NULL,
    mount_path      VARCHAR2(512)   NOT NULL,
    total_gb        NUMBER(14,2),
    used_gb         NUMBER(14,2),
    used_percent    NUMBER(5,2),
    inode_total     NUMBER(14),
    inode_used      NUMBER(14),
    inode_percent   NUMBER(5,2),
    collected_at    TIMESTAMP       NOT NULL,
    created_at      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_fk_mm_host   FOREIGN KEY (host_id)
        REFERENCES recsignal_hosts (id)
);

CREATE INDEX recsignal_idx_mm_host_time ON recsignal_mount_metrics (host_id, collected_at DESC);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  7. PROCESS SNAPSHOTS (FK → hosts)                                         ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_process_snapshots (
    id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id         NUMBER          NOT NULL,
    pid             NUMBER(10)      NOT NULL,
    name            VARCHAR2(256)   NOT NULL,
    username        VARCHAR2(128),
    cpu_percent     NUMBER(6,1),
    memory_percent  NUMBER(6,1),
    status          VARCHAR2(32),
    collected_at    TIMESTAMP       NOT NULL,
    created_at      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_fk_ps_host   FOREIGN KEY (host_id)
        REFERENCES recsignal_hosts (id)
);

CREATE INDEX recsignal_idx_ps_host_time ON recsignal_process_snapshots (host_id, collected_at DESC);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  8. ALERTS (FK → hosts)                                                    ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_alerts (
    id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id         NUMBER          NOT NULL,
    alert_key       VARCHAR2(512)   NOT NULL,
    metric_name     VARCHAR2(64)    NOT NULL,
    mount_path      VARCHAR2(512),
    severity        VARCHAR2(20)    NOT NULL,
    message         VARCHAR2(1000),
    status          VARCHAR2(20)    DEFAULT 'OPEN' NOT NULL,
    triggered_at    TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    resolved_at     TIMESTAMP,
    email_sent      NUMBER(1)       DEFAULT 0 NOT NULL,
    created_at      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_fk_alert_host  FOREIGN KEY (host_id)
        REFERENCES recsignal_hosts (id)
);

CREATE INDEX recsignal_idx_alerts_host_time ON recsignal_alerts (host_id, created_at DESC);
CREATE INDEX recsignal_idx_alerts_key       ON recsignal_alerts (alert_key);
CREATE INDEX recsignal_idx_alerts_status    ON recsignal_alerts (status);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  9. DB INSTANCES (no FK dependencies)                                      ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_db_instances (
    id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    instance_name   VARCHAR2(255)   NOT NULL,
    db_type         VARCHAR2(32)    DEFAULT 'oracle' NOT NULL,
    host            VARCHAR2(255),
    port            NUMBER(10),
    service_name    VARCHAR2(255),
    environment     VARCHAR2(64),
    support_group   VARCHAR2(128),
    status          VARCHAR2(20)    DEFAULT 'unknown',
    is_active       NUMBER(1)       DEFAULT 1,
    last_seen_at    TIMESTAMP,
    created_at      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_uq_db_instance_name UNIQUE (instance_name)
);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  10. TABLESPACE METRICS (FK → db_instances)                                ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_tablespace_metrics (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    db_instance_id    NUMBER          NOT NULL,
    tablespace_name   VARCHAR2(128)   NOT NULL,
    total_mb          NUMBER(14,2),
    used_mb           NUMBER(14,2),
    free_mb           NUMBER(14,2),
    used_percent      NUMBER(5,2),
    autoextensible    VARCHAR2(3),
    max_mb            NUMBER(14,2),
    status            VARCHAR2(20),
    collected_at      TIMESTAMP,
    created_at        TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_fk_ts_db FOREIGN KEY (db_instance_id)
        REFERENCES recsignal_db_instances (id)
);

CREATE INDEX recsignal_idx_ts_db_time ON recsignal_tablespace_metrics (db_instance_id, collected_at DESC);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  11. DB SESSIONS (FK → db_instances)                                       ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_db_sessions (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    db_instance_id    NUMBER          NOT NULL,
    sid               NUMBER(10),
    serial_no         NUMBER(10),
    username          VARCHAR2(128),
    program           VARCHAR2(255),
    machine           VARCHAR2(255),
    status            VARCHAR2(20),
    sql_id            VARCHAR2(64),
    sql_text          CLOB,
    wait_class        VARCHAR2(64),
    wait_event        VARCHAR2(128),
    seconds_in_wait   NUMBER(12,2),
    blocking_session  NUMBER(10),
    logon_time        TIMESTAMP,
    elapsed_seconds   NUMBER(12,2),
    collected_at      TIMESTAMP,
    created_at        TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_fk_sess_db FOREIGN KEY (db_instance_id)
        REFERENCES recsignal_db_instances (id)
);

CREATE INDEX recsignal_idx_sess_db_time ON recsignal_db_sessions (db_instance_id, collected_at DESC);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  12. DB PERFORMANCE METRICS (FK → db_instances)                            ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_db_performance (
    id                      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    db_instance_id          NUMBER          NOT NULL,
    buffer_cache_hit_ratio  NUMBER(5,2),
    library_cache_hit_ratio NUMBER(5,2),
    parse_count_total       NUMBER(10),
    hard_parse_count        NUMBER(10),
    execute_count           NUMBER(10),
    user_commits            NUMBER(10),
    user_rollbacks          NUMBER(10),
    physical_reads          NUMBER(10),
    physical_writes         NUMBER(10),
    redo_size               NUMBER(10),
    sga_total_mb            NUMBER(14,2),
    pga_total_mb            NUMBER(14,2),
    active_sessions         NUMBER(10),
    inactive_sessions       NUMBER(10),
    total_sessions          NUMBER(10),
    max_sessions            NUMBER(10),
    db_uptime_seconds       NUMBER(10),
    collected_at            TIMESTAMP,
    created_at              TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_fk_perf_db FOREIGN KEY (db_instance_id)
        REFERENCES recsignal_db_instances (id)
);

CREATE INDEX recsignal_idx_perf_db_time ON recsignal_db_performance (db_instance_id, collected_at DESC);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  13. DB SLOW QUERIES (FK → db_instances)                                   ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝
CREATE TABLE recsignal_db_slow_queries (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    db_instance_id    NUMBER          NOT NULL,
    sql_id            VARCHAR2(64),
    sql_text          CLOB,
    username          VARCHAR2(128),
    elapsed_seconds   NUMBER(14,2),
    cpu_seconds       NUMBER(14,2),
    buffer_gets       NUMBER(10),
    disk_reads        NUMBER(10),
    rows_processed    NUMBER(10),
    executions        NUMBER(10),
    plan_hash_value   VARCHAR2(64),
    collected_at      TIMESTAMP,
    created_at        TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_fk_sq_db FOREIGN KEY (db_instance_id)
        REFERENCES recsignal_db_instances (id)
);

CREATE INDEX recsignal_idx_sq_db_time ON recsignal_db_slow_queries (db_instance_id, collected_at DESC);

-- ╔══════════════════════════════════════════════════════════════════════════════╗
-- ║  SEED DATA — Default Alert Rules & Notification Target                     ║
-- ╚══════════════════════════════════════════════════════════════════════════════╝

INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity)
VALUES ('CPU Warning', 'cpu_percent', '>', 85, 'WARNING');

INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity)
VALUES ('CPU Critical', 'cpu_percent', '>', 95, 'CRITICAL');

INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity)
VALUES ('Memory Warning', 'memory_percent', '>', 85, 'WARNING');

INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity)
VALUES ('Memory Critical', 'memory_percent', '>', 95, 'CRITICAL');

INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity)
VALUES ('Disk Warning', 'disk_percent_total', '>', 85, 'WARNING');

INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity)
VALUES ('Disk Critical', 'disk_percent_total', '>', 95, 'CRITICAL');

INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity)
VALUES ('Mount Warning', 'mount_used_percent', '>', 85, 'WARNING');

INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity)
VALUES ('Mount Critical', 'mount_used_percent', '>', 95, 'CRITICAL');

INSERT INTO recsignal_notification_targets (support_group, email_to)
VALUES ('default', 'ops-team@example.com');

COMMIT;

-- ==============================================================================
-- VERIFICATION — Run after DDL to confirm all objects created
-- ==============================================================================
SELECT table_name FROM user_tables WHERE table_name LIKE 'RECSIGNAL_%' ORDER BY table_name;
SELECT index_name, table_name FROM user_indexes WHERE index_name LIKE 'RECSIGNAL_%' ORDER BY table_name;
