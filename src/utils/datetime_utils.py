"""Date and time utility functions."""

from datetime import datetime, timezone


def parse_iso_datetime(iso_string: str) -> datetime:
    """
    Parse ISO format datetime string to datetime object.

    Args:
        iso_string: ISO format datetime string

    Returns:
        datetime object with timezone info
    """
    try:
        return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    except ValueError as e:
        raise ValueError(f"Invalid ISO datetime format: {iso_string}") from e


def format_race_datetime(dt: datetime, timezone_offset: str = "+00:00") -> str:
    """
    Format datetime for race schedule display.

    Args:
        dt: datetime object to format
        timezone_offset: Timezone offset string (e.g., "+02:00")

    Returns:
        Formatted datetime string for display
    """
    return dt.strftime("%A, %B %d, %Y at %H:%M %Z")


def get_current_season() -> int:
    """Get the current F1 season year."""
    return datetime.now(timezone.utc).year
