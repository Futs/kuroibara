from typing import Any, List, Optional, Dict
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.providers.registry import provider_registry
from app.models.user import User
from app.schemas.search import SearchQuery, SearchFilter, SearchResponse, SearchResult, ProviderInfo

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/providers", response_model=List[ProviderInfo])
async def get_providers(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get available search providers.
    """
    return provider_registry.get_provider_info()


@router.post("", response_model=SearchResponse)
async def search_manga(
    query: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Search for manga across providers.

    Args:
        query: The search query
        current_user: The current user
        db: The database session
    """
    # If provider is specified, use that provider
    if query.provider:
        provider = provider_registry.get_provider(query.provider)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider '{query.provider}' not found",
            )

        # Search using the provider
        try:
            results, total, has_next = await provider.search(
                query=query.query,
                page=query.page,
                limit=query.limit,
            )

            return {
                "results": results,
                "total": total,
                "page": query.page,
                "limit": query.limit,
                "has_next": has_next,
            }
        except Exception as e:
            logger.error(f"Error searching with provider {provider.name}: {e}")
            return {
                "results": [],
                "total": 0,
                "page": query.page,
                "limit": query.limit,
                "has_next": False,
            }

    # If no provider is specified, search across multiple providers
    # Use a limited number of providers to avoid overwhelming the system
    providers = provider_registry.get_all_providers()

    # Limit to 5 providers for performance
    max_providers = 5
    selected_providers = providers[:max_providers]

    # Search with all selected providers concurrently
    async def search_with_provider(provider):
        try:
            results, _, _ = await provider.search(
                query=query.query,
                page=query.page,
                limit=query.limit // len(selected_providers),  # Distribute limit among providers
            )
            return results
        except Exception as e:
            logger.error(f"Error searching with provider {provider.name}: {e}")
            return []

    # Run searches concurrently
    search_tasks = [search_with_provider(provider) for provider in selected_providers]
    all_results = await asyncio.gather(*search_tasks)

    # Flatten results
    flattened_results = []
    for results in all_results:
        flattened_results.extend(results)

    # Limit results to requested limit
    limited_results = flattened_results[:query.limit]

    return {
        "results": limited_results,
        "total": len(flattened_results),
        "page": query.page,
        "limit": query.limit,
        "has_next": len(flattened_results) > query.limit,
    }


@router.post("/filter", response_model=SearchResponse)
async def filter_manga(
    filter_data: SearchFilter,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Filter manga by various criteria.
    """
    # This would be implemented to filter manga by various criteria
    # For now, return a mock response

    # In a real implementation, this would query the database or external APIs
    # based on the filter criteria

    # Mock response for demonstration purposes
    return {
        "results": [],
        "total": 0,
        "page": page,
        "limit": limit,
        "has_next": False,
    }
