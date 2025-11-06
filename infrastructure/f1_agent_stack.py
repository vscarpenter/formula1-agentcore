"""
AWS CDK stack for F1 Agent infrastructure.

This stack creates:
- DynamoDB tables for user preferences and interaction history
- Lambda functions for action groups
- Bedrock Agent with action group configurations
- IAM roles and permissions
"""

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
)
from constructs import Construct


class F1AgentStack(Stack):
    """CDK Stack for F1 Race Weekend Companion Agent."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table for user preferences
        preferences_table = self.create_preferences_table()

        # DynamoDB table for interaction history
        interactions_table = self.create_interactions_table()

        # Lambda layer with dependencies
        dependencies_layer = self.create_dependencies_layer()

        # Lambda function for F1 data actions
        f1_data_lambda = self.create_f1_data_lambda(
            preferences_table, dependencies_layer
        )

        # Lambda function for race briefing generation
        race_briefing_lambda = self.create_race_briefing_lambda(
            preferences_table, dependencies_layer
        )

        # IAM role for Bedrock Agent
        agent_role = self.create_agent_role(
            f1_data_lambda, race_briefing_lambda
        )

        # Store outputs
        self.preferences_table = preferences_table
        self.interactions_table = interactions_table
        self.f1_data_lambda = f1_data_lambda
        self.race_briefing_lambda = race_briefing_lambda
        self.agent_role = agent_role

    def create_preferences_table(self) -> dynamodb.Table:
        """Create DynamoDB table for user preferences."""
        table = dynamodb.Table(
            self,
            "PreferencesTable",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # For dev/demo purposes
            point_in_time_recovery=True,
        )
        return table

    def create_interactions_table(self) -> dynamodb.Table:
        """Create DynamoDB table for interaction history."""
        table = dynamodb.Table(
            self,
            "InteractionsTable",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl",
        )
        return table

    def create_dependencies_layer(self) -> lambda_.LayerVersion:
        """
        Create Lambda layer with Python dependencies.

        Note: In production, build this layer properly with:
        pip install -r requirements.txt -t python/lib/python3.11/site-packages/
        """
        return lambda_.LayerVersion(
            self,
            "DependenciesLayer",
            code=lambda_.Code.from_asset("../lambda_layer"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="F1 Agent dependencies (requests, boto3, pydantic)",
        )

    def create_f1_data_lambda(
        self,
        preferences_table: dynamodb.Table,
        layer: lambda_.LayerVersion,
    ) -> lambda_.Function:
        """Create Lambda function for F1 data action group."""
        fn = lambda_.Function(
            self,
            "F1DataFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="src.actions.f1_data_actions.lambda_handler",
            code=lambda_.Code.from_asset(".."),
            timeout=Duration.seconds(30),
            memory_size=512,
            layers=[layer],
            environment={
                "PREFERENCES_TABLE_NAME": preferences_table.table_name,
                "LOG_LEVEL": "INFO",
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Grant permissions
        preferences_table.grant_read_data(fn)

        return fn

    def create_race_briefing_lambda(
        self,
        preferences_table: dynamodb.Table,
        layer: lambda_.LayerVersion,
    ) -> lambda_.Function:
        """Create Lambda function for race briefing generation."""
        fn = lambda_.Function(
            self,
            "RaceBriefingFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="src.actions.race_briefing_actions.lambda_handler",
            code=lambda_.Code.from_asset(".."),
            timeout=Duration.seconds(60),
            memory_size=1024,
            layers=[layer],
            environment={
                "PREFERENCES_TABLE_NAME": preferences_table.table_name,
                "LOG_LEVEL": "INFO",
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Grant permissions
        preferences_table.grant_read_data(fn)

        # Grant Bedrock model invocation permission
        fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
                ],
            )
        )

        return fn

    def create_agent_role(
        self,
        f1_data_lambda: lambda_.Function,
        race_briefing_lambda: lambda_.Function,
    ) -> iam.Role:
        """
        Create IAM role for Bedrock Agent.

        The agent needs permissions to invoke Lambda functions
        and use Bedrock foundation models.
        """
        role = iam.Role(
            self,
            "BedrockAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="IAM role for F1 Bedrock Agent",
        )

        # Allow agent to invoke action group Lambda functions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=[
                    f1_data_lambda.function_arn,
                    race_briefing_lambda.function_arn,
                ],
            )
        )

        # Allow agent to use foundation models
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-*"
                ],
            )
        )

        return role
