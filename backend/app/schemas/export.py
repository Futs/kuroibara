from typing import List
from uuid import UUID

from pydantic import BaseModel


class ExportRequest(BaseModel):
    manga_id: UUID
    chapter_id: UUID
    auto_export_cbz: bool = True


class ExportItem(BaseModel):
    manga_id: UUID
    chapter_id: UUID
    auto_export_cbz: bool = True


class BulkExportRequest(BaseModel):
    items: List[ExportItem]
