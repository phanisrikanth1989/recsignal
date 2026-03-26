"""
APM Data Simulator — Generates realistic APM data for RecSignal.
Sends business transactions, traces, logs, and diagnostics to the backend.

Usage:
    python apm_simulator.py --loop --interval 15
    python apm_simulator.py --once
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
import uuid
from datetime import datetime, timezone

import requests

BACKEND_URL = "http://localhost:8000"
API_KEY = "sample-secret-key"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

HOSTNAMES = ["app-server-01", "app-server-02", "api-gateway-01"]
APPS = ["order-service", "payment-service", "user-service", "inventory-service", "notification-service"]
ENDPOINTS = {
    "order-service": [
        ("POST", "/api/orders"),
        ("GET", "/api/orders"),
        ("GET", "/api/orders/{id}"),
        ("PUT", "/api/orders/{id}/status"),
    ],
    "payment-service": [
        ("POST", "/api/payments/charge"),
        ("POST", "/api/payments/refund"),
        ("GET", "/api/payments/{id}"),
    ],
    "user-service": [
        ("POST", "/api/users/register"),
        ("POST", "/api/users/login"),
        ("GET", "/api/users/{id}"),
        ("PUT", "/api/users/{id}/profile"),
    ],
    "inventory-service": [
        ("GET", "/api/inventory/{sku}"),
        ("PUT", "/api/inventory/{sku}/reserve"),
        ("POST", "/api/inventory/restock"),
    ],
    "notification-service": [
        ("POST", "/api/notifications/email"),
        ("POST", "/api/notifications/sms"),
    ],
}

LOG_LEVELS = ["INFO", "INFO", "INFO", "INFO", "WARN", "ERROR", "DEBUG"]
LOG_SOURCES = ["/var/log/app/order-service.log", "/var/log/app/payment-service.log", "/var/log/app/api-gateway.log"]
LOG_MESSAGES = {
    "INFO": [
        "Request processed successfully",
        "Database connection pool initialized",
        "Cache hit for key user:12345",
        "Scheduled job completed: cleanup_expired_sessions",
        "Health check passed",
    ],
    "WARN": [
        "Slow query detected: SELECT * FROM orders WHERE status='pending' (2.3s)",
        "Connection pool nearing capacity: 45/50 active",
        "Retry attempt 2/3 for payment gateway call",
        "High memory usage detected: 87% of heap used",
    ],
    "ERROR": [
        "Failed to connect to payment gateway: Connection timeout after 30s",
        "Unhandled exception in /api/orders: NullPointerException",
        "Database deadlock detected on table: order_items",
        "Circuit breaker OPEN for inventory-service",
    ],
    "DEBUG": [
        "Parsing request body for POST /api/orders",
        "SQL: SELECT id, name FROM users WHERE id = ?",
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_transactions(hostname: str) -> dict:
    """Generate a batch of business transactions."""
    transactions = []
    for _ in range(random.randint(5, 20)):
        app = random.choice(APPS)
        method, endpoint = random.choice(ENDPOINTS[app])
        is_error = 1 if random.random() < 0.05 else 0
        status_code = random.choice([500, 502, 503]) if is_error else 200
        response_time = random.gauss(150, 80) if not is_error else random.gauss(2000, 500)
        response_time = max(5, response_time)

        transactions.append({
            "app_name": app,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": round(response_time, 1),
            "is_error": is_error,
            "error_message": "Internal Server Error" if is_error else None,
            "trace_id": uuid.uuid4().hex,
            "collected_at": utc_now(),
        })

    return {"hostname": hostname, "transactions": transactions}


def generate_traces(hostname: str) -> dict:
    """Generate distributed traces with spans."""
    traces = []
    for _ in range(random.randint(2, 8)):
        trace_id = uuid.uuid4().hex
        root_app = random.choice(APPS)
        root_method, root_endpoint = random.choice(ENDPOINTS[root_app])
        root_span_id = uuid.uuid4().hex[:16]

        has_error = 1 if random.random() < 0.03 else 0
        root_duration = random.gauss(200, 100)
        root_duration = max(10, root_duration)

        started_at = utc_now()

        spans = [{
            "span_id": root_span_id,
            "parent_span_id": None,
            "service_name": root_app,
            "operation_name": f"{root_method} {root_endpoint}",
            "span_kind": "server",
            "status": "error" if has_error else "ok",
            "duration_ms": round(root_duration, 1),
            "started_at": started_at,
            "attributes": json.dumps({"http.method": root_method, "http.url": root_endpoint}),
        }]

        # Add child spans to other services
        downstream_count = random.randint(1, 3)
        downstream_apps = random.sample([a for a in APPS if a != root_app], min(downstream_count, len(APPS) - 1))

        for downstream in downstream_apps:
            child_method, child_endpoint = random.choice(ENDPOINTS[downstream])
            child_duration = random.gauss(50, 30)
            child_duration = max(2, min(child_duration, root_duration * 0.8))

            spans.append({
                "span_id": uuid.uuid4().hex[:16],
                "parent_span_id": root_span_id,
                "service_name": downstream,
                "operation_name": f"{child_method} {child_endpoint}",
                "span_kind": "client",
                "status": "ok",
                "duration_ms": round(child_duration, 1),
                "started_at": started_at,
            })

        traces.append({
            "trace_id": trace_id,
            "root_service": root_app,
            "root_endpoint": root_endpoint,
            "root_method": root_method,
            "status_code": 500 if has_error else 200,
            "total_duration_ms": round(root_duration, 1),
            "has_error": has_error,
            "started_at": started_at,
            "spans": spans,
        })

    return {"hostname": hostname, "traces": traces}


def generate_logs(hostname: str) -> dict:
    """Generate log entries."""
    logs = []
    for _ in range(random.randint(5, 25)):
        level = random.choice(LOG_LEVELS)
        messages = LOG_MESSAGES.get(level, LOG_MESSAGES["INFO"])
        logs.append({
            "source": random.choice(LOG_SOURCES),
            "level": level,
            "message": random.choice(messages),
            "trace_id": uuid.uuid4().hex if random.random() < 0.3 else None,
            "logged_at": utc_now(),
        })

    return {"hostname": hostname, "logs": logs}


def generate_diagnostic(hostname: str) -> dict:
    """Generate a diagnostic snapshot."""
    app = random.choice(APPS)
    snapshot_type = random.choice(["cpu_profile", "memory_profile", "thread_dump"])

    data: dict = {
        "hostname": hostname,
        "app_name": app,
        "snapshot_type": snapshot_type,
        "triggered_by": "auto",
        "collected_at": utc_now(),
    }

    if snapshot_type == "cpu_profile":
        data["duration_seconds"] = round(random.uniform(5, 30), 1)
        data["top_functions"] = json.dumps([
            {"function": "process_order", "file": "services/order.py", "line": 42, "cumtime": 0.85, "calls": 1200},
            {"function": "validate_payment", "file": "services/payment.py", "line": 78, "cumtime": 0.52, "calls": 800},
            {"function": "serialize_response", "file": "utils/serializer.py", "line": 15, "cumtime": 0.31, "calls": 3500},
            {"function": "db_query", "file": "db/session.py", "line": 23, "cumtime": 0.28, "calls": 950},
            {"function": "cache_lookup", "file": "cache/redis.py", "line": 11, "cumtime": 0.12, "calls": 2100},
        ])
    elif snapshot_type == "memory_profile":
        data["memory_summary"] = json.dumps({
            "rss_mb": round(random.uniform(200, 800), 1),
            "vms_mb": round(random.uniform(500, 2000), 1),
            "top_allocations": [
                {"type": "dict", "count": 45000, "size_mb": 12.3},
                {"type": "list", "count": 32000, "size_mb": 8.7},
                {"type": "str", "count": 110000, "size_mb": 6.2},
                {"type": "SQLAlchemy.Row", "count": 15000, "size_mb": 4.8},
            ],
        })
    else:  # thread_dump
        data["thread_dump"] = json.dumps([
            {"thread_id": 1, "name": "MainThread", "state": "RUNNING", "stack": ["main.py:45", "server.py:120"]},
            {"thread_id": 2, "name": "Worker-1", "state": "WAITING", "stack": ["queue.py:88", "worker.py:34"]},
            {"thread_id": 3, "name": "Worker-2", "state": "RUNNING", "stack": ["db/session.py:23", "services/order.py:42"]},
            {"thread_id": 4, "name": "HealthCheck", "state": "TIMED_WAITING", "stack": ["threading.py:300", "health.py:15"]},
        ])

    return data


def send_data(url: str, payload: dict) -> bool:
    try:
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return True
        print(f"  [WARN] {url} returned {resp.status_code}: {resp.text[:200]}")
        return False
    except requests.RequestException as e:
        print(f"  [ERROR] {url}: {e}")
        return False


def run_once():
    hostname = random.choice(HOSTNAMES)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Generating APM data for {hostname}")

    # Business Transactions
    bt_payload = generate_transactions(hostname)
    if send_data(f"{BACKEND_URL}/api/apm/transactions/ingest", bt_payload):
        print(f"  Sent {len(bt_payload['transactions'])} transactions")

    # Traces
    trace_payload = generate_traces(hostname)
    if send_data(f"{BACKEND_URL}/api/apm/traces/ingest", trace_payload):
        print(f"  Sent {len(trace_payload['traces'])} traces")

    # Logs
    log_payload = generate_logs(hostname)
    if send_data(f"{BACKEND_URL}/api/apm/logs/ingest", log_payload):
        print(f"  Sent {len(log_payload['logs'])} logs")

    # Diagnostics (occasionally)
    if random.random() < 0.3:
        diag_payload = generate_diagnostic(hostname)
        if send_data(f"{BACKEND_URL}/api/apm/diagnostics/ingest", diag_payload):
            print(f"  Sent {diag_payload['snapshot_type']} diagnostic")


def main():
    parser = argparse.ArgumentParser(description="RecSignal APM Data Simulator")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=15, help="Seconds between iterations (default: 15)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    print("RecSignal APM Simulator")
    print(f"Backend: {BACKEND_URL}")

    if args.once or not args.loop:
        run_once()
    else:
        print(f"Looping every {args.interval}s (Ctrl+C to stop)")
        while True:
            try:
                run_once()
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\nStopped.")
                break


if __name__ == "__main__":
    main()
