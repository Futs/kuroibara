from fastapi import APIRouter

from app.api.api_v2.endpoints import admin, downloads, me, mangaupdates, reading, series, setup, sources

api_v2_router = APIRouter()
# Sources routes are registered before series so "/sources/{module:path}" cannot shadow other prefixes.
api_v2_router.include_router(sources.router, prefix="/sources", tags=["Sources"])
api_v2_router.include_router(series.router, prefix="/series", tags=["Series"])
api_v2_router.include_router(reading.router, prefix="", tags=["Reading"])
api_v2_router.include_router(me.router, prefix="/me", tags=["Me"])
api_v2_router.include_router(mangaupdates.router, prefix="", tags=["MangaUpdates"])
api_v2_router.include_router(downloads.router, prefix="", tags=["Downloads"])
api_v2_router.include_router(setup.router, prefix="/setup", tags=["Setup"])
api_v2_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
