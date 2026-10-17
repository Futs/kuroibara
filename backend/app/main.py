from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.api.api_v2.api import api_v2_router
from app.core.config import settings
from app.core.events import lifespan

# Import provider registry to ensure it's initialized

app = FastAPI(
    title=settings.APP_NAME,
    description="API for Kuroibara manga/manhua/manhwa library",
    version="0.7.2",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Set up CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

SETUP_OPEN_PREFIXES = ("/api/v2/setup", "/api/v1/health", "/api/docs", "/api/redoc", "/api/openapi.json")


@app.middleware("http")
async def first_run_guard(request, call_next):
    """Until first-run setup is complete, the API answers 503 (with the setup location), except setup itself."""
    from fastapi.responses import JSONResponse

    from app.core import setup as setup_state

    path = request.url.path
    if setup_state.required() and path.startswith("/api/") and not path.startswith(SETUP_OPEN_PREFIXES):
        return JSONResponse(status_code=503, content={"setup_required": True, "setup_url": "/setup"})
    return await call_next(request)


# Include API router
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_v2_router, prefix="/api/v2")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
