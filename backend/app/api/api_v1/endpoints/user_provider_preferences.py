from typing import Any, List, Dict
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.user_provider_preference import UserProviderPreference
from app.models.provider import ProviderStatus
from app.schemas.user_provider_preference import (
    UserProviderPreferencesResponse,
    UserProviderPreferenceUpdate,
    UserProviderPreferenceBulkUpdate,
    ProviderWithPreference
)
from app.core.providers.registry import provider_registry

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=UserProviderPreferencesResponse)
async def get_user_provider_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user's provider preferences with provider information.
    """
    try:
        # Get all available providers from registry
        provider_info_list = provider_registry.get_provider_info()
        
        # Get provider statuses from database
        result = await db.execute(select(ProviderStatus))
        provider_statuses = {ps.provider_id: ps for ps in result.scalars().all()}
        
        # Get user's provider preferences
        result = await db.execute(
            select(UserProviderPreference).where(
                UserProviderPreference.user_id == current_user.id
            )
        )
        user_preferences = {pref.provider_id: pref for pref in result.scalars().all()}
        
        # Combine provider info with user preferences and status
        providers_with_preferences = []
        favorite_count = 0
        
        for provider_info in provider_info_list:
            provider_id = provider_info["id"]
            status_record = provider_statuses.get(provider_id)
            user_pref = user_preferences.get(provider_id)
            
            # Compute health status to avoid greenlet issues with property access
            is_healthy = True
            if status_record:
                from app.models.provider import ProviderStatusEnum
                is_healthy = (
                    status_record.status == ProviderStatusEnum.ACTIVE.value and
                    status_record.consecutive_failures < status_record.max_consecutive_failures and
                    status_record.is_enabled
                )

            # Build enhanced provider info
            provider_with_pref = ProviderWithPreference(
                # Provider info
                id=provider_info["id"],
                name=provider_info["name"],
                url=provider_info["url"],
                supports_nsfw=provider_info["supports_nsfw"],
                status=status_record.status if status_record else "unknown",
                is_enabled=status_record.is_enabled if status_record else True,
                last_check=status_record.last_check.isoformat() if status_record and status_record.last_check else None,
                response_time=status_record.response_time if status_record else None,
                uptime_percentage=status_record.uptime_percentage if status_record else 100,
                consecutive_failures=status_record.consecutive_failures if status_record else 0,
                is_healthy=is_healthy,

                # User preference data
                is_favorite=user_pref.is_favorite if user_pref else False,
                priority_order=user_pref.priority_order if user_pref else None,
                user_enabled=user_pref.is_enabled if user_pref else True,
            )
            
            providers_with_preferences.append(provider_with_pref)
            
            if user_pref and user_pref.is_favorite:
                favorite_count += 1
        
        # Sort providers: favorites first (by priority), then others alphabetically
        def sort_key(provider):
            if provider.is_favorite:
                return (0, provider.priority_order or 999, provider.name.lower())
            else:
                return (1, provider.name.lower())
        
        providers_with_preferences.sort(key=sort_key)
        
        return UserProviderPreferencesResponse(
            providers=providers_with_preferences,
            total_providers=len(providers_with_preferences),
            favorite_count=favorite_count
        )
        
    except Exception as e:
        logger.error(f"Error getting user provider preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get provider preferences"
        )


@router.put("/{provider_id}", response_model=dict)
async def update_provider_preference(
    provider_id: str,
    preference_update: UserProviderPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a specific provider preference for the current user.
    """
    try:
        # Validate provider exists
        provider = provider_registry.get_provider(provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider_id}' not found"
            )
        
        # Get existing preference or create new one
        result = await db.execute(
            select(UserProviderPreference).where(
                and_(
                    UserProviderPreference.user_id == current_user.id,
                    UserProviderPreference.provider_id == provider_id
                )
            )
        )
        existing_pref = result.scalar_one_or_none()
        
        if existing_pref:
            # Update existing preference
            update_data = preference_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(existing_pref, field, value)
        else:
            # Create new preference
            update_data = preference_update.model_dump(exclude_unset=True)
            new_pref = UserProviderPreference(
                user_id=current_user.id,
                provider_id=provider_id,
                **update_data
            )
            db.add(new_pref)
        
        await db.commit()
        
        return {
            "message": f"Provider preference for '{provider_id}' updated successfully",
            "provider_id": provider_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating provider preference: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update provider preference"
        )


@router.post("/bulk", response_model=dict)
async def bulk_update_provider_preferences(
    bulk_update: UserProviderPreferenceBulkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Bulk update provider preferences for the current user.
    """
    try:
        logger.info(f"Bulk updating {len(bulk_update.preferences)} provider preferences for user {current_user.id}")

        # Validate all providers exist
        for pref in bulk_update.preferences:
            logger.debug(f"Validating provider: {pref.provider_id}")
            provider = provider_registry.get_provider(pref.provider_id)
            if not provider:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Provider '{pref.provider_id}' not found"
                )
        
        # Get existing preferences
        result = await db.execute(
            select(UserProviderPreference).where(
                UserProviderPreference.user_id == current_user.id
            )
        )
        existing_prefs = {pref.provider_id: pref for pref in result.scalars().all()}
        
        updated_count = 0
        created_count = 0
        
        # Process each preference update
        for pref_data in bulk_update.preferences:
            provider_id = pref_data.provider_id
            
            if provider_id in existing_prefs:
                # Update existing preference
                existing_pref = existing_prefs[provider_id]
                existing_pref.is_favorite = pref_data.is_favorite
                existing_pref.priority_order = pref_data.priority_order
                existing_pref.is_enabled = pref_data.is_enabled
                updated_count += 1
            else:
                # Create new preference
                new_pref = UserProviderPreference(
                    user_id=current_user.id,
                    provider_id=provider_id,
                    is_favorite=pref_data.is_favorite,
                    priority_order=pref_data.priority_order,
                    is_enabled=pref_data.is_enabled
                )
                db.add(new_pref)
                created_count += 1
        
        await db.commit()
        
        return {
            "message": "Provider preferences updated successfully",
            "updated_count": updated_count,
            "created_count": created_count,
            "total_processed": len(bulk_update.preferences)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk updating provider preferences: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update provider preferences: {str(e)}"
        )


@router.delete("/{provider_id}", response_model=dict)
async def delete_provider_preference(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a provider preference (reset to defaults).
    """
    try:
        # Delete the preference record
        result = await db.execute(
            delete(UserProviderPreference).where(
                and_(
                    UserProviderPreference.user_id == current_user.id,
                    UserProviderPreference.provider_id == provider_id
                )
            )
        )
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No preference found for provider '{provider_id}'"
            )
        
        await db.commit()
        
        return {
            "message": f"Provider preference for '{provider_id}' reset to defaults",
            "provider_id": provider_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting provider preference: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete provider preference"
        )
