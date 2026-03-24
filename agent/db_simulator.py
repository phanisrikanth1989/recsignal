#!/usr/bin/env python3
"""
RecSignal DB Simulator — Sends fake Oracle DB metrics to the backend.

Usage:
    python db_simulator.py                     # single run, 2 instances
    python db_simulator.py --loop --interval 30  # continuous every 30s
"""

from __future__ import annotations

import argparse
import logging
import random
import time
from datetime import datetime, timezone, timedelta

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("db-simulator")

BACKEND_URL = "http://localhost:8000/api/db-monitor/metrics"
API_KEY = "sample-secret-key"

SIMULATED_INSTANCES = [
    {"instance_name": "ORCL_PROD1", "db_type": "oracle", "host": "db-prod-01.internal", "port": 1521, "service_name": "orcl_prod1.svc", "environment": "prod"},
    {"instance_name": "ORCL_UAT1", "db_type": "oracle", "host": "db-uat-01.internal", "port": 1521, "service_name": "orcl_uat1.svc", "environment": "uat"},
]

TABLESPACE_NAMES = [
    "SYSTEM", "SYSAUX", "UNDOTBS1", "USERS", "TEMP", "APP_DATA",
    "APP_INDEX", "ARCHIVE_TS", "REPORTING_TS", "AUDIT_TS",
]

ORACLE_USERS = ["SYS", "SYSTEM", "APP_USER", "BATCH_USER", "REPORT_USER", "DBA_ADMIN", "ETL_USER"]
PROGRAMS = ["sqlplus@db-prod-01", "JDBC Thin Client", "python3@app-server", "SQL Developer", "OEM Agent", "DataPump Worker", "RMAN"]
MACHINES = ["app-server-01", "app-server-02", "batch-server", "etl-host", "dba-workstation", "report-server"]
WAIT_CLASSES = ["CPU", "User I/O", "System I/O", "Concurrency", "Application", "Commit", "Network", "Idle"]
WAIT_EVENTS = [
    "db file sequential read", "db file scattered read", "log file sync",
    "buffer busy waits", "enq: TX - row lock contention", "direct path read",
    "SQL*Net message from client", "SQL*Net message to client",
    "latch: shared pool", "cursor: pin S wait on X",
]

SLOW_SQL_TEMPLATES = [
    ("SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.created_at > :1", "APP_USER"),
    ("UPDATE inventory SET quantity = quantity - :1 WHERE product_id = :2 AND warehouse_id = :3", "APP_USER"),
    ("INSERT INTO audit_log (event_type, user_id, details, created_at) VALUES (:1, :2, :3, SYSDATE)", "BATCH_USER"),
    ("SELECT /*+ FULL(t) */ COUNT(*) FROM transactions t WHERE t.status = 'PENDING' AND t.created_at < SYSDATE - 7", "REPORT_USER"),
    ("DELETE FROM temp_processing WHERE batch_id = :1 AND status = 'COMPLETE'", "ETL_USER"),
    ("SELECT c.name, SUM(o.amount) FROM customers c JOIN orders o ON c.id = o.cust_id GROUP BY c.name HAVING SUM(o.amount) > :1", "REPORT_USER"),
    ("MERGE INTO summary_table s USING source_table src ON (s.key = src.key) WHEN MATCHED THEN UPDATE SET s.val = src.val", "ETL_USER"),
    ("SELECT * FROM v$session WHERE status = 'ACTIVE' AND username IS NOT NULL ORDER BY last_call_et DESC", "DBA_ADMIN"),
    ("BEGIN dbms_stats.gather_schema_stats('APP_USER', cascade => TRUE); END;", "SYS"),
    ("SELECT segment_name, bytes/1024/1024 mb FROM dba_segments WHERE tablespace_name = :1 ORDER BY bytes DESC", "DBA_ADMIN"),
]


def generate_tablespaces() -> list[dict]:
    """Generate random tablespace metrics."""
    num = random.randint(6, len(TABLESPACE_NAMES))
    selected = random.sample(TABLESPACE_NAMES, num)
    tablespaces = []
    for name in selected:
        if name == "TEMP":
            total = random.choice([2048, 4096, 8192])
        elif name in ("SYSTEM", "SYSAUX"):
            total = random.choice([512, 1024, 2048])
        else:
            total = random.choice([4096, 8192, 16384, 32768])

        # Occasionally spike usage
        if random.random() < 0.12:
            used_pct = round(random.uniform(86, 99), 1)
        else:
            used_pct = round(random.uniform(20, 84), 1)

        used = round(total * used_pct / 100, 2)
        free = round(total - used, 2)
        autoext = random.choice(["YES", "YES", "YES", "NO"])
        max_mb = total * 2 if autoext == "YES" else total

        tablespaces.append({
            "tablespace_name": name,
            "total_mb": total,
            "used_mb": used,
            "free_mb": free,
            "used_percent": used_pct,
            "autoextensible": autoext,
            "max_mb": max_mb,
            "status": "ONLINE",
        })
    return tablespaces


def generate_sessions() -> list[dict]:
    """Generate fake Oracle session snapshots."""
    num_sessions = random.randint(15, 50)
    sessions = []
    used_sids: set[int] = set()

    for _ in range(num_sessions):
        sid = random.randint(1, 500)
        while sid in used_sids:
            sid = random.randint(1, 500)
        used_sids.add(sid)

        status = random.choices(["ACTIVE", "INACTIVE"], weights=[30, 70])[0]
        username = random.choice(ORACLE_USERS)
        program = random.choice(PROGRAMS)
        machine = random.choice(MACHINES)

        wait_class = random.choice(WAIT_CLASSES) if status == "ACTIVE" else "Idle"
        wait_event = random.choice(WAIT_EVENTS) if status == "ACTIVE" else "SQL*Net message from client"
        seconds_in_wait = round(random.uniform(0, 300), 2) if status == "ACTIVE" else round(random.uniform(10, 3600), 2)

        # Some sessions are long-running
        elapsed = round(random.uniform(0, 120), 2) if status == "ACTIVE" else round(random.uniform(0, 10), 2)
        if random.random() < 0.1:
            elapsed = round(random.uniform(120, 600), 2)

        # Occasionally create blocking sessions
        blocking = None
        if random.random() < 0.05 and len(used_sids) > 1:
            blocking = random.choice(list(used_sids - {sid}))

        logon_time = (datetime.now(timezone.utc) - timedelta(seconds=random.randint(60, 86400))).isoformat()

        sql_id = f"{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=13))}" if status == "ACTIVE" else None

        sessions.append({
            "sid": sid,
            "serial_no": random.randint(1000, 65000),
            "username": username,
            "program": program,
            "machine": machine,
            "status": status,
            "sql_id": sql_id,
            "sql_text": random.choice(SLOW_SQL_TEMPLATES)[0] if sql_id else None,
            "wait_class": wait_class,
            "wait_event": wait_event,
            "seconds_in_wait": seconds_in_wait,
            "blocking_session": blocking,
            "logon_time": logon_time,
            "elapsed_seconds": elapsed,
        })

    return sessions


def generate_slow_queries() -> list[dict]:
    """Generate fake top slow queries."""
    num = random.randint(5, 10)
    queries = []
    for _ in range(num):
        sql_text, username = random.choice(SLOW_SQL_TEMPLATES)
        queries.append({
            "sql_id": "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=13)),
            "sql_text": sql_text,
            "username": username,
            "elapsed_seconds": round(random.uniform(1, 300), 2),
            "cpu_seconds": round(random.uniform(0.1, 150), 2),
            "buffer_gets": random.randint(1000, 5000000),
            "disk_reads": random.randint(0, 500000),
            "rows_processed": random.randint(1, 1000000),
            "executions": random.randint(1, 10000),
            "plan_hash_value": str(random.randint(100000000, 9999999999)),
        })
    queries.sort(key=lambda q: q["elapsed_seconds"], reverse=True)
    return queries


def generate_performance(sessions: list[dict]) -> dict:
    """Generate fake Oracle performance stats."""
    active = sum(1 for s in sessions if s["status"] == "ACTIVE")
    inactive = sum(1 for s in sessions if s["status"] == "INACTIVE")
    total = len(sessions)

    return {
        "buffer_cache_hit_ratio": round(random.uniform(92, 99.9), 2),
        "library_cache_hit_ratio": round(random.uniform(90, 99.5), 2),
        "parse_count_total": random.randint(5000, 50000),
        "hard_parse_count": random.randint(10, 500),
        "execute_count": random.randint(10000, 200000),
        "user_commits": random.randint(1000, 50000),
        "user_rollbacks": random.randint(0, 200),
        "physical_reads": random.randint(5000, 500000),
        "physical_writes": random.randint(1000, 100000),
        "redo_size": random.randint(1000000, 50000000),
        "sga_total_mb": random.choice([4096, 8192, 16384]),
        "pga_total_mb": random.choice([1024, 2048, 4096]),
        "active_sessions": active,
        "inactive_sessions": inactive,
        "total_sessions": total,
        "max_sessions": 500,
        "db_uptime_seconds": random.randint(86400, 86400 * 90),
    }


def build_payload(instance_info: dict) -> dict:
    sessions = generate_sessions()
    return {
        "instance_name": instance_info["instance_name"],
        "db_type": instance_info["db_type"],
        "host": instance_info["host"],
        "port": instance_info["port"],
        "service_name": instance_info["service_name"],
        "environment": instance_info["environment"],
        "tablespaces": generate_tablespaces(),
        "sessions": sessions,
        "slow_queries": generate_slow_queries(),
        "performance": generate_performance(sessions),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def send_payload(payload: dict, backend_url: str, api_key: str) -> bool:
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    try:
        resp = requests.post(backend_url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        logger.info("✓ %s → %s", payload["instance_name"], resp.json().get("message", "ok"))
        return True
    except requests.exceptions.RequestException as e:
        logger.error("✗ %s → %s", payload["instance_name"], e)
        return False


def run_once(instances: list[dict], backend_url: str, api_key: str):
    logger.info("Sending DB metrics for %d instances to %s", len(instances), backend_url)
    success = 0
    for info in instances:
        payload = build_payload(info)
        if send_payload(payload, backend_url, api_key):
            success += 1
    logger.info("Done: %d/%d successful", success, len(instances))


def main():
    parser = argparse.ArgumentParser(description="RecSignal DB Simulator")
    parser.add_argument("--instances", type=int, default=2, help="Number of simulated instances (max 2)")
    parser.add_argument("--url", default=BACKEND_URL, help="Backend URL")
    parser.add_argument("--api-key", default=API_KEY, help="API key")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between cycles (default: 30)")

    args = parser.parse_args()
    count = min(args.instances, len(SIMULATED_INSTANCES))
    hosts = SIMULATED_INSTANCES[:count]

    if args.loop:
        logger.info("Looping every %ds for %d DB instances (Ctrl+C to stop)", args.interval, count)
        while True:
            run_once(hosts, args.url, args.api_key)
            time.sleep(args.interval)
    else:
        run_once(hosts, args.url, args.api_key)


if __name__ == "__main__":
    main()
