from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
import asyncio

from app.core.config import get_settings
from app.api import api_router
from app.services.cleanup.service import cleanup_service


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


cleanup_task: Optional[asyncio.Task] = None


async def periodic_cleanup():
    """Run periodic cleanup tasks."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            logger.info("running_periodic_cleanup")
            cleanup_service.run_all_cleanups()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("periodic_cleanup_failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global cleanup_task
    logger.info("application_startup", app_name=get_settings().APP_NAME)
    cleanup_task = asyncio.create_task(periodic_cleanup())
    yield
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # CORS middleware with production-ready configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
        max_age=3600,
    )

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    app.include_router(api_router, prefix="/api")

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.APP_VERSION}

    @app.get("/ready")
    async def readiness_check():
        # Check database connectivity
        try:
            from app.core.database import get_db_session
            with get_db_session() as db:
                db.execute("SELECT 1")
            return {"status": "ready", "database": "connected"}
        except Exception as e:
            logger.error("readiness_check_failed", error=str(e))
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "database": "disconnected", "error": str(e)},
            )

    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
        }

    return app


app = create_app()