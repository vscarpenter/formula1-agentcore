"""Tests for DynamoDB preferences store."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.storage import PreferencesStore
from src.storage.preferences_store import PreferencesStoreError
from src.models import UserPreferences


class TestPreferencesStore:
    """Test suite for PreferencesStore."""

    @pytest.fixture
    def store(self) -> PreferencesStore:
        """Create PreferencesStore instance with mocked DynamoDB."""
        with patch("src.storage.preferences_store.boto3.resource"):
            return PreferencesStore(table_name="test-table")

    @pytest.fixture
    def sample_preferences(self) -> UserPreferences:
        """Create sample user preferences for testing."""
        return UserPreferences(
            user_id="test_user",
            favorite_driver="Max Verstappen",
            favorite_team="Red Bull Racing",
            preferred_circuits=["Monaco", "Suzuka"],
            timezone="America/Chicago",
        )

    def test_store_initialization(self, store: PreferencesStore) -> None:
        """Test store initializes with correct table name."""
        assert store.table_name == "test-table"

    def test_get_preferences_success(self, store: PreferencesStore) -> None:
        """Test successful retrieval of user preferences."""
        # Arrange
        mock_item = {
            "user_id": "test_user",
            "favorite_driver": "Lewis Hamilton",
            "favorite_team": "Mercedes",
            "preferred_circuits": [],
            "notification_preferences": {"pre_race_briefing": True},
            "timezone": "UTC",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        store.table.get_item = Mock(return_value={"Item": mock_item})

        # Act
        prefs = store.get_preferences("test_user")

        # Assert
        assert prefs is not None
        assert prefs.user_id == "test_user"
        assert prefs.favorite_driver == "Lewis Hamilton"

    def test_get_preferences_not_found(self, store: PreferencesStore) -> None:
        """Test behavior when preferences don't exist."""
        # Arrange
        store.table.get_item = Mock(return_value={})

        # Act
        prefs = store.get_preferences("nonexistent_user")

        # Assert
        assert prefs is None

    def test_save_preferences_success(
        self, store: PreferencesStore, sample_preferences: UserPreferences
    ) -> None:
        """Test successful saving of preferences."""
        # Arrange
        store.table.put_item = Mock()

        # Act
        store.save_preferences(sample_preferences)

        # Assert
        store.table.put_item.assert_called_once()
        call_args = store.table.put_item.call_args
        assert call_args[1]["Item"]["user_id"] == "test_user"

    def test_update_favorite_driver(self, store: PreferencesStore) -> None:
        """Test updating favorite driver preference."""
        # Arrange
        store.table.update_item = Mock()

        # Act
        store.update_favorite_driver("test_user", "Charles Leclerc")

        # Assert
        store.table.update_item.assert_called_once()

    def test_update_favorite_team(self, store: PreferencesStore) -> None:
        """Test updating favorite team preference."""
        # Arrange
        store.table.update_item = Mock()

        # Act
        store.update_favorite_team("test_user", "Ferrari")

        # Assert
        store.table.update_item.assert_called_once()

    def test_delete_preferences(self, store: PreferencesStore) -> None:
        """Test deleting user preferences."""
        # Arrange
        store.table.delete_item = Mock()

        # Act
        store.delete_preferences("test_user")

        # Assert
        store.table.delete_item.assert_called_once_with(Key={"user_id": "test_user"})
