"""
RecSignal – Comprehensive Data Seeder
Populates SQLite with realistic dummy data for all modules:
  • Server Monitoring (hosts, metrics, mounts, processes, alerts)
  • DB Monitoring (instances, tablespaces, sessions, slow queries, performance)
  • APM (transactions, traces/spans, baselines, anomalies, logs, topology, diagnostics)

Usage:
    cd backend
    python seed_data.py          # seed once
    python seed_data.py --reset  # drop + recreate tables, then seed
"""

from __future__ import annotations

import json
import random
import sys
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.database import engine
from app.db.base import Base
from app.models import *  # noqa: F401,F403  – registers all models

# ── Helpers ──────────────────────────────────────────────────────────

now = datetime.now(tz=None)  # UTC-naive for SQLite compatibility

def ts(minutes_ago: int = 0) -> datetime:
    return now - timedelta(minutes=minutes_ago)

def rand_float(lo: float, hi: float, decimals: int = 2) -> float:
    return round(random.uniform(lo, hi), decimals)

def uid() -> str:
    return uuid.uuid4().hex[:16]


# ── Server Monitoring ────────────────────────────────────────────────

HOSTS = [
    {"hostname": "web-prod-01", "ip_address": "10.1.1.10", "environment": "production", "support_group": "web-team"},
    {"hostname": "web-prod-02", "ip_address": "10.1.1.11", "environment": "production", "support_group": "web-team"},
    {"hostname": "api-prod-01", "ip_address": "10.1.2.10", "environment": "production", "support_group": "api-team"},
    {"hostname": "api-prod-02", "ip_address": "10.1.2.11", "environment": "production", "support_group": "api-team"},
    {"hostname": "db-prod-01", "ip_address": "10.1.3.10", "environment": "production", "support_group": "dba-team"},
    {"hostname": "worker-prod-01", "ip_address": "10.1.4.10", "environment": "production", "support_group": "platform-team"},
    {"hostname": "cache-prod-01", "ip_address": "10.1.5.10", "environment": "production", "support_group": "platform-team"},
    {"hostname": "web-stg-01", "ip_address": "10.2.1.10", "environment": "staging", "support_group": "web-team"},
    {"hostname": "api-stg-01", "ip_address": "10.2.2.10", "environment": "staging", "support_group": "api-team"},
    {"hostname": "db-stg-01", "ip_address": "10.2.3.10", "environment": "staging", "support_group": "dba-team"},
]

MOUNTS = ["/", "/var", "/tmp", "/opt/app", "/data"]

PROCESSES = [
    ("python", "appuser"), ("java", "appuser"), ("nginx", "root"),
    ("node", "appuser"), ("postgres", "postgres"), ("redis-server", "redis"),
    ("crond", "root"), ("sshd", "root"), ("rsyslogd", "root"),
]


def seed_hosts_and_metrics(s: Session) -> list:
    from app.models.host import Host
    from app.models.metrics_latest import MetricsLatest
    from app.models.metrics_history import MetricsHistory
    from app.models.mount_metric import MountMetric
    from app.models.process_snapshot import ProcessSnapshot

    hosts = []
    for h_data in HOSTS:
        host = Host(**h_data, is_active=1, last_seen_at=ts(random.randint(0, 3)))
        s.add(host)
        s.flush()
        hosts.append(host)

        # Status for "latest"
        cpu = rand_float(5, 92)
        mem = rand_float(20, 88)
        swap = rand_float(0, 30)
        disk = rand_float(30, 85)
        status = "healthy"
        if cpu > 85 or mem > 85:
            status = "warning"
        if cpu > 95 or mem > 95:
            status = "critical"

        latest = MetricsLatest(
            host_id=host.id,
            cpu_percent=cpu, memory_percent=mem, swap_percent=swap,
            disk_percent_total=disk, load_avg_1m=rand_float(0.1, 4.0),
            disk_read_bytes_sec=rand_float(100000, 5000000),
            disk_write_bytes_sec=rand_float(50000, 3000000),
            disk_read_iops=rand_float(10, 500),
            disk_write_iops=rand_float(5, 300),
            net_bytes_sent_sec=rand_float(50000, 2000000),
            net_bytes_recv_sec=rand_float(100000, 4000000),
            open_fds=random.randint(200, 3000),
            max_fds=65536,
            process_count=random.randint(80, 350),
            zombie_count=random.randint(0, 3),
            boot_time=ts(random.randint(1440, 43200)),  # 1-30 days ago
            status=status,
            last_heartbeat_at=ts(random.randint(0, 2)),
            collected_at=ts(0),
        )
        s.add(latest)

        # History – 24 hours of 5-min intervals = 288 points
        for i in range(288):
            s.add(MetricsHistory(
                host_id=host.id,
                cpu_percent=rand_float(5, 90),
                memory_percent=rand_float(20, 85),
                swap_percent=rand_float(0, 25),
                disk_percent_total=rand_float(30, 80),
                load_avg_1m=rand_float(0.1, 3.5),
                disk_read_bytes_sec=rand_float(100000, 5000000),
                disk_write_bytes_sec=rand_float(50000, 3000000),
                disk_read_iops=rand_float(10, 500),
                disk_write_iops=rand_float(5, 300),
                net_bytes_sent_sec=rand_float(50000, 2000000),
                net_bytes_recv_sec=rand_float(100000, 4000000),
                open_fds=random.randint(200, 3000),
                max_fds=65536,
                process_count=random.randint(80, 350),
                zombie_count=random.randint(0, 2),
                boot_time=ts(random.randint(1440, 43200)),
                collected_at=ts(i * 5),
            ))

        # Mount metrics
        for mount in MOUNTS:
            total = random.choice([50, 100, 200, 500, 1000])
            used = round(total * rand_float(0.2, 0.85), 2)
            s.add(MountMetric(
                host_id=host.id, mount_path=mount,
                total_gb=total, used_gb=used,
                used_percent=round(used / total * 100, 2),
                inode_total=random.randint(1000000, 10000000),
                inode_used=random.randint(50000, 500000),
                inode_percent=rand_float(1, 20),
                collected_at=ts(0),
            ))

        # Process snapshots (top 10 for each host)
        for pid_offset, (pname, puser) in enumerate(PROCESSES):
            s.add(ProcessSnapshot(
                host_id=host.id, pid=random.randint(1000, 50000),
                name=pname, username=puser,
                cpu_percent=rand_float(0, 25),
                memory_percent=rand_float(0.1, 8),
                status="running",
                collected_at=ts(0),
            ))

    return hosts


def seed_alert_rules_and_alerts(s: Session, hosts: list):
    from app.models.alert_rule import AlertRule
    from app.models.alert import Alert
    from app.models.notification_target import NotificationTarget

    # Alert rules (if none exist already)
    if s.query(AlertRule).count() == 0:
        rules = [
            AlertRule(rule_name="CPU Warning", metric_name="cpu_percent", operator=">", threshold_value=85, severity="warning"),
            AlertRule(rule_name="CPU Critical", metric_name="cpu_percent", operator=">", threshold_value=95, severity="critical"),
            AlertRule(rule_name="Memory Warning", metric_name="memory_percent", operator=">", threshold_value=85, severity="warning"),
            AlertRule(rule_name="Memory Critical", metric_name="memory_percent", operator=">", threshold_value=95, severity="critical"),
            AlertRule(rule_name="Disk Warning", metric_name="disk_percent_total", operator=">", threshold_value=85, severity="warning"),
            AlertRule(rule_name="Disk Critical", metric_name="disk_percent_total", operator=">", threshold_value=95, severity="critical"),
            AlertRule(rule_name="Mount Warning", metric_name="mount_used_percent", operator=">", threshold_value=85, severity="warning"),
            AlertRule(rule_name="Mount Critical", metric_name="mount_used_percent", operator=">", threshold_value=95, severity="critical"),
        ]
        s.add_all(rules)

    # Notification target
    if s.query(NotificationTarget).count() == 0:
        s.add(NotificationTarget(support_group="default", email_to="ops-team@example.com"))

    # Sample alerts (mix of open and resolved)
    alert_templates = [
        ("cpu_percent", "warning", "CPU usage exceeded 85%"),
        ("cpu_percent", "critical", "CPU usage exceeded 95%"),
        ("memory_percent", "warning", "Memory usage exceeded 85%"),
        ("disk_percent_total", "warning", "Disk usage exceeded 85%"),
        ("mount_used_percent", "warning", "/data mount usage exceeded 85%"),
    ]
    for host in hosts[:6]:
        for metric, severity, message in random.sample(alert_templates, k=random.randint(1, 3)):
            is_resolved = random.random() < 0.4
            triggered = ts(random.randint(5, 1440))
            s.add(Alert(
                host_id=host.id,
                alert_key=f"{host.id}:{metric}",
                metric_name=metric,
                mount_path="/data" if "mount" in metric else None,
                severity=severity,
                message=message,
                status="RESOLVED" if is_resolved else "OPEN",
                triggered_at=triggered,
                resolved_at=triggered + timedelta(minutes=random.randint(10, 120)) if is_resolved else None,
                email_sent=1 if is_resolved else 0,
            ))


# ── DB Monitoring ────────────────────────────────────────────────────

DB_INSTANCES = [
    {"instance_name": "ORCL_PROD", "db_type": "oracle", "host": "db-prod-01", "port": 1521, "service_name": "orcl_prod.example.com", "environment": "production"},
    {"instance_name": "ORCL_STG", "db_type": "oracle", "host": "db-stg-01", "port": 1521, "service_name": "orcl_stg.example.com", "environment": "staging"},
    {"instance_name": "ORCL_RPT", "db_type": "oracle", "host": "db-prod-01", "port": 1522, "service_name": "orcl_rpt.example.com", "environment": "production"},
]

TABLESPACES = ["SYSTEM", "SYSAUX", "USERS", "UNDOTBS1", "TEMP", "APP_DATA", "APP_INDEX"]

SLOW_QUERIES = [
    "SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.created_at > :1",
    "UPDATE inventory SET quantity = quantity - :1 WHERE product_id = :2 AND warehouse_id = :3",
    "SELECT /*+ FULL(t) */ * FROM transactions t WHERE t.amount > :1 ORDER BY t.created_at DESC",
    "INSERT INTO audit_log (user_id, action, details, created_at) SELECT :1, :2, :3, SYSDATE FROM dual",
    "SELECT COUNT(*) FROM sessions s WHERE s.status = 'ACTIVE' AND s.last_activity > SYSDATE - :1",
]


def seed_db_monitoring(s: Session):
    from app.models.db_instance import DbInstance
    from app.models.db_performance_metric import DbPerformanceMetric
    from app.models.db_session_snapshot import DbSessionSnapshot
    from app.models.db_slow_query import DbSlowQuery
    from app.models.tablespace_metric import TablespaceMetric

    for inst_data in DB_INSTANCES:
        status = random.choice(["up", "up", "up", "degraded"])
        inst = DbInstance(**inst_data, status=status, is_active=1, last_seen_at=ts(random.randint(0, 5)))
        s.add(inst)
        s.flush()

        # Performance metrics
        s.add(DbPerformanceMetric(
            db_instance_id=inst.id,
            buffer_cache_hit_ratio=rand_float(94, 99.9),
            library_cache_hit_ratio=rand_float(95, 99.9),
            parse_count_total=random.randint(10000, 200000),
            hard_parse_count=random.randint(100, 5000),
            execute_count=random.randint(50000, 500000),
            user_commits=random.randint(1000, 50000),
            user_rollbacks=random.randint(10, 500),
            physical_reads=random.randint(5000, 100000),
            physical_writes=random.randint(1000, 30000),
            redo_size=random.randint(1000000, 50000000),
            sga_total_mb=random.choice([2048, 4096, 8192]),
            pga_total_mb=random.choice([512, 1024, 2048]),
            active_sessions=random.randint(5, 60),
            inactive_sessions=random.randint(20, 100),
            total_sessions=random.randint(40, 200),
            max_sessions=500,
            db_uptime_seconds=random.randint(86400, 2592000),
            collected_at=ts(0),
        ))

        # Tablespace metrics
        for ts_name in TABLESPACES:
            total = random.choice([2048, 4096, 8192, 16384, 32768])
            used_pct = rand_float(15, 88)
            used = round(total * used_pct / 100, 2)
            s.add(TablespaceMetric(
                db_instance_id=inst.id,
                tablespace_name=ts_name,
                total_mb=total, used_mb=used, free_mb=round(total - used, 2),
                used_percent=used_pct,
                autoextensible="YES" if ts_name not in ("TEMP",) else "NO",
                max_mb=total * 2, status="ONLINE",
                collected_at=ts(0),
            ))

        # Sessions
        session_statuses = ["ACTIVE", "ACTIVE", "INACTIVE", "INACTIVE", "INACTIVE"]
        wait_classes = ["CPU", "User I/O", "Application", "Network", "Idle", "Concurrency"]
        for _ in range(random.randint(8, 25)):
            sess_status = random.choice(session_statuses)
            s.add(DbSessionSnapshot(
                db_instance_id=inst.id,
                sid=random.randint(1, 999),
                serial_no=random.randint(10000, 65000),
                username=random.choice(["APP_USER", "REPORT_USER", "SYS", "BATCH_USER", "API_USER"]),
                program=random.choice(["JDBC Thin Client", "sqlplus@db-prod-01", "python3", "java"]),
                machine=random.choice(["app-server-01", "app-server-02", "batch-host-01"]),
                status=sess_status,
                sql_id=uid()[:13] if sess_status == "ACTIVE" else None,
                wait_class=random.choice(wait_classes),
                wait_event=random.choice(["db file sequential read", "log file sync", "SQL*Net message from client", "enq: TX - row lock"]),
                seconds_in_wait=rand_float(0, 300) if sess_status == "ACTIVE" else rand_float(0, 3600),
                logon_time=ts(random.randint(0, 480)),
                elapsed_seconds=rand_float(0, 600),
                collected_at=ts(0),
            ))

        # Slow queries
        for sq_text in random.sample(SLOW_QUERIES, k=random.randint(2, 4)):
            s.add(DbSlowQuery(
                db_instance_id=inst.id,
                sql_id=uid()[:13],
                sql_text=sq_text,
                username=random.choice(["APP_USER", "REPORT_USER", "BATCH_USER"]),
                elapsed_seconds=rand_float(5, 120),
                cpu_seconds=rand_float(1, 60),
                buffer_gets=random.randint(10000, 5000000),
                disk_reads=random.randint(100, 500000),
                rows_processed=random.randint(1, 100000),
                executions=random.randint(1, 1000),
                plan_hash_value=str(random.randint(100000000, 999999999)),
                collected_at=ts(random.randint(0, 60)),
            ))


# ── APM ──────────────────────────────────────────────────────────────

APPS = ["order-service", "payment-service", "inventory-service", "user-service", "notification-service"]
ENDPOINTS = {
    "order-service": [("/api/orders", "POST"), ("/api/orders", "GET"), ("/api/orders/{id}", "GET"), ("/api/orders/{id}/cancel", "PUT")],
    "payment-service": [("/api/payments", "POST"), ("/api/payments/{id}", "GET"), ("/api/refunds", "POST")],
    "inventory-service": [("/api/inventory", "GET"), ("/api/inventory/{sku}", "GET"), ("/api/inventory/reserve", "POST")],
    "user-service": [("/api/users", "GET"), ("/api/users/{id}", "GET"), ("/api/users/login", "POST"), ("/api/users/register", "POST")],
    "notification-service": [("/api/notifications/send", "POST"), ("/api/notifications", "GET")],
}

LOG_MESSAGES = {
    "INFO": [
        "Request processed successfully",
        "Cache hit for key={key}",
        "Connection pool stats: active=5, idle=15",
        "Scheduled job completed in {ms}ms",
        "Health check passed",
    ],
    "WARN": [
        "Slow query detected: {ms}ms",
        "Connection pool exhaustion warning: 90% used",
        "Retry attempt 2/3 for downstream call",
        "Request latency above threshold: p99={ms}ms",
        "Certificate expires in 14 days",
    ],
    "ERROR": [
        "Failed to connect to downstream service: timeout after 5000ms",
        "NullPointerException in OrderProcessor.process()",
        "Database connection refused: max retries exceeded",
        "Payment gateway returned HTTP 503",
        "Unhandled exception in request handler",
    ],
    "DEBUG": [
        "Entering method processOrder(id={id})",
        "SQL: SELECT * FROM orders WHERE id = ?",
        "HTTP response: status=200, body_size=1432",
    ],
}


def seed_business_transactions(s: Session, hosts: list):
    from app.models.business_transaction import BusinessTransaction

    for _ in range(500):
        app = random.choice(APPS)
        endpoint, method = random.choice(ENDPOINTS[app])
        is_error = random.random() < 0.08
        status_code = random.choice([500, 502, 503, 504]) if is_error else random.choice([200, 200, 200, 201, 204])
        s.add(BusinessTransaction(
            host_id=random.choice(hosts[:7]).id,
            app_name=app,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=rand_float(5, 2000) if not is_error else rand_float(1000, 10000),
            is_error=1 if is_error else 0,
            error_message="Internal server error" if is_error else None,
            trace_id=uid(),
            user_id=f"user-{random.randint(1, 200)}",
            collected_at=ts(random.randint(0, 1440)),
        ))


def seed_traces(s: Session):
    from app.models.trace import Trace, Span

    services_chain = [
        ["order-service", "payment-service", "notification-service"],
        ["order-service", "inventory-service"],
        ["user-service", "notification-service"],
        ["order-service", "payment-service", "inventory-service", "notification-service"],
        ["user-service"],
        ["payment-service", "inventory-service"],
    ]

    for _ in range(80):
        trace_id = uuid.uuid4().hex
        chain = random.choice(services_chain)
        root = chain[0]
        endpoint, method = random.choice(ENDPOINTS[root])
        has_error = random.random() < 0.1
        total_dur = rand_float(20, 3000)
        started = ts(random.randint(0, 1440))

        trace = Trace(
            trace_id=trace_id,
            root_service=root,
            root_endpoint=endpoint,
            root_method=method,
            status_code=500 if has_error else 200,
            total_duration_ms=total_dur,
            span_count=len(chain),
            has_error=1 if has_error else 0,
            started_at=started,
        )
        s.add(trace)

        parent_span_id = None
        remaining_dur = total_dur
        for i, svc in enumerate(chain):
            span_id = uuid.uuid4().hex[:16]
            ep, meth = random.choice(ENDPOINTS[svc])
            dur = round(remaining_dur * rand_float(0.3, 0.8), 2) if i < len(chain) - 1 else remaining_dur

            s.add(Span(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                service_name=svc,
                operation_name=f"{meth} {ep}",
                span_kind="server" if i == 0 else "client",
                status="error" if has_error and i == len(chain) - 1 else "ok",
                duration_ms=round(dur, 2),
                started_at=started + timedelta(milliseconds=int(total_dur - remaining_dur)),
                attributes=json.dumps({"http.method": meth, "http.url": ep}),
            ))

            parent_span_id = span_id
            remaining_dur = round(remaining_dur - dur * rand_float(0.1, 0.3), 2)
            if remaining_dur < 1:
                remaining_dur = 1


def seed_baselines_and_anomalies(s: Session, hosts: list):
    from app.models.baseline import MetricBaseline, Anomaly

    metrics = ["cpu_percent", "memory_percent", "swap_percent", "disk_percent_total", "load_avg_1m"]
    means = {"cpu_percent": 45, "memory_percent": 55, "swap_percent": 10, "disk_percent_total": 50, "load_avg_1m": 1.5}
    stddevs = {"cpu_percent": 15, "memory_percent": 12, "swap_percent": 5, "disk_percent_total": 8, "load_avg_1m": 0.8}

    for host in hosts:
        for metric in metrics:
            mean = means[metric] + rand_float(-5, 5)
            stddev = stddevs[metric] + rand_float(-2, 2)
            s.add(MetricBaseline(
                host_id=host.id,
                metric_name=metric,
                mean=mean,
                stddev=max(stddev, 1),
                min_val=max(mean - 3 * stddev, 0),
                max_val=min(mean + 3 * stddev, 100),
                sample_count=random.randint(200, 288),
                window_hours=24,
                computed_at=ts(0),
            ))

        # 1-3 anomalies per host
        for _ in range(random.randint(1, 3)):
            metric = random.choice(metrics)
            mean = means[metric]
            stddev = stddevs[metric]
            sigma = rand_float(2.1, 5.0)
            observed = round(mean + sigma * stddev, 2)
            severity = "warning" if sigma < 3 else "critical"
            is_resolved = random.random() < 0.3
            detected = ts(random.randint(5, 720))
            s.add(Anomaly(
                host_id=host.id,
                metric_name=metric,
                observed_value=observed,
                baseline_mean=mean,
                baseline_stddev=stddev,
                deviation_sigma=sigma,
                severity=severity,
                status="RESOLVED" if is_resolved else "OPEN",
                detected_at=detected,
                resolved_at=detected + timedelta(minutes=random.randint(5, 60)) if is_resolved else None,
            ))


def seed_logs(s: Session, hosts: list):
    from app.models.log_entry import LogEntry

    sources = ["app.order", "app.payment", "app.inventory", "app.user", "system.nginx", "system.cron"]
    levels = ["INFO", "INFO", "INFO", "INFO", "WARN", "WARN", "ERROR", "DEBUG"]

    for _ in range(600):
        level = random.choice(levels)
        templates = LOG_MESSAGES.get(level, LOG_MESSAGES["INFO"])
        msg = random.choice(templates).format(
            key=f"order-{random.randint(1000, 9999)}",
            ms=random.randint(100, 5000),
            id=random.randint(1, 10000),
        )
        host = random.choice(hosts[:7])
        s.add(LogEntry(
            host_id=host.id,
            hostname=host.hostname,
            source=random.choice(sources),
            level=level,
            message=msg,
            trace_id=uid() if random.random() < 0.3 else None,
            logged_at=ts(random.randint(0, 1440)),
        ))


def seed_topology(s: Session):
    from app.models.service_topology import ServiceNode, ServiceDependency

    service_defs = [
        ("order-service", "service"),
        ("payment-service", "service"),
        ("inventory-service", "service"),
        ("user-service", "service"),
        ("notification-service", "service"),
        ("postgres-db", "database"),
        ("redis-cache", "cache"),
        ("rabbitmq", "queue"),
    ]

    for svc_name, svc_type in service_defs:
        s.add(ServiceNode(
            service_name=svc_name,
            service_type=svc_type,
            status=random.choice(["healthy", "healthy", "healthy", "degraded"]),
            avg_response_time_ms=rand_float(5, 500),
            request_rate=rand_float(10, 2000),
            error_rate=rand_float(0, 5),
            last_seen_at=ts(random.randint(0, 5)),
        ))

    dependencies = [
        ("order-service", "payment-service"),
        ("order-service", "inventory-service"),
        ("order-service", "postgres-db"),
        ("order-service", "redis-cache"),
        ("payment-service", "postgres-db"),
        ("payment-service", "notification-service"),
        ("payment-service", "rabbitmq"),
        ("inventory-service", "postgres-db"),
        ("inventory-service", "redis-cache"),
        ("user-service", "postgres-db"),
        ("user-service", "redis-cache"),
        ("notification-service", "rabbitmq"),
    ]

    for src, tgt in dependencies:
        s.add(ServiceDependency(
            source_service=src,
            target_service=tgt,
            call_count=random.randint(500, 50000),
            error_count=random.randint(0, 200),
            avg_duration_ms=rand_float(2, 200),
            last_seen_at=ts(random.randint(0, 10)),
        ))


def seed_diagnostics(s: Session, hosts: list):
    from app.models.diagnostic import DiagnosticSnapshot

    for _ in range(12):
        app = random.choice(APPS)
        snap_type = random.choice(["cpu_profile", "memory_profile", "thread_dump"])
        host = random.choice(hosts[:7])

        top_functions = json.dumps([
            {"function": f"com.example.{app.replace('-', '.')}.Handler.process", "self_time_ms": rand_float(50, 500), "total_time_ms": rand_float(100, 800), "call_count": random.randint(100, 5000)},
            {"function": f"com.example.{app.replace('-', '.')}.Repository.query", "self_time_ms": rand_float(20, 300), "total_time_ms": rand_float(50, 500), "call_count": random.randint(50, 2000)},
            {"function": "java.net.SocketInputStream.read", "self_time_ms": rand_float(10, 200), "total_time_ms": rand_float(30, 400), "call_count": random.randint(200, 8000)},
        ])

        memory_summary = json.dumps({
            "heap_used_mb": rand_float(256, 2048),
            "heap_max_mb": 4096,
            "gc_count": random.randint(50, 500),
            "gc_time_ms": random.randint(500, 5000),
            "top_allocations": [
                {"class": "java.lang.String", "count": random.randint(10000, 100000), "size_mb": rand_float(10, 200)},
                {"class": "byte[]", "count": random.randint(5000, 50000), "size_mb": rand_float(50, 500)},
            ],
        })

        thread_dump = json.dumps({
            "total_threads": random.randint(50, 200),
            "runnable": random.randint(10, 50),
            "waiting": random.randint(20, 100),
            "blocked": random.randint(0, 10),
            "deadlocked": 0,
        })

        s.add(DiagnosticSnapshot(
            host_id=host.id,
            app_name=app,
            snapshot_type=snap_type,
            duration_seconds=rand_float(5, 60),
            top_functions=top_functions if snap_type == "cpu_profile" else None,
            memory_summary=memory_summary if snap_type == "memory_profile" else None,
            thread_dump=thread_dump if snap_type == "thread_dump" else None,
            triggered_by="scheduled",
            collected_at=ts(random.randint(0, 720)),
        ))


# ── Main ─────────────────────────────────────────────────────────────

def seed_all():
    reset = "--reset" in sys.argv

    if reset:
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as s:
        # Check if already seeded
        from app.models.host import Host
        if s.query(Host).count() > 0 and not reset:
            print("Database already contains data. Use --reset to drop and re-seed.")
            return

        print("Seeding hosts & metrics...")
        hosts = seed_hosts_and_metrics(s)

        print("Seeding alerts...")
        seed_alert_rules_and_alerts(s, hosts)

        print("Seeding DB monitoring...")
        seed_db_monitoring(s)

        print("Seeding business transactions...")
        seed_business_transactions(s, hosts)

        print("Seeding traces & spans...")
        seed_traces(s)

        print("Seeding baselines & anomalies...")
        seed_baselines_and_anomalies(s, hosts)

        print("Seeding logs...")
        seed_logs(s, hosts)

        print("Seeding service topology...")
        seed_topology(s)

        print("Seeding diagnostics...")
        seed_diagnostics(s, hosts)

        s.commit()
        print("Done! All dummy data seeded successfully.")

        # Summary
        from app.models.metrics_latest import MetricsLatest
        from app.models.metrics_history import MetricsHistory
        from app.models.alert import Alert
        from app.models.db_instance import DbInstance
        from app.models.business_transaction import BusinessTransaction
        from app.models.trace import Trace, Span
        from app.models.baseline import MetricBaseline, Anomaly
        from app.models.log_entry import LogEntry
        from app.models.service_topology import ServiceNode, ServiceDependency
        from app.models.diagnostic import DiagnosticSnapshot

        print(f"\n  Hosts:                {s.query(Host).count()}")
        print(f"  Metrics (latest):     {s.query(MetricsLatest).count()}")
        print(f"  Metrics (history):    {s.query(MetricsHistory).count()}")
        print(f"  Alerts:               {s.query(Alert).count()}")
        print(f"  DB Instances:         {s.query(DbInstance).count()}")
        print(f"  Transactions:         {s.query(BusinessTransaction).count()}")
        print(f"  Traces:               {s.query(Trace).count()}")
        print(f"  Spans:                {s.query(Span).count()}")
        print(f"  Baselines:            {s.query(MetricBaseline).count()}")
        print(f"  Anomalies:            {s.query(Anomaly).count()}")
        print(f"  Logs:                 {s.query(LogEntry).count()}")
        print(f"  Service Nodes:        {s.query(ServiceNode).count()}")
        print(f"  Service Dependencies: {s.query(ServiceDependency).count()}")
        print(f"  Diagnostics:          {s.query(DiagnosticSnapshot).count()}")


if __name__ == "__main__":
    seed_all()
