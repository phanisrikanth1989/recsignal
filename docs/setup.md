# RecSignal - Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm

---

## 1. Database

RecSignal uses **SQLite** by default — no external database setup needed. The database file (`recsignal.db`) is created automatically on first backend startup.

To use a different database, set `DATABASE_URL` in `backend/.env`:
```
DATABASE_URL=sqlite:///./recsignal.db
```

---

## 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed (defaults work out of the box)

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs

---

## 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend will be available at: http://localhost:8080

---

## 4. Run Simulator (Testing)

```bash
cd agent

# Install dependencies
pip install -r requirements.txt

# Send fake metrics from 4 UAT hosts (single run)
python simulator.py --hosts 4

# Continuous mode (every 30 seconds)
python simulator.py --hosts 4 --loop --interval 30
```

---

## 5. Deploy Agent on Unix Server

```bash
# On the target Unix server:
mkdir -p /opt/recsignal-agent
cd /opt/recsignal-agent

# Copy agent files
# Edit config/config.yaml with correct backend_url

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install systemd service
sudo cp unix/server-monitor-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable server-monitor-agent
sudo systemctl start server-monitor-agent
```

---

## 7. SMTP Configuration

Edit `backend/.env`:

```env
SMTP_HOST=smtp.yourcompany.com
SMTP_PORT=587
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=recsignal@yourcompany.com
SMTP_USE_TLS=true
```

Add notification targets in the database:

```sql
INSERT INTO notification_targets (support_group, email_to, is_active)
VALUES ('linux-team', 'linux-support@company.com', 1);
```
