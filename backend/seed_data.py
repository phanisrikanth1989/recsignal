"""
RecSignal – Comprehensive Data Seeder
Populates SQLite with realistic dummy data for all modules:
  • Server Monitoring (hosts, metrics, mounts, processes, alerts)
  • DB Monitoring (instances, tablespaces, sessions, slow queries, performance)

Usage:
    cd backend
    python seed_data.py          # seed once
    python seed_data.py --reset  # drop + recreate tables, then seed
"""

from __future__ import annotations

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

        # Zombie process snapshots (match zombie_count in latest metrics)
        zombie_count = latest.zombie_count or 0
        zombie_names = ["defunct-worker", "old-cron-job", "orphan-child", "stale-handler"]
        for z in range(zombie_count):
            s.add(ProcessSnapshot(
                host_id=host.id, pid=random.randint(50001, 60000),
                name=random.choice(zombie_names), username="root",
                cpu_percent=0.0,
                memory_percent=0.0,
                status="zombie",
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

        s.commit()
        print("Done! All dummy data seeded successfully.")

        # Summary
        from app.models.metrics_latest import MetricsLatest
        from app.models.metrics_history import MetricsHistory
        from app.models.alert import Alert
        from app.models.db_instance import DbInstance

        print(f"\n  Hosts:                {s.query(Host).count()}")
        print(f"  Metrics (latest):     {s.query(MetricsLatest).count()}")
        print(f"  Metrics (history):    {s.query(MetricsHistory).count()}")
        print(f"  Alerts:               {s.query(Alert).count()}")
        print(f"  DB Instances:         {s.query(DbInstance).count()}")


if __name__ == "__main__":
    seed_all()
