"""System health monitoring endpoints.

These endpoints are public (no authentication required) as they are typically
used by monitoring systems, load balancers, and health check services.
"""

import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.providers.registry import provider_registry
from app.core.services.tiered_indexing import tiered_search_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error messages to prevent information disclosure.

    Logs the full error for debugging but returns a generic message
    to external users to prevent exposing sensitive system information.
    """
    # Log the full error for debugging
    logger.error(f"Health check error: {error}", exc_info=True)

    # Return generic message to prevent information disclosure
    return "Service temporarily unavailable"


@router.get("/")
async def system_health(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comprehensive system health status.

    Returns health information for:
    - Database connectivity
    - Indexer services (MangaUpdates, MadaraDex, MangaDex)
    - Provider registry
    - Overall system status
    """
    start_time = time.time()
    health_data = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",  # TODO: Get from version file
        "components": {},
        "summary": {},
    }

    # Track component health
    healthy_components = 0
    total_components = 0

    try:
        # 1. Database Health Check
        total_components += 1
        try:
            db_start = time.time()
            result = await db.execute(text("SELECT 1"))
            db_response_time = (time.time() - db_start) * 1000  # ms

            health_data["components"]["database"] = {
                "status": "healthy",
                "response_time_ms": round(db_response_time, 2),
                "message": "Database connection successful",
            }
            healthy_components += 1

        except Exception as e:
            health_data["components"]["database"] = {
                "status": "unhealthy",
                "response_time_ms": None,
                "message": f"Database connection failed: {_sanitize_error_message(e)}",
            }
            health_data["status"] = "degraded"

        # 2. Indexer Services Health Check
        total_components += 1
        try:
            indexer_start = time.time()
            indexer_health = await tiered_search_service.test_all_indexers()
            indexer_response_time = (time.time() - indexer_start) * 1000  # ms

            indexer_healthy = 0
            indexer_total = len(indexer_health)
            indexer_details = {}

            for indexer_name, (is_healthy, message) in indexer_health.items():
                tier = (
                    "primary"
                    if indexer_name == "MangaUpdates"
                    else "secondary" if indexer_name == "MadaraDex" else "tertiary"
                )

                indexer_details[indexer_name.lower()] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "tier": tier,
                    "message": message,
                }

                if is_healthy:
                    indexer_healthy += 1

            # Indexers are healthy if at least primary (MangaUpdates) is working
            primary_healthy = indexer_health.get("MangaUpdates", (False, ""))[0]
            indexers_status = "healthy" if primary_healthy else "degraded"

            health_data["components"]["indexers"] = {
                "status": indexers_status,
                "response_time_ms": round(indexer_response_time, 2),
                "healthy_count": indexer_healthy,
                "total_count": indexer_total,
                "details": indexer_details,
                "message": f"{indexer_healthy}/{indexer_total} indexers healthy",
            }

            if indexers_status == "healthy":
                healthy_components += 1
            elif health_data["status"] == "healthy":
                health_data["status"] = "degraded"

        except Exception as e:
            health_data["components"]["indexers"] = {
                "status": "unhealthy",
                "response_time_ms": None,
                "message": f"Indexer health check failed: {_sanitize_error_message(e)}",
            }
            health_data["status"] = "degraded"

        # 3. Provider Registry Health Check
        total_components += 1
        try:
            provider_start = time.time()
            providers = provider_registry.get_all_providers()
            provider_response_time = (time.time() - provider_start) * 1000  # ms

            # Get provider statuses from database
            try:
                from sqlalchemy import select

                from app.models.provider import ProviderStatus

                result = await db.execute(select(ProviderStatus))
                provider_statuses = {
                    ps.provider_id: ps for ps in result.scalars().all()
                }

                enabled_count = 0
                total_provider_count = len(providers)

                for provider in providers:
                    provider_id = provider.name.lower()
                    status_record = provider_statuses.get(provider_id)

                    if not status_record or status_record.is_enabled:
                        enabled_count += 1

                health_data["components"]["providers"] = {
                    "status": "healthy",
                    "response_time_ms": round(provider_response_time, 2),
                    "enabled_count": enabled_count,
                    "total_count": total_provider_count,
                    "message": f"{enabled_count}/{total_provider_count} providers enabled",
                }
                healthy_components += 1

            except Exception as e:
                health_data["components"]["providers"] = {
                    "status": "degraded",
                    "response_time_ms": round(provider_response_time, 2),
                    "enabled_count": len(providers),
                    "total_count": len(providers),
                    "message": f"Provider status check failed, using registry: {_sanitize_error_message(e)}",
                }
                if health_data["status"] == "healthy":
                    health_data["status"] = "degraded"

        except Exception as e:
            health_data["components"]["providers"] = {
                "status": "unhealthy",
                "response_time_ms": None,
                "message": f"Provider registry check failed: {_sanitize_error_message(e)}",
            }
            health_data["status"] = "degraded"

        # 4. Calculate overall health
        total_response_time = (time.time() - start_time) * 1000  # ms

        health_data["summary"] = {
            "healthy_components": healthy_components,
            "total_components": total_components,
            "health_percentage": (
                round((healthy_components / total_components) * 100, 1)
                if total_components > 0
                else 0
            ),
            "total_response_time_ms": round(total_response_time, 2),
        }

        # Set overall status based on component health
        if healthy_components == total_components:
            health_data["status"] = "healthy"
        elif healthy_components > 0:
            health_data["status"] = "degraded"
        else:
            health_data["status"] = "unhealthy"

        return health_data

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "components": {},
            "summary": {
                "healthy_components": 0,
                "total_components": 0,
                "health_percentage": 0,
                "total_response_time_ms": round((time.time() - start_time) * 1000, 2),
            },
            "message": f"Health check failed: {_sanitize_error_message(e)}",
        }


@router.get("/quick")
async def quick_health() -> Dict[str, Any]:
    """
    Quick health check for load balancers and monitoring systems.

    Returns minimal health information with fast response time.
    """
    try:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "message": "Service is running",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "message": f"Service error: {_sanitize_error_message(e)}",
        }


@router.get("/indexers")
async def indexers_health() -> Dict[str, Any]:
    """
    Detailed health check for indexer services only.

    Returns comprehensive indexer status information.
    """
    try:
        start_time = time.time()
        indexer_health = await tiered_search_service.test_all_indexers()
        response_time = (time.time() - start_time) * 1000  # ms

        healthy_count = 0
        indexer_details = {}

        for indexer_name, (is_healthy, message) in indexer_health.items():
            tier = (
                "primary"
                if indexer_name == "MangaUpdates"
                else "secondary" if indexer_name == "MadaraDex" else "tertiary"
            )

            indexer_details[indexer_name.lower()] = {
                "status": "healthy" if is_healthy else "unhealthy",
                "tier": tier,
                "message": message,
            }

            if is_healthy:
                healthy_count += 1

        # Overall indexer health based on primary indexer
        primary_healthy = indexer_health.get("MangaUpdates", (False, ""))[0]
        overall_status = "healthy" if primary_healthy else "degraded"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "response_time_ms": round(response_time, 2),
            "summary": {
                "healthy_count": healthy_count,
                "total_count": len(indexer_health),
                "health_percentage": round(
                    (healthy_count / len(indexer_health)) * 100, 1
                ),
            },
            "indexers": indexer_details,
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "message": f"Indexer health check failed: {_sanitize_error_message(e)}",
        }
