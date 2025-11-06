"""
CLI interface for F1 Race Weekend Companion.

Provides commands to interact with the Bedrock Agent and manage preferences.
"""

import json
import os
from typing import Optional

import boto3
import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from src.clients import OpenF1Client
from src.storage import PreferencesStore
from src.models import UserPreferences
from src.utils import setup_logging

# Load environment variables
load_dotenv()

console = Console()
setup_logging(os.getenv("LOG_LEVEL", "INFO"))


@click.group()
def cli() -> None:
    """F1 Race Weekend Companion - Your intelligent F1 assistant."""
    pass


@cli.command()
@click.option("--year", type=int, help="Season year (defaults to current)")
def calendar(year: Optional[int]) -> None:
    """Display the F1 race calendar."""
    try:
        client = OpenF1Client()
        meetings = client.get_current_season_meetings(year)

        table = Table(title=f"F1 {year or 'Current'} Season Calendar")
        table.add_column("Round", style="cyan")
        table.add_column("Race", style="green")
        table.add_column("Circuit", style="yellow")
        table.add_column("Country", style="magenta")
        table.add_column("Date", style="blue")

        for idx, meeting in enumerate(meetings, 1):
            table.add_row(
                str(idx),
                meeting["meeting_name"],
                meeting["circuit_short_name"],
                meeting["country_name"],
                meeting["date_start"][:10],
            )

        console.print(table)
        console.print(f"\n[green]Total races: {len(meetings)}[/green]")

    except Exception as e:
        console.print(f"[red]Error fetching calendar: {str(e)}[/red]")


@cli.command()
def next_race() -> None:
    """Show information about the next upcoming race."""
    try:
        client = OpenF1Client()
        meetings = client.get_current_season_meetings()

        if not meetings:
            console.print("[yellow]No upcoming races found[/yellow]")
            return

        # For demo, show first race
        next_meeting = meetings[0]

        console.print(f"\n[bold green]Next Race:[/bold green]")
        console.print(f"  Race: {next_meeting['meeting_name']}")
        console.print(f"  Circuit: {next_meeting['circuit_short_name']}")
        console.print(f"  Location: {next_meeting['location']}, {next_meeting['country_name']}")
        console.print(f"  Date: {next_meeting['date_start']}")

    except Exception as e:
        console.print(f"[red]Error fetching next race: {str(e)}[/red]")


@cli.command()
@click.option("--user-id", default="default", help="User ID")
def preferences(user_id: str) -> None:
    """Show current user preferences."""
    try:
        table_name = os.getenv("PREFERENCES_TABLE_NAME", "f1-agent-preferences")
        store = PreferencesStore(table_name)
        prefs = store.get_preferences(user_id)

        if not prefs:
            console.print(f"[yellow]No preferences found for user: {user_id}[/yellow]")
            console.print("[blue]Use 'set-preferences' to configure your preferences[/blue]")
            return

        console.print(f"\n[bold green]Preferences for {user_id}:[/bold green]")
        console.print(f"  Favorite Driver: {prefs.favorite_driver or 'Not set'}")
        console.print(f"  Favorite Team: {prefs.favorite_team or 'Not set'}")
        console.print(f"  Preferred Circuits: {', '.join(prefs.preferred_circuits) or 'None'}")
        console.print(f"  Timezone: {prefs.timezone}")

    except Exception as e:
        console.print(f"[red]Error fetching preferences: {str(e)}[/red]")


@cli.command()
@click.option("--user-id", default="default", help="User ID")
@click.option("--driver", help="Favorite driver name or number")
@click.option("--team", help="Favorite team name")
@click.option("--timezone", default="UTC", help="Preferred timezone")
def set_preferences(
    user_id: str,
    driver: Optional[str],
    team: Optional[str],
    timezone: str,
) -> None:
    """Set user preferences for personalized content."""
    try:
        table_name = os.getenv("PREFERENCES_TABLE_NAME", "f1-agent-preferences")
        store = PreferencesStore(table_name)

        # Get existing preferences or create new
        prefs = store.get_preferences(user_id)
        if not prefs:
            prefs = UserPreferences(user_id=user_id, timezone=timezone)

        # Update fields
        if driver:
            prefs.favorite_driver = driver
        if team:
            prefs.favorite_team = team
        if timezone:
            prefs.timezone = timezone

        store.save_preferences(prefs)
        console.print(f"[green]Preferences updated for {user_id}![/green]")

    except Exception as e:
        console.print(f"[red]Error saving preferences: {str(e)}[/red]")


@cli.command()
@click.argument("message")
@click.option("--agent-id", help="Bedrock Agent ID")
@click.option("--agent-alias-id", help="Bedrock Agent Alias ID")
@click.option("--session-id", help="Session ID for conversation continuity")
def chat(
    message: str,
    agent_id: Optional[str],
    agent_alias_id: Optional[str],
    session_id: Optional[str],
) -> None:
    """Send a message to the F1 Agent."""
    try:
        # Get agent configuration from environment or parameters
        agent_id = agent_id or os.getenv("AGENT_ID")
        agent_alias_id = agent_alias_id or os.getenv("AGENT_ALIAS_ID")
        session_id = session_id or "default-session"

        if not agent_id or not agent_alias_id:
            console.print("[red]Error: AGENT_ID and AGENT_ALIAS_ID must be set[/red]")
            console.print("[yellow]Set them in .env file or use --agent-id and --agent-alias-id[/yellow]")
            return

        # Initialize Bedrock Agent Runtime client
        region = os.getenv("AWS_REGION", "us-east-1")
        client = boto3.client("bedrock-agent-runtime", region_name=region)

        console.print(f"[blue]Sending message to agent...[/blue]")

        # Invoke the agent
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=message,
        )

        # Process streaming response
        console.print("\n[bold green]Agent Response:[/bold green]")
        for event in response["completion"]:
            if "chunk" in event:
                chunk = event["chunk"]
                if "bytes" in chunk:
                    text = chunk["bytes"].decode("utf-8")
                    console.print(text, end="")

        console.print("\n")

    except Exception as e:
        console.print(f"[red]Error communicating with agent: {str(e)}[/red]")


@cli.command()
def export_schemas() -> None:
    """Export OpenAPI schemas for manual agent creation."""
    try:
        from src.agent import get_openapi_schemas

        schemas = get_openapi_schemas()

        for name, schema in schemas.items():
            filename = f"{name}_openapi.json"
            with open(filename, "w") as f:
                json.dump(schema, f, indent=2)
            console.print(f"[green]Exported {filename}[/green]")

        console.print("\n[blue]Use these schemas when creating the agent in AWS Console[/blue]")

    except Exception as e:
        console.print(f"[red]Error exporting schemas: {str(e)}[/red]")


if __name__ == "__main__":
    cli()
