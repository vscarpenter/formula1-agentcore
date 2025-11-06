"""DynamoDB storage for user preferences and settings."""

import logging
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from src.models import UserPreferences

logger = logging.getLogger(__name__)


class PreferencesStoreError(Exception):
    """Raised when DynamoDB operations fail."""

    pass


class PreferencesStore:
    """
    Manages user preferences in DynamoDB.

    Provides methods to create, read, update, and manage user
    preferences for personalized F1 content.
    """

    def __init__(self, table_name: str, region: str = "us-east-1"):
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)

    def get_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """
        Retrieve user preferences from DynamoDB.

        Args:
            user_id: Unique user identifier

        Returns:
            UserPreferences object or None if not found

        Raises:
            PreferencesStoreError: If DynamoDB operation fails
        """
        try:
            response = self.table.get_item(Key={"user_id": user_id})

            if "Item" not in response:
                logger.info(f"No preferences found for user: {user_id}")
                return None

            item = response["Item"]
            # Convert DynamoDB timestamps back to datetime
            item["created_at"] = datetime.fromisoformat(item["created_at"])
            item["updated_at"] = datetime.fromisoformat(item["updated_at"])

            return UserPreferences(**item)

        except ClientError as e:
            error_msg = f"Failed to get preferences for {user_id}: {e.response['Error']['Message']}"
            logger.error(error_msg)
            raise PreferencesStoreError(error_msg) from e

    def save_preferences(self, preferences: UserPreferences) -> None:
        """
        Save or update user preferences in DynamoDB.

        Args:
            preferences: UserPreferences object to save

        Raises:
            PreferencesStoreError: If DynamoDB operation fails
        """
        try:
            # Update timestamp
            preferences.updated_at = datetime.utcnow()

            # Convert to dict and handle datetime serialization
            item = preferences.model_dump()
            item["created_at"] = item["created_at"].isoformat()
            item["updated_at"] = item["updated_at"].isoformat()

            self.table.put_item(Item=item)
            logger.info(f"Saved preferences for user: {preferences.user_id}")

        except ClientError as e:
            error_msg = f"Failed to save preferences: {e.response['Error']['Message']}"
            logger.error(error_msg)
            raise PreferencesStoreError(error_msg) from e

    def update_favorite_driver(self, user_id: str, driver: str) -> None:
        """
        Update user's favorite driver preference.

        Args:
            user_id: Unique user identifier
            driver: Driver name or number

        Raises:
            PreferencesStoreError: If update fails
        """
        try:
            self.table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="SET favorite_driver = :driver, updated_at = :updated",
                ExpressionAttributeValues={
                    ":driver": driver,
                    ":updated": datetime.utcnow().isoformat(),
                },
            )
            logger.info(f"Updated favorite driver for {user_id} to {driver}")

        except ClientError as e:
            error_msg = f"Failed to update favorite driver: {e.response['Error']['Message']}"
            logger.error(error_msg)
            raise PreferencesStoreError(error_msg) from e

    def update_favorite_team(self, user_id: str, team: str) -> None:
        """
        Update user's favorite team preference.

        Args:
            user_id: Unique user identifier
            team: Team name

        Raises:
            PreferencesStoreError: If update fails
        """
        try:
            self.table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="SET favorite_team = :team, updated_at = :updated",
                ExpressionAttributeValues={
                    ":team": team,
                    ":updated": datetime.utcnow().isoformat(),
                },
            )
            logger.info(f"Updated favorite team for {user_id} to {team}")

        except ClientError as e:
            error_msg = f"Failed to update favorite team: {e.response['Error']['Message']}"
            logger.error(error_msg)
            raise PreferencesStoreError(error_msg) from e

    def delete_preferences(self, user_id: str) -> None:
        """
        Delete user preferences from DynamoDB.

        Args:
            user_id: Unique user identifier

        Raises:
            PreferencesStoreError: If delete fails
        """
        try:
            self.table.delete_item(Key={"user_id": user_id})
            logger.info(f"Deleted preferences for user: {user_id}")

        except ClientError as e:
            error_msg = f"Failed to delete preferences: {e.response['Error']['Message']}"
            logger.error(error_msg)
            raise PreferencesStoreError(error_msg) from e
