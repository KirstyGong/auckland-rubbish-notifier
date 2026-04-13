"""Main orchestrator for Auckland rubbish collection notifier."""
import os
import sys
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from src.scraper import get_collections_for_street, CollectionEvent
from src.notifier import send_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_todays_collections(events: list[CollectionEvent]) -> list[CollectionEvent]:
    """Filter events to only those occurring today."""
    today = date.today()
    return [e for e in events if e.collection_date == today]


def is_notification_hour() -> tuple[bool, int, int]:
    """
    Check if current NZT hour matches configured notification hour.

    Returns:
        Tuple of (is_correct_hour, current_hour, configured_hour)
    """
    notify_hour = int(os.environ.get("NOTIFY_HOUR", "17"))
    nzt = ZoneInfo("Pacific/Auckland")
    current_hour = datetime.now(nzt).hour
    return current_hour == notify_hour, current_hour, notify_hour


def format_collection_types(events: list[CollectionEvent]) -> str:
    """Format collection types into readable string."""
    type_names = {
        "rubbish": "Rubbish",
        "recycle": "Recycling",
        "food-waste": "Food Scraps",
    }
    types = [type_names.get(e.collection_type, e.collection_type) for e in events]
    return ", ".join(types)


def main() -> int:
    """
    Main entry point.

    Fetches collection dates, checks if any are today,
    and sends notification if so.

    Returns:
        0 on success, 1 on error
    """
    # Load configuration from environment
    street = os.environ.get("AUCKLAND_STREET")
    topic = os.environ.get("NTFY_TOPIC")
    test_mode = os.environ.get("TEST_MODE", "").lower() == "true"

    if not street:
        logger.error("AUCKLAND_STREET environment variable not set")
        return 1

    if not topic:
        logger.error("NTFY_TOPIC environment variable not set")
        return 1

    # Check if it's the right hour to notify (skip in test mode)
    if not test_mode:
        is_right_hour, current_hour, configured_hour = is_notification_hour()
        if not is_right_hour:
            logger.info(f"Skipping - current hour {current_hour} NZT, configured hour {configured_hour} NZT")
            return 0

    try:
        # Fetch collection dates
        logger.info(f"Fetching collections for: {street}")
        events = get_collections_for_street(street)
        logger.info(f"Found {len(events)} upcoming collections")

        # Check if any collections are today
        todays_events = get_todays_collections(events)

        if test_mode:
            logger.info("TEST MODE: Sending test notification")
            send_notification(
                title="Test: Bin Day Notification",
                message="This is a test notification. Your setup is working!",
                topic=topic
            )
            logger.info("Test notification sent successfully")
            return 0

        if not todays_events:
            logger.info("No collections today")
            return 0

        # Send notification
        collection_types = format_collection_types(todays_events)
        logger.info(f"Collections today: {collection_types}")

        send_notification(
            title="Bin Day Today",
            message=f"Put out: {collection_types}",
            topic=topic
        )
        logger.info("Notification sent successfully")

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
