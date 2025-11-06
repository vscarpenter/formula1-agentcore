"""
Lambda handler for race briefing action group.

This Lambda function uses Bedrock's foundation models to generate
personalized race briefings based on F1 data and user preferences.
"""

import json
import logging
import os
from typing import Any

import boto3

from src.clients import OpenF1Client
from src.storage import PreferencesStore
from src.utils import setup_logging

setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize clients (reused across Lambda invocations)
openf1_client = OpenF1Client()
bedrock_runtime = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
preferences_store = PreferencesStore(
    table_name=os.getenv("PREFERENCES_TABLE_NAME", "f1-agent-preferences")
)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handle Bedrock Agent action group requests for race briefings.

    Actions supported:
    - generate_pre_race_briefing: Create pre-race analysis
    - generate_post_race_summary: Create post-race narrative

    Args:
        event: Bedrock Agent event containing action and parameters
        context: Lambda context object

    Returns:
        Response dictionary formatted for Bedrock Agent
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        api_path = event.get("apiPath", "")
        parameters = event.get("parameters", [])
        params_dict = {param["name"]: param["value"] for param in parameters}

        logger.info(f"Processing briefing action: {api_path}")

        if api_path == "/briefing/pre-race":
            response_body = handle_generate_pre_race_briefing(params_dict)
        elif api_path == "/briefing/post-race":
            response_body = handle_generate_post_race_summary(params_dict)
        else:
            raise ValueError(f"Unknown API path: {api_path}")

        return build_success_response(response_body)

    except Exception as e:
        logger.error(f"Error processing briefing request: {str(e)}", exc_info=True)
        return build_error_response(str(e))


def handle_generate_pre_race_briefing(params: dict[str, str]) -> dict[str, Any]:
    """
    Generate a pre-race briefing using Bedrock foundation model.

    Args:
        params: Dictionary containing meeting_key and optional user_id

    Returns:
        Generated briefing content
    """
    meeting_key = params.get("meeting_key")
    user_id = params.get("user_id", "default")

    if not meeting_key:
        raise ValueError("meeting_key parameter is required")

    # Fetch race data
    meetings = openf1_client.get_current_season_meetings()
    target_meeting = next(
        (m for m in meetings if str(m["meeting_key"]) == meeting_key), None
    )

    if not target_meeting:
        raise ValueError(f"Meeting not found: {meeting_key}")

    # Get user preferences for personalization
    user_prefs = preferences_store.get_preferences(user_id)

    # Build prompt for Bedrock
    briefing_prompt = build_pre_race_prompt(target_meeting, user_prefs)

    # Generate briefing using Bedrock
    briefing_text = generate_with_bedrock(briefing_prompt)

    return {
        "race_name": target_meeting["meeting_name"],
        "circuit": target_meeting["circuit_short_name"],
        "date": target_meeting["date_start"],
        "briefing": briefing_text,
        "personalized": user_prefs is not None,
    }


def handle_generate_post_race_summary(params: dict[str, str]) -> dict[str, Any]:
    """Generate a post-race narrative summary (placeholder)."""
    return {
        "message": "Post-race summary generation",
        "note": "Requires race results and telemetry data",
        "status": "not_implemented",
    }


def build_pre_race_prompt(meeting: dict[str, Any], user_prefs: Any) -> str:
    """
    Build prompt for pre-race briefing generation.

    Args:
        meeting: Race weekend meeting data
        user_prefs: User preferences for personalization

    Returns:
        Formatted prompt string
    """
    base_prompt = f"""Generate a comprehensive pre-race briefing for the {meeting['meeting_name']}.

Race Details:
- Circuit: {meeting['circuit_short_name']}
- Location: {meeting['location']}, {meeting['country_name']}
- Date: {meeting['date_start']}

Please include:
1. Track characteristics and key features
2. Historical context and memorable moments at this circuit
3. Weather considerations for this location and time of year
4. Key storylines and what to watch for
5. Strategic considerations (tire strategy, overtaking opportunities)
"""

    # Add personalization if user preferences exist
    if user_prefs:
        if user_prefs.favorite_driver:
            base_prompt += f"\n\nFocus on {user_prefs.favorite_driver}'s prospects and performance at this track."
        if user_prefs.favorite_team:
            base_prompt += f"\nInclude analysis of {user_prefs.favorite_team}'s competitive position."

    base_prompt += "\n\nKeep the briefing engaging, informative, and under 500 words."

    return base_prompt


def generate_with_bedrock(prompt: str, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0") -> str:
    """
    Generate text using Bedrock foundation model.

    Args:
        prompt: Input prompt for generation
        model_id: Bedrock model identifier

    Returns:
        Generated text content
    """
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
        )

        response_body = json.loads(response["body"].read())
        generated_text = response_body["content"][0]["text"]

        logger.info(f"Successfully generated briefing ({len(generated_text)} chars)")
        return generated_text

    except Exception as e:
        logger.error(f"Bedrock generation failed: {str(e)}")
        raise


def build_success_response(body: dict[str, Any]) -> dict[str, Any]:
    """Build successful response for Bedrock Agent."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": "race_briefing_actions",
            "apiPath": "/",
            "httpMethod": "POST",
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": json.dumps(body)}},
        },
    }


def build_error_response(error_message: str) -> dict[str, Any]:
    """Build error response for Bedrock Agent."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": "race_briefing_actions",
            "apiPath": "/",
            "httpMethod": "POST",
            "httpStatusCode": 500,
            "responseBody": {
                "application/json": {"body": json.dumps({"error": error_message})}
            },
        },
    }
