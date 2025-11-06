"""
Lambda handler for F1 data action group.

This Lambda function serves as an action group for the Bedrock Agent,
providing F1 race calendar, standings, and session information.
"""

import json
import logging
import os
from typing import Any

from src.clients import OpenF1Client
from src.utils import get_current_season, setup_logging

setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize OpenF1 client (reused across Lambda invocations)
openf1_client = OpenF1Client()


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handle Bedrock Agent action group requests for F1 data.

    The agent will call this Lambda with different actions:
    - get_race_calendar: Get current season race schedule
    - get_driver_standings: Get current driver championship standings
    - get_team_standings: Get current constructor standings
    - get_next_race: Get details about the upcoming race
    - get_race_sessions: Get sessions for a specific race weekend

    Args:
        event: Bedrock Agent event containing action and parameters
        context: Lambda context object

    Returns:
        Response dictionary formatted for Bedrock Agent
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Extract action and parameters from Bedrock Agent event
        action_group = event.get("actionGroup", "")
        api_path = event.get("apiPath", "")
        parameters = event.get("parameters", [])

        # Convert parameters list to dict for easier access
        params_dict = {param["name"]: param["value"] for param in parameters}

        logger.info(f"Processing action: {api_path} with params: {params_dict}")

        # Route to appropriate handler
        if api_path == "/calendar":
            response_body = handle_get_calendar(params_dict)
        elif api_path == "/standings/drivers":
            response_body = handle_get_driver_standings(params_dict)
        elif api_path == "/standings/teams":
            response_body = handle_get_team_standings(params_dict)
        elif api_path == "/race/next":
            response_body = handle_get_next_race(params_dict)
        elif api_path == "/race/sessions":
            response_body = handle_get_race_sessions(params_dict)
        else:
            raise ValueError(f"Unknown API path: {api_path}")

        # Return response in Bedrock Agent format
        return build_success_response(response_body)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return build_error_response(str(e))


def handle_get_calendar(params: dict[str, str]) -> dict[str, Any]:
    """Get F1 race calendar for the season."""
    year = int(params.get("year", get_current_season()))

    meetings = openf1_client.get_current_season_meetings(year)

    # Format for easier consumption
    calendar = [
        {
            "race_name": meeting["meeting_name"],
            "circuit": meeting["circuit_short_name"],
            "country": meeting["country_name"],
            "date": meeting["date_start"],
            "round": idx + 1,
        }
        for idx, meeting in enumerate(meetings)
    ]

    return {"year": year, "races": calendar, "total_races": len(calendar)}


def handle_get_driver_standings(params: dict[str, str]) -> dict[str, Any]:
    """
    Get driver championship standings.

    Note: OpenF1 API doesn't provide standings directly.
    This is a placeholder - you'd need to calculate from race results
    or use a different data source like Ergast API.
    """
    return {
        "message": "Driver standings require race results aggregation",
        "note": "Consider integrating Ergast API for historical standings data",
        "status": "not_implemented",
    }


def handle_get_team_standings(params: dict[str, str]) -> dict[str, Any]:
    """
    Get constructor championship standings.

    Note: Similar to driver standings, this requires aggregation
    of race results or a different data source.
    """
    return {
        "message": "Team standings require race results aggregation",
        "note": "Consider integrating Ergast API for historical standings data",
        "status": "not_implemented",
    }


def handle_get_next_race(params: dict[str, str]) -> dict[str, Any]:
    """Get information about the next upcoming race."""
    year = int(params.get("year", get_current_season()))
    meetings = openf1_client.get_current_season_meetings(year)

    if not meetings:
        return {"message": "No upcoming races found", "next_race": None}

    # For now, return the first race in the calendar
    # In production, you'd filter by current date
    next_meeting = meetings[0]

    return {
        "race_name": next_meeting["meeting_name"],
        "circuit": next_meeting["circuit_short_name"],
        "country": next_meeting["country_name"],
        "location": next_meeting["location"],
        "date_start": next_meeting["date_start"],
    }


def handle_get_race_sessions(params: dict[str, str]) -> dict[str, Any]:
    """Get all sessions for a specific race weekend."""
    meeting_key = params.get("meeting_key")

    if not meeting_key:
        raise ValueError("meeting_key parameter is required")

    sessions = openf1_client.get_sessions_for_meeting(int(meeting_key))

    session_list = [
        {
            "session_name": session["session_name"],
            "session_type": session["session_type"],
            "date_start": session["date_start"],
            "date_end": session["date_end"],
        }
        for session in sessions
    ]

    return {"meeting_key": meeting_key, "sessions": session_list, "total_sessions": len(session_list)}


def build_success_response(body: dict[str, Any]) -> dict[str, Any]:
    """Build successful response for Bedrock Agent."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": "f1_data_actions",
            "apiPath": "/",
            "httpMethod": "GET",
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": json.dumps(body)}},
        },
    }


def build_error_response(error_message: str) -> dict[str, Any]:
    """Build error response for Bedrock Agent."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": "f1_data_actions",
            "apiPath": "/",
            "httpMethod": "GET",
            "httpStatusCode": 500,
            "responseBody": {
                "application/json": {"body": json.dumps({"error": error_message})}
            },
        },
    }
