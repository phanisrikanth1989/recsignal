"""System metrics collector using psutil."""

from __future__ import annotations

import socket
import psutil


def get_hostname() -> str:
    return socket.gethostname()


def get_ip_address() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_cpu_percent() -> float:
    return psutil.cpu_percent(interval=1)


def get_memory_percent() -> float:
    return psutil.virtual_memory().percent


def get_disk_percent_total() -> float:
    return psutil.disk_usage("/").percent


def get_load_avg_1m() -> float:
    try:
        return round(psutil.getloadavg()[0], 4)
    except (AttributeError, OSError):
        # getloadavg not available on Windows
        return 0.0


def get_mount_usage(mounts_include: list[str]) -> list[dict]:
    """Collect disk usage for specified mount points."""
    results = []
    for mount in mounts_include:
        try:
            usage = psutil.disk_usage(mount)
            results.append({
                "mount_path": mount,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "used_percent": round(usage.percent, 1),
            })
        except (FileNotFoundError, PermissionError, OSError):
            pass
    return results


def collect_all(mounts_include: list[str]) -> dict:
    """Collect all system metrics and return as payload dict."""
    return {
        "hostname": get_hostname(),
        "ip_address": get_ip_address(),
        "cpu_percent": get_cpu_percent(),
        "memory_percent": get_memory_percent(),
        "disk_percent_total": get_disk_percent_total(),
        "load_avg_1m": get_load_avg_1m(),
        "mounts": get_mount_usage(mounts_include),
    }
