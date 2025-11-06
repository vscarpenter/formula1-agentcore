# F1 Race Weekend Companion

An intelligent Formula 1 assistant built with AWS Bedrock AgentCore that provides personalized race insights, briefings, and data.

## Features

- **Race Calendar & Schedules**: Get current season calendar and upcoming race information
- **Pre-Race Briefings**: AI-generated analysis with track characteristics, weather, and strategic insights
- **Personalized Content**: Track your favorite drivers and teams for customized recommendations
- **Real-time F1 Data**: Integration with OpenF1 API for live race weekend information
- **Conversational Interface**: Natural language interaction through Bedrock Agent

## Architecture

This project demonstrates AWS Bedrock AgentCore capabilities:

```
┌─────────────┐
│   CLI/User  │
└──────┬──────┘
       │
       v
┌──────────────────────────────────────────┐
│     AWS Bedrock Agent                    │
│  (Orchestration & Foundation Model)      │
└──────┬───────────────────────────────────┘
       │
       ├──> Action Group: F1 Data
       │    └──> Lambda: f1_data_actions
       │         └──> OpenF1 API
       │
       ├──> Action Group: Race Briefings
       │    └──> Lambda: race_briefing_actions
       │         └──> Bedrock Models (Claude)
       │
       └──> DynamoDB: User Preferences
```

### Components

1. **Bedrock Agent**: Orchestrates conversations and routes requests to action groups
2. **Action Groups**: Lambda functions that provide specific capabilities
   - `f1_data_actions`: Fetch F1 calendar, standings, and race data
   - `race_briefing_actions`: Generate AI-powered race briefings
3. **Data Storage**: DynamoDB tables for user preferences and interaction history
4. **External APIs**: OpenF1 for real-time F1 data

## Prerequisites

- Python 3.11+
- AWS Account with Bedrock access
- AWS CLI configured with appropriate credentials
- Node.js 18+ (for AWS CDK)

## Setup

### 1. Clone and Install Dependencies

```bash
# Install Python dependencies
pip install -e ".[dev,infra]"

# Install CDK (if not already installed)
npm install -g aws-cdk
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:
```
AWS_REGION=us-east-1
AWS_PROFILE=default
```

### 3. Deploy Infrastructure

```bash
# Bootstrap CDK (first time only)
cd infrastructure
cdk bootstrap

# Deploy the stack
cdk deploy
```

This creates:
- DynamoDB tables (preferences and interactions)
- Lambda functions for action groups
- IAM roles for Bedrock Agent

### 4. Create Bedrock Agent

The Bedrock Agent must be created through AWS Console (CLI support coming):

1. Go to AWS Console → Bedrock → Agents
2. Create new agent with name: `F1RaceWeekendCompanion`
3. Configure foundation model: `Claude 3 Sonnet`
4. Add agent instruction (see `src/agent/agent_config.py`)
5. Create two action groups:

   **Action Group 1: f1_data_actions**
   - Name: `f1_data_actions`
   - Lambda: Select the `F1DataFunction` from CDK stack
   - API Schema: Use `f1_data_actions_openapi.json` (export with CLI)

   **Action Group 2: race_briefing_actions**
   - Name: `race_briefing_actions`
   - Lambda: Select the `RaceBriefingFunction` from CDK stack
   - API Schema: Use `race_briefing_actions_openapi.json`

6. Create alias: `production`
7. Copy Agent ID and Alias ID to `.env`

### 5. Export OpenAPI Schemas

```bash
f1-agent export-schemas
```

Use the generated JSON files when creating action groups in AWS Console.

## Usage

### CLI Commands

**View F1 Calendar**
```bash
f1-agent calendar
f1-agent calendar --year 2024
```

**Get Next Race**
```bash
f1-agent next-race
```

**Manage Preferences**
```bash
# View preferences
f1-agent preferences --user-id your-id

# Set preferences
f1-agent set-preferences \
  --user-id your-id \
  --driver "Max Verstappen" \
  --team "Red Bull Racing" \
  --timezone "America/Chicago"
```

**Chat with Agent**
```bash
f1-agent chat "Tell me about the next race"
f1-agent chat "Generate a pre-race briefing for Monaco"
f1-agent chat "What's the current championship standings?"
```

### Python API

```python
from src.clients import OpenF1Client
from src.storage import PreferencesStore
from src.models import UserPreferences

# Fetch F1 data
client = OpenF1Client()
meetings = client.get_current_season_meetings()
sessions = client.get_sessions_for_meeting(meeting_key=1234)

# Manage preferences
store = PreferencesStore(table_name="f1-agent-preferences")
prefs = UserPreferences(
    user_id="user123",
    favorite_driver="Max Verstappen",
    favorite_team="Red Bull Racing",
)
store.save_preferences(prefs)
```

## Development

### Project Structure

```
formula1-agentcore/
├── src/
│   ├── actions/           # Lambda handlers for action groups
│   ├── agent/             # Agent configuration and schemas
│   ├── clients/           # API clients (OpenF1, etc.)
│   ├── models/            # Pydantic data models
│   ├── storage/           # DynamoDB storage layer
│   └── utils/             # Shared utilities
├── infrastructure/        # AWS CDK infrastructure code
├── cli/                   # Command-line interface
├── tests/                 # Test suite
└── pyproject.toml        # Project configuration
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_openf1_client.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy src cli
```

## AgentCore Concepts Demonstrated

### 1. Agent Orchestration
The Bedrock Agent acts as the orchestrator, understanding user intent and routing requests to appropriate action groups.

### 2. Action Groups
Lambda functions that extend agent capabilities:
- `f1_data_actions.py:45`: Demonstrates routing different API paths
- `race_briefing_actions.py:60`: Shows Bedrock model invocation within action

### 3. Foundation Model Integration
- Agent uses Claude 3 Sonnet for conversation understanding
- Action group uses Bedrock Runtime for content generation
- See `race_briefing_actions.py:177` for model invocation

### 4. OpenAPI Schema Definition
Action groups are defined with OpenAPI specs:
- `agent_config.py:85`: F1 data API schema
- `agent_config.py:185`: Race briefing API schema

### 5. Session Management
Agent maintains conversation context across multiple interactions using session IDs.

### 6. Personalization
User preferences stored in DynamoDB enable personalized responses:
- `preferences_store.py`: Storage layer
- `race_briefing_actions.py:95`: Preference-based content generation

## Cost Optimization Tips

1. **Cache API Responses**: OpenF1 data changes infrequently
2. **Use Bedrock On-Demand Pricing**: Pay only for what you use
3. **Set DynamoDB to On-Demand**: Better for variable traffic
4. **Lambda Memory Sizing**: 512MB for data, 1024MB for briefings
5. **CloudWatch Log Retention**: Set to 1 week for development

## Troubleshooting

**Agent Not Found Error**
- Ensure `AGENT_ID` and `AGENT_ALIAS_ID` are set in `.env`
- Verify agent was created and aliased in AWS Console

**OpenF1 API Timeout**
- Check internet connectivity
- OpenF1 API may be rate-limited (implement caching)

**Lambda Permission Errors**
- Verify IAM roles have correct permissions
- Check Lambda execution role can access DynamoDB

**Bedrock Access Denied**
- Enable Bedrock models in AWS Console
- Verify IAM role has `bedrock:InvokeModel` permission

## Future Enhancements

- [ ] Weather API integration for race conditions
- [ ] Historical race data analysis with knowledge bases
- [ ] Post-race narrative summaries
- [ ] Push notifications for race events
- [ ] Multi-language support
- [ ] Ergast API integration for historical standings
- [ ] Real-time race telemetry analysis
- [ ] Circuit of the Americas special features

## References

- [AWS Bedrock Agent Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [OpenF1 API](https://openf1.org/)
- [AWS CDK Python](https://docs.aws.amazon.com/cdk/v2/guide/home.html)

## License

MIT License - See LICENSE file for details

## Acknowledgments

- OpenF1 for providing free F1 data API
- AWS Bedrock team for AgentCore capabilities
- F1 community for inspiration
