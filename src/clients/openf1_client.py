"""Client for OpenF1 API with error handling and retry logic."""

import logging
import time
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# API rate limiting and retry configuration
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]


class OpenF1APIError(Exception):
    """Raised when OpenF1 API returns an error."""

    pass


class OpenF1Client:
    """
    Client for interacting with the OpenF1 API.

    Provides methods to fetch F1 data including sessions, drivers,
    meetings, and more. Implements exponential backoff retry logic
    for transient failures.
    """

    def __init__(
        self,
        base_url: str = "https://api.openf1.org/v1",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = self._create_session(max_retries)

    def _create_session(self, max_retries: int) -> requests.Session:
        """Create a requests session with retry configuration."""
        session = requests.Session()

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=RETRY_STATUS_CODES,
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _make_request(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """
        Make a GET request to the OpenF1 API.

        Args:
            endpoint: API endpoint path (e.g., "/sessions")
            params: Query parameters

        Returns:
            List of data objects from the API

        Raises:
            OpenF1APIError: If the API returns an error or request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            logger.info(f"Requesting: {url} with params: {params}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Successfully fetched {len(data)} records from {endpoint}")
            return data

        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout for {url}: {str(e)}"
            logger.error(error_msg)
            raise OpenF1APIError(error_msg) from e

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error for {url}: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise OpenF1APIError(error_msg) from e

        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed for {url}: {str(e)}"
            logger.error(error_msg)
            raise OpenF1APIError(error_msg) from e

        except ValueError as e:
            error_msg = f"Invalid JSON response from {url}: {str(e)}"
            logger.error(error_msg)
            raise OpenF1APIError(error_msg) from e

    def get_current_season_meetings(self, year: Optional[int] = None) -> list[dict[str, Any]]:
        """
        Fetch all meetings (race weekends) for a season.

        Args:
            year: Year to fetch (defaults to current year)

        Returns:
            List of meeting data dictionaries
        """
        params = {}
        if year:
            params["year"] = year
        return self._make_request("meetings", params)

    def get_sessions_for_meeting(self, meeting_key: int) -> list[dict[str, Any]]:
        """
        Fetch all sessions for a specific race weekend.

        Args:
            meeting_key: Unique identifier for the race weekend

        Returns:
            List of session data dictionaries
        """
        return self._make_request("sessions", {"meeting_key": meeting_key})

    def get_drivers(self, session_key: Optional[int] = None) -> list[dict[str, Any]]:
        """
        Fetch driver information.

        Args:
            session_key: Optional session to filter drivers

        Returns:
            List of driver data dictionaries
        """
        params = {}
        if session_key:
            params["session_key"] = session_key
        return self._make_request("drivers", params)

    def get_latest_session(self) -> Optional[dict[str, Any]]:
        """
        Fetch the most recent session.

        Returns:
            Latest session data or None if not found
        """
        sessions = self._make_request("sessions", {"session_name": "Race"})
        return sessions[0] if sessions else None

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
