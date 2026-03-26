#!/usr/bin/env python3
"""
RecSignal Oracle DB Collector Agent

Connects to Oracle databases, collects metrics (tablespaces, sessions,
performance, slow queries), and sends them to the backend.

Usage:
    python db_agent.py                           # single run
    python db_agent.py --loop --interval 30      # continuous
    python db_agent.py --config /path/to/db_config.yaml
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import yaml
import requests

logger = logging.getLogger("recsignal-db-agent")


def load_config(config_path: str | None = None) -> dict:
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config", "db_config.yaml")
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    # Resolve db_instances from the pipe-delimited file
    instances_file = cfg.get("db_instances_file")
    if instances_file:
        if not os.path.isabs(instances_file):
            instances_file = os.path.join(os.path.dirname(config_path), instances_file)
        cfg["db_instances"] = load_db_instances(instances_file)
    else:
        cfg.setdefault("db_instances", [])

    return cfg


def load_db_instances(file_path: str) -> list[dict]:
    """Parse the pipe-delimited DB instances file.

    Format: environment|schema:DBNAME|host|port|schema|servicename|oraclehomepath
    """
    instances = []
    with open(file_path) as f:
        for line_no, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) != 7:
                logger.warning("Skipping line %d in %s: expected 7 fields, got %d", line_no, file_path, len(parts))
                continue
            environment, schema_dbname, host, port, schema, service_name, oracle_home = parts
            # schema:DBNAME → extract instance_name (DBNAME)
            if ":" in schema_dbname:
                _, instance_name = schema_dbname.split(":", 1)
            else:
                instance_name = schema_dbname
            instances.append({
                "instance_name": instance_name.strip(),
                "db_type": "oracle",
                "host": host.strip(),
                "port": int(port.strip()),
                "service_name": service_name.strip(),
                "environment": environment.strip(),
                "username": schema.strip(),
                "oracle_home": oracle_home.strip(),
            })
    logger.info("Loaded %d DB instances from %s", len(instances), file_path)
    return instances


def get_password(instance_cfg: dict, password_script: str | None = None) -> str | None:
    """Resolve password by calling the password script."""
    if not password_script:
        logger.warning("No password_script configured for %s", instance_cfg["instance_name"])
        return None
    return _run_password_script(password_script, instance_cfg)


def _run_password_script(script_path: str, cfg: dict) -> str | None:
    """Call an external script to retrieve the DB password.

    The script is invoked as:
        /path/to/script.sh <instance_name> <username>
    and must print the password to stdout (first line).
    """
    instance_name = cfg["instance_name"]
    cmd = [script_path, instance_name, cfg["username"]]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.error(
                "Password script failed for %s (exit %d): %s",
                instance_name, result.returncode, result.stderr.strip(),
            )
            return None
        pw = result.stdout.strip().split("\n")[0]  # first line only
        if not pw:
            logger.warning("Password script returned empty output for %s", instance_name)
            return None
        return pw
    except FileNotFoundError:
        logger.error("Password script not found: %s", script_path)
        return None
    except subprocess.TimeoutExpired:
        logger.error("Password script timed out for %s", instance_name)
        return None
    except Exception:
        logger.exception("Error running password script for %s", instance_name)
        return None


def connect_oracle(cfg: dict, password_script: str | None = None):
    """Create an Oracle DB connection using oracledb (thin mode)."""
    try:
        import oracledb
    except ImportError:
        logger.error("oracledb not installed. Run: pip install oracledb")
        raise

    password = get_password(cfg, password_script)
    if not password:
        raise ValueError(f"No password available for {cfg['instance_name']}")

    return oracledb.connect(
        user=cfg["username"],
        password=password,
        host=cfg["host"],
        port=cfg["port"],
        service_name=cfg["service_name"],
    )


def collect_tablespaces(cursor) -> list[dict]:
    cursor.execute("""
        SELECT
            t.tablespace_name,
            ROUND(t.total_mb, 2) AS total_mb,
            ROUND(t.total_mb - NVL(f.free_mb, 0), 2) AS used_mb,
            ROUND(NVL(f.free_mb, 0), 2) AS free_mb,
            ROUND((t.total_mb - NVL(f.free_mb, 0)) / t.total_mb * 100, 2) AS used_percent,
            t.autoextensible,
            ROUND(t.max_mb, 2) AS max_mb,
            t.status
        FROM (
            SELECT tablespace_name,
                   SUM(bytes) / 1048576 AS total_mb,
                   MAX(autoextensible) AS autoextensible,
                   SUM(maxbytes) / 1048576 AS max_mb,
                   'ONLINE' AS status
            FROM dba_data_files
            GROUP BY tablespace_name
        ) t
        LEFT JOIN (
            SELECT tablespace_name, SUM(bytes) / 1048576 AS free_mb
            FROM dba_free_space
            GROUP BY tablespace_name
        ) f ON t.tablespace_name = f.tablespace_name
        ORDER BY used_percent DESC
    """)
    return [
        {
            "tablespace_name": row[0],
            "total_mb": row[1],
            "used_mb": row[2],
            "free_mb": row[3],
            "used_percent": row[4],
            "autoextensible": row[5],
            "max_mb": row[6],
            "status": row[7],
        }
        for row in cursor.fetchall()
    ]


def collect_sessions(cursor) -> list[dict]:
    cursor.execute("""
        SELECT
            s.sid, s.serial#, s.username, s.program, s.machine,
            s.status, s.sql_id,
            (SELECT SUBSTR(sql_text, 1, 500) FROM v$sql q WHERE q.sql_id = s.sql_id AND ROWNUM = 1) AS sql_text,
            s.wait_class, s.event,
            s.seconds_in_wait,
            s.blocking_session,
            s.logon_time,
            s.last_call_et AS elapsed_seconds
        FROM v$session s
        WHERE s.type = 'USER' AND s.username IS NOT NULL
        ORDER BY s.status, s.last_call_et DESC
        FETCH FIRST 100 ROWS ONLY
    """)
    return [
        {
            "sid": row[0],
            "serial_no": row[1],
            "username": row[2],
            "program": row[3],
            "machine": row[4],
            "status": row[5],
            "sql_id": row[6],
            "sql_text": row[7],
            "wait_class": row[8],
            "wait_event": row[9],
            "seconds_in_wait": float(row[10]) if row[10] else None,
            "blocking_session": row[11],
            "logon_time": row[12].isoformat() if row[12] else None,
            "elapsed_seconds": float(row[13]) if row[13] else None,
        }
        for row in cursor.fetchall()
    ]


def collect_performance(cursor) -> dict:
    stats = {}

    # Buffer cache hit ratio
    cursor.execute("""
        SELECT ROUND(
            (1 - (SUM(CASE name WHEN 'physical reads' THEN value END) /
                  NULLIF(SUM(CASE name WHEN 'db block gets' THEN value END) +
                         SUM(CASE name WHEN 'consistent gets' THEN value END), 0))) * 100, 2
        ) FROM v$sysstat WHERE name IN ('physical reads', 'db block gets', 'consistent gets')
    """)
    stats["buffer_cache_hit_ratio"] = cursor.fetchone()[0]

    # Library cache hit ratio
    cursor.execute("""
        SELECT ROUND(SUM(pins - reloads) / NULLIF(SUM(pins), 0) * 100, 2) FROM v$librarycache
    """)
    stats["library_cache_hit_ratio"] = cursor.fetchone()[0]

    # Key sysstat counters
    cursor.execute("""
        SELECT name, value FROM v$sysstat
        WHERE name IN ('parse count (total)', 'parse count (hard)', 'execute count',
                       'user commits', 'user rollbacks', 'physical reads',
                       'physical writes', 'redo size')
    """)
    stat_map = {
        "parse count (total)": "parse_count_total",
        "parse count (hard)": "hard_parse_count",
        "execute count": "execute_count",
        "user commits": "user_commits",
        "user rollbacks": "user_rollbacks",
        "physical reads": "physical_reads",
        "physical writes": "physical_writes",
        "redo size": "redo_size",
    }
    for row in cursor.fetchall():
        key = stat_map.get(row[0])
        if key:
            stats[key] = int(row[1]) if row[1] else None

    # SGA/PGA
    cursor.execute("SELECT SUM(value)/1048576 FROM v$sga")
    stats["sga_total_mb"] = round(cursor.fetchone()[0] or 0, 2)

    cursor.execute("SELECT value/1048576 FROM v$pgastat WHERE name = 'total PGA allocated'")
    row = cursor.fetchone()
    stats["pga_total_mb"] = round(row[0], 2) if row and row[0] else None

    # Sessions
    cursor.execute("""
        SELECT
            SUM(CASE WHEN status = 'ACTIVE' AND username IS NOT NULL THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'INACTIVE' AND username IS NOT NULL THEN 1 ELSE 0 END),
            COUNT(*),
            (SELECT value FROM v$parameter WHERE name = 'sessions')
        FROM v$session WHERE type = 'USER'
    """)
    row = cursor.fetchone()
    stats["active_sessions"] = int(row[0]) if row[0] else 0
    stats["inactive_sessions"] = int(row[1]) if row[1] else 0
    stats["total_sessions"] = int(row[2]) if row[2] else 0
    stats["max_sessions"] = int(row[3]) if row[3] else None

    # Uptime
    cursor.execute("SELECT (SYSDATE - startup_time) * 86400 FROM v$instance")
    stats["db_uptime_seconds"] = int(cursor.fetchone()[0] or 0)

    return stats


def collect_slow_queries(cursor, limit: int = 10) -> list[dict]:
    cursor.execute(f"""
        SELECT
            sql_id,
            SUBSTR(sql_text, 1, 500) AS sql_text,
            parsing_schema_name AS username,
            ROUND(elapsed_time / 1000000, 2) AS elapsed_seconds,
            ROUND(cpu_time / 1000000, 2) AS cpu_seconds,
            buffer_gets,
            disk_reads,
            rows_processed,
            executions,
            TO_CHAR(plan_hash_value) AS plan_hash_value
        FROM v$sql
        WHERE parsing_schema_name NOT IN ('SYS', 'SYSTEM', 'DBSNMP', 'SYSMAN')
          AND elapsed_time > 0
        ORDER BY elapsed_time DESC
        FETCH FIRST :limit ROWS ONLY
    """, {"limit": limit})
    return [
        {
            "sql_id": row[0],
            "sql_text": row[1],
            "username": row[2],
            "elapsed_seconds": row[3],
            "cpu_seconds": row[4],
            "buffer_gets": row[5],
            "disk_reads": row[6],
            "rows_processed": row[7],
            "executions": row[8],
            "plan_hash_value": row[9],
        }
        for row in cursor.fetchall()
    ]


def collect_instance_metrics(cfg: dict, password_script: str | None = None) -> dict | None:
    """Connect to one Oracle instance and collect all metrics."""
    instance_name = cfg["instance_name"]
    try:
        conn = connect_oracle(cfg, password_script)
        cursor = conn.cursor()

        tablespaces = collect_tablespaces(cursor)
        sessions = collect_sessions(cursor)
        performance = collect_performance(cursor)
        slow_queries = collect_slow_queries(cursor)

        cursor.close()
        conn.close()

        return {
            "instance_name": instance_name,
            "db_type": cfg.get("db_type", "oracle"),
            "host": cfg["host"],
            "port": cfg["port"],
            "service_name": cfg["service_name"],
            "environment": cfg.get("environment", "prod"),
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "tablespaces": tablespaces,
            "sessions": sessions,
            "performance": performance,
            "slow_queries": slow_queries,
        }

    except Exception:
        logger.exception("Failed to collect metrics from %s", instance_name)
        return None


def send_payload(payload: dict, backend_url: str, api_key: str) -> bool:
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    try:
        resp = requests.post(backend_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        logger.info("✓ %s → %s", payload["instance_name"], resp.json().get("message", "ok"))
        return True
    except requests.exceptions.RequestException as e:
        logger.error("✗ %s → %s", payload["instance_name"], e)
        return False


def run_once(config: dict):
    backend_url = config["backend_url"]
    api_key = config.get("api_key", "")
    password_script = config.get("password_script")
    instances = config.get("db_instances", [])

    logger.info("Collecting DB metrics for %d instances", len(instances))
    success = 0
    for cfg in instances:
        payload = collect_instance_metrics(cfg, password_script)
        if payload and send_payload(payload, backend_url, api_key):
            success += 1
    logger.info("Done: %d/%d successful", success, len(instances))


def main():
    parser = argparse.ArgumentParser(description="RecSignal Oracle DB Collector Agent")
    parser.add_argument("--config", default=None, help="Path to db_config.yaml")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=None, help="Override interval_seconds")
    args = parser.parse_args()

    config = load_config(args.config)
    interval = args.interval or config.get("interval_seconds", 30)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    if args.loop:
        logger.info("Looping every %ds for %d DB instances (Ctrl+C to stop)", interval, len(config.get("db_instances", [])))
        while True:
            run_once(config)
            time.sleep(interval)
    else:
        run_once(config)


if __name__ == "__main__":
    main()
