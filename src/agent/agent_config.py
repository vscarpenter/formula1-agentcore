"""
Bedrock Agent configuration and OpenAPI schemas.

This module defines the agent instruction and action group schemas
that tell the agent what capabilities it has and how to use them.
"""

import json
from typing import Any


def get_agent_config() -> dict[str, Any]:
    """
    Get the Bedrock Agent configuration.

    This configuration tells the agent:
    - Who it is and what its purpose is
    - How to interact with users
    - What capabilities it has through action groups
    """
    return {
        "agentName": "F1RaceWeekendCompanion",
        "description": "Intelligent F1 assistant for race weekend insights and analysis",
        "instruction": get_agent_instruction(),
        "foundationModel": "anthropic.claude-3-sonnet-20240229-v1:0",
        "idleSessionTTLInSeconds": 600,
    }


def get_agent_instruction() -> str:
    """
    Get the agent instruction that defines its behavior.

    This is the system prompt that tells the agent how to act
    and what its capabilities are.
    """
    return """You are the F1 Race Weekend Companion, an AI assistant specialized in Formula 1 racing.

Your purpose is to help F1 fans stay informed and engaged with:
- Race schedules and upcoming events
- Track characteristics and historical context
- Pre-race briefings with strategic insights
- Personalized content based on user preferences

Capabilities:
1. F1 Data Queries: Access current season calendar, race schedules, and session information
2. Race Briefings: Generate comprehensive pre-race analysis and predictions
3. User Preferences: Remember favorite drivers and teams for personalized insights

Communication Style:
- Be enthusiastic but knowledgeable about F1
- Provide context for casual fans while satisfying hardcore enthusiasts
- Use racing terminology appropriately
- Keep responses concise but informative
- Always cite data sources when providing statistics

Special Focus:
- Pay extra attention to Circuit of the Americas races (user's home circuit)
- Highlight strategic elements that make races interesting
- Connect current events to historical F1 moments

When users ask about races, always offer to generate a detailed briefing.
When discussing drivers or teams, check if the user has preferences stored."""


def get_openapi_schemas() -> dict[str, dict[str, Any]]:
    """
    Get OpenAPI schemas for action groups.

    These schemas define the APIs that the agent can call
    through Lambda function action groups.
    """
    return {
        "f1_data_actions": get_f1_data_schema(),
        "race_briefing_actions": get_race_briefing_schema(),
    }


def get_f1_data_schema() -> dict[str, Any]:
    """
    OpenAPI schema for F1 data action group.

    Defines endpoints for fetching F1 calendar, standings,
    and race information.
    """
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "F1 Data API",
            "description": "API for retrieving F1 race data, schedules, and standings",
            "version": "1.0.0",
        },
        "paths": {
            "/calendar": {
                "get": {
                    "summary": "Get F1 race calendar",
                    "description": "Retrieve the race calendar for a specific season",
                    "operationId": "getCalendar",
                    "parameters": [
                        {
                            "name": "year",
                            "in": "query",
                            "description": "Season year (defaults to current year)",
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Race calendar retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "year": {"type": "integer"},
                                            "races": {"type": "array"},
                                            "total_races": {"type": "integer"},
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/standings/drivers": {
                "get": {
                    "summary": "Get driver championship standings",
                    "description": "Retrieve current driver standings",
                    "operationId": "getDriverStandings",
                    "responses": {
                        "200": {
                            "description": "Driver standings retrieved",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        }
                    },
                }
            },
            "/standings/teams": {
                "get": {
                    "summary": "Get constructor championship standings",
                    "description": "Retrieve current team standings",
                    "operationId": "getTeamStandings",
                    "responses": {
                        "200": {
                            "description": "Team standings retrieved",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        }
                    },
                }
            },
            "/race/next": {
                "get": {
                    "summary": "Get next upcoming race",
                    "description": "Retrieve information about the next race on the calendar",
                    "operationId": "getNextRace",
                    "responses": {
                        "200": {
                            "description": "Next race information retrieved",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        }
                    },
                }
            },
            "/race/sessions": {
                "get": {
                    "summary": "Get race weekend sessions",
                    "description": "Retrieve all sessions for a specific race weekend",
                    "operationId": "getRaceSessions",
                    "parameters": [
                        {
                            "name": "meeting_key",
                            "in": "query",
                            "description": "Unique meeting identifier",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Race sessions retrieved",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        }
                    },
                }
            },
        },
    }


def get_race_briefing_schema() -> dict[str, Any]:
    """
    OpenAPI schema for race briefing action group.

    Defines endpoints for generating AI-powered race briefings
    and analysis.
    """
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Race Briefing API",
            "description": "API for generating AI-powered race briefings and analysis",
            "version": "1.0.0",
        },
        "paths": {
            "/briefing/pre-race": {
                "post": {
                    "summary": "Generate pre-race briefing",
                    "description": "Create a comprehensive pre-race analysis and briefing",
                    "operationId": "generatePreRaceBriefing",
                    "parameters": [
                        {
                            "name": "meeting_key",
                            "in": "query",
                            "description": "Unique meeting identifier for the race",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "user_id",
                            "in": "query",
                            "description": "User ID for personalization",
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Pre-race briefing generated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "race_name": {"type": "string"},
                                            "circuit": {"type": "string"},
                                            "date": {"type": "string"},
                                            "briefing": {"type": "string"},
                                            "personalized": {"type": "boolean"},
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/briefing/post-race": {
                "post": {
                    "summary": "Generate post-race summary",
                    "description": "Create a narrative summary of race results and highlights",
                    "operationId": "generatePostRaceSummary",
                    "parameters": [
                        {
                            "name": "meeting_key",
                            "in": "query",
                            "description": "Unique meeting identifier for the race",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "user_id",
                            "in": "query",
                            "description": "User ID for personalization",
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Post-race summary generated successfully",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        }
                    },
                }
            },
        },
    }


def export_schemas_to_file(output_dir: str = ".") -> None:
    """
    Export OpenAPI schemas to JSON files.

    Useful for manual agent creation through AWS Console.
    """
    schemas = get_openapi_schemas()

    for name, schema in schemas.items():
        filename = f"{output_dir}/{name}_openapi.json"
        with open(filename, "w") as f:
            json.dump(schema, f, indent=2)
        print(f"Exported {name} schema to {filename}")
