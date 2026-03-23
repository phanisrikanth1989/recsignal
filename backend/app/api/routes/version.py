from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter()


@router.get("/api/version")
def get_version():
    settings = get_settings()
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
