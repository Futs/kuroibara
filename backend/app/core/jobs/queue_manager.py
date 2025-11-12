"""
Download Queue Manager for coordinating job execution.

This module provides the central queue management system for coordinating
download jobs, health checks, and other background tasks.
"""

import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from .events import (
    JobEvent,
    JobEventType,
    JobPriority,
    JobStatus,
    JobType,
    is_download_job,
    is_health_job,
    is_organization_job,
)
from .models import BaseJob
from .workers import DownloadWorker, HealthCheckWorker, OrganizationWorker

logger = logging.getLogger(__name__)


class DownloadQueueManager:
    """
    Central manager for job queues with priority-based scheduling.

    Features:
    - Priority-based job scheduling
    - Worker coordination and load balancing
    - Job dependency management
    - Rate limiting integration
    - Progress tracking integration
    - Health monitoring integration
    """

    def __init__(
        self, max_concurrent_downloads: int = 3, max_concurrent_health_checks: int = 2
    ):
        # Job storage
        self._jobs: Dict[str, BaseJob] = {}
        self._priority_queues: Dict[JobPriority, deque] = {
            priority: deque() for priority in JobPriority
        }

        # Worker management
        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_concurrent_health_checks = max_concurrent_health_checks
        self._active_workers: Dict[str, asyncio.Task] = {}
        self._worker_jobs: Dict[str, str] = {}  # worker_id -> job_id

        # Job tracking
        self._jobs_by_status: Dict[JobStatus, Set[str]] = defaultdict(set)
        self._jobs_by_type: Dict[JobType, Set[str]] = defaultdict(set)
        self._jobs_by_user: Dict[str, Set[str]] = defaultdict(set)

        # Event handlers
        self._event_handlers: List[callable] = []

        # Queue management
        self._scheduler_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False

        # Statistics
        self._stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "cancelled_jobs": 0,
            "jobs_per_hour": 0.0,
            "average_job_duration": 0.0,
        }

        logger.info("DownloadQueueManager initialized")

    async def start(self) -> None:
        """Start the queue manager and background tasks."""
        if self._is_running:
            return

        self._is_running = True

        # Start scheduler task
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("DownloadQueueManager started")

    async def stop(self) -> None:
        """Stop the queue manager and all workers."""
        self._is_running = False

        # Cancel all active workers
        for worker_id, task in list(self._active_workers.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Cancel background tasks
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("DownloadQueueManager stopped")

    def add_job(self, job: BaseJob) -> str:
        """
        Add a job to the queue.

        Args:
            job: Job to add

        Returns:
            Job ID
        """
        # Store job
        self._jobs[job.id] = job

        # Add to priority queue
        self._priority_queues[job.priority].append(job.id)

        # Update tracking
        self._jobs_by_status[job.status].add(job.id)
        self._jobs_by_type[job.job_type].add(job.id)
        if job.user_id:
            self._jobs_by_user[job.user_id].add(job.id)

        # Update statistics
        self._stats["total_jobs"] += 1

        # Emit event
        self._emit_job_event(job, JobEventType.QUEUED, "Job added to queue")

        logger.info(
            f"Added job {job.id} ({job.job_type.value}) to queue with priority {job.priority.value}"
        )
        return job.id

    def get_job(self, job_id: str) -> Optional[BaseJob]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    def get_jobs(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[BaseJob]:
        """Get jobs with optional filtering."""
        job_ids = set(self._jobs.keys())

        # Apply filters
        if status:
            job_ids &= self._jobs_by_status[status]

        if job_type:
            job_ids &= self._jobs_by_type[job_type]

        if user_id:
            job_ids &= self._jobs_by_user[user_id]

        # Get jobs and sort by priority and creation time
        jobs = [self._jobs[job_id] for job_id in job_ids if job_id in self._jobs]
        jobs.sort(key=lambda j: (j.priority.value, j.created_at), reverse=False)

        return jobs[:limit]

    def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        job = self._jobs.get(job_id)
        if not job or job.status != JobStatus.PROCESSING:
            return False

        # Find and cancel worker
        worker_id = None
        for wid, jid in self._worker_jobs.items():
            if jid == job_id:
                worker_id = wid
                break

        if worker_id and worker_id in self._active_workers:
            self._active_workers[worker_id].cancel()

        # Update job status
        job.mark_paused()
        self._update_job_tracking(job)

        self._emit_job_event(job, JobEventType.PAUSED, "Job paused")

        logger.info(f"Paused job {job_id}")
        return True

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        job = self._jobs.get(job_id)
        if not job or job.status != JobStatus.PAUSED:
            return False

        # Add back to queue
        job.status = JobStatus.PENDING
        self._priority_queues[job.priority].appendleft(job_id)  # Add to front
        self._update_job_tracking(job)

        self._emit_job_event(job, JobEventType.RESUMED, "Job resumed")

        logger.info(f"Resumed job {job_id}")
        return True

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        job = self._jobs.get(job_id)
        if not job or job.is_finished():
            return False

        # Find and cancel worker if running
        worker_id = None
        for wid, jid in self._worker_jobs.items():
            if jid == job_id:
                worker_id = wid
                break

        if worker_id and worker_id in self._active_workers:
            self._active_workers[worker_id].cancel()

        # Remove from queue if pending
        if job.status == JobStatus.PENDING:
            try:
                self._priority_queues[job.priority].remove(job_id)
            except ValueError:
                pass

        # Update job status
        job.mark_cancelled()
        self._update_job_tracking(job)

        # Update statistics
        self._stats["cancelled_jobs"] += 1

        self._emit_job_event(job, JobEventType.CANCELLED, "Job cancelled")

        logger.info(f"Cancelled job {job_id}")
        return True

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        # Count jobs by status
        status_counts = {}
        for status in JobStatus:
            status_counts[status.value] = len(self._jobs_by_status[status])

        # Count jobs by type
        type_counts = {}
        for job_type in JobType:
            type_counts[job_type.value] = len(self._jobs_by_type[job_type])

        # Count active workers
        active_downloads = sum(
            1
            for job_id in self._worker_jobs.values()
            if self._jobs.get(job_id)
            and self._jobs[job_id].job_type
            in [
                JobType.DOWNLOAD_CHAPTER,
                JobType.DOWNLOAD_MANGA,
                JobType.DOWNLOAD_COVER,
            ]
        )

        active_health_checks = sum(
            1
            for job_id in self._worker_jobs.values()
            if self._jobs.get(job_id)
            and self._jobs[job_id].job_type
            in [JobType.HEALTH_CHECK, JobType.PROVIDER_TEST]
        )

        return {
            "is_running": self._is_running,
            "total_jobs": len(self._jobs),
            "jobs_by_status": status_counts,
            "jobs_by_type": type_counts,
            "active_workers": len(self._active_workers),
            "active_downloads": active_downloads,
            "active_health_checks": active_health_checks,
            "max_concurrent_downloads": self.max_concurrent_downloads,
            "max_concurrent_health_checks": self.max_concurrent_health_checks,
            "queue_lengths": {
                priority.value: len(queue)
                for priority, queue in self._priority_queues.items()
            },
            "statistics": self._stats,
        }

    def add_event_handler(self, handler: callable) -> None:
        """Add an event handler for job events."""
        self._event_handlers.append(handler)

    def remove_event_handler(self, handler: callable) -> None:
        """Remove an event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    def _emit_job_event(
        self, job: BaseJob, event_type: JobEventType, message: str
    ) -> None:
        """Emit a job event to all handlers."""
        event = JobEvent(
            job_id=job.id,
            job_type=job.job_type,
            event_type=event_type,
            message=message,
            progress_percentage=job.progress_percentage,
            current_step=job.current_step,
            items_processed=job.items_processed,
            items_total=job.items_total,
            user_id=job.user_id,
            session_id=job.session_id,
            metadata=job.metadata,
        )

        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in job event handler: {e}")

    def _update_job_tracking(self, job: BaseJob) -> None:
        """Update job tracking indices."""
        # Remove from old status
        for status, job_set in self._jobs_by_status.items():
            job_set.discard(job.id)

        # Add to new status
        self._jobs_by_status[job.status].add(job.id)

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop for processing jobs."""
        while self._is_running:
            try:
                await self._process_queue()
                await asyncio.sleep(1)  # Check every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(5)

    async def _process_queue(self) -> None:
        """Process jobs from the priority queues."""
        # Check if we can start more workers
        active_downloads = sum(
            1
            for job_id in self._worker_jobs.values()
            if self._jobs.get(job_id)
            and self._jobs[job_id].job_type
            in [
                JobType.DOWNLOAD_CHAPTER,
                JobType.DOWNLOAD_MANGA,
                JobType.DOWNLOAD_COVER,
            ]
        )

        active_health_checks = sum(
            1
            for job_id in self._worker_jobs.values()
            if self._jobs.get(job_id)
            and self._jobs[job_id].job_type
            in [JobType.HEALTH_CHECK, JobType.PROVIDER_TEST]
        )

        # Process jobs by priority
        for priority in JobPriority:
            queue = self._priority_queues[priority]

            while queue and self._is_running:
                # Check worker limits
                job_id = queue[0]  # Peek at next job
                job = self._jobs.get(job_id)

                if not job or job.status != JobStatus.PENDING:
                    queue.popleft()  # Remove invalid job
                    continue

                # Check if we can start this type of job
                can_start = False
                if job.job_type in [
                    JobType.DOWNLOAD_CHAPTER,
                    JobType.DOWNLOAD_MANGA,
                    JobType.DOWNLOAD_COVER,
                ]:
                    can_start = active_downloads < self.max_concurrent_downloads
                elif job.job_type in [JobType.HEALTH_CHECK, JobType.PROVIDER_TEST]:
                    can_start = active_health_checks < self.max_concurrent_health_checks
                else:
                    can_start = True  # Other job types have no specific limits

                if not can_start:
                    break  # Can't start more jobs of this type

                # Start the job
                queue.popleft()
                await self._start_job(job)

                # Update counters
                if job.job_type in [
                    JobType.DOWNLOAD_CHAPTER,
                    JobType.DOWNLOAD_MANGA,
                    JobType.DOWNLOAD_COVER,
                ]:
                    active_downloads += 1
                elif job.job_type in [JobType.HEALTH_CHECK, JobType.PROVIDER_TEST]:
                    active_health_checks += 1

    async def _start_job(self, job: BaseJob) -> None:
        """Start executing a job."""
        worker_id = str(uuid4())

        # Mark job as started
        job.mark_started()
        self._update_job_tracking(job)

        # Create worker task
        worker_task = asyncio.create_task(self._execute_job(job, worker_id))
        self._active_workers[worker_id] = worker_task
        self._worker_jobs[worker_id] = job.id

        self._emit_job_event(
            job, JobEventType.STARTED, f"Job started by worker {worker_id}"
        )

        logger.info(f"Started job {job.id} with worker {worker_id}")

    async def _execute_job(self, job: BaseJob, worker_id: str) -> None:
        """Execute a job using the appropriate worker."""
        try:
            # Create appropriate worker based on job type
            worker = self._create_worker(job, worker_id)
            if not worker:
                raise Exception(
                    f"No worker available for job type {job.job_type.value}"
                )

            # Execute job with worker
            await worker.run_job(job, self)

        except asyncio.CancelledError:
            # Job was cancelled - worker.run_job handles this
            pass

        except Exception as e:
            # Job failed - worker.run_job handles this
            logger.error(f"Job {job.id} execution failed: {e}")

        finally:
            # Clean up worker
            if worker_id in self._active_workers:
                del self._active_workers[worker_id]
            if worker_id in self._worker_jobs:
                del self._worker_jobs[worker_id]

    def _create_worker(self, job: BaseJob, worker_id: str):
        """Create appropriate worker for the job type."""
        if is_download_job(job.job_type):
            return DownloadWorker(worker_id)
        elif is_health_job(job.job_type):
            return HealthCheckWorker(worker_id)
        elif is_organization_job(job.job_type):
            return OrganizationWorker(worker_id)
        else:
            logger.warning(
                f"No specific worker for job type {job.job_type.value}, using base worker"
            )
            return None

    async def _cleanup_loop(self) -> None:
        """Cleanup loop for removing old completed jobs."""
        while self._is_running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_old_jobs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_old_jobs(self) -> None:
        """Remove old completed jobs to prevent memory bloat."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)  # Keep jobs for 24 hours

        jobs_to_remove = []
        for job_id, job in self._jobs.items():
            if (
                job.is_finished()
                and job.completed_at
                and job.completed_at < cutoff_time
            ):
                jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            job = self._jobs[job_id]

            # Remove from tracking
            self._jobs_by_status[job.status].discard(job_id)
            self._jobs_by_type[job.job_type].discard(job_id)
            if job.user_id:
                self._jobs_by_user[job.user_id].discard(job_id)

            # Remove job
            del self._jobs[job_id]

        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")


# Global queue manager instance
queue_manager = DownloadQueueManager()
