-- ============================================================================
-- RecSignal - Unix Server Monitoring MVP
-- Oracle Database Schema - Phase 1
-- ============================================================================

-- 1. HOSTS - registered Unix servers
CREATE TABLE recsignal_hosts (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hostname          VARCHAR2(255) NOT NULL UNIQUE,
    ip_address        VARCHAR2(45),
    environment       VARCHAR2(64),
    support_group     VARCHAR2(128),
    is_active         NUMBER(1) DEFAULT 1 CHECK (is_active IN (0, 1)),
    last_seen_at      TIMESTAMP,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_hosts_hostname ON recsignal_hosts(hostname);
CREATE INDEX recsignal_idx_hosts_environment ON recsignal_hosts(environment);
CREATE INDEX recsignal_idx_hosts_is_active ON recsignal_hosts(is_active);

-- 2. METRICS_LATEST - most recent metric snapshot per host
CREATE TABLE recsignal_metrics_latest (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER NOT NULL UNIQUE REFERENCES recsignal_hosts(id),
    cpu_percent       NUMBER(5,2),
    memory_percent    NUMBER(5,2),
    swap_percent      NUMBER(5,2),
    disk_percent_total NUMBER(5,2),
    load_avg_1m       NUMBER(8,4),
    disk_read_bytes_sec  NUMBER(14,2),
    disk_write_bytes_sec NUMBER(14,2),
    disk_read_iops    NUMBER(10,2),
    disk_write_iops   NUMBER(10,2),
    net_bytes_sent_sec NUMBER(14,2),
    net_bytes_recv_sec NUMBER(14,2),
    open_fds          NUMBER(10),
    max_fds           NUMBER(10),
    process_count     NUMBER(10),
    zombie_count      NUMBER(10),
    boot_time         TIMESTAMP,
    status            VARCHAR2(20) DEFAULT 'unknown' CHECK (status IN ('healthy','warning','critical','stale','unknown')),
    last_heartbeat_at TIMESTAMP,
    collected_at      TIMESTAMP,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_ml_host ON recsignal_metrics_latest(host_id);
CREATE INDEX recsignal_idx_ml_status ON recsignal_metrics_latest(status);

-- 3. METRICS_HISTORY - time-series historical metrics
CREATE TABLE recsignal_metrics_history (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER NOT NULL REFERENCES recsignal_hosts(id),
    cpu_percent       NUMBER(5,2),
    memory_percent    NUMBER(5,2),
    swap_percent      NUMBER(5,2),
    disk_percent_total NUMBER(5,2),
    load_avg_1m       NUMBER(8,4),
    disk_read_bytes_sec  NUMBER(14,2),
    disk_write_bytes_sec NUMBER(14,2),
    disk_read_iops    NUMBER(10,2),
    disk_write_iops   NUMBER(10,2),
    net_bytes_sent_sec NUMBER(14,2),
    net_bytes_recv_sec NUMBER(14,2),
    open_fds          NUMBER(10),
    max_fds           NUMBER(10),
    process_count     NUMBER(10),
    zombie_count      NUMBER(10),
    boot_time         TIMESTAMP,
    collected_at      TIMESTAMP NOT NULL,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_mh_host_time ON recsignal_metrics_history(host_id, collected_at DESC);

-- 4. MOUNT_METRICS - per-mount disk/filesystem usage
CREATE TABLE recsignal_mount_metrics (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER NOT NULL REFERENCES recsignal_hosts(id),
    mount_path        VARCHAR2(512) NOT NULL,
    total_gb          NUMBER(14,2),
    used_gb           NUMBER(14,2),
    used_percent      NUMBER(5,2),
    inode_total       NUMBER(14),
    inode_used        NUMBER(14),
    inode_percent     NUMBER(5,2),
    collected_at      TIMESTAMP NOT NULL,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_mm_host_time ON recsignal_mount_metrics(host_id, collected_at DESC);

-- 5. PROCESS_SNAPSHOTS - latest process list per host
CREATE TABLE recsignal_process_snapshots (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER NOT NULL REFERENCES recsignal_hosts(id),
    pid               NUMBER(10) NOT NULL,
    name              VARCHAR2(256) NOT NULL,
    username          VARCHAR2(128),
    cpu_percent       NUMBER(6,1),
    memory_percent    NUMBER(6,1),
    status            VARCHAR2(32),
    collected_at      TIMESTAMP NOT NULL,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_ps_host_time ON recsignal_process_snapshots(host_id, collected_at DESC);

-- 6. ALERT_RULES - configurable alert thresholds
CREATE TABLE recsignal_alert_rules (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rule_name         VARCHAR2(128) NOT NULL,
    metric_name       VARCHAR2(64) NOT NULL,
    operator          VARCHAR2(4) DEFAULT '>' CHECK (operator IN ('>','>=','<','<=')),
    threshold_value   NUMBER(10,2) NOT NULL,
    severity          VARCHAR2(20) NOT NULL CHECK (severity IN ('warning','critical')),
    duration_minutes  NUMBER(6) DEFAULT 0,
    is_active         NUMBER(1) DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

-- Default alert rules
INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('CPU Warning', 'cpu_percent', '>', 85, 'warning');
INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('CPU Critical', 'cpu_percent', '>', 95, 'critical');
INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Memory Warning', 'memory_percent', '>', 85, 'warning');
INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Memory Critical', 'memory_percent', '>', 95, 'critical');
INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Disk Warning', 'disk_percent_total', '>', 85, 'warning');
INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Disk Critical', 'disk_percent_total', '>', 95, 'critical');
INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Mount Warning', 'mount_used_percent', '>', 85, 'warning');
INSERT INTO recsignal_alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Mount Critical', 'mount_used_percent', '>', 95, 'critical');
COMMIT;

-- 6. ALERTS - alert events
CREATE TABLE recsignal_alerts (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER NOT NULL REFERENCES recsignal_hosts(id),
    alert_key         VARCHAR2(512) NOT NULL,
    metric_name       VARCHAR2(64) NOT NULL,
    mount_path        VARCHAR2(512),
    severity          VARCHAR2(20) NOT NULL CHECK (severity IN ('warning','critical')),
    message           VARCHAR2(1000),
    status            VARCHAR2(20) DEFAULT 'OPEN' CHECK (status IN ('OPEN','RESOLVED')),
    triggered_at      TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    resolved_at       TIMESTAMP,
    email_sent        NUMBER(1) DEFAULT 0 CHECK (email_sent IN (0, 1)),
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_alerts_host ON recsignal_alerts(host_id, created_at DESC);
CREATE INDEX recsignal_idx_alerts_key ON recsignal_alerts(alert_key);
CREATE INDEX recsignal_idx_alerts_status ON recsignal_alerts(status);
CREATE INDEX recsignal_idx_alerts_severity ON recsignal_alerts(severity, status);

-- 7. NOTIFICATION_TARGETS - email recipients per support group
CREATE TABLE recsignal_notification_targets (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    support_group     VARCHAR2(128) NOT NULL,
    email_to          VARCHAR2(512) NOT NULL,
    is_active         NUMBER(1) DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

-- Default notification target
INSERT INTO recsignal_notification_targets (support_group, email_to) VALUES ('default', 'ops-team@example.com');
COMMIT;


-- ============================================================================
-- RecSignal - DB Monitor  (Phase 2)
-- Oracle Database Schema
-- ============================================================================

-- 9. DB INSTANCES - registered database instances
CREATE TABLE recsignal_db_instances (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    instance_name     VARCHAR2(255) NOT NULL UNIQUE,
    db_type           VARCHAR2(32)  DEFAULT 'oracle' NOT NULL,
    host              VARCHAR2(255),
    port              NUMBER(5),
    service_name      VARCHAR2(255),
    environment       VARCHAR2(64),
    support_group     VARCHAR2(128),
    status            VARCHAR2(20)  DEFAULT 'unknown',
    is_active         NUMBER(1) DEFAULT 1 CHECK (is_active IN (0, 1)),
    last_seen_at      TIMESTAMP,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_dbi_name ON recsignal_db_instances(instance_name);
CREATE INDEX recsignal_idx_dbi_env ON recsignal_db_instances(environment);

-- 10. TABLESPACE METRICS - per-tablespace usage snapshots
CREATE TABLE recsignal_tablespace_metrics (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    db_instance_id    NUMBER NOT NULL REFERENCES recsignal_db_instances(id),
    tablespace_name   VARCHAR2(128) NOT NULL,
    total_mb          NUMBER(14,2),
    used_mb           NUMBER(14,2),
    free_mb           NUMBER(14,2),
    used_percent      NUMBER(5,2),
    autoextensible    VARCHAR2(3),
    max_mb            NUMBER(14,2),
    status            VARCHAR2(20),
    collected_at      TIMESTAMP,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_ts_inst ON recsignal_tablespace_metrics(db_instance_id);

-- 11. DB SESSION SNAPSHOTS - active/inactive Oracle sessions
CREATE TABLE recsignal_db_sessions (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    db_instance_id    NUMBER NOT NULL REFERENCES recsignal_db_instances(id),
    sid               NUMBER,
    serial_no         NUMBER,
    username          VARCHAR2(128),
    program           VARCHAR2(255),
    machine           VARCHAR2(255),
    status            VARCHAR2(20),
    sql_id            VARCHAR2(64),
    sql_text          CLOB,
    wait_class        VARCHAR2(64),
    wait_event        VARCHAR2(128),
    seconds_in_wait   NUMBER(12,2),
    blocking_session  NUMBER,
    logon_time        TIMESTAMP,
    elapsed_seconds   NUMBER(12,2),
    collected_at      TIMESTAMP,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_sess_inst ON recsignal_db_sessions(db_instance_id);

-- 12. DB PERFORMANCE METRICS - instance-level Oracle stats
CREATE TABLE recsignal_db_performance (
    id                     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    db_instance_id         NUMBER NOT NULL REFERENCES recsignal_db_instances(id),
    buffer_cache_hit_ratio NUMBER(5,2),
    library_cache_hit_ratio NUMBER(5,2),
    parse_count_total      NUMBER,
    hard_parse_count       NUMBER,
    execute_count          NUMBER,
    user_commits           NUMBER,
    user_rollbacks         NUMBER,
    physical_reads         NUMBER,
    physical_writes        NUMBER,
    redo_size              NUMBER,
    sga_total_mb           NUMBER(14,2),
    pga_total_mb           NUMBER(14,2),
    active_sessions        NUMBER,
    inactive_sessions      NUMBER,
    total_sessions         NUMBER,
    max_sessions           NUMBER,
    db_uptime_seconds      NUMBER,
    collected_at           TIMESTAMP,
    created_at             TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_perf_inst ON recsignal_db_performance(db_instance_id);

-- 13. DB SLOW QUERIES - top resource-consuming SQL
CREATE TABLE recsignal_db_slow_queries (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    db_instance_id    NUMBER NOT NULL REFERENCES recsignal_db_instances(id),
    sql_id            VARCHAR2(64),
    sql_text          CLOB,
    username          VARCHAR2(128),
    elapsed_seconds   NUMBER(14,2),
    cpu_seconds       NUMBER(14,2),
    buffer_gets       NUMBER,
    disk_reads        NUMBER,
    rows_processed    NUMBER,
    executions        NUMBER,
    plan_hash_value   VARCHAR2(64),
    collected_at      TIMESTAMP,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_sq_inst ON recsignal_db_slow_queries(db_instance_id);
CREATE INDEX recsignal_idx_sq_elapsed ON recsignal_db_slow_queries(elapsed_seconds DESC);


-- ============================================================================
-- Phase 3: APM (Application Performance Monitoring)
-- ============================================================================

-- 14. BUSINESS TRANSACTIONS
CREATE TABLE recsignal_business_transactions (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER,
    app_name          VARCHAR2(255) NOT NULL,
    endpoint          VARCHAR2(512) NOT NULL,
    method            VARCHAR2(10) NOT NULL,
    status_code       NUMBER NOT NULL,
    response_time_ms  NUMBER NOT NULL,
    is_error          NUMBER DEFAULT 0,
    error_message     CLOB,
    trace_id          VARCHAR2(64),
    user_id           VARCHAR2(255),
    collected_at      TIMESTAMP NOT NULL,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_bt_app ON recsignal_business_transactions(app_name);
CREATE INDEX recsignal_idx_bt_app_collected ON recsignal_business_transactions(app_name, collected_at);
CREATE INDEX recsignal_idx_bt_trace ON recsignal_business_transactions(trace_id);

-- 15. TRACES
CREATE TABLE recsignal_traces (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trace_id          VARCHAR2(64) NOT NULL UNIQUE,
    root_service      VARCHAR2(255) NOT NULL,
    root_endpoint     VARCHAR2(512),
    root_method       VARCHAR2(10),
    status_code       NUMBER,
    total_duration_ms NUMBER NOT NULL,
    span_count        NUMBER DEFAULT 1,
    has_error         NUMBER DEFAULT 0,
    started_at        TIMESTAMP NOT NULL,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_trace_svc ON recsignal_traces(root_service, started_at);

-- 16. SPANS
CREATE TABLE recsignal_spans (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trace_id          VARCHAR2(64) NOT NULL,
    span_id           VARCHAR2(64) NOT NULL UNIQUE,
    parent_span_id    VARCHAR2(64),
    service_name      VARCHAR2(255) NOT NULL,
    operation_name    VARCHAR2(512) NOT NULL,
    span_kind         VARCHAR2(20) DEFAULT 'internal',
    status            VARCHAR2(20) DEFAULT 'ok',
    duration_ms       NUMBER NOT NULL,
    started_at        TIMESTAMP NOT NULL,
    attributes        CLOB,
    events            CLOB,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_span_trace ON recsignal_spans(trace_id);
CREATE INDEX recsignal_idx_span_trace_parent ON recsignal_spans(trace_id, parent_span_id);

-- 17. METRIC BASELINES
CREATE TABLE recsignal_metric_baselines (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER NOT NULL,
    metric_name       VARCHAR2(64) NOT NULL,
    mean              NUMBER NOT NULL,
    stddev            NUMBER NOT NULL,
    min_val           NUMBER NOT NULL,
    max_val           NUMBER NOT NULL,
    sample_count      NUMBER NOT NULL,
    window_hours      NUMBER DEFAULT 24,
    computed_at       TIMESTAMP NOT NULL,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_uq_baseline UNIQUE (host_id, metric_name)
);

-- 18. ANOMALIES
CREATE TABLE recsignal_anomalies (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER NOT NULL,
    metric_name       VARCHAR2(64) NOT NULL,
    observed_value    NUMBER NOT NULL,
    baseline_mean     NUMBER NOT NULL,
    baseline_stddev   NUMBER NOT NULL,
    deviation_sigma   NUMBER NOT NULL,
    severity          VARCHAR2(20) NOT NULL,
    status            VARCHAR2(20) DEFAULT 'OPEN',
    detected_at       TIMESTAMP NOT NULL,
    resolved_at       TIMESTAMP,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_anomaly_host ON recsignal_anomalies(host_id);
CREATE INDEX recsignal_idx_anomaly_status ON recsignal_anomalies(host_id, status);

-- 19. LOG ENTRIES
CREATE TABLE recsignal_logs (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER NOT NULL,
    hostname          VARCHAR2(255) NOT NULL,
    source            VARCHAR2(255) NOT NULL,
    level             VARCHAR2(20) NOT NULL,
    message           CLOB NOT NULL,
    trace_id          VARCHAR2(64),
    logged_at         TIMESTAMP NOT NULL,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_log_host ON recsignal_logs(host_id, logged_at);
CREATE INDEX recsignal_idx_log_level ON recsignal_logs(level, logged_at);
CREATE INDEX recsignal_idx_log_trace ON recsignal_logs(trace_id);

-- 20. SERVICE NODES (topology)
CREATE TABLE recsignal_service_nodes (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_name      VARCHAR2(255) NOT NULL UNIQUE,
    service_type      VARCHAR2(50) DEFAULT 'service',
    host_id           NUMBER,
    status            VARCHAR2(20) DEFAULT 'healthy',
    avg_response_time_ms NUMBER,
    request_rate      NUMBER,
    error_rate        NUMBER,
    last_seen_at      TIMESTAMP,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

-- 21. SERVICE DEPENDENCIES (topology edges)
CREATE TABLE recsignal_service_dependencies (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_service    VARCHAR2(255) NOT NULL,
    target_service    VARCHAR2(255) NOT NULL,
    call_count        NUMBER DEFAULT 0,
    error_count       NUMBER DEFAULT 0,
    avg_duration_ms   NUMBER,
    last_seen_at      TIMESTAMP NOT NULL,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT recsignal_uq_svc_dep UNIQUE (source_service, target_service)
);

-- 22. DIAGNOSTIC SNAPSHOTS
CREATE TABLE recsignal_diagnostic_snapshots (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER,
    app_name          VARCHAR2(255) NOT NULL,
    snapshot_type     VARCHAR2(50) NOT NULL,
    duration_seconds  NUMBER,
    top_functions     CLOB,
    memory_summary    CLOB,
    thread_dump       CLOB,
    triggered_by      VARCHAR2(255),
    collected_at      TIMESTAMP NOT NULL,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_diag_app ON recsignal_diagnostic_snapshots(app_name);
CREATE INDEX recsignal_idx_diag_host ON recsignal_diagnostic_snapshots(host_id);
