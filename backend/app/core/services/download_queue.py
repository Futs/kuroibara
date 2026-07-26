import logging
from asyncio import PriorityQueue
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass(order=True)
class PriorityDownload:
    priority: int
    download_id: UUID = field(compare=False)
    manga_id: UUID = field(compare=False)
    chapter_id: UUID = field(compare=False)
    provider_name: str = field(compare=False)
    external_manga_id: str = field(compare=False)
    external_chapter_id: str = field(compare=False)
    task_id: Optional[str] = field(compare=False)
    retry_count: int = field(default=0, compare=False)


class DownloadQueueManager:
    def __init__(self, max_concurrent: int = 3):
        self.queue: PriorityQueue[PriorityDownload] = PriorityQueue()
        self.active_downloads: Dict[str, Any] = {}
        self.max_concurrent = max_concurrent
        self.running_count = 0

    async def add_to_queue(self, item: PriorityDownload):
        await self.queue.put(item)
        logger.info(
            f"Added task {item.download_id} to queue with priority {item.priority}"
        )

    async def get_next_task(self) -> Optional[PriorityDownload]:
        if self.running_count < self.max_concurrent and not self.queue.empty():
            return await self.queue.get()
        return None

    def release_task(self, task_id: str):
        self.running_count -= 1
        logger.info(
            f"Released task {task_id}, current running count: {self.running_count}"
        )

    def increment_running_count(self):
        self.running_count += 1


# Global instance
queue_manager = DownloadQueueManager()
