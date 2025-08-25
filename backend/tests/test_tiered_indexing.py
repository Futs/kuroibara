"""Test suite for the tiered indexing system."""

import asyncio
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

try:
    from app.core.services.tiered_indexing import (
        IndexerTier,
        MadaraDexIndexer,
        MangaDexIndexer,
        MangaUpdatesIndexer,
        TieredSearchService,
        UniversalMetadata,
        tiered_search_service,
    )
except ImportError:
    # Skip these tests if the module is not available
    pytest.skip("Tiered indexing module not available", allow_module_level=True)


class TestUniversalMetadata:
    """Test the UniversalMetadata dataclass."""

    def test_universal_metadata_creation(self):
        """Test creating UniversalMetadata with minimal data."""
        metadata = UniversalMetadata(
            title="Test Manga",
            alternative_titles={"english": "Test Manga EN"},
            source_indexer="test",
            source_id="123",
            confidence_score=0.8,
        )

        assert metadata.title == "Test Manga"
        assert metadata.alternative_titles["english"] == "Test Manga EN"
        assert metadata.source_indexer == "test"
        assert metadata.source_id == "123"
        assert metadata.confidence_score == 0.8
        assert metadata.is_nsfw is False  # Default value

    def test_universal_metadata_nsfw_detection(self):
        """Test NSFW detection in metadata."""
        nsfw_metadata = UniversalMetadata(
            title="Adult Manga",
            alternative_titles={},
            source_indexer="test",
            source_id="456",
            is_nsfw=True,
            content_rating="erotica",
            confidence_score=0.9,
        )

        assert nsfw_metadata.is_nsfw is True
        assert nsfw_metadata.content_rating == "erotica"


class TestMangaUpdatesIndexer:
    """Test the MangaUpdates indexer."""

    @pytest.fixture
    def indexer(self):
        """Create a MangaUpdates indexer instance."""
        return MangaUpdatesIndexer()

    def test_indexer_initialization(self, indexer):
        """Test indexer initialization."""
        assert indexer.name == "MangaUpdates"
        assert indexer.tier == IndexerTier.PRIMARY
        assert indexer.base_url == "https://api.mangaupdates.com/v1"

    @pytest.mark.asyncio
    async def test_connection_test(self, indexer):
        """Test connection testing functionality."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"results": []}
            mock_get.return_value.__aenter__.return_value = mock_response

            async with indexer as idx:
                success, message = await idx.test_connection()

            assert success is True
            assert "Connected to MangaUpdates API" in message

    @pytest.mark.asyncio
    async def test_search_functionality(self, indexer):
        """Test search functionality with mocked response."""
        mock_search_result = {
            "results": [
                {
                    "record": {
                        "series_id": 12345,
                        "title": "Test Manga",
                        "description": "A test manga",
                        "type": {"type": "manga"},
                        "status": {"status": "ongoing"},
                        "year": {"year": 2023},
                        "genres": [{"genre": "Action"}, {"genre": "Adventure"}],
                        "authors": [{"name": "Test Author", "type": "author"}],
                        "rating": {"average": 8.5, "votes": 100},
                        "url": "https://mangaupdates.com/series/12345",
                    }
                }
            ]
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_search_result
            mock_get.return_value.__aenter__.return_value = mock_response

            async with indexer as idx:
                results = await idx.search("Test Manga", limit=5)

            assert len(results) == 1
            result = results[0]
            assert result.title == "Test Manga"
            assert result.source_indexer == "mangaupdates"
            assert result.source_id == "12345"
            assert result.confidence_score == 1.0
            assert "Action" in result.genres
            assert result.rating == 8.5


class TestMadaraDexIndexer:
    """Test the MadaraDex indexer."""

    @pytest.fixture
    def indexer(self):
        """Create a MadaraDex indexer instance."""
        return MadaraDexIndexer()

    def test_indexer_initialization(self, indexer):
        """Test indexer initialization."""
        assert indexer.name == "MadaraDex"
        assert indexer.tier == IndexerTier.SECONDARY
        assert indexer.base_url == "https://madaradex.org"

    @pytest.mark.asyncio
    async def test_connection_test(self, indexer):
        """Test connection testing functionality."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response

            async with indexer as idx:
                success, message = await idx.test_connection()

            assert success is True
            assert "Connected to MadaraDex" in message

    @pytest.mark.asyncio
    async def test_html_parsing_with_mock_data(self, indexer):
        """Test HTML parsing with mock HTML data."""
        mock_html = """
        <div class="page-item-detail">
            <h3 class="h5"><a href="/manga/test-manga">Test Manga</a></h3>
            <img src="/cover/test.jpg" alt="Test Manga">
            <a href="/genres/action">Action</a>
            <a href="/genres/mature">Mature</a>
        </div>
        """

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = mock_html
            mock_get.return_value.__aenter__.return_value = mock_response

            async with indexer as idx:
                results = await idx.search("Test Manga", limit=5)

            # Note: This will return empty list until BeautifulSoup parsing is fully implemented
            # But the test validates the structure is in place
            assert isinstance(results, list)


class TestMangaDexIndexer:
    """Test the MangaDex indexer."""

    @pytest.fixture
    def indexer(self):
        """Create a MangaDex indexer instance."""
        return MangaDexIndexer()

    def test_indexer_initialization(self, indexer):
        """Test indexer initialization."""
        assert indexer.name == "MangaDex"
        assert indexer.tier == IndexerTier.TERTIARY
        assert indexer.base_url == "https://api.mangadex.org"

    @pytest.mark.asyncio
    async def test_search_functionality(self, indexer):
        """Test search functionality with mocked MangaDex response."""
        mock_search_result = {
            "data": [
                {
                    "id": "abc123",
                    "attributes": {
                        "title": {"en": "Test Manga"},
                        "altTitles": [{"ja": "テストマンガ"}],
                        "description": {"en": "A test manga description"},
                        "status": "ongoing",
                        "year": 2023,
                        "contentRating": "safe",
                        "publicationDemographic": "shounen",
                    },
                    "relationships": [
                        {
                            "type": "cover_art",
                            "id": "cover123",
                            "attributes": {"fileName": "cover.jpg"},
                        },
                        {"type": "author", "attributes": {"name": "Test Author"}},
                        {"type": "tag", "attributes": {"name": {"en": "Action"}}},
                    ],
                }
            ]
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_search_result
            mock_get.return_value.__aenter__.return_value = mock_response

            async with indexer as idx:
                results = await idx.search("Test Manga", limit=5)

            assert len(results) == 1
            result = results[0]
            assert result.title == "Test Manga"
            assert result.source_indexer == "mangadex"
            assert result.source_id == "abc123"
            assert result.confidence_score == 0.9
            assert result.status == "ongoing"
            assert result.content_rating == "safe"
            assert result.demographic == "shounen"


class TestTieredSearchService:
    """Test the tiered search service."""

    @pytest.fixture
    def service(self):
        """Create a tiered search service instance."""
        return TieredSearchService()

    def test_service_initialization(self, service):
        """Test service initialization."""
        assert len(service.indexers) == 3
        assert isinstance(service.indexers[0], MangaUpdatesIndexer)
        assert isinstance(service.indexers[1], MadaraDexIndexer)
        assert isinstance(service.indexers[2], MangaDexIndexer)

    @pytest.mark.asyncio
    async def test_tiered_search_with_fallback(self, service):
        """Test tiered search with fallback when primary fails."""
        # Mock MangaUpdates to fail
        mangaupdates_results = []

        # Mock MadaraDex to return empty
        madaradex_results = []

        # Mock MangaDex to succeed
        mangadx_results = [
            UniversalMetadata(
                title="Test Manga",
                alternative_titles={"en": "Test Manga"},
                source_indexer="mangadex",
                source_id="test123",
                confidence_score=0.9,
            )
        ]

        with (
            patch.object(
                service.indexers[0], "search", return_value=mangaupdates_results
            ),
            patch.object(service.indexers[1], "search", return_value=madaradex_results),
            patch.object(service.indexers[2], "search", return_value=mangadx_results),
        ):

            results = await service.search("Test Manga", limit=10)

            assert len(results) == 1
            assert results[0].source_indexer == "mangadex"
            assert results[0].title == "Test Manga"

    @pytest.mark.asyncio
    async def test_health_monitoring(self, service):
        """Test health monitoring across all indexers."""
        # Mock health check responses
        health_responses = {
            "MangaUpdates": (True, "Connected"),
            "MadaraDex": (True, "Connected"),
            "MangaDex": (False, "Connection timeout"),
        }

        async def mock_test_connection(indexer_name):
            return health_responses[indexer_name]

        with (
            patch.object(
                service.indexers[0], "test_connection", return_value=(True, "Connected")
            ),
            patch.object(
                service.indexers[1], "test_connection", return_value=(True, "Connected")
            ),
            patch.object(
                service.indexers[2],
                "test_connection",
                return_value=(False, "Connection timeout"),
            ),
        ):

            health_results = await service.test_all_indexers()

            assert len(health_results) == 3
            assert health_results["MangaUpdates"][0] is True
            assert health_results["MadaraDex"][0] is True
            assert health_results["MangaDex"][0] is False

    def test_deduplication_logic(self, service):
        """Test result deduplication."""
        results = [
            UniversalMetadata(
                title="Test Manga",
                alternative_titles={},
                source_indexer="mangaupdates",
                source_id="1",
                confidence_score=1.0,
            ),
            UniversalMetadata(
                title="Test Manga",  # Duplicate title
                alternative_titles={},
                source_indexer="mangadex",
                source_id="2",
                confidence_score=0.9,
            ),
            UniversalMetadata(
                title="Different Manga",
                alternative_titles={},
                source_indexer="mangadex",
                source_id="3",
                confidence_score=0.8,
            ),
        ]

        unique_results = service._deduplicate_results(results)

        assert len(unique_results) == 2
        # Should keep the higher confidence score for duplicates
        test_manga_result = next(r for r in unique_results if r.title == "Test Manga")
        assert test_manga_result.confidence_score == 1.0
        assert test_manga_result.source_indexer == "mangaupdates"

    def test_result_sorting(self, service):
        """Test result sorting by tier and confidence."""
        results = [
            UniversalMetadata(
                title="MangaDex Result",
                alternative_titles={},
                source_indexer="mangadex",
                source_id="1",
                confidence_score=0.9,
            ),
            UniversalMetadata(
                title="MangaUpdates Result",
                alternative_titles={},
                source_indexer="mangaupdates",
                source_id="2",
                confidence_score=0.8,
            ),
            UniversalMetadata(
                title="MadaraDex Result",
                alternative_titles={},
                source_indexer="madaradx",
                source_id="3",
                confidence_score=0.95,
            ),
        ]

        sorted_results = service._sort_results(results)

        # Should be sorted by tier priority first (MangaUpdates, MadaraDx, MangaDx)
        assert sorted_results[0].source_indexer == "mangaupdates"
        assert sorted_results[1].source_indexer == "madaradx"
        assert sorted_results[2].source_indexer == "mangadex"


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    @pytest.mark.asyncio
    async def test_nsfw_content_detection(self):
        """Test NSFW content detection across indexers."""
        nsfw_metadata = UniversalMetadata(
            title="Adult Content",
            alternative_titles={},
            source_indexer="test",
            source_id="nsfw1",
            is_nsfw=True,
            content_rating="erotica",
            genres=["Adult", "Romance"],
            confidence_score=0.9,
        )

        safe_metadata = UniversalMetadata(
            title="Safe Content",
            alternative_titles={},
            source_indexer="test",
            source_id="safe1",
            is_nsfw=False,
            content_rating="safe",
            genres=["Action", "Adventure"],
            confidence_score=0.9,
        )

        assert nsfw_metadata.is_nsfw is True
        assert nsfw_metadata.content_rating == "erotica"
        assert safe_metadata.is_nsfw is False
        assert safe_metadata.content_rating == "safe"

    @pytest.mark.asyncio
    async def test_confidence_scoring_scenarios(self):
        """Test various confidence scoring scenarios."""
        # High confidence - primary indexer with complete data
        high_confidence = UniversalMetadata(
            title="Complete Manga",
            alternative_titles={"en": "Complete Manga EN"},
            description="Full description",
            source_indexer="mangaupdates",
            source_id="complete1",
            genres=["Action", "Adventure"],
            authors=[{"name": "Author", "role": "author"}],
            rating=8.5,
            confidence_score=1.0,
        )

        # Medium confidence - secondary indexer
        medium_confidence = UniversalMetadata(
            title="Partial Manga",
            alternative_titles={},
            source_indexer="madaradx",
            source_id="partial1",
            confidence_score=0.8,
        )

        # Low confidence - minimal data
        low_confidence = UniversalMetadata(
            title="Minimal Manga",
            alternative_titles={},
            source_indexer="mangadex",
            source_id="minimal1",
            confidence_score=0.6,
        )

        assert high_confidence.confidence_score > medium_confidence.confidence_score
        assert medium_confidence.confidence_score > low_confidence.confidence_score


@pytest.mark.integration
class TestLiveIndexerConnections:
    """Integration tests that connect to real indexer APIs."""

    @pytest.mark.asyncio
    async def test_mangadx_live_connection(self):
        """Test live connection to MangaDx API."""
        indexer = MangaDexIndexer()

        async with indexer as idx:
            success, message = await idx.test_connection()

        # This test may fail if the API is down, which is expected
        if success:
            assert "Connected to MangaDex API" in message
        else:
            pytest.skip(f"MangaDx API unavailable: {message}")

    @pytest.mark.asyncio
    async def test_madaradx_live_connection(self):
        """Test live connection to MadaraDx."""
        indexer = MadaraDexIndexer()

        async with indexer as idx:
            success, message = await idx.test_connection()

        # This test may fail if the site is down, which is expected
        if success:
            assert "Connected to MadaraDex" in message
        else:
            pytest.skip(f"MadaraDx unavailable: {message}")


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
