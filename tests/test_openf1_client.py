"""Tests for OpenF1 API client."""

import pytest
from unittest.mock import Mock, patch

from src.clients import OpenF1Client
from src.clients.openf1_client import OpenF1APIError


class TestOpenF1Client:
    """Test suite for OpenF1Client."""

    @pytest.fixture
    def client(self) -> OpenF1Client:
        """Create OpenF1Client instance for testing."""
        return OpenF1Client()

    def test_client_initialization(self, client: OpenF1Client) -> None:
        """Test client initializes with correct default values."""
        assert client.base_url == "https://api.openf1.org/v1"
        assert client.timeout == 30
        assert client.session is not None

    @patch("src.clients.openf1_client.requests.Session.get")
    def test_get_current_season_meetings_success(
        self, mock_get: Mock, client: OpenF1Client
    ) -> None:
        """Test successful retrieval of season meetings."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "meeting_key": 1234,
                "meeting_name": "Monaco Grand Prix",
                "circuit_short_name": "Monaco",
                "country_name": "Monaco",
                "date_start": "2024-05-26T00:00:00",
            }
        ]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Act
        meetings = client.get_current_season_meetings(2024)

        # Assert
        assert len(meetings) == 1
        assert meetings[0]["meeting_name"] == "Monaco Grand Prix"
        mock_get.assert_called_once()

    @patch("src.clients.openf1_client.requests.Session.get")
    def test_get_meetings_handles_timeout(
        self, mock_get: Mock, client: OpenF1Client
    ) -> None:
        """Test client handles timeout errors appropriately."""
        # Arrange
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        # Act & Assert
        with pytest.raises(OpenF1APIError, match="Request timeout"):
            client.get_current_season_meetings()

    @patch("src.clients.openf1_client.requests.Session.get")
    def test_get_meetings_handles_http_error(
        self, mock_get: Mock, client: OpenF1Client
    ) -> None:
        """Test client handles HTTP errors appropriately."""
        # Arrange
        import requests
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response

        # Act & Assert
        with pytest.raises(OpenF1APIError, match="HTTP error"):
            client.get_current_season_meetings()

    @patch("src.clients.openf1_client.requests.Session.get")
    def test_get_sessions_for_meeting(
        self, mock_get: Mock, client: OpenF1Client
    ) -> None:
        """Test retrieval of sessions for a specific meeting."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "session_key": 9999,
                "session_name": "Race",
                "session_type": "Race",
                "date_start": "2024-05-26T15:00:00",
                "date_end": "2024-05-26T17:00:00",
            }
        ]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Act
        sessions = client.get_sessions_for_meeting(1234)

        # Assert
        assert len(sessions) == 1
        assert sessions[0]["session_name"] == "Race"

    def test_client_close(self, client: OpenF1Client) -> None:
        """Test client session closes properly."""
        # Act
        client.close()

        # Assert - no exception should be raised
        assert True
