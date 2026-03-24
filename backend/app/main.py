from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.database import engine
from app.db.base import Base
from app.models import *  # noqa: F401,F403  – registers all models with Base
from app.api.routes import health, version, agent, dashboard, hosts, metrics, alerts, auth, ws


def _seed_defaults(eng):
    """Insert default alert rules and notification target if tables are empty."""
    from sqlalchemy.orm import Session
    from app.models.alert_rule import AlertRule
    from app.models.notification_target import NotificationTarget

    with Session(eng) as session:
        if session.query(AlertRule).count() == 0:
            defaults = [
                AlertRule(rule_name="CPU Warning", metric_name="cpu_percent", operator=">", threshold_value=85, severity="warning"),
                AlertRule(rule_name="CPU Critical", metric_name="cpu_percent", operator=">", threshold_value=95, severity="critical"),
                AlertRule(rule_name="Memory Warning", metric_name="memory_percent", operator=">", threshold_value=85, severity="warning"),
                AlertRule(rule_name="Memory Critical", metric_name="memory_percent", operator=">", threshold_value=95, severity="critical"),
                AlertRule(rule_name="Disk Warning", metric_name="disk_percent_total", operator=">", threshold_value=85, severity="warning"),
                AlertRule(rule_name="Disk Critical", metric_name="disk_percent_total", operator=">", threshold_value=95, severity="critical"),
                AlertRule(rule_name="Mount Warning", metric_name="mount_used_percent", operator=">", threshold_value=85, severity="warning"),
                AlertRule(rule_name="Mount Critical", metric_name="mount_used_percent", operator=">", threshold_value=95, severity="critical"),
            ]
            session.add_all(defaults)
            session.commit()
        if session.query(NotificationTarget).count() == 0:
            session.add(NotificationTarget(support_group="default", email_to="ops-team@example.com"))
            session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.DEBUG)
    # Create tables and seed data
    Base.metadata.create_all(bind=engine)
    _seed_defaults(engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # CORS
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(auth.router, tags=["Auth"])
    app.include_router(health.router, tags=["Health"])
    app.include_router(version.router, tags=["Version"])
    app.include_router(agent.router, tags=["Agent"])
    app.include_router(dashboard.router, tags=["Dashboard"])
    app.include_router(hosts.router, tags=["Hosts"])
    app.include_router(metrics.router, tags=["Metrics"])
    app.include_router(alerts.router, tags=["Alerts"])
    app.include_router(ws.router)

    return app


app = create_app()
