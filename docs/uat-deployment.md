# RecSignal — UAT Deployment Guide

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         UAT CENTRAL SERVER                         │
│                                                                     │
│   ┌───────────┐     ┌──────────────┐     ┌───────────────────────┐ │
│   │  Nginx    │────▶│  Backend     │────▶│  Oracle Database      │ │
│   │  (443)    │     │  (Uvicorn    │     │  (recsignal schema)   │ │
│   │           │     │   :8000)     │     │                       │ │
│   │  Serves   │     └──────────────┘     └───────────────────────┘ │
│   │  Frontend │                                                     │
│   │  (dist/)  │                                                     │
│   └───────────┘                                                     │
└─────────────────────────────────────────────────────────────────────┘
          ▲                    ▲
          │ HTTPS              │ POST /api/agent/metrics
          │                    │ POST /api/db-monitor/metrics
          │                    │
    ┌─────┘                    └──────────────────────────────┐
    │                                                          │
┌───┴───┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┴──┐
│Browser│  │UAT Srv 1│  │UAT Srv 2│  │UAT Srv 3│  │UAT Srv 4   │
│       │  │ (agent) │  │ (agent) │  │ (agent) │  │  (agent)   │
└───────┘  └─────────┘  └─────────┘  └─────────┘  └────────────┘
```

**Components:**

- **Central Server** — Runs Backend (FastAPI) + Frontend (static files) + Nginx reverse proxy
- **4 UAT Servers** — Each runs the RecSignal agent that collects and pushes OS metrics
- **Oracle Database** — Stores all metrics, alerts, DB monitoring data

---

## Prerequisites

| Component | Requirement |
| --- | --- |
| Central Server | Linux (RHEL/OEL 7+), Python 3.11+, Node.js 18+, Nginx |
| UAT Servers (x4) | Linux (any), Python 3.11+, psutil |
| Oracle DB | Oracle 12c+ with a dedicated schema |
| Network | UAT servers to Central server (port 443 or 8000) |
| SMTP | Relay host for alert emails (optional) |

---

## PART 1 — Oracle Database Setup

### 1.1 Create Schema User

```sql
-- Connect as SYSDBA
CREATE USER recsignal_owner IDENTIFIED BY "<strong_password>"
    DEFAULT TABLESPACE USERS
    TEMPORARY TABLESPACE TEMP
    QUOTA UNLIMITED ON USERS;

GRANT CONNECT, RESOURCE TO recsignal_owner;
GRANT CREATE TABLE, CREATE SEQUENCE, CREATE INDEX TO recsignal_owner;
```

### 1.2 Run DDL Script

```bash
cd /path/to/recsignal

# Option A: SQL*Plus
sqlplus recsignal_owner/<password>@<host>:1521/<service_name> @infra/sql/oracle_ddl.sql

# Option B: SQL Developer
# Open infra/sql/oracle_ddl.sql and execute as recsignal_owner
```

### 1.3 Verify Tables Created

```sql
-- Should return 13 tables
SELECT table_name FROM user_tables
WHERE table_name LIKE 'RECSIGNAL_%'
ORDER BY table_name;
```

Expected output:

```text
RECSIGNAL_ALERT_RULES
RECSIGNAL_ALERTS
RECSIGNAL_DB_INSTANCES
RECSIGNAL_DB_PERFORMANCE
RECSIGNAL_DB_SESSIONS
RECSIGNAL_DB_SLOW_QUERIES
RECSIGNAL_HOSTS
RECSIGNAL_METRICS_HISTORY
RECSIGNAL_METRICS_LATEST
RECSIGNAL_MOUNT_METRICS
RECSIGNAL_NOTIFICATION_TARGETS
RECSIGNAL_PROCESS_SNAPSHOTS
RECSIGNAL_TABLESPACE_METRICS
```

---

## PART 2 — Backend Deployment (Central Server)

### 2.1 Install System Dependencies

```bash
# RHEL / OEL
sudo yum install python3.11 python3.11-pip python3.11-devel nginx gcc

# Or if Python 3.11 is not in standard repos:
sudo yum install python311 python311-pip -y
```

### 2.2 Deploy Backend Code

```bash
sudo mkdir -p /opt/recsignal/backend
sudo chown $(whoami):$(whoami) /opt/recsignal

# Copy backend code from your repo
cp -r backend/* /opt/recsignal/backend/

cd /opt/recsignal/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Oracle DB driver for SQLAlchemy
pip install oracledb
```

### 2.3 Configure Environment File

Create `/opt/recsignal/backend/.env`:

```env
# ── App ───────────────────────────────────────────────────────
APP_NAME=RecSignal
APP_VERSION=1.0.0
DEBUG=false

# ── CORS (frontend URL) ──────────────────────────────────────
ALLOWED_ORIGINS=https://recsignal-uat.yourcompany.com

# ── Database (Oracle) ────────────────────────────────────────
# Format: oracle+oracledb://user:password@host:port/?service_name=XXX
DATABASE_URL=oracle+oracledb://recsignal_owner:<password>@<db_host>:1521/?service_name=<service_name>

# ── SMTP (for alert emails) ──────────────────────────────────
SMTP_HOST=smtp.yourcompany.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=recsignal-uat@yourcompany.com
SMTP_USE_TLS=true

# ── Security ─────────────────────────────────────────────────
# This key must match what agents use. Change to a strong random value.
AGENT_API_KEY=<generate_a_strong_random_key>
SECRET_KEY=<generate_another_random_key>

# ── Monitoring Thresholds ────────────────────────────────────
STALE_THRESHOLD_MINUTES=2
HISTORY_INTERVAL_SECONDS=300
```

> **Generate strong keys:**
>
> ```bash
> python3 -c "import secrets; print(secrets.token_urlsafe(32))"
> ```

### 2.4 Secure the .env File

```bash
chmod 600 /opt/recsignal/backend/.env
```

### 2.5 Test Backend Manually

```bash
cd /opt/recsignal/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify:

```bash
curl http://127.0.0.1:8000/health
# Expected: {"status":"ok"}

curl http://127.0.0.1:8000/api/version
# Expected: {"app":"RecSignal","version":"1.0.0"}
```

### 2.6 Create systemd Service

Create `/etc/systemd/system/recsignal-backend.service`:

```ini
[Unit]
Description=RecSignal Backend (Uvicorn)
After=network.target

[Service]
Type=simple
User=recsignal
Group=recsignal
WorkingDirectory=/opt/recsignal/backend
EnvironmentFile=/opt/recsignal/backend/.env
ExecStart=/opt/recsignal/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=recsignal-backend

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
# Create service user (if not exists)
sudo useradd --system --no-create-home --shell /usr/sbin/nologin recsignal
sudo chown -R recsignal:recsignal /opt/recsignal

sudo systemctl daemon-reload
sudo systemctl enable recsignal-backend
sudo systemctl start recsignal-backend

# Check status
sudo systemctl status recsignal-backend
journalctl -u recsignal-backend -f
```

---

## PART 3 — Frontend Deployment (Central Server)

### 3.1 Build Frontend

```bash
# On your build machine (or on the central server if Node.js is installed)
cd frontend

npm install
npm run build
# Output: frontend/dist/
```

### 3.2 Deploy Static Files

```bash
sudo mkdir -p /opt/recsignal/frontend
sudo cp -r dist/* /opt/recsignal/frontend/
sudo chown -R recsignal:recsignal /opt/recsignal/frontend
```

### 3.3 Configure Nginx

Create `/etc/nginx/conf.d/recsignal.conf`:

```nginx
server {
    listen 80;
    server_name recsignal-uat.yourcompany.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name recsignal-uat.yourcompany.com;

    ssl_certificate     /etc/ssl/certs/recsignal-uat.crt;
    ssl_certificate_key /etc/ssl/private/recsignal-uat.key;

    # Frontend — Serve static files
    root /opt/recsignal/frontend;
    index index.html;

    # SPA fallback — all non-API routes serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API — Proxy to Uvicorn backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

> **Note:** If you don't have SSL certificates, use HTTP only for UAT by removing the SSL block and changing `listen 80;` in the second server block.

Enable and start:

```bash
sudo nginx -t                 # Validate config
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### 3.4 Verify Frontend

Open browser: `https://recsignal-uat.yourcompany.com`

The Dashboard page should load directly (no login required).

---

## PART 4 — Agent Deployment (All 4 UAT Servers)

> **Repeat these steps on each of the 4 UAT servers.**

### 4.1 Install Dependencies

```bash
sudo yum install python3.11 python3.11-pip -y
# Or: sudo apt install python3.11 python3.11-venv -y
```

### 4.2 Deploy Agent Code

```bash
sudo mkdir -p /opt/recsignal-agent
sudo chown $(whoami):$(whoami) /opt/recsignal-agent

# Copy agent files from your repo
cp -r agent/* /opt/recsignal-agent/

cd /opt/recsignal-agent

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3 Configure Agent

Edit `/opt/recsignal-agent/config/config.yaml`:

```yaml
# Backend URL — point to the central server
backend_url: "https://recsignal-uat.yourcompany.com/api/agent/metrics"

# Must match AGENT_API_KEY in backend .env
api_key: "<same_key_as_backend_AGENT_API_KEY>"

# Environment tag
environment: "uat"

# Collection interval (seconds)
interval_seconds: 10

# Mount points to monitor (adjust per server)
mounts_include:
  - /
  - /opt
  - /var
  - /tmp
  - /home
  - /data01
  - /oradata

# Log file
log_file: "/var/log/recsignal-agent.log"
```

> **Adjust `mounts_include`** per server — list only the mount points that exist on that server.

### 4.4 Create Log File

```bash
sudo touch /var/log/recsignal-agent.log
sudo chown recsignal:recsignal /var/log/recsignal-agent.log
```

### 4.5 Install systemd Service

```bash
sudo cp /opt/recsignal-agent/unix/server-monitor-agent.service /etc/systemd/system/recsignal-agent.service

sudo systemctl daemon-reload
sudo systemctl enable recsignal-agent
sudo systemctl start recsignal-agent
```

### 4.6 Verify Agent is Running

```bash
# Check service status
sudo systemctl status recsignal-agent

# Watch logs
journalctl -u recsignal-agent -f

# You should see:
# Collected: cpu=12.3% mem=45.6% disk=67.8% load=0.5200 mounts=7
# Metrics sent successfully (HTTP 200)
```

### 4.7 Verify Data in UI

After all 4 agents are running:

1. Open the RecSignal Dashboard
2. Server Monitor tab should show 4 hosts
3. Each host should show CPU, Memory, Disk metrics
4. Click a host to see detailed metrics, mounts, processes

---

## PART 5 — DB Monitoring Agent (Optional)

If you want to monitor Oracle databases from the UAT servers:

### 5.1 Configure DB Agent

Edit `/opt/recsignal-agent/config/db_config.yaml`:

```yaml
backend_url: "https://recsignal-uat.yourcompany.com/api/db-monitor/metrics"
api_key: "<same_key_as_backend_AGENT_API_KEY>"
interval_seconds: 30
password_script: /opt/recsignal-agent/bin/get_db_password.sh
db_instances_file: config/db_instances.cfg
```

Edit `/opt/recsignal-agent/config/db_instances.cfg`:

```text
# Format: environment|schema:DBNAME|host|port|schema|servicename|oraclehomepath
UAT|recsignal_mon:ORCL_UAT1|db-uat-01.internal|1521|recsignal_mon|orcl_uat1.svc|/opt/oracle/product/19c/dbhome_1
UAT|recsignal_mon:ORCL_UAT2|db-uat-02.internal|1521|recsignal_mon|orcl_uat2.svc|/opt/oracle/product/19c/dbhome_1
```

### 5.2 Set Up Password Script

```bash
# Copy and customize the password script
cp /opt/recsignal-agent/scripts/get_db_password.sh /opt/recsignal-agent/bin/
chmod 700 /opt/recsignal-agent/bin/get_db_password.sh

# Edit with your credential-store logic (CyberArk, Vault, etc.)
vi /opt/recsignal-agent/bin/get_db_password.sh

# Test it manually
/opt/recsignal-agent/bin/get_db_password.sh ORCL_UAT1 recsignal_mon
```

### 5.3 Create Oracle Monitoring User (on DB server)

```sql
-- Connect as SYSDBA on each Oracle instance
CREATE USER recsignal_mon IDENTIFIED BY "<strong_password>"
    DEFAULT TABLESPACE USERS
    TEMPORARY TABLESPACE TEMP
    QUOTA 0 ON USERS;

-- Read-only grants (NO data modification)
GRANT CREATE SESSION TO recsignal_mon;
GRANT SELECT ON v_$session TO recsignal_mon;
GRANT SELECT ON v_$sql TO recsignal_mon;
GRANT SELECT ON v_$sysstat TO recsignal_mon;
GRANT SELECT ON v_$librarycache TO recsignal_mon;
GRANT SELECT ON v_$sga TO recsignal_mon;
GRANT SELECT ON v_$pgastat TO recsignal_mon;
GRANT SELECT ON v_$parameter TO recsignal_mon;
GRANT SELECT ON v_$instance TO recsignal_mon;
GRANT SELECT ON dba_data_files TO recsignal_mon;
GRANT SELECT ON dba_free_space TO recsignal_mon;
```

### 5.4 Create DB Agent Service

Create `/etc/systemd/system/recsignal-db-agent.service`:

```ini
[Unit]
Description=RecSignal DB Monitor Agent
After=network.target

[Service]
Type=simple
User=recsignal
Group=recsignal
WorkingDirectory=/opt/recsignal-agent
ExecStart=/opt/recsignal-agent/venv/bin/python db_agent.py --loop --interval 30
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=recsignal-db-agent

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable recsignal-db-agent
sudo systemctl start recsignal-db-agent
```

---

## Quick Reference — All Services

| Service                 | Server          | Command                                                  |
|-------------------------|-----------------|----------------------------------------------------------|
| Backend (Uvicorn)       | Central         | `sudo systemctl start recsignal-backend`                 |
| Nginx                   | Central         | `sudo systemctl start nginx`                             |
| Server Agent            | UAT 1-4         | `sudo systemctl start recsignal-agent`                   |
| DB Agent (optional)     | Central or UAT  | `sudo systemctl start recsignal-db-agent`                |

### Start All

```bash
# Central server
sudo systemctl start recsignal-backend nginx

# Each UAT server
sudo systemctl start recsignal-agent
```

### Stop All

```bash
# Each UAT server
sudo systemctl stop recsignal-agent

# Central server
sudo systemctl stop recsignal-backend
```

### View Logs

```bash
# Backend logs
journalctl -u recsignal-backend -f

# Agent logs (on each UAT server)
journalctl -u recsignal-agent -f

# Nginx access/error logs
tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

---

## Troubleshooting

### Agent cannot reach backend

```bash
# Test connectivity from UAT server
curl -X POST https://recsignal-uat.yourcompany.com/api/agent/metrics \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your_api_key>" \
  -d '{"hostname":"test","cpu_percent": 10}'

# If using self-signed SSL, add to agent config or disable verification
```

### Backend cannot connect to Oracle

```bash
cd /opt/recsignal/backend
source venv/bin/activate
python -c "
from sqlalchemy import create_engine, text
e = create_engine('oracle+oracledb://recsignal_owner:<pwd>@<host>:1521/?service_name=<svc>')
with e.connect() as c:
    print(c.execute(text('SELECT 1 FROM dual')).fetchone())
"
```

### Host shows STALE in Dashboard

- Agent is not running or cannot POST to backend
- Check agent logs: `journalctl -u recsignal-agent -f`
- Check firewall rules between UAT server and central server
- Verify `api_key` in agent config matches `AGENT_API_KEY` in backend `.env`

### Frontend shows blank page

- Check Nginx serves the correct `dist/` folder
- Verify `try_files` directive includes `/index.html` fallback
- Check browser console for errors (F12 → Console)

### Tables not found error

- Ensure DDL was run against the correct schema
- Verify `DATABASE_URL` in `.env` connects to that schema
- Run verification query in section 1.3

---

## Checklist

- [ ] Oracle schema created and DDL executed (13 tables + indexes + seed data)
- [ ] Backend deployed and tested (`/health` returns OK)
- [ ] `.env` configured with correct Oracle DSN, API key, SMTP
- [ ] Frontend built (`npm run build`) and `dist/` deployed to Nginx
- [ ] Nginx configured and running (HTTPS → proxy to :8000)
- [ ] Agent deployed on UAT Server 1 and verified
- [ ] Agent deployed on UAT Server 2 and verified
- [ ] Agent deployed on UAT Server 3 and verified
- [ ] Agent deployed on UAT Server 4 and verified
- [ ] Dashboard shows all 4 hosts with live metrics
- [ ] DB Agent configured and running (if monitoring Oracle)
- [ ] Alert email notification tested (optional)
