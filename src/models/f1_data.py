"""F1 data models using Pydantic for validation and type safety."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Driver(BaseModel):
    """Represents an F1 driver."""

    driver_number: int
    full_name: str
    name_acronym: str  # e.g., "VER" for Max Verstappen
    team_name: Optional[str] = None
    country_code: str


class Team(BaseModel):
    """Represents an F1 team/constructor."""

    team_name: str
    team_color: Optional[str] = None


class Circuit(BaseModel):
    """Represents an F1 circuit."""

    circuit_key: int
    circuit_short_name: str
    location: str
    country: str


class Meeting(BaseModel):
    """Represents a race weekend meeting."""

    meeting_key: int
    meeting_name: str  # e.g., "British Grand Prix"
    circuit_key: int
    circuit_short_name: str
    country_name: str
    date_start: datetime
    gmt_offset: str
    location: str
    year: int


class Session(BaseModel):
    """Represents a session within a race weekend (Practice, Qualifying, Race)."""

    session_key: int
    session_name: str  # e.g., "Race", "Qualifying", "Practice 1"
    session_type: str
    date_start: datetime
    date_end: datetime
    gmt_offset: str
    meeting_key: int


class Race(BaseModel):
    """Combined race weekend information."""

    meeting: Meeting
    sessions: list[Session]


class DriverStanding(BaseModel):
    """Driver championship standing."""

    position: int
    driver: Driver
    points: float
    wins: int


class TeamStanding(BaseModel):
    """Team/Constructor championship standing."""

    position: int
    team: Team
    points: float
    wins: int


class UserPreferences(BaseModel):
    """User preferences for personalized F1 content."""

    user_id: str
    favorite_driver: Optional[str] = None  # driver number or name
    favorite_team: Optional[str] = None
    preferred_circuits: list[str] = Field(default_factory=list)
    notification_preferences: dict[str, bool] = Field(
        default_factory=lambda: {
            "pre_race_briefing": True,
            "race_start_reminder": True,
            "post_race_summary": True,
        }
    )
    timezone: str = "UTC"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RaceBriefing(BaseModel):
    """Generated race briefing with AI insights."""

    race_name: str
    circuit_name: str
    date: datetime
    weather_forecast: Optional[str] = None
    track_characteristics: str
    driver_form_analysis: str
    key_storylines: list[str]
    prediction_summary: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
