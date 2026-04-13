"""Main orchestrator for Auckland rubbish collection notifier."""
import json
import os
import sys
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from src.scraper import get_collections_for_street, CollectionEvent
from src.notifier import send_notification


@dataclass
class UserConfig:
    """Configuration for a single user."""
    name: str
    street: str
    topic: str
    notify_hour: int = 17


def load_users_config() -> list[UserConfig]:
    """
    Load user configuration from USERS_CONFIG environment variable.

    Returns:
        List of UserConfig objects

    Raises:
        ValueError: If USERS_CONFIG is not set, invalid JSON, or missing fields
    """
    users_json = os.environ.get("USERS_CONFIG")

    if not users_json:
        raise ValueError("USERS_CONFIG environment variable not set")

    try:
        data = json.loads(users_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"USERS_CONFIG is not valid JSON: {e}")

    if not isinstance(data, list):
        raise ValueError("USERS_CONFIG must be a JSON array")

    users = []
    for i, u in enumerate(data):
        for field in ("name", "street", "topic"):
            if field not in u:
                raise ValueError(f"User {i} missing required field: {field}")
        users.append(UserConfig(
            name=u["name"],
            street=u["street"],
            topic=u["topic"],
            notify_hour=u.get("notify_hour", 17)
        ))

    return users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_tomorrows_collections(events: list[CollectionEvent]) -> list[CollectionEvent]:
    """Filter events to only those occurring tomorrow."""
    tomorrow = date.today() + timedelta(days=1)
    return [e for e in events if e.collection_date == tomorrow]


def format_collection_types(events: list[CollectionEvent]) -> str:
    """Format collection types into readable string with emojis."""
    type_names = {
        "rubbish": "🔴 Rubbish",
        "recycle": "♻️ Recycling",
        "food-waste": "🥗 Food Scraps",
    }
    types = [type_names.get(e.collection_type, e.collection_type) for e in events]
    return ", ".join(types)


def is_user_notification_hour(user: UserConfig) -> tuple[bool, int, int]:
    """
    Check if current NZT hour matches user's configured notification hour.

    Returns:
        Tuple of (is_correct_hour, current_hour, configured_hour)
    """
    nzt = ZoneInfo("Pacific/Auckland")
    current_hour = datetime.now(nzt).hour
    return current_hour == user.notify_hour, current_hour, user.notify_hour


def process_user(user: UserConfig, test_mode: bool) -> tuple[str, bool, str]:
    """
    Process notifications for a single user.

    Args:
        user: User configuration
        test_mode: If True, send test notification regardless of date

    Returns:
        Tuple of (user_name, success, message)
    """
    try:
        # In test mode, skip hour check and send test notification
        if test_mode:
            send_notification(
                title="Test: Bin Day Notification",
                message="This is a test notification. Your setup is working!",
                topic=user.topic
            )
            return (user.name, True, "Test notification sent")

        # Check if it's the right hour
        is_right_hour, current_hour, configured_hour = is_user_notification_hour(user)
        if not is_right_hour:
            return (user.name, True, f"Skipped - hour {current_hour}, configured {configured_hour}")

        # Fetch collections
        events = get_collections_for_street(user.street)
        tomorrows_events = get_tomorrows_collections(events)

        if not tomorrows_events:
            return (user.name, True, "No collections tomorrow")

        # Send notification for tomorrow's collection
        collection_types = format_collection_types(tomorrows_events)
        send_notification(
            title="Bin Day Tomorrow",
            message=f"Put out: {collection_types}",
            topic=user.topic
        )
        return (user.name, True, f"Tomorrow: {collection_types}")

    except Exception as e:
        return (user.name, False, f"Error: {e}")


def main() -> int:
    """
    Main entry point - processes all users.

    Returns:
        0 if at least one user succeeded, 1 if all failed
    """
    test_mode = os.environ.get("TEST_MODE", "").lower() == "true"

    try:
        users = load_users_config()
    except ValueError as e:
        logger.error(str(e))
        return 1

    logger.info(f"Processing {len(users)} user(s)")

    results = []
    for user in users:
        name, success, message = process_user(user, test_mode)
        results.append((name, success, message))
        logger.info(f"[{name}] {message}")

    # Return 1 only if ALL users failed
    if all(not success for _, success, _ in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
