import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.download import download_chapter_with_fallback
from app.db.session import get_db
from app.models.manga import Chapter, Manga
from app.schemas.export import BulkExportRequest, ExportRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chapters", tags=["Chapters"])


@router.post("/export")
async def export_chapter_cbz(
    request: ExportRequest, db: AsyncSession = Depends(get_db)
):
    """
    Export a specific chapter as a CBZ file.
    """
    manga = await db.get(Manga, request.manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")

    chapter = await db.get(Chapter, request.chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if not chapter.file_path or not os.path.exists(chapter.file_path):
        raise HTTPException(status_code=404, detail="Chapter file not found on server")

    primary_provider = chapter.source if chapter.source else "MangaDx"

    external_manga_id = str(request.manga_id)
    external_chapter_id = str(request.chapter_id)

    try:
        cbz_path = await download_chapter_with_fallback(
            manga_id=request.manga_id,
            chapter_id=request.chapter_id,
            primary_provider=primary_provider,
            external_manga_id=external_manga_id,
            external_chapter_id=external_chapter_id,
            db=db,
            auto_export_cbz=request.auto_export_cbz,
        )

        return {"message": "Chapter exported successfully", "cbz_path": cbz_path}
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/bulk/export")
async def bulk_export_chapters(
    request: BulkExportRequest, db: AsyncSession = Depends(get_db)
):
    """
    Export multiple chapters as CBZ files in bulk.
    """
    results = []
    for item in request.items:
        try:
            manga = await db.get(Manga, item.manga_id)
            if not manga:
                results.append(
                    {
                        "chapter_id": str(item.chapter_id),
                        "status": "failed",
                        "error": "Manga not found",
                    }
                )
                continue

            chapter = await db.get(Chapter, item.chapter_id)
            if not chapter:
                results.append(
                    {
                        "chapter_id": str(item.chapter_id),
                        "status": "failed",
                        "error": "Chapter not found",
                    }
                )
                continue

            if not chapter.file_path or not os.path.exists(chapter.file_path):
                results.append(
                    {
                        "chapter_id": str(item.chapter_id),
                        "status": "failed",
                        "error": "Chapter file not found on server",
                    }
                )
                continue

            primary_provider = chapter.source if chapter.source else "MangaDx"
            external_manga_id = str(item.manga_id)
            external_chapter_id = str(item.chapter_id)

            cbz_path = await download_chapter_with_fallback(
                manga_id=item.manga_id,
                chapter_id=item.chapter_id,
                primary_provider=primary_provider,
                external_manga_id=external_manga_id,
                external_chapter_id=external_chapter_id,
                db=db,
                auto_export_cbz=item.auto_export_cbz,
            )

            results.append(
                {
                    "chapter_id": str(item.chapter_id),
                    "status": "success",
                    "cbz_path": cbz_path,
                }
            )
        except Exception as e:
            logger.error(
                f"Bulk export failed for manga_id={item.manga_id}, chapter_id={item.chapter_id}: {e}"
            )
            results.append(
                {
                    "chapter_id": str(item.chapter_id),
                    "status": "failed",
                    "error": str(e),
                }
            )

    return {"results": results}
