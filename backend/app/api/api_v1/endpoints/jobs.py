"""
Job Queue and Health Monitoring API endpoints.

This module provides REST API endpoints for managing the job queue system
and provider health monitoring.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.core.jobs import (
    DownloadJob,
    HealthCheckJob,
    JobPriority,
    JobStatus,
    JobType,
    OrganizationJob,
    health_monitor,
    queue_manager,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models


class JobCreateRequest(BaseModel):
    """Request model for creating jobs."""

    job_type: str
    title: str
    description: str = ""
    priority: str = "normal"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

    # Download job specific
    provider_name: Optional[str] = None
    manga_id: Optional[str] = None
    chapter_id: Optional[str] = None
    external_manga_id: Optional[str] = None
    external_chapter_id: Optional[str] = None
    quality: str = "high"
    format: str = "cbz"

    # Health check specific
    check_type: str = "basic"
    test_search: bool = True
    test_metadata: bool = True
    test_download: bool = False
    performance_benchmark: bool = False

    # Organization specific
    target_path: Optional[str] = None
    organization_type: str = "by_series"
    create_folders: bool = True
    move_files: bool = False


class JobResponse(BaseModel):
    """Response model for jobs."""

    id: str
    job_type: str
    status: str
    priority: str
    title: str
    description: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    updated_at: str
    progress_percentage: float
    current_step: str
    items_processed: int
    items_total: Optional[int]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    user_id: Optional[str]
    session_id: Optional[str]
    timeout_seconds: int
    metadata: Dict[str, Any]
    parent_job_id: Optional[str]
    duration: Optional[float]
    estimated_completion: Optional[str]


class QueueStatusResponse(BaseModel):
    """Response model for queue status."""

    is_running: bool
    total_jobs: int
    jobs_by_status: Dict[str, int]
    jobs_by_type: Dict[str, int]
    active_workers: int
    active_downloads: int
    active_health_checks: int
    max_concurrent_downloads: int
    max_concurrent_health_checks: int
    queue_lengths: Dict[str, int]
    statistics: Dict[str, Any]


class HealthSummaryResponse(BaseModel):
    """Response model for health summary."""

    total_providers: int
    healthy: int
    degraded: int
    unhealthy: int
    disabled: int
    overall_health_percentage: float
    monitoring_active: bool
    active_monitoring_tasks: int


class ProviderHealthResponse(BaseModel):
    """Response model for provider health."""

    provider_name: str
    status: str
    last_check: Optional[str]
    last_success: Optional[str]
    last_failure: Optional[str]
    average_response_time: float
    success_rate: float
    consecutive_failures: int
    total_failures: int
    total_successes: int
    health_score: float
    auto_disabled: bool
    manual_override: bool


# Job Queue Endpoints


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status():
    """Get current job queue status."""
    try:
        status = queue_manager.get_queue_status()
        return QueueStatusResponse(**status)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving queue status: {str(e)}",
        )


@router.post("/queue/start")
async def start_queue():
    """Start the job queue manager."""
    try:
        await queue_manager.start()
        return {"message": "Job queue started successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting job queue: {str(e)}",
        )


@router.post("/queue/stop")
async def stop_queue():
    """Stop the job queue manager."""
    try:
        await queue_manager.stop()
        return {"message": "Job queue stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping job queue: {str(e)}",
        )


@router.get("/jobs", response_model=List[JobResponse])
async def get_jobs(
    status_filter: Optional[str] = Query(None, description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(
        50, ge=1, le=500, description="Maximum number of jobs to return"
    ),
):
    """Get jobs with optional filtering."""
    try:
        # Convert string parameters to enums if provided
        status_enum = None
        if status_filter:
            try:
                status_enum = JobStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid job status: {status_filter}",
                )

        job_type_enum = None
        if job_type:
            try:
                job_type_enum = JobType(job_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid job type: {job_type}",
                )

        jobs = queue_manager.get_jobs(
            status=status_enum, job_type=job_type_enum, user_id=user_id, limit=limit
        )

        return [JobResponse(**job.to_dict()) for job in jobs]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving jobs: {str(e)}",
        )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get details of a specific job."""
    try:
        job = queue_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
            )

        return JobResponse(**job.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job: {str(e)}",
        )


@router.post("/jobs", response_model=Dict[str, str])
async def create_job(job_request: JobCreateRequest):
    """Create a new job."""
    try:
        # Convert priority string to enum
        try:
            priority = JobPriority[job_request.priority.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {job_request.priority}",
            )

        # Convert job type string to enum
        try:
            job_type = JobType(job_request.job_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job type: {job_request.job_type}",
            )

        # Create appropriate job based on type
        if job_type in [
            JobType.DOWNLOAD_CHAPTER,
            JobType.DOWNLOAD_MANGA,
            JobType.DOWNLOAD_COVER,
            JobType.BULK_DOWNLOAD,
        ]:
            if not job_request.provider_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="provider_name is required for download jobs",
                )

            job = DownloadJob(
                job_type=job_type,
                title=job_request.title,
                description=job_request.description,
                priority=priority,
                user_id=job_request.user_id,
                session_id=job_request.session_id,
                metadata=job_request.metadata,
                provider_name=job_request.provider_name,
                manga_id=job_request.manga_id,
                chapter_id=job_request.chapter_id,
                external_manga_id=job_request.external_manga_id or "",
                external_chapter_id=job_request.external_chapter_id or "",
                quality=job_request.quality,
                format=job_request.format,
            )

        elif job_type in [
            JobType.HEALTH_CHECK,
            JobType.PROVIDER_TEST,
            JobType.PERFORMANCE_BENCHMARK,
        ]:
            if not job_request.provider_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="provider_name is required for health check jobs",
                )

            job = HealthCheckJob(
                job_type=job_type,
                title=job_request.title,
                description=job_request.description,
                priority=priority,
                user_id=job_request.user_id,
                session_id=job_request.session_id,
                metadata=job_request.metadata,
                provider_name=job_request.provider_name,
                check_type=job_request.check_type,
                test_search=job_request.test_search,
                test_metadata=job_request.test_metadata,
                test_download=job_request.test_download,
                performance_benchmark=job_request.performance_benchmark,
            )

        elif job_type in [
            JobType.ORGANIZE_LIBRARY,
            JobType.ORGANIZE_MANGA,
            JobType.CONVERT_FORMAT,
            JobType.CLEANUP_FILES,
        ]:
            job = OrganizationJob(
                job_type=job_type,
                title=job_request.title,
                description=job_request.description,
                priority=priority,
                user_id=job_request.user_id,
                session_id=job_request.session_id,
                metadata=job_request.metadata,
                target_path=job_request.target_path or "",
                organization_type=job_request.organization_type,
                create_folders=job_request.create_folders,
                move_files=job_request.move_files,
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported job type: {job_request.job_type}",
            )

        # Add job to queue
        job_id = queue_manager.add_job(job)

        return {"job_id": job_id, "message": "Job created successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating job: {str(e)}",
        )


@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a job."""
    try:
        success = queue_manager.pause_job(job_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found or cannot be paused",
            )

        return {"message": f"Job {job_id} paused successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error pausing job: {str(e)}",
        )


@router.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """Resume a paused job."""
    try:
        success = queue_manager.resume_job(job_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found or cannot be resumed",
            )

        return {"message": f"Job {job_id} resumed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resuming job: {str(e)}",
        )


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a job."""
    try:
        success = queue_manager.cancel_job(job_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found or cannot be cancelled",
            )

        return {"message": f"Job {job_id} cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling job: {str(e)}",
        )


# Health Monitoring Endpoints


@router.get("/health/summary", response_model=HealthSummaryResponse)
async def get_health_summary():
    """Get overall provider health summary."""
    try:
        summary = health_monitor.get_health_summary()
        return HealthSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving health summary: {str(e)}",
        )


@router.get("/health/providers", response_model=List[ProviderHealthResponse])
async def get_all_provider_health():
    """Get health status for all providers."""
    try:
        all_health = health_monitor.get_all_provider_health()

        response = []
        for provider_name, metrics in all_health.items():
            response.append(
                ProviderHealthResponse(
                    provider_name=metrics.provider_name,
                    status=metrics.status.value,
                    last_check=(
                        metrics.last_check.isoformat() if metrics.last_check else None
                    ),
                    last_success=(
                        metrics.last_success.isoformat()
                        if metrics.last_success
                        else None
                    ),
                    last_failure=(
                        metrics.last_failure.isoformat()
                        if metrics.last_failure
                        else None
                    ),
                    average_response_time=metrics.average_response_time,
                    success_rate=metrics.success_rate,
                    consecutive_failures=metrics.consecutive_failures,
                    total_failures=metrics.total_failures,
                    total_successes=metrics.total_successes,
                    health_score=metrics.get_health_score(),
                    auto_disabled=metrics.auto_disabled,
                    manual_override=metrics.manual_override,
                )
            )

        # Sort by health score (descending)
        response.sort(key=lambda x: x.health_score, reverse=True)

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving provider health: {str(e)}",
        )


@router.get("/health/providers/{provider_name}", response_model=ProviderHealthResponse)
async def get_provider_health(provider_name: str):
    """Get health status for a specific provider."""
    try:
        metrics = health_monitor.get_provider_health(provider_name)
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider {provider_name} not found",
            )

        return ProviderHealthResponse(
            provider_name=metrics.provider_name,
            status=metrics.status.value,
            last_check=metrics.last_check.isoformat() if metrics.last_check else None,
            last_success=(
                metrics.last_success.isoformat() if metrics.last_success else None
            ),
            last_failure=(
                metrics.last_failure.isoformat() if metrics.last_failure else None
            ),
            average_response_time=metrics.average_response_time,
            success_rate=metrics.success_rate,
            consecutive_failures=metrics.consecutive_failures,
            total_failures=metrics.total_failures,
            total_successes=metrics.total_successes,
            health_score=metrics.get_health_score(),
            auto_disabled=metrics.auto_disabled,
            manual_override=metrics.manual_override,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving provider health: {str(e)}",
        )


@router.post("/health/providers/{provider_name}/check")
async def schedule_health_check(
    provider_name: str,
    check_type: str = Query("manual", description="Type of health check"),
    test_search: bool = Query(True, description="Test search functionality"),
    test_metadata: bool = Query(True, description="Test metadata retrieval"),
    test_download: bool = Query(False, description="Test download capability"),
    performance_benchmark: bool = Query(False, description="Run performance benchmark"),
):
    """Schedule a health check for a provider."""
    try:
        from app.core.jobs.health_monitor import HealthCheckType

        # Convert check type
        try:
            check_type_enum = HealthCheckType(check_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid check type: {check_type}",
            )

        job_id = await health_monitor.schedule_health_check(
            provider_name=provider_name,
            check_type=check_type_enum,
            test_search=test_search,
            test_metadata=test_metadata,
            test_download=test_download,
            performance_benchmark=performance_benchmark,
        )

        if not job_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to schedule health check",
            )

        return {
            "job_id": job_id,
            "message": f"Health check scheduled for {provider_name}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling health check: {str(e)}",
        )


@router.post("/health/providers/{provider_name}/disable")
async def disable_provider(
    provider_name: str, reason: str = Query("", description="Reason for disabling")
):
    """Manually disable a provider."""
    try:
        success = health_monitor.disable_provider(
            provider_name, auto=False, reason=reason
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider {provider_name} not found",
            )

        return {"message": f"Provider {provider_name} disabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disabling provider: {str(e)}",
        )


@router.post("/health/providers/{provider_name}/enable")
async def enable_provider(provider_name: str):
    """Enable a disabled provider."""
    try:
        success = health_monitor.enable_provider(provider_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider {provider_name} not found",
            )

        return {"message": f"Provider {provider_name} enabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enabling provider: {str(e)}",
        )


@router.get("/health/rankings")
async def get_provider_rankings():
    """Get providers ranked by health score."""
    try:
        rankings = health_monitor.get_provider_ranking()

        return {
            "rankings": [
                {"provider_name": name, "health_score": score}
                for name, score in rankings
            ],
            "total_providers": len(rankings),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving provider rankings: {str(e)}",
        )


@router.post("/health/start")
async def start_health_monitoring():
    """Start health monitoring."""
    try:
        health_monitor.queue_manager = queue_manager
        await health_monitor.start()
        return {"message": "Health monitoring started successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting health monitoring: {str(e)}",
        )


@router.post("/health/stop")
async def stop_health_monitoring():
    """Stop health monitoring."""
    try:
        await health_monitor.stop()
        return {"message": "Health monitoring stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping health monitoring: {str(e)}",
        )
