#!/bin/bash

###############################################################################
# Quick .env Update Script
#
# Use this script to update .env with an existing agent ID
#
# Usage:
#   ./update_env_with_agent.sh AGENT_ID AGENT_ALIAS_ID
#   OR run without arguments for interactive mode
#
###############################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

ENV_FILE=".env"

# Get AWS region
AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")

# If arguments provided, use them
if [ $# -eq 2 ]; then
    AGENT_ID=$1
    AGENT_ALIAS_ID=$2
else
    # Interactive mode
    echo "Enter Agent ID (or press Enter to use existing agent: K8D2LLHTKN):"
    read -r input_agent_id
    AGENT_ID=${input_agent_id:-K8D2LLHTKN}

    # Try to get alias for this agent
    echo ""
    print_info "Fetching aliases for agent $AGENT_ID..."
    ALIASES=$(aws bedrock-agent list-agent-aliases \
        --agent-id "$AGENT_ID" \
        --region "$AWS_REGION" \
        --output json 2>/dev/null)

    if [ -n "$ALIASES" ]; then
        ALIAS_ID=$(echo "$ALIASES" | jq -r '.agentAliasSummaries[0].agentAliasId' 2>/dev/null)
        if [ -n "$ALIAS_ID" ] && [ "$ALIAS_ID" != "null" ]; then
            print_info "Found alias: $ALIAS_ID"
            AGENT_ALIAS_ID=$ALIAS_ID
        fi
    fi

    # If no alias found, ask user
    if [ -z "$AGENT_ALIAS_ID" ]; then
        echo "Enter Agent Alias ID:"
        read -r AGENT_ALIAS_ID
    fi
fi

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

# Function to update or add env var
update_env_var() {
    local key=$1
    local value=$2

    if grep -q "^${key}=" "$ENV_FILE"; then
        # Update existing - handle both macOS and Linux sed
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

# Update values
update_env_var "AWS_REGION" "$AWS_REGION"
update_env_var "AGENT_ID" "$AGENT_ID"
update_env_var "AGENT_ALIAS_ID" "$AGENT_ALIAS_ID"

print_success "Updated .env file:"
echo ""
echo "  AWS_REGION=$AWS_REGION"
echo "  AGENT_ID=$AGENT_ID"
echo "  AGENT_ALIAS_ID=$AGENT_ALIAS_ID"
echo ""

print_info "You can now test with:"
echo "  f1-agent chat \"What's the next race?\""
