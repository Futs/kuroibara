from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth,
    categories,
    favorites,
    import_files,
    library,
    manga,
    providers,
    reading_lists,
    search,
    user_provider_preferences,
    users,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(manga.router, prefix="/manga", tags=["Manga"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(
    reading_lists.router, prefix="/reading-lists", tags=["Reading Lists"]
)
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(library.router, prefix="/library", tags=["Library"])
api_router.include_router(import_files.router, prefix="/import", tags=["Import"])
api_router.include_router(providers.router, prefix="/providers", tags=["Providers"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])
api_router.include_router(
    user_provider_preferences.router,
    prefix="/users/me/provider-preferences",
    tags=["User Provider Preferences"],
)
