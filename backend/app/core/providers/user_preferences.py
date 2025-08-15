"""
User provider preferences utilities for search prioritization.
"""

import logging
from typing import Dict, List, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.providers.base import BaseProvider
from app.models.user_provider_preference import UserProviderPreference

logger = logging.getLogger(__name__)


async def get_user_provider_preferences(
    db: AsyncSession, user_id: UUID
) -> Dict[str, UserProviderPreference]:
    """
    Get user's provider preferences as a dictionary keyed by provider_id.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Dictionary mapping provider_id to UserProviderPreference
    """
    try:
        result = await db.execute(
            select(UserProviderPreference).where(
                UserProviderPreference.user_id == user_id
            )
        )
        preferences = result.scalars().all()
        return {pref.provider_id: pref for pref in preferences}
    except Exception as e:
        logger.error(f"Error getting user provider preferences: {e}")
        return {}


def prioritize_providers_by_user_preferences(
    providers: List[BaseProvider], user_preferences: Dict[str, UserProviderPreference]
) -> Tuple[List[BaseProvider], List[BaseProvider]]:
    """
    Prioritize providers based on user preferences.

    Args:
        providers: List of available providers
        user_preferences: User's provider preferences

    Returns:
        Tuple of (priority_providers, regular_providers)
        - priority_providers: User's favorite providers sorted by priority
        - regular_providers: Non-favorite enabled providers
    """
    logger.info(
        f"Prioritizing providers with user preferences: {len(user_preferences)} preferences found"
    )
    for pref_id, pref in user_preferences.items():
        logger.debug(
            f"User preference: {pref_id} -> enabled={pref.is_enabled}, favorite={pref.is_favorite}"
        )

    favorite_providers = []
    enabled_providers = []

    for provider in providers:
        provider_id = provider.name.lower()
        user_pref = user_preferences.get(provider_id)

        # Skip disabled providers
        if user_pref and not user_pref.is_enabled:
            logger.info(
                f"Skipping disabled provider: {provider.name} (user preference)"
            )
            continue

        # Check if provider is a favorite
        if user_pref and user_pref.is_favorite:
            priority_order = user_pref.priority_order or 999
            favorite_providers.append((provider, priority_order))
        else:
            # Include providers without preferences (default enabled)
            # or providers explicitly enabled but not favorited
            enabled_providers.append(provider)

    # Sort favorite providers by priority order (lower number = higher priority)
    favorite_providers.sort(key=lambda x: x[1])
    priority_providers = [provider for provider, _ in favorite_providers]

    # Sort regular providers alphabetically for consistency
    enabled_providers.sort(key=lambda x: x.name)

    return priority_providers, enabled_providers


def get_fallback_provider_priority() -> List[str]:
    """
    Get fallback provider priority for users without preferences.
    This maintains the current hardcoded priority system.

    Returns:
        List of provider class names in priority order
    """
    return ["MangaDexProvider", "MangaPlusProvider", "MangaSeeProvider"]


def get_fallback_provider_names() -> List[str]:
    """
    Get fallback provider names (by provider name, not class) for mainstream providers.
    These are providers that are likely to have popular manga.

    Returns:
        List of provider names in priority order
    """
    return [
        "MangaDex",
        "MangaPlus",
        "MangaSee",  # Priority providers
        "MangaKakalot",
        "MangaBat",
        "MangaFox",
        "MangaTown",  # Popular generic providers
        "MangaLife",
        "MangaReaderTo",
        "ReadM",
        "Toonily",
        "ManhwaHub",
        "ManhuaZ",
        "Manhuaga",  # Popular manhwa/manhua providers
    ]


def apply_fallback_prioritization(
    providers: List[BaseProvider],
) -> Tuple[List[BaseProvider], List[BaseProvider]]:
    """
    Apply fallback prioritization for users without preferences.
    This prioritizes mainstream providers that are likely to have popular manga.

    Args:
        providers: List of available providers

    Returns:
        Tuple of (priority_providers, generic_providers)
    """
    priority_class_names = get_fallback_provider_priority()
    mainstream_provider_names = get_fallback_provider_names()
    priority_providers = []
    mainstream_providers = []
    generic_providers = []

    for provider in providers:
        if provider.__class__.__name__ in priority_class_names:
            priority_providers.append(provider)
        elif provider.name in mainstream_provider_names:
            mainstream_providers.append(provider)
        else:
            generic_providers.append(provider)

    # Sort priority providers by the defined order
    priority_providers.sort(
        key=lambda x: priority_class_names.index(x.__class__.__name__)
    )

    # Sort mainstream providers by the defined order
    mainstream_providers.sort(
        key=lambda x: (
            mainstream_provider_names.index(x.name)
            if x.name in mainstream_provider_names
            else 999
        )
    )

    # Combine mainstream and generic providers, limit total to reasonable number
    combined_generic = (
        mainstream_providers + generic_providers[:5]
    )  # Mainstream + 5 others

    return priority_providers, combined_generic
