"""
Mineploy - Minecraft Server Management Panel
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from core.config import settings
from core.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Runs on startup and shutdown.
    """
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📊 Database: MySQL ({settings.db_host}:{settings.db_port}/{settings.db_name})")
    print(f"🔧 Debug mode: {settings.debug}")

    # Initialize database
    await init_db()
    print("✅ Database initialized")

    yield

    # Shutdown
    print("🛑 Shutting down...")
    await close_db()
    print("✅ Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Open-source Minecraft server management panel",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint - redirect to docs
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


# Health check endpoint
@app.get(
    f"{settings.api_prefix}/health",
    tags=["Health"],
    summary="Health check",
    response_model=dict,
)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "mysql",
    }


# Info endpoint
@app.get(
    f"{settings.api_prefix}/info",
    tags=["Info"],
    summary="Application information",
    response_model=dict,
)
async def app_info():
    """
    Get application information.

    Returns:
        dict: Application metadata
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Open-source Minecraft server management panel",
        "repository": "https://github.com/yourusername/mineploy",
        "documentation": "https://docs.mineploy.dev",
        "max_servers": settings.max_servers,
        "features": {
            "multi_version": True,
            "console": True,
            "file_explorer": True,
            "backups": True,
            "multi_user": True,
            "rcon": True,
        },
    }


# Import and include routers
from api import setup, auth, users, permissions

app.include_router(setup.router, prefix=f"{settings.api_prefix}/setup")
app.include_router(auth.router, prefix=f"{settings.api_prefix}")
app.include_router(users.router, prefix=f"{settings.api_prefix}")
app.include_router(permissions.router, prefix=f"{settings.api_prefix}")

# Additional routers (will be created later)
# from api import servers, console, files, backups
# app.include_router(servers.router, prefix=f"{settings.api_prefix}/servers", tags=["Servers"])
# app.include_router(console.router, prefix=f"{settings.api_prefix}/console", tags=["Console"])
# app.include_router(files.router, prefix=f"{settings.api_prefix}/files", tags=["Files"])
# app.include_router(backups.router, prefix=f"{settings.api_prefix}/backups", tags=["Backups"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
