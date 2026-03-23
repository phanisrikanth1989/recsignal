# Phase 1 Scope - RecSignal Unix Server Monitoring

## Objective

Build a Phase 1 MVP for monitoring Unix server health and disk space.

## In Scope

- Monitor Unix server heartbeat (15-minute collection interval)
- Collect CPU, memory, disk usage per host
- Collect mount-point disk usage
- Store latest status and historical metrics in Oracle DB
- React dashboard for support team
- Server details page with metrics, mounts, history
- Alert threshold evaluation (CPU, memory, disk, mount, stale heartbeat)
- Email alerts via SMTP for new threshold breaches
- Lightweight Python agent on each Unix server
- Simulator for testing without real servers

## Not in Scope (Phase 2+)

- Kubernetes deployment
- Redis / Celery message queues
- SSH polling from backend
- Teams / Slack integrations
- Complex workflow engines
- Advanced auth / IAM / RBAC
- Auto-remediation
- Metric charting / graphing
- Audit logs

## Architecture

```
Unix Servers → Python Agent (every 15 min) → FastAPI Backend → Oracle DB
                                                  ↓
                                            Email Alerts (SMTP)
                                                  ↓
React Dashboard ← REST APIs ←─────────────── FastAPI Backend
```

## Technology Stack

| Component   | Technology                        |
|-------------|-----------------------------------|
| Backend     | Python 3.11+, FastAPI, SQLAlchemy |
| Database    | Oracle (XE / Enterprise)          |
| Frontend    | React, Vite, TypeScript, Tailwind |
| Agent       | Python 3.11+, psutil              |
| Email       | SMTP (smtplib)                    |

## Collection Interval

- Agent sends metrics every **15 minutes** (900 seconds)
- Stale heartbeat threshold: **20 minutes** (1 interval + 5 min buffer)

## Alert Thresholds (Default)

| Metric             | Warning | Critical |
|--------------------|---------|----------|
| CPU %              | > 85    | > 95     |
| Memory %           | > 85    | > 95     |
| Total Disk %       | > 85    | > 95     |
| Mount Usage %      | > 85    | > 95     |
| Stale Heartbeat    | > 20 minutes       |

## Host Status Logic

- `critical` - any open critical alert
- `warning` - any open warning alert
- `stale` - last heartbeat > 20 minutes ago
- `healthy` - no issues
