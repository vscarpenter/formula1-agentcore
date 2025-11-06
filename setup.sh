#!/bin/bash

###############################################################################
# Complete Setup Script for F1 Agent
#
# This script automates the entire setup process:
# 1. Python environment setup
# 2. Lambda layer build
# 3. CDK stack deployment
# 4. Bedrock Agent creation
#
# Usage:
#   ./setup.sh
#
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

clear
echo -e "${BLUE}"
cat << "EOF"
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║        F1 Race Weekend Companion - Complete Setup            ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Step 1: Python Environment
print_header "Step 1: Setting Up Python Environment"

if [ -d ".venv" ]; then
    print_warning "Virtual environment already exists"
else
    print_info "Creating virtual environment..."

    # Try uv first, fall back to python -m venv
    if command -v uv &> /dev/null; then
        print_info "Using uv (fast!)"
        uv venv
    else
        print_warning "uv not found, using standard Python venv"
        python3 -m venv .venv
    fi

    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate
print_success "Virtual environment activated"

# Install dependencies
print_info "Installing Python dependencies..."
if command -v uv &> /dev/null; then
    uv pip install -e ".[dev,infra]"
else
    pip install -e ".[dev,infra]"
fi
print_success "Dependencies installed"

# Step 2: Build Lambda Layer
print_header "Step 2: Building Lambda Layer"

if [ -d "lambda_layer" ]; then
    print_warning "Lambda layer already exists, rebuilding..."
    rm -rf lambda_layer
fi

print_info "Building Lambda layer with Linux dependencies..."
make lambda-layer
print_success "Lambda layer built"

# Step 3: Deploy CDK Stack
print_header "Step 3: Deploying CDK Infrastructure"

cd infrastructure

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    print_error "CDK not installed. Installing..."
    npm install -g aws-cdk
fi

# Bootstrap if needed
print_info "Checking CDK bootstrap status..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit &> /dev/null; then
    print_info "Bootstrapping CDK..."
    cdk bootstrap
else
    print_success "CDK already bootstrapped"
fi

# Deploy the stack
print_info "Deploying CDK stack..."
cdk deploy --require-approval never

if [ $? -eq 0 ]; then
    print_success "CDK stack deployed successfully"
else
    print_error "CDK deployment failed"
    exit 1
fi

cd ..

# Verify stack outputs
print_info "Verifying stack outputs..."
OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name F1AgentStack \
    --query 'Stacks[0].Outputs' \
    --output json 2>/dev/null)

if [ "$OUTPUTS" != "null" ] && [ -n "$OUTPUTS" ]; then
    print_success "Stack outputs verified"
else
    print_warning "No outputs found (stack may be older version)"
fi

# Step 4: Create Bedrock Agent
print_header "Step 4: Creating Bedrock Agent"

print_info "Running Bedrock Agent automation script..."
./create_bedrock_agent.sh

if [ $? -eq 0 ]; then
    print_success "Bedrock Agent created successfully!"
else
    print_error "Bedrock Agent creation failed"
    print_info "You can run './create_bedrock_agent.sh' manually to retry"
    exit 1
fi

# Final Summary
print_header "Setup Complete! 🏁"

echo -e "${GREEN}All components are now deployed and ready to use!${NC}\n"

echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Test the agent:"
echo -e "     ${YELLOW}source .venv/bin/activate${NC}"
echo -e "     ${YELLOW}f1-agent chat \"What's the next race?\"${NC}\n"

echo -e "  2. View the calendar:"
echo -e "     ${YELLOW}f1-agent calendar${NC}\n"

echo -e "  3. Check next race:"
echo -e "     ${YELLOW}f1-agent next-race${NC}\n"

echo -e "${BLUE}Helpful Commands:${NC}"
echo -e "  - ${YELLOW}f1-agent --help${NC} - Show all available commands"
echo -e "  - ${YELLOW}f1-agent preferences${NC} - View your preferences"
echo -e "  - ${YELLOW}f1-agent set-preferences${NC} - Set favorite driver/team\n"

echo -e "${GREEN}Enjoy your F1 Race Weekend Companion! 🏁${NC}\n"
