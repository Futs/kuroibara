"""
Agent-based architecture for Kuroibara providers.

This module provides a new agent-based architecture that replaces the existing
provider system with better error isolation, monitoring, and modularity.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.search import SearchResult

# Import progress tracking (with fallback if not available)
try:
    from ..progress import OperationType, progress_tracker

    PROGRESS_AVAILABLE = True
except ImportError:
    PROGRESS_AVAILABLE = False
    progress_tracker = None
    OperationType = None

logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Capabilities that an agent can support."""

    SEARCH = "search"
    MANGA_DETAILS = "manga_details"
    CHAPTERS = "chapters"
    PAGES = "pages"
    DOWNLOAD_PAGE = "download_page"
    DOWNLOAD_COVER = "download_cover"
    HEALTH_CHECK = "health_check"


class AgentStatus(Enum):
    """Status of an agent."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CIRCUIT_OPEN = "circuit_open"


class AgentMetrics:
    """Metrics tracking for an agent."""

    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.last_request_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.last_error_time: Optional[datetime] = None
        self.circuit_breaker_count = 0
        self.average_response_time = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    def record_request(
        self, success: bool, response_time: float, error: Optional[str] = None
    ):
        """Record a request and its outcome."""
        self.total_requests += 1
        self.last_request_time = datetime.utcnow()

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if error:
                self.last_error = error
                self.last_error_time = datetime.utcnow()

        # Update average response time
        if self.total_requests == 1:
            self.average_response_time = response_time
        else:
            self.average_response_time = (
                self.average_response_time * (self.total_requests - 1) + response_time
            ) / self.total_requests


class BaseAgent(ABC):
    """
    Base class for all agents in the Kuroibara system.

    This provides a standardized interface with error isolation, metrics tracking,
    progress tracking, and capability-based functionality. It's designed to be
    backward compatible with existing providers.
    """

    def __init__(self, name: str, capabilities: List[AgentCapability]):
        self.name = name
        self.capabilities = capabilities
        self.status = AgentStatus.ACTIVE
        self.metrics = AgentMetrics()
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_timeout = 300  # 5 minutes
        self._circuit_opened_at: Optional[datetime] = None

        # Progress tracking
        self._current_operations: Dict[str, str] = {}  # operation_name -> operation_id
        self._operation_metadata: Dict[str, Dict[str, Any]] = {}

    @property
    @abstractmethod
    def url(self) -> str:
        """Get the base URL of the agent."""

    @property
    @abstractmethod
    def supports_nsfw(self) -> bool:
        """Check if the agent supports NSFW content."""

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if the agent has a specific capability."""
        return capability in self.capabilities

    def is_healthy(self) -> bool:
        """Check if the agent is in a healthy state."""
        return self.status in [AgentStatus.ACTIVE, AgentStatus.INACTIVE]

    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows requests."""
        if self.status != AgentStatus.CIRCUIT_OPEN:
            return True

        if self._circuit_opened_at is None:
            return True

        # Check if timeout has passed
        time_since_open = (datetime.utcnow() - self._circuit_opened_at).total_seconds()
        if time_since_open > self._circuit_breaker_timeout:
            logger.info(
                f"Circuit breaker timeout passed for {self.name}, attempting recovery"
            )
            self.status = AgentStatus.ACTIVE
            return True

        return False

    def _open_circuit_breaker(self):
        """Open the circuit breaker due to too many failures."""
        self.status = AgentStatus.CIRCUIT_OPEN
        self._circuit_opened_at = datetime.utcnow()
        self.metrics.circuit_breaker_count += 1
        logger.warning(f"Circuit breaker opened for agent {self.name}")

    async def _execute_with_error_handling(
        self, operation_name: str, operation_func, *args, **kwargs
    ):
        """Execute an operation with error handling, rate limiting, and metrics tracking."""
        if not self._check_circuit_breaker():
            raise Exception(f"Circuit breaker is open for agent {self.name}")

        # Use rate limiting and error isolation systems if available
        try:
            from .rate_limiting import rate_limiter_manager

            return await rate_limiter_manager.execute_with_rate_limit(
                self.name,
                self._execute_with_isolation,
                operation_name,
                operation_func,
                *args,
                **kwargs,
            )
        except ImportError:
            # Fallback to error isolation only
            try:
                from .error_isolation import isolation_manager

                return await isolation_manager.execute_with_isolation(
                    self.name,
                    self._execute_operation_with_metrics,
                    operation_name,
                    operation_func,
                    *args,
                    **kwargs,
                )
            except ImportError:
                # Fallback to basic error handling
                return await self._execute_operation_with_metrics(
                    operation_name, operation_func, *args, **kwargs
                )

    async def _execute_with_isolation(
        self, operation_name: str, operation_func, *args, **kwargs
    ):
        """Execute operation with error isolation."""
        try:
            from .error_isolation import isolation_manager

            return await isolation_manager.execute_with_isolation(
                self.name,
                self._execute_operation_with_metrics,
                operation_name,
                operation_func,
                *args,
                **kwargs,
            )
        except ImportError:
            # Fallback to basic error handling if isolation system not available
            return await self._execute_operation_with_metrics(
                operation_name, operation_func, *args, **kwargs
            )

    async def _execute_operation_with_metrics(
        self, operation_name: str, operation_func, *args, **kwargs
    ):
        """Execute operation with metrics tracking."""
        start_time = time.time()
        try:
            result = await operation_func(*args, **kwargs)
            response_time = time.time() - start_time
            self.metrics.record_request(True, response_time)

            # Reset status to active on successful request
            if self.status == AgentStatus.ERROR:
                self.status = AgentStatus.ACTIVE
                logger.info(f"Agent {self.name} recovered from error state")

            return result

        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"{operation_name} failed: {str(e)}"
            self.metrics.record_request(False, response_time, error_msg)

            # Check if we should open circuit breaker
            if self.metrics.failed_requests >= self._circuit_breaker_threshold:
                recent_failures = self.metrics.failed_requests
                if recent_failures >= self._circuit_breaker_threshold:
                    self._open_circuit_breaker()
            else:
                self.status = AgentStatus.ERROR

            logger.error(f"Agent {self.name} - {error_msg}")
            raise

    # Abstract methods that agents must implement
    @abstractmethod
    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search for manga."""

    @abstractmethod
    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get details for a manga."""

    @abstractmethod
    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Get chapters for a manga."""

    @abstractmethod
    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages for a chapter."""

    @abstractmethod
    async def download_page(self, page_url: str) -> bytes:
        """Download a page."""

    @abstractmethod
    async def download_cover(self, manga_id: str) -> bytes:
        """Download a manga cover."""

    async def health_check(
        self, timeout: int = 30
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """Perform a health check on the agent."""
        return await self._execute_with_error_handling(
            "health_check", self._health_check_impl, timeout
        )

    async def _health_check_impl(
        self, timeout: int
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """Default health check implementation."""
        start_time = time.time()

        try:
            import aiohttp

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(self.url) as response:
                    response_time = int((time.time() - start_time) * 1000)

                    if response.status == 200:
                        return True, response_time, None
                    else:
                        return False, response_time, f"HTTP {response.status}"

        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            return False, response_time, str(e)

    # Progress tracking methods
    async def start_progress_operation(
        self,
        operation_name: str,
        operation_type,  # OperationType if available
        title: str,
        description: str = "",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        total_steps: Optional[int] = None,
        total_items: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a progress operation if progress tracking is available."""
        if not PROGRESS_AVAILABLE or not progress_tracker:
            return ""

        try:
            # Add agent information to metadata
            agent_metadata = {
                "agent_name": self.name,
                "agent_type": self.__class__.__name__,
                **(metadata or {}),
            }

            operation_id = await progress_tracker.start_operation(
                operation_type=operation_type,
                title=f"[{self.name}] {title}",
                description=description,
                user_id=user_id,
                session_id=session_id,
                total_steps=total_steps,
                total_items=total_items,
                metadata=agent_metadata,
            )

            # Track the operation
            self._current_operations[operation_name] = operation_id
            self._operation_metadata[operation_id] = {
                "operation_name": operation_name,
                "started_by": self.name,
            }

            logger.debug(
                f"Started progress operation {operation_name} ({operation_id}) for agent {self.name}"
            )
            return operation_id

        except Exception as e:
            logger.error(f"Error starting progress operation {operation_name}: {e}")
            return ""

    async def update_progress(
        self,
        operation_name: str,
        progress: Optional[float] = None,
        current_step: Optional[str] = None,
        message: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """Update progress for an operation if progress tracking is available."""
        if not PROGRESS_AVAILABLE or not progress_tracker:
            return False

        operation_id = self._current_operations.get(operation_name)
        if not operation_id:
            return False

        try:
            return await progress_tracker.update_progress(
                operation_id=operation_id,
                progress=progress,
                current_step=current_step,
                message=message,
                **kwargs,
            )
        except Exception as e:
            logger.error(f"Error updating progress for {operation_name}: {e}")
            return False

    async def complete_operation(
        self, operation_name: str, message: Optional[str] = None
    ) -> bool:
        """Complete an operation if progress tracking is available."""
        if not PROGRESS_AVAILABLE or not progress_tracker:
            return False

        operation_id = self._current_operations.get(operation_name)
        if not operation_id:
            return False

        try:
            success = await progress_tracker.complete_operation(
                operation_id=operation_id, message=message
            )

            if success:
                # Clean up tracking
                del self._current_operations[operation_name]
                if operation_id in self._operation_metadata:
                    del self._operation_metadata[operation_id]

            return success
        except Exception as e:
            logger.error(f"Error completing operation {operation_name}: {e}")
            return False

    async def fail_operation(self, operation_name: str, error_message: str) -> bool:
        """Fail an operation if progress tracking is available."""
        if not PROGRESS_AVAILABLE or not progress_tracker:
            return False

        operation_id = self._current_operations.get(operation_name)
        if not operation_id:
            return False

        try:
            success = await progress_tracker.fail_operation(
                operation_id=operation_id, error_message=error_message
            )

            if success:
                # Clean up tracking
                del self._current_operations[operation_name]
                if operation_id in self._operation_metadata:
                    del self._operation_metadata[operation_id]

            return success
        except Exception as e:
            logger.error(f"Error failing operation {operation_name}: {e}")
            return False
