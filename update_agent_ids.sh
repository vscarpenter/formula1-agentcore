#!/bin/bash
# Helper script to update .env with Agent IDs

echo "🤖 F1 Agent ID Configuration Helper"
echo ""

# Check if .env exists, create if not
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# Prompt for Agent ID
echo "Enter your Bedrock Agent ID (e.g., ABCDEFGHIJ):"
read AGENT_ID

# Prompt for Alias ID
echo "Enter your Agent Alias ID (e.g., TSTALIASID):"
read AGENT_ALIAS_ID

# Check if values are already in .env
if grep -q "^AGENT_ID=" .env; then
    # Update existing
    sed -i.bak "s/^AGENT_ID=.*/AGENT_ID=$AGENT_ID/" .env
    echo "✅ Updated AGENT_ID in .env"
else
    # Add new
    echo "AGENT_ID=$AGENT_ID" >> .env
    echo "✅ Added AGENT_ID to .env"
fi

if grep -q "^AGENT_ALIAS_ID=" .env; then
    # Update existing
    sed -i.bak "s/^AGENT_ALIAS_ID=.*/AGENT_ALIAS_ID=$AGENT_ALIAS_ID/" .env
    echo "✅ Updated AGENT_ALIAS_ID in .env"
else
    # Add new
    echo "AGENT_ALIAS_ID=$AGENT_ALIAS_ID" >> .env
    echo "✅ Added AGENT_ALIAS_ID to .env"
fi

echo ""
echo "✅ Configuration complete!"
echo ""
echo "You can now test your agent with:"
echo "  f1-agent chat \"What's the next race?\""

# Clean up backup
rm -f .env.bak
