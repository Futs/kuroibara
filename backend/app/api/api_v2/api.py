from fastapi import APIRouter

from app.api.api_v2.endpoints import downloads, me, mangaupdates, reading, series, sources

api_v2_router = APIRouter()
# Sources routes are registered before series so "/sources/{module:path}" cannot shadow other prefixes.
api_v2_router.include_router(sources.router, prefix="/sources", tags=["Sources"])
api_v2_router.include_router(series.router, prefix="/series", tags=["Series"])
api_v2_router.include_router(reading.router, prefix="", tags=["Reading"])
api_v2_router.include_router(me.router, prefix="/me", tags=["Me"])
api_v2_router.include_router(mangaupdates.router, prefix="", tags=["MangaUpdates"])
api_v2_router.include_router(downloads.router, prefix="", tags=["Downloads"])
