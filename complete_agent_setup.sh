#!/bin/bash

###############################################################################
# Complete Agent Setup Script
#
# This script completes the setup for an already-created Bedrock Agent
# by adding action groups, preparing it, and creating an alias.
#
# Usage:
#   ./complete_agent_setup.sh AGENT_ID
#
###############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Configuration
STACK_NAME="F1AgentStack"
ALIAS_NAME="production"

# Get agent ID from argument or default
AGENT_ID=${1:-K8D2LLHTKN}
AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")

print_header "Completing Bedrock Agent Setup"
print_info "Agent ID: $AGENT_ID"
print_info "Region: $AWS_REGION"

# Get Lambda ARNs from CDK stack
print_header "Retrieving Lambda Functions"

STACK_OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs' \
    --output json 2>/dev/null || echo "null")

if [ "$STACK_OUTPUTS" != "null" ] && [ -n "$STACK_OUTPUTS" ]; then
    F1_DATA_LAMBDA_ARN=$(echo "$STACK_OUTPUTS" | jq -r '.[]? | select(.OutputKey? | contains("F1DataFunction"))? | .OutputValue' 2>/dev/null | head -1)
    RACE_BRIEFING_LAMBDA_ARN=$(echo "$STACK_OUTPUTS" | jq -r '.[]? | select(.OutputKey? | contains("RaceBriefingFunction"))? | .OutputValue' 2>/dev/null | head -1)
fi

# Fallback to resource lookup
if [ -z "$F1_DATA_LAMBDA_ARN" ] || [ "$F1_DATA_LAMBDA_ARN" = "null" ]; then
    print_info "Getting Lambda ARNs from stack resources..."
    RESOURCES=$(aws cloudformation describe-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --output json 2>/dev/null)

    F1_DATA_LAMBDA_NAME=$(echo "$RESOURCES" | jq -r '.StackResources[]? | select(.LogicalResourceId == "F1DataFunction")? | .PhysicalResourceId' 2>/dev/null)
    RACE_BRIEFING_LAMBDA_NAME=$(echo "$RESOURCES" | jq -r '.StackResources[]? | select(.LogicalResourceId == "RaceBriefingFunction")? | .PhysicalResourceId' 2>/dev/null)

    if [ -n "$F1_DATA_LAMBDA_NAME" ]; then
        F1_DATA_LAMBDA_ARN=$(aws lambda get-function --function-name "$F1_DATA_LAMBDA_NAME" --region "$AWS_REGION" --query 'Configuration.FunctionArn' --output text 2>/dev/null)
    fi

    if [ -n "$RACE_BRIEFING_LAMBDA_NAME" ]; then
        RACE_BRIEFING_LAMBDA_ARN=$(aws lambda get-function --function-name "$RACE_BRIEFING_LAMBDA_NAME" --region "$AWS_REGION" --query 'Configuration.FunctionArn' --output text 2>/dev/null)
    fi
fi

if [ -z "$F1_DATA_LAMBDA_ARN" ] || [ -z "$RACE_BRIEFING_LAMBDA_ARN" ]; then
    print_error "Could not find Lambda functions"
    exit 1
fi

print_success "F1 Data Lambda: $F1_DATA_LAMBDA_ARN"
print_success "Race Briefing Lambda: $RACE_BRIEFING_LAMBDA_ARN"

# Export schemas if needed
print_header "Checking OpenAPI Schemas"

if [ ! -f "f1_data_actions_openapi.json" ] || [ ! -f "race_briefing_actions_openapi.json" ]; then
    print_info "Exporting schemas..."
    f1-agent export-schemas 2>/dev/null || python -c "from src.agent.agent_config import export_schemas_to_file; export_schemas_to_file('.')"
    print_success "Schemas exported"
else
    print_success "Schemas already exist"
fi

# Create action groups
print_header "Creating Action Groups"

print_info "Creating F1 Data action group..."
F1_DATA_AG_RESPONSE=$(aws bedrock-agent create-agent-action-group \
    --agent-id "$AGENT_ID" \
    --agent-version "DRAFT" \
    --action-group-name "f1_data_actions" \
    --action-group-executor lambda="$F1_DATA_LAMBDA_ARN" \
    --api-schema payload="file://f1_data_actions_openapi.json" \
    --description "Action group for F1 race data and schedules" \
    --region "$AWS_REGION" \
    --output json 2>&1)

if echo "$F1_DATA_AG_RESPONSE" | grep -q "ConflictException"; then
    print_warning "F1 Data action group already exists"
elif echo "$F1_DATA_AG_RESPONSE" | grep -q "Error"; then
    print_error "Failed to create F1 Data action group"
    echo "$F1_DATA_AG_RESPONSE"
else
    F1_DATA_AG_ID=$(echo "$F1_DATA_AG_RESPONSE" | jq -r '.agentActionGroup.actionGroupId' 2>/dev/null)
    print_success "F1 Data action group created: $F1_DATA_AG_ID"
fi

print_info "Creating Race Briefing action group..."
RACE_BRIEFING_AG_RESPONSE=$(aws bedrock-agent create-agent-action-group \
    --agent-id "$AGENT_ID" \
    --agent-version "DRAFT" \
    --action-group-name "race_briefing_actions" \
    --action-group-executor lambda="$RACE_BRIEFING_LAMBDA_ARN" \
    --api-schema payload="file://race_briefing_actions_openapi.json" \
    --description "Action group for generating race briefings" \
    --region "$AWS_REGION" \
    --output json 2>&1)

if echo "$RACE_BRIEFING_AG_RESPONSE" | grep -q "ConflictException"; then
    print_warning "Race Briefing action group already exists"
elif echo "$RACE_BRIEFING_AG_RESPONSE" | grep -q "Error"; then
    print_error "Failed to create Race Briefing action group"
    echo "$RACE_BRIEFING_AG_RESPONSE"
else
    RACE_BRIEFING_AG_ID=$(echo "$RACE_BRIEFING_AG_RESPONSE" | jq -r '.agentActionGroup.actionGroupId' 2>/dev/null)
    print_success "Race Briefing action group created: $RACE_BRIEFING_AG_ID"
fi

# Add Lambda permissions
print_header "Configuring Lambda Permissions"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws lambda add-permission \
    --function-name "$F1_DATA_LAMBDA_ARN" \
    --statement-id "AllowBedrockAgent_$AGENT_ID" \
    --action "lambda:InvokeFunction" \
    --principal "bedrock.amazonaws.com" \
    --source-arn "arn:aws:bedrock:$AWS_REGION:$ACCOUNT_ID:agent/$AGENT_ID" \
    --region "$AWS_REGION" \
    --output json > /dev/null 2>&1 && print_success "F1 Data Lambda permission added" || print_warning "F1 Data Lambda permission may already exist"

aws lambda add-permission \
    --function-name "$RACE_BRIEFING_LAMBDA_ARN" \
    --statement-id "AllowBedrockAgent_$AGENT_ID" \
    --action "lambda:InvokeFunction" \
    --principal "bedrock.amazonaws.com" \
    --source-arn "arn:aws:bedrock:$AWS_REGION:$ACCOUNT_ID:agent/$AGENT_ID" \
    --region "$AWS_REGION" \
    --output json > /dev/null 2>&1 && print_success "Race Briefing Lambda permission added" || print_warning "Race Briefing Lambda permission may already exist"

# Prepare agent
print_header "Preparing Agent"

print_info "Preparing agent for use..."
PREPARE_RESPONSE=$(aws bedrock-agent prepare-agent \
    --agent-id "$AGENT_ID" \
    --region "$AWS_REGION" \
    --output json 2>&1)

if echo "$PREPARE_RESPONSE" | grep -q "Error"; then
    print_error "Failed to prepare agent"
    echo "$PREPARE_RESPONSE"
else
    print_success "Agent preparation initiated"

    print_info "Waiting for agent to be prepared (this may take 30-60 seconds)..."
    sleep 5

    MAX_ATTEMPTS=30
    for i in $(seq 1 $MAX_ATTEMPTS); do
        AGENT_INFO=$(aws bedrock-agent get-agent \
            --agent-id "$AGENT_ID" \
            --region "$AWS_REGION" \
            --output json 2>/dev/null)

        STATUS=$(echo "$AGENT_INFO" | jq -r '.agent.agentStatus' 2>/dev/null)

        if [ "$STATUS" = "PREPARED" ]; then
            print_success "Agent is ready!"
            break
        elif [ "$STATUS" = "FAILED" ]; then
            print_error "Agent preparation failed"
            exit 1
        fi

        echo -n "."
        sleep 2
    done
    echo ""
fi

# Create or get alias
print_header "Creating Agent Alias"

EXISTING_ALIASES=$(aws bedrock-agent list-agent-aliases \
    --agent-id "$AGENT_ID" \
    --region "$AWS_REGION" \
    --output json 2>/dev/null)

EXISTING_ALIAS_ID=$(echo "$EXISTING_ALIASES" | jq -r ".agentAliasSummaries[] | select(.agentAliasName == \"$ALIAS_NAME\") | .agentAliasId" 2>/dev/null)

if [ -n "$EXISTING_ALIAS_ID" ] && [ "$EXISTING_ALIAS_ID" != "null" ]; then
    print_warning "Alias '$ALIAS_NAME' already exists: $EXISTING_ALIAS_ID"
    AGENT_ALIAS_ID="$EXISTING_ALIAS_ID"
else
    print_info "Creating alias '$ALIAS_NAME'..."
    ALIAS_RESPONSE=$(aws bedrock-agent create-agent-alias \
        --agent-id "$AGENT_ID" \
        --agent-alias-name "$ALIAS_NAME" \
        --description "Production alias for F1 Race Weekend Companion" \
        --region "$AWS_REGION" \
        --output json 2>&1)

    if echo "$ALIAS_RESPONSE" | grep -q "Error"; then
        print_error "Failed to create alias"
        echo "$ALIAS_RESPONSE"
    else
        AGENT_ALIAS_ID=$(echo "$ALIAS_RESPONSE" | jq -r '.agentAlias.agentAliasId' 2>/dev/null)
        print_success "Alias created: $AGENT_ALIAS_ID"
    fi
fi

# Update .env
print_header "Updating .env File"

./update_env_with_agent.sh "$AGENT_ID" "$AGENT_ALIAS_ID"

print_header "Setup Complete!"

echo -e "${GREEN}Your Bedrock Agent is now ready!${NC}\n"
echo -e "${BLUE}Test it with:${NC}"
echo -e "  ${YELLOW}f1-agent chat \"What's the next race?\"${NC}\n"
