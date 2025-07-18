"""
Tests for storage settings functionality
"""

import os

import pytest
from sqlalchemy import create_engine, text

from app.models.user import User
from app.schemas.user import UserSettings, UserSettingsUpdate


class TestStorageSettings:
    """Test storage settings functionality"""

    def test_user_model_has_storage_fields(self):
        """Test that User model includes storage fields"""
        user_columns = {col.name for col in User.__table__.columns}

        assert (
            "storage_type" in user_columns
        ), "storage_type column missing from User model"
        assert (
            "max_upload_size" in user_columns
        ), "max_upload_size column missing from User model"

    def test_user_settings_schema_includes_storage_fields(self):
        """Test that UserSettings schema includes storage fields"""
        schema_fields = set(UserSettings.__annotations__.keys())

        assert (
            "storage_type" in schema_fields
        ), "storage_type missing from UserSettings schema"
        assert (
            "max_upload_size" in schema_fields
        ), "max_upload_size missing from UserSettings schema"

    def test_user_settings_update_schema_includes_storage_fields(self):
        """Test that UserSettingsUpdate schema includes storage fields"""
        update_fields = set(UserSettingsUpdate.__annotations__.keys())

        assert (
            "storage_type" in update_fields
        ), "storage_type missing from UserSettingsUpdate schema"
        assert (
            "max_upload_size" in update_fields
        ), "max_upload_size missing from UserSettingsUpdate schema"

    def test_storage_type_validation(self):
        """Test that valid storage types are accepted"""
        valid_types = ["local", "s3", "gcs", "azure"]

        for storage_type in valid_types:
            # Should not raise an exception
            settings = UserSettingsUpdate(storage_type=storage_type)
            assert settings.storage_type == storage_type

    def test_max_upload_size_validation(self):
        """Test that valid upload sizes are accepted"""
        valid_sizes = ["50MB", "100MB", "250MB", "500MB", "1GB", "2GB"]

        for size in valid_sizes:
            # Should not raise an exception
            settings = UserSettingsUpdate(max_upload_size=size)
            assert settings.max_upload_size == size

    @pytest.mark.asyncio
    async def test_database_schema_has_storage_columns(self, db):
        """Test that database has storage columns with correct defaults"""
        # Use the test database session to check schema
        from sqlalchemy import text

        # Check columns exist using the test database session
        result = await db.execute(
            text(
                """
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'users'
                AND column_name IN ('storage_type', 'max_upload_size')
                ORDER BY column_name;
            """
            )
        )

        columns = {
            row[0]: {"type": row[1], "default": row[2]} for row in result.fetchall()
        }

        assert (
            "storage_type" in columns
        ), "storage_type column missing from database"
        assert (
            "max_upload_size" in columns
        ), "max_upload_size column missing from database"

        # Check defaults
        assert (
            "'local'" in columns["storage_type"]["default"]
        ), "storage_type default should be 'local'"
        assert (
            "'100MB'" in columns["max_upload_size"]["default"]
        ), "max_upload_size default should be '100MB'"

    def test_user_settings_complete_schema(self):
        """Test that UserSettings can be created with all fields including storage"""
        settings = UserSettings(
            id=1,
            email="test@example.com",
            username="testuser",
            is_active=True,
            theme="dark",
            nsfw_blur=True,
            download_quality="high",
            download_path="/downloads",
            naming_format_manga="{Manga Title}",
            naming_format_chapter="{Chapter Number}",
            auto_organize_imports=True,
            create_cbz_files=True,
            preserve_original_files=False,
            chapter_auto_refresh_interval=300,
            chapter_check_on_tab_focus=True,
            chapter_show_update_notifications=True,
            chapter_enable_manual_refresh=True,
            storage_type="s3",
            max_upload_size="500MB",
        )

        assert settings.storage_type == "s3"
        assert settings.max_upload_size == "500MB"

    def test_user_settings_update_partial(self):
        """Test that UserSettingsUpdate works with partial updates"""
        # Test updating only storage_type
        settings = UserSettingsUpdate(storage_type="gcs")
        assert settings.storage_type == "gcs"
        assert settings.max_upload_size is None

        # Test updating only max_upload_size
        settings = UserSettingsUpdate(max_upload_size="1GB")
        assert settings.max_upload_size == "1GB"
        assert settings.storage_type is None

        # Test updating both
        settings = UserSettingsUpdate(storage_type="azure", max_upload_size="2GB")
        assert settings.storage_type == "azure"
        assert settings.max_upload_size == "2GB"
