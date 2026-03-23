-- ============================================================
-- RecSignal Oracle DDL - All Tables
-- Run in order (parent tables first, then FK-dependent tables)
-- ============================================================

-- 1. HOSTS (no FK dependencies)
CREATE TABLE hosts (
    id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hostname      VARCHAR2(255)  NOT NULL UNIQUE,
    ip_address    VARCHAR2(45),
    environment   VARCHAR2(64),
    support_group VARCHAR2(128),
    is_active     NUMBER(1)      DEFAULT 1 NOT NULL,
    last_seen_at  TIMESTAMP,
    created_at    TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at    TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL
);

-- 2. ALERT_RULES (no FK dependencies)
CREATE TABLE alert_rules (
    id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rule_name       VARCHAR2(128)  NOT NULL,
    metric_name     VARCHAR2(64)   NOT NULL,
    operator        VARCHAR2(4)    DEFAULT '>' NOT NULL,
    threshold_value NUMBER(10,2)   NOT NULL,
    severity        VARCHAR2(20)   NOT NULL,
    duration_minutes NUMBER(10)    DEFAULT 0 NOT NULL,
    is_active       NUMBER(1)      DEFAULT 1 NOT NULL,
    created_at      TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at      TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL
);

-- 3. NOTIFICATION_TARGETS (no FK dependencies)
CREATE TABLE notification_targets (
    id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    support_group VARCHAR2(128)  NOT NULL,
    email_to      VARCHAR2(512)  NOT NULL,
    is_active     NUMBER(1)      DEFAULT 1 NOT NULL,
    created_at    TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at    TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL
);

-- 4. METRICS_LATEST (FK → hosts)
CREATE TABLE metrics_latest (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER         NOT NULL UNIQUE,
    cpu_percent       NUMBER(5,2),
    memory_percent    NUMBER(5,2),
    disk_percent_total NUMBER(5,2),
    load_avg_1m       NUMBER(8,4),
    status            VARCHAR2(20)   DEFAULT 'unknown' NOT NULL,
    last_heartbeat_at TIMESTAMP,
    collected_at      TIMESTAMP,
    created_at        TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at        TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT fk_ml_host FOREIGN KEY (host_id) REFERENCES hosts (id)
);

-- 5. METRICS_HISTORY (FK → hosts)
CREATE TABLE metrics_history (
    id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id           NUMBER         NOT NULL,
    cpu_percent       NUMBER(5,2),
    memory_percent    NUMBER(5,2),
    disk_percent_total NUMBER(5,2),
    load_avg_1m       NUMBER(8,4),
    collected_at      TIMESTAMP      NOT NULL,
    created_at        TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT fk_mh_host FOREIGN KEY (host_id) REFERENCES hosts (id)
);

CREATE INDEX idx_mh_host_time ON metrics_history (host_id, collected_at DESC);

-- 6. MOUNT_METRICS (FK → hosts)
CREATE TABLE mount_metrics (
    id           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id      NUMBER         NOT NULL,
    mount_path   VARCHAR2(512)  NOT NULL,
    total_gb     NUMBER(14,2),
    used_gb      NUMBER(14,2),
    used_percent NUMBER(5,2),
    collected_at TIMESTAMP      NOT NULL,
    created_at   TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT fk_mm_host FOREIGN KEY (host_id) REFERENCES hosts (id)
);

CREATE INDEX idx_mm_host_time ON mount_metrics (host_id, collected_at DESC);

-- 7. ALERTS (FK → hosts)
CREATE TABLE alerts (
    id           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id      NUMBER         NOT NULL,
    alert_key    VARCHAR2(512)  NOT NULL,
    metric_name  VARCHAR2(64)   NOT NULL,
    mount_path   VARCHAR2(512),
    severity     VARCHAR2(20)   NOT NULL,
    message      VARCHAR2(1000),
    status       VARCHAR2(20)   DEFAULT 'OPEN' NOT NULL,
    triggered_at TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
    resolved_at  TIMESTAMP,
    email_sent   NUMBER(1)      DEFAULT 0 NOT NULL,
    created_at   TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at   TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT fk_alert_host FOREIGN KEY (host_id) REFERENCES hosts (id)
);

CREATE INDEX idx_alerts_host_time ON alerts (host_id, created_at DESC);
CREATE INDEX idx_alerts_key ON alerts (alert_key);
CREATE INDEX idx_alerts_status ON alerts (status);

-- ============================================================
-- Seed Data (default alert rules + notification target)
-- ============================================================

INSERT INTO alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('CPU Warning', 'cpu_percent', '>', 85, 'WARNING');
INSERT INTO alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('CPU Critical', 'cpu_percent', '>', 95, 'CRITICAL');
INSERT INTO alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Memory Warning', 'memory_percent', '>', 85, 'WARNING');
INSERT INTO alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Memory Critical', 'memory_percent', '>', 95, 'CRITICAL');
INSERT INTO alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Disk Warning', 'disk_percent_total', '>', 85, 'WARNING');
INSERT INTO alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Disk Critical', 'disk_percent_total', '>', 95, 'CRITICAL');
INSERT INTO alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Mount Warning', 'mount_used_percent', '>', 85, 'WARNING');
INSERT INTO alert_rules (rule_name, metric_name, operator, threshold_value, severity) VALUES ('Mount Critical', 'mount_used_percent', '>', 95, 'CRITICAL');

INSERT INTO notification_targets (support_group, email_to) VALUES ('default', 'ops-team@example.com');

COMMIT;
