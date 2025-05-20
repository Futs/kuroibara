from typing import Any, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.library import LibraryCategory as Category
from app.schemas.library import Category as CategorySchema, CategoryCreate, CategoryUpdate

router = APIRouter()


@router.get("", response_model=List[CategorySchema])
async def read_categories(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve categories.
    """
    # Get default categories and user's categories
    result = await db.execute(
        select(Category).where(
            (Category.is_default == True) | (Category.user_id == current_user.id)
        ).offset(skip).limit(limit)
    )
    categories = result.scalars().all()
    return categories


@router.post("", response_model=CategorySchema)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new category.
    """
    # Check if category with same name already exists for this user
    result = await db.execute(
        select(Category).where(
            (Category.name == category_data.name) & (Category.user_id == current_user.id)
        )
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists",
        )

    # Create category
    category = Category(
        **category_data.model_dump(),
        user_id=current_user.id,
    )

    db.add(category)
    await db.commit()
    await db.refresh(category)

    return category


@router.get("/{category_id}", response_model=CategorySchema)
async def read_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get category by ID.
    """
    category = await db.get(Category, uuid.UUID(category_id))

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Check if category belongs to user or is a default category
    if not category.is_default and category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return category


@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: str,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a category.
    """
    category = await db.get(Category, uuid.UUID(category_id))

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Check if category belongs to user
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Check if name is being updated and if it's already taken
    if category_update.name and category_update.name != category.name:
        result = await db.execute(
            select(Category).where(
                (Category.name == category_update.name) & (Category.user_id == current_user.id)
            )
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists",
            )

    # Update category
    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a category.
    """
    category = await db.get(Category, uuid.UUID(category_id))

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Check if category belongs to user
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Check if category is a default category
    if category.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default category",
        )

    # Delete category
    await db.delete(category)
    await db.commit()
