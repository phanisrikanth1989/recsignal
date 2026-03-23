# RecSignal - Deployment Guide

## Production Deployment

### Infrastructure Requirements

#### Central Server (Backend + Frontend)

- 1 Linux VM (4 CPU, 8 GB RAM recommended)
- Oracle Database access (separate DB server or same VM)
- SMTP relay access
- SSL certificate (for HTTPS)
- DNS entry for UI/API
- Nginx reverse proxy

#### Per Monitored Unix Server

- Python 3.11+
- `psutil` package
- Outbound HTTPS access to backend API
- systemd for service management

---

## Deployment Steps

### 1. Oracle Database

Ensure the `recsignal` schema exists with all tables from `infra/sql/oracle_schema.sql`.

```bash
sqlplus recsignal/recsignal@<host>:1521/<service> @infra/sql/oracle_schema.sql
```

### 2. Backend Deployment

```bash
# On the central server
mkdir -p /opt/recsignal/backend
cd /opt/recsignal/backend

# Copy backend code
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env from template
cp .env.example .env
# Edit .env with production Oracle DSN, SMTP config, API key

# Run with Uvicorn behind Nginx
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
```

Consider using systemd or supervisord to manage the process:

```ini
[Unit]
Description=RecSignal Backend
After=network.target

[Service]
User=recsignal
WorkingDirectory=/opt/recsignal/backend
ExecStart=/opt/recsignal/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. Frontend Deployment

```bash
cd /opt/recsignal/frontend
npm install
npm run build

# Serve dist/ via Nginx
```

### 4. Nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name recsignal.yourcompany.com;

    ssl_certificate     /etc/ssl/certs/recsignal.crt;
    ssl_certificate_key /etc/ssl/private/recsignal.key;

    root /opt/recsignal/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### 5. Agent Deployment (Per Unix Server)

```bash
mkdir -p /opt/recsignal-agent
cd /opt/recsignal-agent

# Copy agent files
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Edit config
vi config/config.yaml
# Set backend_url to https://recsignal.yourcompany.com/api/agent/metrics
# Set api_key to match backend AGENT_API_KEY
# Set environment (prod/staging/dev)
# Set mounts_include to relevant mount points

# Install and start service
sudo cp unix/server-monitor-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable server-monitor-agent
sudo systemctl start server-monitor-agent

# Verify
sudo systemctl status server-monitor-agent
journalctl -u server-monitor-agent -f
```

---

## Monitoring Intervals

| Parameter              | Value       |
|------------------------|-------------|
| Agent collection       | 15 minutes  |
| Stale heartbeat        | 20 minutes  |
| Frontend auto-refresh  | 60 seconds  |

---

## Phase 2 Enhancements

- Authentication / RBAC
- Metric charts and trend graphs
- Slack / Teams integration
- Host grouping and filtering
- Bulk alert acknowledgement
- Data retention / archival
- Agent auto-update mechanism
- Performance metrics baseline
