# Deployment Verification Guide

## ✅ What's Been Deployed

### Infrastructure (All Created Successfully)
- ✅ **2 DynamoDB Tables**
  - PreferencesTable: `F1AgentStack-PreferencesTableC3683986-GV5T7IXX2IGH`
  - InteractionsTable: `F1AgentStack-InteractionsTable6E66EFF7-MEIV02CSDUSY`
  
- ✅ **2 Lambda Functions**
  - F1DataFunction: `F1AgentStack-F1DataFunctionD5B716CD-OW8umJk5l4Az`
  - RaceBriefingFunction: `F1AgentStack-RaceBriefingFunctionEB65CDD8-JFF6EAOPYLHi`

- ✅ **Lambda Layer (V3 with Linux binaries)**
  - arn:aws:lambda:us-east-1:710603110067:layer:DependenciesLayerV3B216E7C4:1

- ✅ **IAM Roles**
  - BedrockAgentRole
  - Lambda execution roles with proper permissions

## 🧪 Test the Infrastructure

### 1. Test DynamoDB Tables
```bash
# List tables
aws dynamodb list-tables | grep F1AgentStack

# Check table schema
aws dynamodb describe-table --table-name F1AgentStack-PreferencesTableC3683986-GV5T7IXX2IGH
```

### 2. Test with CLI (No Agent Required Yet)
The CLI can interact with DynamoDB and OpenF1 API directly:

```bash
# Activate virtual environment
source .venv/bin/activate

# Test calendar fetch (uses OpenF1 API directly)
f1-agent calendar

# Test next race
f1-agent next-race

# Set preferences (writes to DynamoDB)
f1-agent set-preferences \
  --driver "Max Verstappen" \
  --team "Red Bull Racing"

# View preferences (reads from DynamoDB)
f1-agent preferences
```

### 3. Verify DynamoDB Write
```bash
# Check if preferences were saved
aws dynamodb scan --table-name F1AgentStack-PreferencesTableC3683986-GV5T7IXX2IGH
```

## 📋 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| DynamoDB Tables | ✅ Working | Can store/retrieve preferences |
| Lambda Functions | ⚠️  Deployed | Need dependency testing |
| Lambda Layer | ⚠️  Deployed | Linux binaries installed |
| IAM Roles | ✅ Working | Proper permissions configured |
| CLI Tool | ✅ Working | Can fetch F1 data & manage prefs |
| Bedrock Agent | ❌ Not Created | Next step |

## 🎯 Next Steps

### 1. Test Lambda Functions Independently (Optional)

The Lambda functions are deployed but may need the layer dependencies verified. To test:

```bash
# Create test event
cat > /tmp/test-calendar.json << 'PAYLOAD'
{
  "actionGroup": "f1_data_actions",
  "apiPath": "/calendar",
  "parameters": []
}
PAYLOAD

# Invoke Lambda
aws lambda invoke \
  --function-name F1AgentStack-F1DataFunctionD5B716CD-OW8umJk5l4Az \
  --payload file:///tmp/test-calendar.json \
  --cli-binary-format raw-in-base64-out \
  /tmp/response.json

# Check response
cat /tmp/response.json
```

### 2. Create Bedrock Agent (Main Next Step)

Follow `DEPLOYMENT.md` Step 5 to create the Bedrock Agent:

1. **Export OpenAPI Schemas**
   ```bash
   f1-agent export-schemas
   ```

2. **Go to AWS Console → Bedrock → Agents**

3. **Create Agent**
   - Name: `F1RaceWeekendCompanion`
   - Model: Claude 3 Sonnet
   - Role: Use existing `BedrockAgentRole`

4. **Add Action Groups**
   - **f1_data_actions**: Link to `F1DataFunction`
   - **race_briefing_actions**: Link to `RaceBriefingFunction`
   - Upload the exported JSON schemas

5. **Create Alias** named `production`

6. **Save Agent ID and Alias ID to `.env`**

### 3. Test End-to-End

Once the agent is created:

```bash
# Update .env with agent IDs
echo "AGENT_ID=your-agent-id" >> .env
echo "AGENT_ALIAS_ID=your-alias-id" >> .env

# Test agent interaction
f1-agent chat "What's the next race?"
f1-agent chat "Tell me about Monaco Grand Prix"
```

## 🔍 Troubleshooting

### Lambda Import Errors
If Lambda functions show import errors:
1. The functions are packaged correctly
2. The Lambda layer structure is: `python/lib/python3.11/site-packages/`
3. Linux binaries were installed with: `python3.11 -m pip install --platform manylinux2014_x86_64 --only-binary=:all:`

To rebuild the layer:
```bash
make lambda-layer
cd infrastructure && cdk deploy --require-approval never
```

### CLI Commands Not Working
Ensure dependencies are installed:
```bash
source .venv/bin/activate
uv pip install -e ".[dev,infra]"
```

### DynamoDB Access Issues
Check AWS credentials:
```bash
aws sts get-caller-identity
aws dynamodb list-tables
```

## 🎉 What's Working Right Now

You can immediately use:

1. **F1 Calendar Viewing**
   ```bash
   f1-agent calendar
   f1-agent calendar --year 2024
   ```

2. **Next Race Information**
   ```bash
   f1-agent next-race
   ```

3. **Preference Management**
   ```bash
   f1-agent set-preferences --driver "Lewis Hamilton" --team "Mercedes"
   f1-agent preferences
   ```

These commands work without the Bedrock Agent because they interact directly with OpenF1 API and DynamoDB.

## 📚 Documentation

- **Full Setup**: See `README.md`
- **Quick Start**: See `QUICKSTART.md`
- **Deployment Details**: See `DEPLOYMENT.md`
- **uv Usage**: See `UV_GUIDE.md`

