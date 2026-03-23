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
    disk_percent_total NUMBER(5,2),
    load_avg_1m       NUMBER(8,4),
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
    disk_percent_total NUMBER(5,2),
    load_avg_1m       NUMBER(8,4),
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
    collected_at      TIMESTAMP NOT NULL,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX recsignal_idx_mm_host_time ON recsignal_mount_metrics(host_id, collected_at DESC);

-- 5. ALERT_RULES - configurable alert thresholds
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
