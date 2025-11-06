#!/bin/bash

###############################################################################
# Bedrock Agent Creation Script
#
# This script automates the creation of an AWS Bedrock Agent for the
# F1 Race Weekend Companion. It handles:
# - CDK stack deployment verification
# - OpenAPI schema export
# - Bedrock Agent creation
# - Action group configuration
# - Agent preparation and alias creation
# - Environment file updates
#
# Prerequisites:
# - AWS CLI installed and configured
# - jq installed (brew install jq)
# - AWS credentials configured with appropriate permissions
# - CDK infrastructure deployed (or script will prompt to deploy)
#
# Usage:
#   ./create_bedrock_agent.sh
#
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="F1AgentStack"
AGENT_NAME="F1RaceWeekendCompanion"
FOUNDATION_MODEL="anthropic.claude-3-sonnet-20240229-v1:0"
IDLE_SESSION_TTL=600
ALIAS_NAME="production"

# Agent instruction
AGENT_INSTRUCTION='You are the F1 Race Weekend Companion, an AI assistant specialized in Formula 1 racing.

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
- Pay extra attention to Circuit of the Americas races (user'\''s home circuit)
- Highlight strategic elements that make races interesting
- Connect current events to historical F1 moments

When users ask about races, always offer to generate a detailed briefing.
When discussing drivers or teams, check if the user has preferences stored.'

###############################################################################
# Helper Functions
###############################################################################

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

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check for AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install it first:"
        echo "  brew install awscli"
        exit 1
    fi
    print_success "AWS CLI installed"

    # Check for jq
    if ! command -v jq &> /dev/null; then
        print_error "jq not found. Installing via Homebrew..."
        if command -v brew &> /dev/null; then
            brew install jq
            print_success "jq installed"
        else
            print_error "Homebrew not found. Please install jq manually:"
            echo "  brew install jq"
            exit 1
        fi
    else
        print_success "jq installed"
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured or invalid"
        echo "  Run: aws configure"
        exit 1
    fi
    print_success "AWS credentials configured"

    # Get AWS region
    AWS_REGION=$(aws configure get region)
    if [ -z "$AWS_REGION" ]; then
        print_warning "No default region set, using us-east-1"
        AWS_REGION="us-east-1"
    fi
    print_info "Using AWS region: $AWS_REGION"
}

check_cdk_deployment() {
    print_header "Checking CDK Stack Deployment"

    # Check if stack exists
    if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" &> /dev/null; then
        print_warning "CDK stack '$STACK_NAME' not found"
        echo -e "\nWould you like to deploy it now? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            deploy_cdk_stack
        else
            print_error "CDK stack required. Please deploy it first:"
            echo "  cd infrastructure"
            echo "  cdk deploy"
            exit 1
        fi
    else
        print_success "CDK stack found"
    fi

    # Get stack outputs
    print_info "Retrieving stack outputs..."
    STACK_OUTPUTS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs' \
        --output json 2>/dev/null || echo "null")

    # Try to extract resource ARNs from outputs (if they exist)
    F1_DATA_LAMBDA_ARN=""
    RACE_BRIEFING_LAMBDA_ARN=""
    BEDROCK_ROLE_ARN=""
    PREFERENCES_TABLE=""

    if [ "$STACK_OUTPUTS" != "null" ] && [ -n "$STACK_OUTPUTS" ]; then
        F1_DATA_LAMBDA_ARN=$(echo "$STACK_OUTPUTS" | jq -r '.[]? | select(.OutputKey? | contains("F1DataFunction"))? | .OutputValue' 2>/dev/null | head -1)
        RACE_BRIEFING_LAMBDA_ARN=$(echo "$STACK_OUTPUTS" | jq -r '.[]? | select(.OutputKey? | contains("RaceBriefingFunction"))? | .OutputValue' 2>/dev/null | head -1)
        BEDROCK_ROLE_ARN=$(echo "$STACK_OUTPUTS" | jq -r '.[]? | select(.OutputKey? | contains("BedrockAgentRole"))? | .OutputValue' 2>/dev/null | head -1)
        PREFERENCES_TABLE=$(echo "$STACK_OUTPUTS" | jq -r '.[]? | select(.OutputKey? | contains("PreferencesTable"))? | .OutputValue' 2>/dev/null | head -1)
    fi

    # If outputs are not available, get resources directly from stack
    if [ -z "$F1_DATA_LAMBDA_ARN" ] || [ "$F1_DATA_LAMBDA_ARN" = "null" ]; then
        print_warning "Stack outputs not found, retrieving resources directly..."
        print_info "Note: Redeploy the stack to add outputs for faster lookup next time"

        RESOURCES=$(aws cloudformation describe-stack-resources \
            --stack-name "$STACK_NAME" \
            --region "$AWS_REGION" \
            --output json 2>/dev/null)

        if [ -z "$RESOURCES" ]; then
            print_error "Unable to retrieve stack resources"
            exit 1
        fi

        # Get resource physical IDs
        F1_DATA_LAMBDA_NAME=$(echo "$RESOURCES" | jq -r '.StackResources[]? | select(.LogicalResourceId == "F1DataFunction")? | .PhysicalResourceId' 2>/dev/null)
        RACE_BRIEFING_LAMBDA_NAME=$(echo "$RESOURCES" | jq -r '.StackResources[]? | select(.LogicalResourceId == "RaceBriefingFunction")? | .PhysicalResourceId' 2>/dev/null)
        BEDROCK_ROLE_ARN=$(echo "$RESOURCES" | jq -r '.StackResources[]? | select(.LogicalResourceId == "BedrockAgentRole")? | .PhysicalResourceId' 2>/dev/null)
        PREFERENCES_TABLE=$(echo "$RESOURCES" | jq -r '.StackResources[]? | select(.LogicalResourceId == "PreferencesTable")? | .PhysicalResourceId' 2>/dev/null)

        # Get full ARNs for Lambda functions if we got valid names
        if [ -n "$F1_DATA_LAMBDA_NAME" ] && [ "$F1_DATA_LAMBDA_NAME" != "null" ]; then
            if [[ ! "$F1_DATA_LAMBDA_NAME" =~ ^arn: ]]; then
                print_info "Getting ARN for F1 Data Lambda..."
                F1_DATA_LAMBDA_ARN=$(aws lambda get-function \
                    --function-name "$F1_DATA_LAMBDA_NAME" \
                    --region "$AWS_REGION" \
                    --query 'Configuration.FunctionArn' \
                    --output text 2>/dev/null)
            else
                F1_DATA_LAMBDA_ARN="$F1_DATA_LAMBDA_NAME"
            fi
        fi

        if [ -n "$RACE_BRIEFING_LAMBDA_NAME" ] && [ "$RACE_BRIEFING_LAMBDA_NAME" != "null" ]; then
            if [[ ! "$RACE_BRIEFING_LAMBDA_NAME" =~ ^arn: ]]; then
                print_info "Getting ARN for Race Briefing Lambda..."
                RACE_BRIEFING_LAMBDA_ARN=$(aws lambda get-function \
                    --function-name "$RACE_BRIEFING_LAMBDA_NAME" \
                    --region "$AWS_REGION" \
                    --query 'Configuration.FunctionArn' \
                    --output text 2>/dev/null)
            else
                RACE_BRIEFING_LAMBDA_ARN="$RACE_BRIEFING_LAMBDA_NAME"
            fi
        fi
    fi

    # Display found resources
    if [ -n "$F1_DATA_LAMBDA_ARN" ] && [ "$F1_DATA_LAMBDA_ARN" != "null" ]; then
        print_success "F1 Data Lambda: $F1_DATA_LAMBDA_ARN"
    else
        print_error "F1 Data Lambda not found"
    fi

    if [ -n "$RACE_BRIEFING_LAMBDA_ARN" ] && [ "$RACE_BRIEFING_LAMBDA_ARN" != "null" ]; then
        print_success "Race Briefing Lambda: $RACE_BRIEFING_LAMBDA_ARN"
    else
        print_error "Race Briefing Lambda not found"
    fi

    if [ -n "$BEDROCK_ROLE_ARN" ] && [ "$BEDROCK_ROLE_ARN" != "null" ]; then
        print_success "Bedrock Agent Role: $BEDROCK_ROLE_ARN"
    else
        print_error "Bedrock Agent Role not found"
    fi

    if [ -n "$PREFERENCES_TABLE" ] && [ "$PREFERENCES_TABLE" != "null" ]; then
        print_success "Preferences Table: $PREFERENCES_TABLE"
    fi

    # Verify we have all required resources
    if [ -z "$F1_DATA_LAMBDA_ARN" ] || [ "$F1_DATA_LAMBDA_ARN" = "null" ] || \
       [ -z "$RACE_BRIEFING_LAMBDA_ARN" ] || [ "$RACE_BRIEFING_LAMBDA_ARN" = "null" ] || \
       [ -z "$BEDROCK_ROLE_ARN" ] || [ "$BEDROCK_ROLE_ARN" = "null" ]; then
        print_error "Missing required resources from CDK stack"
        print_info "Please ensure the CDK stack is properly deployed with all resources"
        exit 1
    fi
}

deploy_cdk_stack() {
    print_header "Deploying CDK Stack"

    cd infrastructure

    # Check if CDK is installed
    if ! command -v cdk &> /dev/null; then
        print_error "CDK not installed. Installing..."
        npm install -g aws-cdk
    fi

    # Bootstrap if needed
    print_info "Checking CDK bootstrap..."
    cdk bootstrap

    # Build Lambda layer
    print_info "Building Lambda layer..."
    cd ..
    make lambda-layer

    # Deploy stack
    print_info "Deploying stack..."
    cd infrastructure
    cdk deploy --require-approval never

    cd ..
    print_success "CDK stack deployed"
}

export_openapi_schemas() {
    print_header "Exporting OpenAPI Schemas"

    # Run the export schemas command
    if [ -f "cli/main.py" ]; then
        print_info "Exporting schemas..."
        f1-agent export-schemas || python -m cli.main export-schemas || {
            print_warning "Could not run f1-agent command, using Python directly"
            python -c "from src.agent.agent_config import export_schemas_to_file; export_schemas_to_file('.')"
        }
        print_success "Schemas exported"
    else
        print_error "Cannot find schema export functionality"
        exit 1
    fi

    # Verify schema files exist
    if [ ! -f "f1_data_actions_openapi.json" ] || [ ! -f "race_briefing_actions_openapi.json" ]; then
        print_error "Schema files not found"
        exit 1
    fi

    print_success "f1_data_actions_openapi.json"
    print_success "race_briefing_actions_openapi.json"
}

create_bedrock_agent() {
    print_header "Creating Bedrock Agent"

    # Check if agent already exists
    EXISTING_AGENTS=$(aws bedrock-agent list-agents --region "$AWS_REGION" --output json)
    EXISTING_AGENT_ID=$(echo "$EXISTING_AGENTS" | jq -r ".agentSummaries[] | select(.agentName == \"$AGENT_NAME\") | .agentId")

    if [ -n "$EXISTING_AGENT_ID" ] && [ "$EXISTING_AGENT_ID" != "null" ]; then
        print_warning "Agent '$AGENT_NAME' already exists with ID: $EXISTING_AGENT_ID"
        echo -e "\nWould you like to use the existing agent? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            AGENT_ID="$EXISTING_AGENT_ID"
            print_info "Using existing agent"
            return
        else
            echo -e "\nEnter a new agent name:"
            read -r AGENT_NAME
        fi
    fi

    # Create the agent
    print_info "Creating agent '$AGENT_NAME'..."
    CREATE_RESPONSE=$(aws bedrock-agent create-agent \
        --agent-name "$AGENT_NAME" \
        --foundation-model "$FOUNDATION_MODEL" \
        --instruction "$AGENT_INSTRUCTION" \
        --agent-resource-role-arn "$BEDROCK_ROLE_ARN" \
        --idle-session-ttl-in-seconds "$IDLE_SESSION_TTL" \
        --region "$AWS_REGION" \
        --output json)

    AGENT_ID=$(echo "$CREATE_RESPONSE" | jq -r '.agent.agentId')
    AGENT_ARN=$(echo "$CREATE_RESPONSE" | jq -r '.agent.agentArn')

    if [ -z "$AGENT_ID" ] || [ "$AGENT_ID" = "null" ]; then
        print_error "Failed to create agent"
        echo "$CREATE_RESPONSE"
        exit 1
    fi

    print_success "Agent created with ID: $AGENT_ID"
    print_info "Agent ARN: $AGENT_ARN"

    # Wait for agent to be ready
    print_info "Waiting for agent to be ready..."
    sleep 5
}

create_action_groups() {
    print_header "Creating Action Groups"

    # Verify schema files exist
    if [ ! -f "f1_data_actions_openapi.json" ] || [ ! -f "race_briefing_actions_openapi.json" ]; then
        print_error "Schema files not found. Please run export_openapi_schemas first."
        exit 1
    fi

    # Create F1 Data action group
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

    # Check if command succeeded
    if echo "$F1_DATA_AG_RESPONSE" | grep -q "Error parsing parameter"; then
        print_error "Failed to create F1 Data action group - parameter error"
        echo "$F1_DATA_AG_RESPONSE"
        exit 1
    fi

    F1_DATA_AG_ID=$(echo "$F1_DATA_AG_RESPONSE" | jq -r '.agentActionGroup.actionGroupId' 2>/dev/null)

    if [ -z "$F1_DATA_AG_ID" ] || [ "$F1_DATA_AG_ID" = "null" ]; then
        print_error "Failed to create F1 Data action group"
        echo "$F1_DATA_AG_RESPONSE"
        exit 1
    else
        print_success "F1 Data action group created: $F1_DATA_AG_ID"
    fi

    # Create Race Briefing action group
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

    # Check if command succeeded
    if echo "$RACE_BRIEFING_AG_RESPONSE" | grep -q "Error parsing parameter"; then
        print_error "Failed to create Race Briefing action group - parameter error"
        echo "$RACE_BRIEFING_AG_RESPONSE"
        exit 1
    fi

    RACE_BRIEFING_AG_ID=$(echo "$RACE_BRIEFING_AG_RESPONSE" | jq -r '.agentActionGroup.actionGroupId' 2>/dev/null)

    if [ -z "$RACE_BRIEFING_AG_ID" ] || [ "$RACE_BRIEFING_AG_ID" = "null" ]; then
        print_error "Failed to create Race Briefing action group"
        echo "$RACE_BRIEFING_AG_RESPONSE"
        exit 1
    else
        print_success "Race Briefing action group created: $RACE_BRIEFING_AG_ID"
    fi

    # Add Lambda permissions for Bedrock to invoke
    print_info "Adding Lambda invoke permissions..."

    aws lambda add-permission \
        --function-name "$F1_DATA_LAMBDA_ARN" \
        --statement-id "AllowBedrockAgent_$AGENT_ID" \
        --action "lambda:InvokeFunction" \
        --principal "bedrock.amazonaws.com" \
        --source-arn "arn:aws:bedrock:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):agent/$AGENT_ID" \
        --region "$AWS_REGION" \
        --output json > /dev/null 2>&1 || print_warning "Permission may already exist for F1 Data Lambda"

    aws lambda add-permission \
        --function-name "$RACE_BRIEFING_LAMBDA_ARN" \
        --statement-id "AllowBedrockAgent_$AGENT_ID" \
        --action "lambda:InvokeFunction" \
        --principal "bedrock.amazonaws.com" \
        --source-arn "arn:aws:bedrock:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):agent/$AGENT_ID" \
        --region "$AWS_REGION" \
        --output json > /dev/null 2>&1 || print_warning "Permission may already exist for Race Briefing Lambda"

    print_success "Lambda permissions configured"
}

prepare_agent() {
    print_header "Preparing Agent"

    print_info "Preparing agent for use..."
    PREPARE_RESPONSE=$(aws bedrock-agent prepare-agent \
        --agent-id "$AGENT_ID" \
        --region "$AWS_REGION" \
        --output json)

    AGENT_STATUS=$(echo "$PREPARE_RESPONSE" | jq -r '.agentStatus')

    if [ "$AGENT_STATUS" != "PREPARED" ] && [ "$AGENT_STATUS" != "PREPARING" ]; then
        print_warning "Agent status: $AGENT_STATUS"
    else
        print_success "Agent prepared successfully"
    fi

    # Wait for preparation to complete
    print_info "Waiting for agent preparation (this may take 30-60 seconds)..."
    MAX_ATTEMPTS=30
    ATTEMPT=0

    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        sleep 3
        AGENT_INFO=$(aws bedrock-agent get-agent \
            --agent-id "$AGENT_ID" \
            --region "$AWS_REGION" \
            --output json)

        CURRENT_STATUS=$(echo "$AGENT_INFO" | jq -r '.agent.agentStatus')

        if [ "$CURRENT_STATUS" = "PREPARED" ]; then
            print_success "Agent is ready!"
            break
        elif [ "$CURRENT_STATUS" = "FAILED" ]; then
            print_error "Agent preparation failed"
            exit 1
        fi

        ATTEMPT=$((ATTEMPT + 1))
        echo -n "."
    done
    echo ""

    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        print_warning "Agent preparation taking longer than expected, but continuing..."
    fi
}

create_agent_alias() {
    print_header "Creating Agent Alias"

    # Check if alias already exists
    EXISTING_ALIASES=$(aws bedrock-agent list-agent-aliases \
        --agent-id "$AGENT_ID" \
        --region "$AWS_REGION" \
        --output json)

    EXISTING_ALIAS_ID=$(echo "$EXISTING_ALIASES" | jq -r ".agentAliasSummaries[] | select(.agentAliasName == \"$ALIAS_NAME\") | .agentAliasId")

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
            --output json)

        AGENT_ALIAS_ID=$(echo "$ALIAS_RESPONSE" | jq -r '.agentAlias.agentAliasId')

        if [ -z "$AGENT_ALIAS_ID" ] || [ "$AGENT_ALIAS_ID" = "null" ]; then
            print_error "Failed to create alias"
            echo "$ALIAS_RESPONSE"
            exit 1
        fi

        print_success "Alias created: $AGENT_ALIAS_ID"
    fi
}

update_env_file() {
    print_header "Updating Environment Configuration"

    ENV_FILE=".env"

    # Create .env from example if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example "$ENV_FILE"
            print_info "Created .env from .env.example"
        else
            touch "$ENV_FILE"
            print_info "Created new .env file"
        fi
    fi

    # Update or add configuration values
    print_info "Updating .env file..."

    # Function to update or add env var
    update_env_var() {
        local key=$1
        local value=$2

        if grep -q "^${key}=" "$ENV_FILE"; then
            # Update existing
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
            else
                sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
            fi
        else
            # Add new
            echo "${key}=${value}" >> "$ENV_FILE"
        fi
    }

    update_env_var "AWS_REGION" "$AWS_REGION"
    update_env_var "AGENT_ID" "$AGENT_ID"
    update_env_var "AGENT_ALIAS_ID" "$AGENT_ALIAS_ID"

    if [ -n "$PREFERENCES_TABLE" ]; then
        update_env_var "PREFERENCES_TABLE_NAME" "$PREFERENCES_TABLE"
    fi

    print_success "Environment file updated"
}

print_summary() {
    print_header "Setup Complete!"

    echo -e "${GREEN}Your Bedrock Agent is now ready to use!${NC}\n"

    echo -e "${BLUE}Agent Details:${NC}"
    echo -e "  Name:      $AGENT_NAME"
    echo -e "  ID:        ${GREEN}$AGENT_ID${NC}"
    echo -e "  Alias:     $ALIAS_NAME"
    echo -e "  Alias ID:  ${GREEN}$AGENT_ALIAS_ID${NC}"
    echo -e "  Region:    $AWS_REGION"
    echo -e "  Model:     $FOUNDATION_MODEL\n"

    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "  1. Test the agent with the CLI:"
    echo -e "     ${YELLOW}f1-agent chat \"What's the next race?\"${NC}\n"
    echo -e "  2. View the calendar:"
    echo -e "     ${YELLOW}f1-agent calendar${NC}\n"
    echo -e "  3. Check next race:"
    echo -e "     ${YELLOW}f1-agent next-race${NC}\n"

    echo -e "${BLUE}Configuration:${NC}"
    echo -e "  The .env file has been updated with your agent credentials.\n"

    echo -e "${BLUE}AWS Console:${NC}"
    echo -e "  View your agent at:"
    echo -e "  https://$AWS_REGION.console.aws.amazon.com/bedrock/home?region=$AWS_REGION#/agents/$AGENT_ID\n"
}

###############################################################################
# Main Execution
###############################################################################

main() {
    clear
    echo -e "${BLUE}"
    cat << "EOF"
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║        F1 Race Weekend Companion - Agent Setup               ║
    ║        Automated Bedrock Agent Creation                      ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    check_prerequisites
    check_cdk_deployment
    export_openapi_schemas
    create_bedrock_agent
    create_action_groups
    prepare_agent
    create_agent_alias
    update_env_file
    print_summary

    print_success "All done! 🏁"
}

# Run main function
main
