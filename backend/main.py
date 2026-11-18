"""
BusArrival AI - Backend Application Entry Point
FastAPI REST API server with MongoDB Atlas, JWT authentication, and role guards.
Fails fast on startup if configuration is missing or invalid.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings

# Immediately validate configuration on module load.
# Startup will fail fast with a clear error banner if .env is missing or invalid.
settings = get_settings()

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.deps import limiter
from backend.routers import health, auth, audit, routes, trips, import_data, analytics, features, models, predict, accuracy, reports, admin


app = FastAPI(
    title="BusArrival AI API",
    description="Predictive Public Transit Arrival-Time Intelligence API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach SlowAPI Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Custom Request Validation Error Handler formatted per Section 12: {detail, code, fields}
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    field_errors = {}
    for err in exc.errors():
        loc = ".".join(str(l) for l in err["loc"] if l != "body")
        field_errors[loc or "body"] = err["msg"]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Input validation failed. Please check the submitted fields.",
            "code": "VALIDATION_ERROR",
            "fields": field_errors,
        },
    )


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount Routers under /api
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(routes.router, prefix="/api")
app.include_router(trips.router, prefix="/api")
app.include_router(import_data.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(features.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(predict.router, prefix="/api")
app.include_router(predict.alerts_router, prefix="/api")
app.include_router(accuracy.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Verify database connection and initialize indexes upon startup."""
    if os.getenv("APP_ENV") == "test" or os.getenv("TESTING") == "true" or settings.APP_ENV == "test":
        return
    try:
        from src.db.mongo import init_database
        init_database()
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.APP_ENV == "development",
    )
