from fastapi import APIRouter
from app.api.datasets import router as datasets_router
from app.api.analytics import router as analytics_router
from app.api.ai import router as ai_router
from app.api.visualization import router as visualization_router
from app.api.dashboard import router as dashboard_router
from app.api.reports import router as reports_router
from app.api.auth import router as auth_router

api_router = APIRouter()

api_router.include_router(datasets_router)
api_router.include_router(analytics_router)
api_router.include_router(ai_router)
api_router.include_router(visualization_router)
api_router.include_router(dashboard_router)
api_router.include_router(reports_router)
api_router.include_router(auth_router)