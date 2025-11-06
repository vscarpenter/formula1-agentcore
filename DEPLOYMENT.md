# Deployment Guide

Step-by-step guide to deploy the F1 Race Weekend Companion to AWS.

## Prerequisites Checklist

- [ ] AWS Account with administrator access
- [ ] AWS CLI installed and configured
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed (for CDK)
- [ ] Bedrock model access enabled in your AWS account

## Step 1: Enable Bedrock Models

1. Log into AWS Console
2. Navigate to Amazon Bedrock
3. Go to "Model access" in the left sidebar
4. Click "Modify model access"
5. Enable:
   - Anthropic Claude 3 Sonnet
   - Anthropic Claude 3.5 Sonnet (optional)
6. Submit and wait for approval (usually instant)

## Step 2: Set Up Local Environment

```bash
# Clone the repository (if not already done)
cd formula1-agentcore

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,infra]"

# Copy environment template
cp .env.example .env
```

Edit `.env` and set:
```
AWS_REGION=us-east-1  # or your preferred region
AWS_PROFILE=default   # or your AWS profile name
```

## Step 3: Create Lambda Layer

Lambda functions need their dependencies packaged as a layer:

```bash
# Create layer directory
mkdir -p lambda_layer/python/lib/python3.11/site-packages

# Install dependencies to layer
pip install \
  boto3 \
  botocore \
  requests \
  pydantic \
  -t lambda_layer/python/lib/python3.11/site-packages/

# Verify layer size (should be < 50MB)
du -sh lambda_layer
```

## Step 4: Deploy Infrastructure with CDK

```bash
# Navigate to infrastructure directory
cd infrastructure

# Bootstrap CDK (first time only, per account/region)
cdk bootstrap

# Review what will be deployed
cdk diff

# Deploy the stack
cdk deploy

# Note the outputs - you'll need these values
```

Expected outputs:
- `PreferencesTableName`: DynamoDB table name
- `F1DataFunctionArn`: Lambda ARN for F1 data actions
- `RaceBriefingFunctionArn`: Lambda ARN for briefings
- `BedrockAgentRoleArn`: IAM role for the agent

## Step 5: Create Bedrock Agent

Currently, agents must be created via AWS Console:

### 5.1 Export OpenAPI Schemas

```bash
cd ..
python -m cli.main export-schemas
```

This creates:
- `f1_data_actions_openapi.json`
- `race_briefing_actions_openapi.json`

### 5.2 Create Agent in Console

1. Go to AWS Console → Amazon Bedrock → Agents
2. Click "Create Agent"
3. Configure agent:
   - **Agent name**: `F1RaceWeekendCompanion`
   - **Description**: "Intelligent F1 assistant for race insights"
   - **User input**: Enable
   - **IAM role**: Select "Use existing role" → Choose `BedrockAgentRole` from CDK

4. Configure agent instruction:
   ```
   You are the F1 Race Weekend Companion, an AI assistant specialized in Formula 1 racing.

   Your purpose is to help F1 fans stay informed with race schedules, track insights,
   pre-race briefings with strategic analysis, and personalized content based on user preferences.

   Be enthusiastic but knowledgeable. Provide context for casual fans while satisfying
   hardcore enthusiasts. Always offer to generate detailed briefings when discussing races.
   ```

5. Select model: **Anthropic Claude 3 Sonnet**

6. Click "Next"

### 5.3 Add Action Groups

**Action Group 1: F1 Data**
1. Click "Add Action Group"
2. Name: `f1_data_actions`
3. Description: "Fetch F1 calendar, standings, and race data"
4. Action group type: "Define with API schemas"
5. Action group invocation:
   - Select Lambda function: `F1AgentStack-F1DataFunction...`
6. Action group schema:
   - Select "Define via in-line schema editor"
   - Copy contents of `f1_data_actions_openapi.json`
7. Click "Create"

**Action Group 2: Race Briefings**
1. Click "Add Action Group"
2. Name: `race_briefing_actions`
3. Description: "Generate AI-powered race briefings"
4. Action group type: "Define with API schemas"
5. Action group invocation:
   - Select Lambda function: `F1AgentStack-RaceBriefingFunction...`
6. Action group schema:
   - Copy contents of `race_briefing_actions_openapi.json`
7. Click "Create"

8. Click "Next"

### 5.4 Create Agent Alias

1. Click "Create"
2. Name: `production`
3. Description: "Production alias for F1 Agent"
4. Click "Create alias"

### 5.5 Note Agent IDs

After creation, note:
- **Agent ID**: Found at top of agent detail page (e.g., `ABCDE12345`)
- **Alias ID**: Found in aliases tab (e.g., `TSTALIASID`)

Add these to your `.env` file:
```
AGENT_ID=your-agent-id-here
AGENT_ALIAS_ID=your-alias-id-here
```

## Step 6: Test the Deployment

### Test via CLI

```bash
# Test calendar fetch
f1-agent calendar

# Test next race
f1-agent next-race

# Test preferences
f1-agent set-preferences \
  --driver "Max Verstappen" \
  --team "Red Bull Racing"

f1-agent preferences

# Test agent chat
f1-agent chat "What's the next race?"
f1-agent chat "Tell me about Monaco Grand Prix"
```

### Test Lambda Functions Directly

```bash
# Test F1 data Lambda
aws lambda invoke \
  --function-name F1AgentStack-F1DataFunction... \
  --payload '{"actionGroup": "f1_data_actions", "apiPath": "/calendar", "parameters": []}' \
  response.json

cat response.json
```

## Step 7: Verify DynamoDB Tables

```bash
# List tables
aws dynamodb list-tables

# Check preferences table
aws dynamodb scan \
  --table-name F1AgentStack-PreferencesTable...
```

## Troubleshooting

### Lambda Permission Errors

If Lambda can't access DynamoDB:
```bash
# Check Lambda execution role
aws lambda get-function --function-name F1AgentStack-F1DataFunction... | jq .Configuration.Role

# Verify DynamoDB permissions in IAM
```

### Bedrock Access Denied

Ensure:
1. Models are enabled in Bedrock console
2. IAM role has `bedrock:InvokeModel` permission
3. You're in a supported region (us-east-1, us-west-2, etc.)

### Agent Not Responding

1. Check agent is prepared and has an alias
2. Verify action groups are linked to correct Lambdas
3. Check Lambda logs in CloudWatch
4. Test Lambda functions independently

### OpenF1 API Issues

If API calls fail:
- Check internet connectivity from Lambda (needs VPC NAT if in VPC)
- Verify no rate limiting (add caching if needed)
- OpenF1 API status: https://openf1.org/

## Cost Estimate

For moderate usage (10-20 queries/day):

- **Bedrock**: ~$0.50-2/day (Claude 3 Sonnet: $3/M input tokens, $15/M output tokens)
- **Lambda**: ~$0.01/day (generous free tier)
- **DynamoDB**: ~$0.05/day (on-demand, light usage)
- **Total**: ~$0.60-2.10/day or $18-63/month

To minimize costs:
- Use caching for F1 data (changes infrequently)
- Set DynamoDB to on-demand mode
- Use CloudWatch log retention = 1 week
- Monitor Bedrock token usage

## Cleanup

To remove all resources:

```bash
cd infrastructure
cdk destroy

# Manually delete:
# 1. Bedrock Agent (in console)
# 2. CloudWatch Log Groups (optional)
```

## Production Considerations

Before production use:

1. **Security**
   - [ ] Enable VPC for Lambda functions
   - [ ] Use Secrets Manager for API keys
   - [ ] Enable DynamoDB point-in-time recovery
   - [ ] Set up AWS WAF for API protection

2. **Monitoring**
   - [ ] Set up CloudWatch alarms for errors
   - [ ] Create dashboard for metrics
   - [ ] Enable X-Ray tracing

3. **Scaling**
   - [ ] Implement API response caching
   - [ ] Add DynamoDB DAX for hot data
   - [ ] Set Lambda reserved concurrency

4. **Cost Optimization**
   - [ ] Use Bedrock Provisioned Throughput for high volume
   - [ ] Implement smart caching strategy
   - [ ] Set up cost alerts

## Next Steps

After successful deployment:

1. Customize agent instruction for your preferences
2. Add more action groups (weather, news, etc.)
3. Implement knowledge bases for F1 history
4. Build a web UI or mobile app
5. Add push notifications for race events

## Support

For issues or questions:
- Check CloudWatch logs for Lambda errors
- Review Bedrock agent trace in console
- Open issue on GitHub
- Consult AWS Bedrock documentation
