"""System metrics collector using psutil."""

from __future__ import annotations

import os
import socket
import time
from datetime import datetime, timezone

import psutil

# ---------------------------------------------------------------------------
# Module-level state for rate-based metrics (disk I/O & network I/O).
# The first collection will return None for rates; subsequent calls compute
# deltas from the previous reading.
# ---------------------------------------------------------------------------
_prev_disk_io: psutil._common.sdiskio | None = None
_prev_disk_io_ts: float | None = None
_prev_net_io: psutil._common.snetio | None = None
_prev_net_io_ts: float | None = None


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


def get_swap_percent() -> float:
    return psutil.swap_memory().percent


def get_disk_percent_total() -> float:
    return psutil.disk_usage("/").percent


def get_load_avg_1m() -> float:
    try:
        return round(psutil.getloadavg()[0], 4)
    except (AttributeError, OSError):
        # getloadavg not available on Windows
        return 0.0


def get_disk_io() -> dict | None:
    """Return disk I/O rates (bytes/s and IOPS). None on first call."""
    global _prev_disk_io, _prev_disk_io_ts
    try:
        counters = psutil.disk_io_counters()
    except Exception:
        return None
    if counters is None:
        return None
    now = time.monotonic()
    if _prev_disk_io is None or _prev_disk_io_ts is None:
        _prev_disk_io, _prev_disk_io_ts = counters, now
        return None
    dt = now - _prev_disk_io_ts
    if dt <= 0:
        return None
    result = {
        "disk_read_bytes_sec": round((counters.read_bytes - _prev_disk_io.read_bytes) / dt, 2),
        "disk_write_bytes_sec": round((counters.write_bytes - _prev_disk_io.write_bytes) / dt, 2),
        "disk_read_iops": round((counters.read_count - _prev_disk_io.read_count) / dt, 2),
        "disk_write_iops": round((counters.write_count - _prev_disk_io.write_count) / dt, 2),
    }
    _prev_disk_io, _prev_disk_io_ts = counters, now
    return result


def get_network_io() -> dict | None:
    """Return network I/O rates (bytes/s). None on first call."""
    global _prev_net_io, _prev_net_io_ts
    try:
        counters = psutil.net_io_counters()
    except Exception:
        return None
    if counters is None:
        return None
    now = time.monotonic()
    if _prev_net_io is None or _prev_net_io_ts is None:
        _prev_net_io, _prev_net_io_ts = counters, now
        return None
    dt = now - _prev_net_io_ts
    if dt <= 0:
        return None
    result = {
        "net_bytes_sent_sec": round((counters.bytes_sent - _prev_net_io.bytes_sent) / dt, 2),
        "net_bytes_recv_sec": round((counters.bytes_recv - _prev_net_io.bytes_recv) / dt, 2),
    }
    _prev_net_io, _prev_net_io_ts = counters, now
    return result


def get_open_fds() -> dict:
    """Return open file descriptors and system max."""
    try:
        import resource
        soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        max_fds = soft
    except Exception:
        max_fds = None
    try:
        proc = psutil.Process()
        open_fds = proc.num_fds()
    except Exception:
        open_fds = None
    return {"open_fds": open_fds, "max_fds": max_fds}


def get_process_count() -> int:
    return len(psutil.pids())


def get_zombie_count() -> int:
    count = 0
    for proc in psutil.process_iter(["status"]):
        try:
            if proc.info["status"] == psutil.STATUS_ZOMBIE:
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return count


def get_boot_time() -> str:
    """Return system boot time as ISO-8601 UTC string."""
    return datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).isoformat()


def get_top_processes(limit: int = 50) -> list[dict]:
    """Return top processes sorted by CPU %, including all zombies."""
    procs: list[dict] = []
    for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent", "status"]):
        try:
            info = proc.info
            procs.append({
                "pid": info["pid"],
                "name": info["name"] or "",
                "username": info["username"] or "",
                "cpu_percent": round(info["cpu_percent"] or 0.0, 1),
                "memory_percent": round(info["memory_percent"] or 0.0, 1),
                "status": info["status"] or "unknown",
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    # Sort by CPU descending and return top N
    procs.sort(key=lambda p: p["cpu_percent"], reverse=True)
    return procs[:limit]


def get_mount_usage(mounts_include: list[str]) -> list[dict]:
    """Collect disk usage + inode usage for specified mount points."""
    results = []
    for mount in mounts_include:
        try:
            usage = psutil.disk_usage(mount)
            entry: dict = {
                "mount_path": mount,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "used_percent": round(usage.percent, 1),
            }
            # Inode usage (Unix only)
            try:
                st = os.statvfs(mount)
                inode_total = st.f_files
                inode_used = inode_total - st.f_ffree
                entry["inode_total"] = inode_total
                entry["inode_used"] = inode_used
                entry["inode_percent"] = round((inode_used / inode_total) * 100, 1) if inode_total > 0 else 0.0
            except (AttributeError, OSError):
                entry["inode_total"] = None
                entry["inode_used"] = None
                entry["inode_percent"] = None
            results.append(entry)
        except (FileNotFoundError, PermissionError, OSError):
            pass
    return results


def collect_all(mounts_include: list[str]) -> dict:
    """Collect all system metrics and return as payload dict."""
    fds = get_open_fds()
    disk_io = get_disk_io()
    net_io = get_network_io()

    payload: dict = {
        "hostname": get_hostname(),
        "ip_address": get_ip_address(),
        "cpu_percent": get_cpu_percent(),
        "memory_percent": get_memory_percent(),
        "swap_percent": get_swap_percent(),
        "disk_percent_total": get_disk_percent_total(),
        "load_avg_1m": get_load_avg_1m(),
        "open_fds": fds["open_fds"],
        "max_fds": fds["max_fds"],
        "process_count": get_process_count(),
        "zombie_count": get_zombie_count(),
        "boot_time": get_boot_time(),
        "processes": get_top_processes(),
        "mounts": get_mount_usage(mounts_include),
    }
    if disk_io:
        payload.update(disk_io)
    if net_io:
        payload.update(net_io)
    return payload
