#!/usr/bin/env python3
"""
RecSignal Simulator - Sends fake metrics from simulated Unix hosts.
Useful for testing the backend and frontend without real servers.

Usage:
    python simulator.py                    # 5 hosts, single run
    python simulator.py --hosts 10         # 10 hosts, single run
    python simulator.py --loop --interval 30   # continuous every 30s
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
import time
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("simulator")

BACKEND_URL = "http://localhost:8000/api/agent/metrics"
API_KEY = "sample-secret-key"

SIMULATED_HOSTS = [
    # UAT
    {"hostname": "lswtlmap1u", "ip_address": "10.10.1.20", "environment": "uat"},
    {"hostname": "lswtlmap2u", "ip_address": "10.10.1.21", "environment": "uat"},
    {"hostname": "lswtlmap3u", "ip_address": "10.10.1.22", "environment": "uat"},
    {"hostname": "sd-20d3-4317", "ip_address": "10.10.1.23", "environment": "uat"},
]

MOUNT_PATHS = [
    "/dev",
    "/dev/shm",
    "/run",
    "/sys/fs/cgroup",
    "/",
    "/opt",
    "/var",
    "/tmp",
    "/home",
    "/var/crash",
    "/archivelog",
    "/opt/middleware",
    "/oraredolog",
    "/dumps",
    "/boot",
    "/optware",
    "/dumps_1",
    "/data01",
    "/oradata",
    "/opt/rectify_archives9",
    "/opt/rectify_archives2",
    "/opt/rectify_archives10",
    "/opt/rectify_archives",
    "/opt/rectify_archives14",
    "/opt/rectify_archives3",
    "/opt/rectify_archives11",
    "/opt/rectify_archives15",
    "/opt/rectify_archives12",
]


def generate_metric_value(base: float = 50, spike_chance: float = 0.15) -> float:
    """Generate a metric value, occasionally spiking to warning/critical levels."""
    if random.random() < spike_chance:
        # Spike to warning or critical range
        return round(random.uniform(86, 99), 1)
    return round(random.uniform(max(5, base - 30), min(84, base + 30)), 1)


def generate_mounts() -> list[dict]:
    """Generate random mount usage data with inode info."""
    num_mounts = random.randint(6, 12)
    selected = random.sample(MOUNT_PATHS, min(num_mounts, len(MOUNT_PATHS)))
    mounts = []
    for mp in selected:
        total = random.choice([50, 100, 200, 500])
        used_pct = generate_metric_value(base=60, spike_chance=0.1)
        used = round(total * used_pct / 100, 2)
        inode_total = random.choice([500000, 1000000, 2000000, 5000000])
        inode_pct = generate_metric_value(base=30, spike_chance=0.05)
        inode_used = int(inode_total * inode_pct / 100)
        mounts.append({
            "mount_path": mp,
            "total_gb": total,
            "used_gb": used,
            "used_percent": used_pct,
            "inode_total": inode_total,
            "inode_used": inode_used,
            "inode_percent": inode_pct,
        })
    return mounts


# Simulated boot time (1-90 days ago)
_SIM_BOOT_TIME = datetime.now(timezone.utc).replace(
    hour=3, minute=15, second=0, microsecond=0
).isoformat()

FAKE_PROCESS_NAMES = [
    ("java", "appuser"), ("python3", "appuser"), ("nginx", "www-data"),
    ("postgres", "postgres"), ("node", "appuser"), ("redis-server", "redis"),
    ("sshd", "root"), ("cron", "root"), ("rsyslogd", "syslog"),
    ("systemd", "root"), ("kworker/0:1", "root"), ("kworker/1:0", "root"),
    ("bash", "appuser"), ("top", "appuser"), ("sleep", "root"),
    ("httpd", "apache"), ("mongod", "mongod"), ("dockerd", "root"),
    ("containerd", "root"), ("kubelet", "root"), ("etcd", "etcd"),
    ("mysqld", "mysql"), ("beam.smp", "rabbitmq"), ("supervisord", "root"),
]


def generate_processes(process_count: int, zombie_count: int) -> list[dict]:
    """Generate a fake process list with the given counts."""
    procs: list[dict] = []
    used_pids: set[int] = set()

    # Generate zombie processes first
    for _ in range(zombie_count):
        pid = random.randint(1000, 65000)
        while pid in used_pids:
            pid = random.randint(1000, 65000)
        used_pids.add(pid)
        name = random.choice(["defunct", "zombie_worker", "old_task"])
        procs.append({
            "pid": pid,
            "name": f"[{name}]",
            "username": "root",
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "status": "zombie",
        })

    # Fill remaining with normal processes
    normal_count = min(process_count, 50) - zombie_count
    for _ in range(max(0, normal_count)):
        pid = random.randint(1, 65000)
        while pid in used_pids:
            pid = random.randint(1, 65000)
        used_pids.add(pid)
        name, user = random.choice(FAKE_PROCESS_NAMES)
        status = random.choice(["running", "sleeping", "sleeping", "sleeping"])
        procs.append({
            "pid": pid,
            "name": name,
            "username": user,
            "cpu_percent": round(random.uniform(0, 40), 1),
            "memory_percent": round(random.uniform(0, 15), 1),
            "status": status,
        })

    procs.sort(key=lambda p: p["cpu_percent"], reverse=True)
    return procs


def build_payload(host_info: dict) -> dict:
    process_count = random.randint(100, 800)
    zombie_count = random.choice([0, 0, 0, 0, 0, 1, 2])
    return {
        "hostname": host_info["hostname"],
        "ip_address": host_info["ip_address"],
        "environment": host_info["environment"],
        "cpu_percent": generate_metric_value(base=45),
        "memory_percent": generate_metric_value(base=55),
        "swap_percent": generate_metric_value(base=20, spike_chance=0.08),
        "disk_percent_total": generate_metric_value(base=60),
        "load_avg_1m": round(random.uniform(0.1, 4.0), 4),
        "disk_read_bytes_sec": round(random.uniform(0, 200_000_000), 2),
        "disk_write_bytes_sec": round(random.uniform(0, 150_000_000), 2),
        "disk_read_iops": round(random.uniform(0, 5000), 2),
        "disk_write_iops": round(random.uniform(0, 4000), 2),
        "net_bytes_sent_sec": round(random.uniform(0, 125_000_000), 2),
        "net_bytes_recv_sec": round(random.uniform(0, 125_000_000), 2),
        "open_fds": random.randint(50, 2000),
        "max_fds": 65536,
        "process_count": process_count,
        "zombie_count": zombie_count,
        "boot_time": _SIM_BOOT_TIME,
        "processes": generate_processes(process_count, zombie_count),
        "mounts": generate_mounts(),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def send_payload(payload: dict, backend_url: str, api_key: str) -> bool:
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    try:
        resp = requests.post(backend_url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        logger.info("✓ %s → %s", payload["hostname"], resp.json().get("message", "ok"))
        return True
    except requests.exceptions.RequestException as e:
        logger.error("✗ %s → %s", payload["hostname"], e)
        return False


def run_once(hosts: list[dict], backend_url: str, api_key: str):
    logger.info("Sending metrics for %d hosts to %s", len(hosts), backend_url)
    success = 0
    for host_info in hosts:
        payload = build_payload(host_info)
        if send_payload(payload, backend_url, api_key):
            success += 1
    logger.info("Done: %d/%d successful", success, len(hosts))


def main():
    parser = argparse.ArgumentParser(description="RecSignal Fake Agent Simulator")
    parser.add_argument("--hosts", type=int, default=4, help="Number of simulated hosts (max 4)")
    parser.add_argument("--url", default=BACKEND_URL, help="Backend URL")
    parser.add_argument("--api-key", default=API_KEY, help="API key")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=10, help="Seconds between cycles in loop mode (default: 10s for live monitoring)")
    args = parser.parse_args()

    num_hosts = min(args.hosts, len(SIMULATED_HOSTS))
    hosts = SIMULATED_HOSTS[:num_hosts]

    if args.loop:
        logger.info("Running in loop mode (interval=%ds)", args.interval)
        while True:
            run_once(hosts, args.url, args.api_key)
            time.sleep(args.interval)
    else:
        run_once(hosts, args.url, args.api_key)


if __name__ == "__main__":
    main()
