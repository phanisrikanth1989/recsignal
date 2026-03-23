from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.alert import Alert
from app.models.host import Host
from app.models.notification_target import NotificationTarget

logger = logging.getLogger(__name__)


def _get_recipients(db: Session, support_group: str | None) -> list[str]:
    """Look up email recipients for a support group."""
    group = support_group or "default"
    targets = (
        db.query(NotificationTarget)
        .filter(NotificationTarget.support_group == group, NotificationTarget.is_active == 1)
        .all()
    )
    if not targets:
        # Fallback to default group
        targets = (
            db.query(NotificationTarget)
            .filter(NotificationTarget.support_group == "default", NotificationTarget.is_active == 1)
            .all()
        )
    return [t.email_to for t in targets]


def send_alert_email(db: Session, alert: Alert, host: Host) -> bool:
    """Send email notification for a new alert. Returns True on success."""
    settings = get_settings()

    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured, skipping email for alert id=%s", alert.id)
        return False

    recipients = _get_recipients(db, host.support_group)
    if not recipients:
        logger.warning("No email recipients found for host %s (group: %s)", host.hostname, host.support_group)
        return False

    subject = f"[{alert.severity.upper()}] {host.hostname} - {alert.metric_name}"
    body = (
        f"Alert: {alert.message}\n\n"
        f"Host: {host.hostname}\n"
        f"IP: {host.ip_address}\n"
        f"Environment: {host.environment}\n"
        f"Severity: {alert.severity}\n"
        f"Metric: {alert.metric_name}\n"
        f"Triggered At: {alert.triggered_at}\n\n"
        f"-- RecSignal Monitoring"
    )

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        if settings.SMTP_USE_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)

        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        server.sendmail(settings.SMTP_FROM_EMAIL, recipients, msg.as_string())
        server.quit()

        alert.email_sent = 1
        db.flush()
        logger.info("Alert email sent for alert id=%s to %s", alert.id, recipients)
        return True
    except Exception:
        logger.exception("Failed to send alert email for alert id=%s", alert.id)
        return False
