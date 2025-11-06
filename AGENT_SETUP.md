# Automated Bedrock Agent Setup

This guide explains how to use the automated script to create your Bedrock Agent on AWS without using the AWS Console.

## Overview

The `create_bedrock_agent.sh` script automates the entire process of creating and configuring your F1 Race Weekend Companion Bedrock Agent, including:

- ✅ Verifying CDK infrastructure deployment
- ✅ Exporting OpenAPI schemas for action groups
- ✅ Creating the Bedrock Agent
- ✅ Configuring two Lambda-based action groups
- ✅ Preparing the agent for use
- ✅ Creating a production alias
- ✅ Updating your `.env` file with credentials

## Prerequisites

### Required Software

1. **AWS CLI** - Must be installed and configured
   ```bash
   # Check if installed
   aws --version

   # Install on Mac
   brew install awscli

   # Configure credentials
   aws configure
   ```

2. **jq** - JSON processor (script will attempt to install if missing)
   ```bash
   # Install on Mac
   brew install jq
   ```

3. **AWS CDK** - For infrastructure deployment
   ```bash
   npm install -g aws-cdk
   ```

### AWS Permissions

Your AWS user/role needs permissions for:
- CloudFormation (read stacks and resources)
- Bedrock (create/manage agents)
- Lambda (get function details, add permissions)
- IAM (PassRole for Bedrock agent role)
- DynamoDB (if checking table names)

### Bedrock Model Access

**IMPORTANT:** You must enable Claude 3 Sonnet in AWS Bedrock before running the script.

1. Go to AWS Console → Bedrock → Model access
2. Click "Manage model access"
3. Enable "Claude 3 Sonnet"
4. Wait for access to be granted (usually instant)

## Quick Start

### Step 1: Ensure CDK Infrastructure is Deployed

The script can deploy it for you, but it's recommended to do this first:

```bash
# Build the Lambda layer with Linux-compatible dependencies
make lambda-layer

# Deploy the infrastructure
cd infrastructure
cdk bootstrap  # First time only
cdk deploy
cd ..
```

### Step 2: Run the Automated Setup Script

```bash
./create_bedrock_agent.sh
```

The script will:
1. Check all prerequisites
2. Verify CDK stack is deployed (or prompt to deploy)
3. Export OpenAPI schemas
4. Create the Bedrock Agent
5. Configure action groups
6. Prepare the agent
7. Create an alias
8. Update your `.env` file

### Step 3: Test Your Agent

```bash
# Test with a simple query
f1-agent chat "What's the next race?"

# View the calendar
f1-agent calendar

# Get next race details
f1-agent next-race
```

## What the Script Does (Detailed)

### 1. Prerequisites Check
- Verifies AWS CLI is installed and configured
- Checks for jq (installs if missing on Mac)
- Validates AWS credentials
- Detects AWS region

### 2. CDK Stack Verification
- Checks if `F1AgentStack` is deployed
- Retrieves Lambda function ARNs
- Gets Bedrock agent IAM role ARN
- Extracts DynamoDB table names

### 3. OpenAPI Schema Export
- Generates `f1_data_actions_openapi.json`
- Generates `race_briefing_actions_openapi.json`
- These define the APIs available to the agent

### 4. Agent Creation
- Creates Bedrock Agent with:
  - Name: `F1RaceWeekendCompanion`
  - Foundation Model: Claude 3 Sonnet
  - Session TTL: 600 seconds (10 minutes)
  - Custom instruction prompt
  - IAM role for permissions

### 5. Action Group Configuration
- Creates `f1_data_actions` action group
  - Linked to F1DataFunction Lambda
  - Provides calendar, standings, race info
- Creates `race_briefing_actions` action group
  - Linked to RaceBriefingFunction Lambda
  - Generates AI-powered briefings

### 6. Lambda Permissions
- Adds resource-based policies to Lambda functions
- Allows Bedrock service to invoke them
- Scoped to specific agent ARN

### 7. Agent Preparation
- Prepares the agent (compiles configuration)
- Waits for preparation to complete (30-60 seconds)
- Verifies agent is ready

### 8. Alias Creation
- Creates `production` alias
- Points to the prepared agent version
- Used for stable API access

### 9. Environment Update
- Updates/creates `.env` file
- Sets `AGENT_ID` and `AGENT_ALIAS_ID`
- Configures region and table names

## Troubleshooting

### "Agent already exists" Error

If you've run the script before:

```bash
# Option 1: Use existing agent
# The script will prompt you - answer 'y'

# Option 2: Delete existing agent first
aws bedrock-agent delete-agent --agent-id <AGENT_ID> --region us-east-1
```

### "CDK stack not found" Error

Deploy the infrastructure first:

```bash
cd infrastructure
cdk deploy
cd ..
```

### "Model access denied" Error

Enable Claude 3 Sonnet in Bedrock:
1. AWS Console → Bedrock → Model access
2. Enable "Claude 3 Sonnet"

### "Permission denied" Error

Make the script executable:

```bash
chmod +x create_bedrock_agent.sh
```

### "jq: command not found" Error

Install jq:

```bash
brew install jq
```

### Lambda Permission Already Exists

This is normal if re-running the script. The warning can be ignored.

## Script Output

The script provides colorful, informative output:

- 🟢 Green checkmarks for successful steps
- 🔴 Red X for errors
- 🟡 Yellow warnings for non-critical issues
- 🔵 Blue info messages

Example successful run:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Checking Prerequisites
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ AWS CLI installed
✓ jq installed
✓ AWS credentials configured
ℹ Using AWS region: us-east-1

[... more steps ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Setup Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Agent Details:
  Name:      F1RaceWeekendCompanion
  ID:        ABC123XYZ
  Alias:     production
  Alias ID:  DEF456UVW
  Region:    us-east-1
```

## Manual Verification

After the script completes, you can verify in AWS Console:

```
https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/agents/<AGENT_ID>
```

Check that:
- ✅ Agent status is "Prepared"
- ✅ Two action groups are configured
- ✅ Production alias exists
- ✅ IAM role is attached

## Configuration Files Updated

The script updates `.env` with:

```bash
AWS_REGION=us-east-1
AGENT_ID=ABC123XYZ
AGENT_ALIAS_ID=DEF456UVW
PREFERENCES_TABLE_NAME=F1AgentStack-PreferencesTable-XXXXX
```

## Cost Considerations

The script creates:
- 1 Bedrock Agent (charges per use)
- Uses existing Lambda functions (from CDK)
- No additional infrastructure costs

Estimated costs with moderate usage:
- **Bedrock**: $0.50-$2/day
- **Total**: ~$15-$60/month

See main README for detailed cost breakdown.

## Advanced Usage

### Using a Different Region

```bash
# Set region before running
export AWS_REGION=us-west-2
./create_bedrock_agent.sh
```

### Custom Agent Name

The script will prompt if an agent with the default name exists. You can:
1. Use the existing agent
2. Enter a new name when prompted

### Re-running the Script

Safe to re-run! The script will:
- Detect existing resources
- Prompt before creating duplicates
- Update configurations as needed

## Next Steps

After successful setup:

1. **Test the agent** with various queries
2. **Set user preferences** to personalize responses
3. **Review CloudWatch logs** for Lambda functions
4. **Monitor costs** in AWS Cost Explorer
5. **Read VERIFICATION.md** for testing checklist

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review CloudFormation stack outputs
3. Check Bedrock agent logs in CloudWatch
4. Verify IAM permissions
5. Ensure Bedrock model access is enabled

## Script Reference

**Location:** `./create_bedrock_agent.sh`

**Functions:**
- `check_prerequisites()` - Verify tools installed
- `check_cdk_deployment()` - Ensure infrastructure exists
- `export_openapi_schemas()` - Generate API schemas
- `create_bedrock_agent()` - Create agent in Bedrock
- `create_action_groups()` - Configure Lambda integrations
- `prepare_agent()` - Prepare agent for use
- `create_agent_alias()` - Create production alias
- `update_env_file()` - Update configuration

**Exit Codes:**
- `0` - Success
- `1` - Error (with descriptive message)

## Comparison with Manual Setup

| Task | Manual (Console) | Automated (Script) |
|------|------------------|-------------------|
| Time Required | 20-30 minutes | 2-3 minutes |
| Error Prone | Yes (many steps) | No (automated) |
| Repeatable | Tedious | One command |
| Documentation | Manual notes | Auto-updated .env |
| Verification | Manual checks | Automated |

## Security Notes

The script:
- ✅ Never stores credentials
- ✅ Uses AWS CLI authentication
- ✅ Creates minimal permissions
- ✅ Follows AWS best practices
- ✅ Uses resource-based policies

## Contributing

Found a bug or have improvements?
1. Test your changes thoroughly
2. Ensure backward compatibility
3. Update this documentation
4. Submit a pull request

---

**Last Updated:** 2025-11-06
**Script Version:** 1.0
**Supported Platforms:** macOS (should work on Linux with minor tweaks)
