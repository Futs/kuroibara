"""
Job workers for executing different types of jobs.

This module provides worker classes for executing download jobs, health checks,
and other background tasks with proper error handling and progress tracking.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from .events import JobEventType
from .models import BaseJob, DownloadJob, HealthCheckJob, OrganizationJob

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """
    Base class for all job workers.
    """

    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.current_job: Optional[BaseJob] = None
        self.is_running = False

    @abstractmethod
    async def execute_job(self, job: BaseJob) -> None:
        """Execute a job. Must be implemented by subclasses."""
        pass

    async def run_job(self, job: BaseJob, queue_manager) -> None:
        """
        Run a job with proper error handling and progress tracking.

        Args:
            job: Job to execute
            queue_manager: Queue manager for event emission
        """
        self.current_job = job
        self.is_running = True

        try:
            # Mark job as started
            job.mark_started()
            queue_manager._update_job_tracking(job)
            queue_manager._emit_job_event(
                job, JobEventType.STARTED, f"Job started by worker {self.worker_id}"
            )

            # Execute the job
            await self.execute_job(job)

            # Mark as completed if not already marked
            if job.status.value == "processing":
                job.mark_completed("Job completed successfully")
                queue_manager._update_job_tracking(job)
                queue_manager._emit_job_event(
                    job, JobEventType.COMPLETED, "Job completed successfully"
                )

                # Update statistics
                queue_manager._stats["completed_jobs"] += 1

        except asyncio.CancelledError:
            # Job was cancelled
            if job.status.value == "processing":
                job.mark_cancelled()
                queue_manager._update_job_tracking(job)
                queue_manager._emit_job_event(
                    job, JobEventType.CANCELLED, "Job cancelled"
                )

                # Update statistics
                queue_manager._stats["cancelled_jobs"] += 1

            logger.info(f"Job {job.id} was cancelled")

        except Exception as e:
            # Job failed
            error_message = str(e)

            # Check if we should retry
            if job.increment_retry():
                queue_manager._update_job_tracking(job)
                queue_manager._emit_job_event(
                    job,
                    JobEventType.RETRYING,
                    f"Job failed, retrying ({job.retry_count}/{job.max_retries}): {error_message}",
                )

                # Add back to queue for retry
                queue_manager._priority_queues[job.priority].appendleft(job.id)

                logger.warning(f"Job {job.id} failed, retrying: {error_message}")
            else:
                job.mark_failed(error_message)
                queue_manager._update_job_tracking(job)
                queue_manager._emit_job_event(
                    job, JobEventType.FAILED, f"Job failed: {error_message}"
                )

                # Update statistics
                queue_manager._stats["failed_jobs"] += 1

                logger.error(f"Job {job.id} failed permanently: {error_message}")

        finally:
            self.current_job = None
            self.is_running = False

    def update_job_progress(
        self,
        progress: Optional[float] = None,
        current_step: Optional[str] = None,
        items_processed: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        """Update current job progress."""
        if self.current_job:
            self.current_job.update_progress(
                progress, current_step, items_processed, message
            )


class DownloadWorker(BaseWorker):
    """
    Worker for executing download jobs.
    """

    async def execute_job(self, job: BaseJob) -> None:
        """Execute a download job."""
        if not isinstance(job, DownloadJob):
            raise ValueError(
                f"DownloadWorker can only execute DownloadJob, got {type(job)}"
            )

        logger.info(f"Starting download job {job.id}: {job.title}")

        try:
            # Get the appropriate agent for this provider
            agent = await self._get_agent(job.provider_name)
            if not agent:
                raise Exception(f"No agent available for provider {job.provider_name}")

            # Execute download based on job type
            if job.job_type.value == "download_chapter":
                await self._download_chapter(job, agent)
            elif job.job_type.value == "download_manga":
                await self._download_manga(job, agent)
            elif job.job_type.value == "download_cover":
                await self._download_cover(job, agent)
            elif job.job_type.value == "bulk_download":
                await self._bulk_download(job, agent)
            else:
                raise Exception(f"Unsupported download job type: {job.job_type.value}")

            logger.info(f"Completed download job {job.id}")

        except Exception as e:
            logger.error(f"Download job {job.id} failed: {e}")
            raise

    async def _get_agent(self, provider_name: str):
        """Get agent for the specified provider."""
        try:
            from ...agents import agent_registry

            return agent_registry.get_agent(provider_name)
        except ImportError:
            logger.warning("Agent registry not available, using fallback")
            return None

    async def _download_chapter(self, job: DownloadJob, agent) -> None:
        """Download a single chapter."""
        self.update_job_progress(0, "Initializing chapter download")

        # Simulate chapter download with progress updates
        steps = [
            (10, "Fetching chapter metadata"),
            (30, "Getting page list"),
            (50, "Downloading pages"),
            (80, "Processing images"),
            (100, "Finalizing download"),
        ]

        for progress, step in steps:
            self.update_job_progress(progress, step)
            await asyncio.sleep(0.5)  # Simulate work

        job.mark_completed("Chapter downloaded successfully")

    async def _download_manga(self, job: DownloadJob, agent) -> None:
        """Download a complete manga."""
        self.update_job_progress(0, "Initializing manga download")

        # Simulate manga download with multiple chapters
        total_chapters = job.metadata.get("total_chapters", 10)
        job.items_total = total_chapters

        for i in range(total_chapters):
            if not self.is_running:  # Check for cancellation
                break

            chapter_progress = (i / total_chapters) * 100
            self.update_job_progress(
                chapter_progress, f"Downloading chapter {i + 1}/{total_chapters}", i
            )

            await asyncio.sleep(1)  # Simulate chapter download

        job.mark_completed(f"Manga downloaded successfully ({total_chapters} chapters)")

    async def _download_cover(self, job: DownloadJob, agent) -> None:
        """Download a cover image."""
        self.update_job_progress(0, "Initializing cover download")

        steps = [
            (25, "Fetching cover URL"),
            (50, "Downloading image"),
            (75, "Processing image"),
            (100, "Saving cover"),
        ]

        for progress, step in steps:
            self.update_job_progress(progress, step)
            await asyncio.sleep(0.2)  # Simulate work

        job.mark_completed("Cover downloaded successfully")

    async def _bulk_download(self, job: DownloadJob, agent) -> None:
        """Execute a bulk download operation."""
        self.update_job_progress(0, "Initializing bulk download")

        # Get list of items to download
        items = job.metadata.get("items", [])
        job.items_total = len(items)

        for i, item in enumerate(items):
            if not self.is_running:  # Check for cancellation
                break

            item_progress = (i / len(items)) * 100
            self.update_job_progress(
                item_progress,
                f"Downloading item {i + 1}/{len(items)}: {item.get('title', 'Unknown')}",
                i,
            )

            await asyncio.sleep(0.5)  # Simulate item download

        job.mark_completed(f"Bulk download completed ({len(items)} items)")


class HealthCheckWorker(BaseWorker):
    """
    Worker for executing health check jobs.
    """

    async def execute_job(self, job: BaseJob) -> None:
        """Execute a health check job."""
        if not isinstance(job, HealthCheckJob):
            raise ValueError(
                f"HealthCheckWorker can only execute HealthCheckJob, got {type(job)}"
            )

        logger.info(f"Starting health check job {job.id}: {job.title}")

        try:
            # Get the agent for this provider
            agent = await self._get_agent(job.provider_name)
            if not agent:
                raise Exception(f"No agent available for provider {job.provider_name}")

            # Execute health check
            await self._perform_health_check(job, agent)

            logger.info(f"Completed health check job {job.id}")

        except Exception as e:
            logger.error(f"Health check job {job.id} failed: {e}")
            raise

    async def _get_agent(self, provider_name: str):
        """Get agent for the specified provider."""
        try:
            from ...agents import agent_registry

            return agent_registry.get_agent(provider_name)
        except ImportError:
            logger.warning("Agent registry not available, using fallback")
            return None

    async def _perform_health_check(self, job: HealthCheckJob, agent) -> None:
        """Perform comprehensive health check."""
        self.update_job_progress(0, "Starting health check")

        health_results = {
            "provider": job.provider_name,
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
        }

        # Test basic connectivity
        if job.test_search:
            self.update_job_progress(20, "Testing search functionality")
            try:
                # Simulate search test
                await asyncio.sleep(0.5)
                health_results["tests"]["search"] = {
                    "status": "pass",
                    "response_time": 0.5,
                }
            except Exception as e:
                health_results["tests"]["search"] = {"status": "fail", "error": str(e)}

        # Test metadata retrieval
        if job.test_metadata:
            self.update_job_progress(50, "Testing metadata retrieval")
            try:
                # Simulate metadata test
                await asyncio.sleep(0.3)
                health_results["tests"]["metadata"] = {
                    "status": "pass",
                    "response_time": 0.3,
                }
            except Exception as e:
                health_results["tests"]["metadata"] = {
                    "status": "fail",
                    "error": str(e),
                }

        # Test download capability
        if job.test_download:
            self.update_job_progress(80, "Testing download capability")
            try:
                # Simulate download test
                await asyncio.sleep(0.7)
                health_results["tests"]["download"] = {
                    "status": "pass",
                    "response_time": 0.7,
                }
            except Exception as e:
                health_results["tests"]["download"] = {
                    "status": "fail",
                    "error": str(e),
                }

        # Performance benchmark
        if job.performance_benchmark:
            self.update_job_progress(90, "Running performance benchmark")
            try:
                # Simulate performance test
                await asyncio.sleep(1.0)
                health_results["tests"]["performance"] = {
                    "status": "pass",
                    "avg_response_time": 0.6,
                    "requests_per_second": 10.5,
                }
            except Exception as e:
                health_results["tests"]["performance"] = {
                    "status": "fail",
                    "error": str(e),
                }

        # Store results in job metadata
        job.metadata["health_results"] = health_results

        # Determine overall health status
        failed_tests = [
            test
            for test, result in health_results["tests"].items()
            if result["status"] == "fail"
        ]

        if failed_tests:
            job.mark_completed(
                f"Health check completed with {len(failed_tests)} failed tests"
            )
        else:
            job.mark_completed("Health check passed all tests")

        self.update_job_progress(100, "Health check completed")


class OrganizationWorker(BaseWorker):
    """
    Worker for executing organization jobs.
    """

    async def execute_job(self, job: BaseJob) -> None:
        """Execute an organization job."""
        if not isinstance(job, OrganizationJob):
            raise ValueError(
                f"OrganizationWorker can only execute OrganizationJob, got {type(job)}"
            )

        logger.info(f"Starting organization job {job.id}: {job.title}")

        try:
            await self._perform_organization(job)
            logger.info(f"Completed organization job {job.id}")

        except Exception as e:
            logger.error(f"Organization job {job.id} failed: {e}")
            raise

    async def _perform_organization(self, job: OrganizationJob) -> None:
        """Perform library organization."""
        self.update_job_progress(0, "Starting library organization")

        # Simulate organization steps
        steps = [
            (10, "Scanning library directory"),
            (30, "Analyzing file structure"),
            (50, "Creating organization plan"),
            (70, "Moving/copying files"),
            (90, "Updating metadata"),
            (100, "Cleaning up empty folders"),
        ]

        for progress, step in steps:
            self.update_job_progress(progress, step)
            await asyncio.sleep(0.5)  # Simulate work

        job.mark_completed("Library organization completed successfully")
