# RecSignal - API Contract

Base URL: `http://localhost:8000`

---

## Health & Version

### GET /health

```json
{ "status": "ok" }
```

### GET /api/version

```json
{ "app": "RecSignal", "version": "1.0.0" }
```

---

## Agent Ingestion

### POST /api/agent/metrics

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: <api_key>`

**Request Body:**

```json
{
  "hostname": "unix-app-01",
  "ip_address": "10.10.1.20",
  "environment": "prod",
  "cpu_percent": 44.2,
  "memory_percent": 68.5,
  "disk_percent_total": 72.1,
  "load_avg_1m": 1.28,
  "mounts": [
    {
      "mount_path": "/",
      "total_gb": 100,
      "used_gb": 62,
      "used_percent": 62
    },
    {
      "mount_path": "/app",
      "total_gb": 200,
      "used_gb": 184,
      "used_percent": 92
    }
  ],
  "collected_at": "2026-03-23T10:00:00Z"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Metrics received",
  "host_id": 1
}
```

---

## Dashboard

### GET /api/dashboard/summary

```json
{
  "total_hosts": 10,
  "healthy_hosts": 6,
  "warning_hosts": 2,
  "critical_hosts": 1,
  "stale_hosts": 1,
  "active_alerts": 5
}
```

---

## Hosts

### GET /api/hosts

Returns array of:

```json
[
  {
    "id": 1,
    "hostname": "unix-app-01",
    "ip_address": "10.10.1.20",
    "environment": "prod",
    "status": "healthy",
    "cpu_percent": 44.2,
    "memory_percent": 68.5,
    "disk_percent_total": 72.1,
    "last_heartbeat_at": "2026-03-23T10:00:00"
  }
]
```

### GET /api/hosts/{host_id}

Returns full host detail including:
- host metadata
- latest metrics
- mount usage array
- recent_history array (last 96 entries)
- active_alerts array

### GET /api/hosts/{host_id}/metrics/latest

```json
{
  "cpu_percent": 44.2,
  "memory_percent": 68.5,
  "disk_percent_total": 72.1,
  "load_avg_1m": 1.28,
  "collected_at": "2026-03-23T10:00:00"
}
```

### GET /api/hosts/{host_id}/metrics/history?limit=96

Returns array of metric history entries.

---

## Alerts

### GET /api/alerts?status=OPEN&limit=200

```json
[
  {
    "id": 1,
    "host_id": 1,
    "hostname": "unix-app-01",
    "metric_name": "cpu_percent",
    "mount_path": null,
    "severity": "warning",
    "message": "cpu_percent is 88.5% (warning)",
    "status": "OPEN",
    "triggered_at": "2026-03-23T10:00:00",
    "resolved_at": null
  }
]
```

Query parameters:
- `status`: Filter by `OPEN` or `RESOLVED` (optional)
- `limit`: Max results (default 200, max 1000)
