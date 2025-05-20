from sqlalchemy import Column, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class MangaUserLibraryCategory(Base):
    """Association model for MangaUserLibrary and Category."""
    __tablename__ = "manga_user_library_category"
    __table_args__ = {'extend_existing': True}

    manga_user_library_id = Column(UUID(as_uuid=True), ForeignKey("manga_user_library.id"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("category.id"), primary_key=True)

    # Relationships
    manga_user_library = relationship("MangaUserLibrary", back_populates="category_associations")
    category = relationship("Category", back_populates="manga_user_libraries")


class Category(Base):
    """Category model for organizing manga in user libraries."""
    __tablename__ = "category"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_default = Column(Boolean, default=False)

    # Relationships
    manga_user_libraries = relationship(
        "MangaUserLibraryCategory",
        back_populates="category",
        cascade="all, delete-orphan"
    )
