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
    """Generate random mount usage data."""
    num_mounts = random.randint(6, 12)
    selected = random.sample(MOUNT_PATHS, min(num_mounts, len(MOUNT_PATHS)))
    mounts = []
    for mp in selected:
        total = random.choice([50, 100, 200, 500])
        used_pct = generate_metric_value(base=60, spike_chance=0.1)
        used = round(total * used_pct / 100, 2)
        mounts.append({
            "mount_path": mp,
            "total_gb": total,
            "used_gb": used,
            "used_percent": used_pct,
        })
    return mounts


def build_payload(host_info: dict) -> dict:
    return {
        "hostname": host_info["hostname"],
        "ip_address": host_info["ip_address"],
        "environment": host_info["environment"],
        "cpu_percent": generate_metric_value(base=45),
        "memory_percent": generate_metric_value(base=55),
        "disk_percent_total": generate_metric_value(base=60),
        "load_avg_1m": round(random.uniform(0.1, 4.0), 4),
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
    parser.add_argument("--interval", type=int, default=60, help="Seconds between cycles in loop mode")
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
