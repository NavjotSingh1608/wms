"""
WMS FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import (
    auth, grn, qc, dispensing, retesting,
    grade_transfer, finished_goods, qr, reports, notifications, audit,
)

app = FastAPI(
    title="WMS API",
    description="Warehouse Management System — API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Health check for Docker and load balancers."""
    return {"status": "ok", "service": "wms-api"}


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(grn.router, prefix="/api/v1", tags=["grn"])
app.include_router(qc.router, prefix="/api/v1", tags=["qc"])
app.include_router(dispensing.router, prefix="/api/v1", tags=["dispensing"])
app.include_router(retesting.router, prefix="/api/v1", tags=["retesting"])
app.include_router(grade_transfer.router, prefix="/api/v1", tags=["grade-transfer"])
app.include_router(finished_goods.router, prefix="/api/v1", tags=["finished-goods"])
app.include_router(qr.router, prefix="/api/v1", tags=["qr"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])


# Optional: create tables on startup (alternative to Alembic for first run)
# Uncomment only if not using Alembic yet.
# @app.on_event("startup")
# async def startup():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
