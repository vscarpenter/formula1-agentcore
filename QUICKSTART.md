# Quick Start Guide

Get up and running with the F1 Race Weekend Companion in 15 minutes.

## TL;DR

```bash
# 1. Install dependencies
pip install -e ".[dev,infra]"

# 2. Set up environment
cp .env.example .env
# Edit .env with your AWS credentials

# 3. Build Lambda layer
make lambda-layer

# 4. Deploy infrastructure
cd infrastructure && cdk bootstrap && cdk deploy

# 5. Create agent in AWS Console (see DEPLOYMENT.md)

# 6. Test it!
f1-agent calendar
f1-agent chat "Tell me about the next race"
```

## What You'll Build

An intelligent F1 assistant that can:
- Answer questions about races and schedules
- Generate pre-race briefings with AI
- Remember your favorite drivers and teams
- Provide personalized racing insights

## Prerequisites (5 minutes)

1. **AWS Account** with Bedrock access
   - Sign up at: https://aws.amazon.com
   - Enable Bedrock in your account

2. **Python 3.11+**
   ```bash
   python3 --version  # Should be 3.11 or higher
   ```

3. **AWS CLI configured**
   ```bash
   aws configure
   # Enter your AWS credentials
   ```

4. **Node.js 18+** (for CDK)
   ```bash
   node --version  # Should be 18 or higher
   npm install -g aws-cdk
   ```

## Step-by-Step Setup

### 1. Environment Setup (2 minutes)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install all dependencies
pip install -e ".[dev,infra]"

# Set up environment variables
cp .env.example .env
```

Edit `.env`:
```bash
AWS_REGION=us-east-1
AWS_PROFILE=default  # or your profile name
```

### 2. Build Lambda Layer (2 minutes)

```bash
make lambda-layer
```

This packages Python dependencies for Lambda functions.

### 3. Deploy Infrastructure (5 minutes)

```bash
cd infrastructure

# First time only - bootstrap CDK
cdk bootstrap

# Deploy the stack
cdk deploy

# Type 'y' when prompted
```

This creates:
- 2 DynamoDB tables (preferences, interactions)
- 2 Lambda functions (data, briefings)
- IAM roles and permissions

**Note the outputs** - you'll need the Lambda ARNs in the next step.

### 4. Create Bedrock Agent (5 minutes)

The agent must be created through AWS Console (for now):

1. **Export schemas**
   ```bash
   cd ..
   f1-agent export-schemas
   ```

2. **Create agent in AWS Console**
   - Go to: AWS Console → Bedrock → Agents
   - Click "Create Agent"
   - Name: `F1RaceWeekendCompanion`
   - Model: Claude 3 Sonnet
   - Copy agent instruction from `src/agent/agent_config.py`

3. **Add action groups**
   - Action 1: `f1_data_actions` → Link to F1DataFunction Lambda
   - Action 2: `race_briefing_actions` → Link to RaceBriefingFunction Lambda
   - Upload the exported JSON schemas for each

4. **Create alias**
   - Name: `production`

5. **Save IDs to .env**
   ```bash
   AGENT_ID=ABC123...
   AGENT_ALIAS_ID=XYZ789...
   ```

Full details in [DEPLOYMENT.md](DEPLOYMENT.md).

### 5. Test It! (1 minute)

```bash
# View F1 calendar
f1-agent calendar

# Get next race info
f1-agent next-race

# Set your preferences
f1-agent set-preferences \
  --driver "Max Verstappen" \
  --team "Red Bull Racing"

# Chat with the agent
f1-agent chat "What's the next race?"
f1-agent chat "Generate a pre-race briefing"
```

## What's Happening Under the Hood?

```
You → CLI → Bedrock Agent → Action Groups → Lambda → OpenF1 API
                  ↓
            Claude AI Model
                  ↓
         DynamoDB (preferences)
```

1. **You ask a question** via CLI
2. **Bedrock Agent** understands your intent using Claude AI
3. **Action Groups** (Lambda functions) fetch data or generate content
4. **OpenF1 API** provides real-time F1 data
5. **Agent responds** with personalized insights

## Architecture Highlights

- **AgentCore**: Orchestrates conversation and routes requests
- **Action Groups**: Extend agent with custom capabilities
- **Foundation Models**: Claude 3 Sonnet for AI responses
- **OpenAPI Schemas**: Define agent capabilities declaratively
- **DynamoDB**: Store user preferences for personalization

## Common Commands

```bash
# Development
make test          # Run tests
make lint          # Check code quality
make format        # Auto-format code

# AWS
make deploy        # Deploy infrastructure
make diff          # Preview changes
make destroy       # Delete everything

# Usage
f1-agent --help    # Show all commands
f1-agent calendar --year 2024
f1-agent preferences
```

## What to Try Next

1. **Ask complex questions**
   ```bash
   f1-agent chat "Compare Red Bull and Ferrari's performance this season"
   ```

2. **Generate briefings**
   ```bash
   f1-agent chat "Give me a detailed Monaco GP briefing"
   ```

3. **Personalize**
   ```bash
   f1-agent set-preferences --driver "Lewis Hamilton" --team "Mercedes"
   f1-agent chat "How is my favorite driver doing?"
   ```

## Troubleshooting

**"Agent not found"**
- Make sure you created the agent in AWS Console
- Check AGENT_ID and AGENT_ALIAS_ID in .env

**"OpenF1 API timeout"**
- Check internet connectivity
- API might be rate-limited (implement caching)

**"Bedrock access denied"**
- Enable Claude models in Bedrock console
- Verify IAM permissions

**"Lambda permission errors"**
- Check CDK deployed successfully
- Verify Lambda execution roles

## Learning Resources

- [AWS Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [OpenF1 API Docs](https://openf1.org/)
- [CDK Python Guide](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- [Full Deployment Guide](DEPLOYMENT.md)

## Project Structure

```
formula1-agentcore/
├── src/
│   ├── actions/       # Lambda handlers (action groups)
│   ├── agent/         # Agent config & schemas
│   ├── clients/       # OpenF1 API client
│   ├── models/        # Data models
│   ├── storage/       # DynamoDB layer
│   └── utils/         # Utilities
├── infrastructure/    # CDK infrastructure
├── cli/              # Command-line interface
└── tests/            # Test suite
```

## Get Help

- Read [README.md](README.md) for full documentation
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment steps
- Review code comments for AgentCore concepts
- Open an issue for bugs or questions

## Next Steps

After you've got it working:

1. Customize the agent instruction
2. Add more action groups (weather, news, etc.)
3. Implement caching for better performance
4. Build a web UI
5. Add push notifications

Enjoy your F1 Agent! 🏎️
