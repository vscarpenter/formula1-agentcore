#!/usr/bin/env python3
"""CDK app entry point for F1 Agent infrastructure."""

import os

import aws_cdk as cdk

from f1_agent_stack import F1AgentStack

app = cdk.App()

F1AgentStack(
    app,
    "F1AgentStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION", "us-east-1"),
    ),
    description="F1 Race Weekend Companion using AWS Bedrock AgentCore",
)

app.synth()
