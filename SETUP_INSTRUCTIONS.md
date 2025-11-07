# Quick Setup Instructions for Mac

Follow these steps to get everything working:

## Step 1: Set Up Python Environment

From the project root directory:

```bash
# Install uv if you don't have it (ultra-fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip if you prefer
# pip install uv

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install all dependencies (including CDK)
uv pip install -e ".[dev,infra]"
```

**Alternative if you don't want to use uv:**

```bash
# Create virtual environment with standard Python
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev,infra]"
```

## Step 2: Build Lambda Layer

The Lambda functions need Linux-compatible dependencies:

```bash
make lambda-layer
```

This will create a `lambda_layer/` directory with Python packages compiled for Linux.

## Step 3: Deploy CDK Stack

```bash
cd infrastructure

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the stack (this will now include outputs)
cdk deploy

# Go back to project root
cd ..
```

**What this creates:**
- DynamoDB tables (Preferences, Interactions)
- Lambda functions (F1Data, RaceBriefing)
- IAM role for Bedrock Agent
- CloudFormation outputs for easy resource lookup

## Step 4: Run Automation Script

Now the script should work:

```bash
./create_bedrock_agent.sh
```

This will:
- Export OpenAPI schemas
- Create the Bedrock Agent
- Configure action groups
- Set up all permissions
- Update your `.env` file

## Troubleshooting

### "ModuleNotFoundError: No module named 'aws_cdk'"
- Make sure you activated the virtual environment: `source .venv/bin/activate`
- Install dependencies: `uv pip install -e ".[dev,infra]"`

### "Resources not found" in script
- Make sure you deployed the CDK stack first: `cd infrastructure && cdk deploy`
- Check stack exists: `aws cloudformation describe-stacks --stack-name F1AgentStack`

### "Lambda layer not found"
- Build the layer: `make lambda-layer`
- Check it exists: `ls -la lambda_layer/`

## Verify Setup

After successful deployment, you should see:

```bash
# Check stack outputs
aws cloudformation describe-stacks \
  --stack-name F1AgentStack \
  --query 'Stacks[0].Outputs' \
  --output table

# Test the CLI (after running automation script)
f1-agent calendar
```

## Full Command Sequence

Here's the complete sequence if starting fresh:

```bash
# 1. Setup environment
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,infra]"

# 2. Build Lambda layer
make lambda-layer

# 3. Deploy infrastructure
cd infrastructure
cdk bootstrap  # First time only
cdk deploy
cd ..

# 4. Create Bedrock Agent
./create_bedrock_agent.sh

# 5. Test it works
f1-agent chat "What's the next race?"
```

That's it! 🏁
