"""Tests for main orchestrator multi-user support."""
import pytest
from unittest.mock import patch, Mock
from datetime import date, timedelta

from src.main import UserConfig, process_user, get_tomorrows_collections
from src.scraper import CollectionEvent


class TestLoadUsersConfig:
    """Tests for loading user configuration from USERS_CONFIG env var."""

    def test_parses_single_user(self):
        """Given one user line, returns list with one UserConfig."""
        from src.main import load_users_config

        config = "test|Queen Street, Auckland|test-topic"

        with patch.dict("os.environ", {"USERS_CONFIG": config}, clear=True):
            users = load_users_config()

        assert len(users) == 1
        assert users[0].name == "test"
        assert users[0].street == "Queen Street, Auckland"
        assert users[0].topic == "test-topic"
        assert users[0].notify_hour == 17  # default

    def test_parses_multiple_users(self):
        """Given multiple user lines, returns all UserConfigs."""
        from src.main import load_users_config

        config = """user1|Street 1|topic1
user2|Street 2|topic2|18"""

        with patch.dict("os.environ", {"USERS_CONFIG": config}, clear=True):
            users = load_users_config()

        assert len(users) == 2
        assert users[0].name == "user1"
        assert users[0].notify_hour == 17
        assert users[1].name == "user2"
        assert users[1].notify_hour == 18

    def test_raises_error_for_too_few_fields(self):
        """Given line with fewer than 3 fields, raises ValueError."""
        from src.main import load_users_config

        with patch.dict("os.environ", {"USERS_CONFIG": "name|street"}, clear=True):
            with pytest.raises(ValueError, match="expected at least 3 fields"):
                load_users_config()

    def test_raises_error_for_invalid_hour(self):
        """Given non-numeric hour, raises ValueError."""
        from src.main import load_users_config

        with patch.dict("os.environ", {"USERS_CONFIG": "name|street|topic|abc"}, clear=True):
            with pytest.raises(ValueError, match="notify_hour must be a number"):
                load_users_config()

    def test_raises_error_when_env_var_not_set(self):
        """Given no USERS_CONFIG env var, raises ValueError."""
        from src.main import load_users_config

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="USERS_CONFIG.*not set"):
                load_users_config()

    def test_skips_empty_lines(self):
        """Given empty lines in config, skips them."""
        from src.main import load_users_config

        config = """user1|Street 1|topic1

user2|Street 2|topic2"""

        with patch.dict("os.environ", {"USERS_CONFIG": config}, clear=True):
            users = load_users_config()

        assert len(users) == 2


class TestProcessUser:
    """Tests for processing a single user's notifications."""

    def test_sends_notification_when_collection_tomorrow(self):
        """Given collection tomorrow, sends notification and returns success."""
        user = UserConfig(name="test", street="Queen St", topic="test-topic")
        tomorrow = date.today() + timedelta(days=1)
        events = [CollectionEvent(collection_type="rubbish", collection_date=tomorrow)]

        with patch("src.main.get_collections_for_street", return_value=events), \
             patch("src.main.send_notification") as mock_notify, \
             patch("src.main.is_user_notification_hour", return_value=(True, 17, 17)):
            name, success, message = process_user(user, test_mode=False)

        assert success is True
        assert "Rubbish" in message
        mock_notify.assert_called_once()

    def test_skips_when_not_notification_hour(self):
        """Given wrong hour, skips and returns success."""
        user = UserConfig(name="test", street="Queen St", topic="test-topic", notify_hour=17)

        with patch("src.main.is_user_notification_hour", return_value=(False, 10, 17)):
            name, success, message = process_user(user, test_mode=False)

        assert success is True
        assert "Skipped" in message

    def test_returns_no_collections_message(self):
        """Given no collections tomorrow, returns appropriate message."""
        user = UserConfig(name="test", street="Queen St", topic="test-topic")

        with patch("src.main.get_collections_for_street", return_value=[]), \
             patch("src.main.is_user_notification_hour", return_value=(True, 17, 17)):
            name, success, message = process_user(user, test_mode=False)

        assert success is True
        assert "No collections tomorrow" in message

    def test_sends_test_notification_in_test_mode(self):
        """Given test_mode=True, sends test notification regardless of date."""
        user = UserConfig(name="test", street="Queen St", topic="test-topic")

        with patch("src.main.get_collections_for_street", return_value=[]), \
             patch("src.main.send_notification") as mock_notify:
            name, success, message = process_user(user, test_mode=True)

        assert success is True
        assert "Test" in message
        mock_notify.assert_called_once()

    def test_returns_failure_on_exception(self):
        """Given scraper error, returns failure without raising."""
        user = UserConfig(name="test", street="Bad St", topic="test-topic")

        with patch("src.main.get_collections_for_street", side_effect=Exception("API error")), \
             patch("src.main.is_user_notification_hour", return_value=(True, 17, 17)):
            name, success, message = process_user(user, test_mode=False)

        assert success is False
        assert "Error" in message
        assert name == "test"

class TestGetTomorrowsCollections:
    """Tests for filtering collections to tomorrow (NZT)."""

    def test_returns_events_for_tomorrow(self):
        """Given events including tomorrow (NZT), returns only tomorrow's events."""
        fixed_nzt_today = date(2026, 4, 21)
        fixed_nzt_tomorrow = date(2026, 4, 22)
        events = [
            CollectionEvent(collection_type="rubbish", collection_date=fixed_nzt_today),
            CollectionEvent(collection_type="recycle", collection_date=fixed_nzt_tomorrow),
        ]

        with patch("src.main.datetime") as mock_dt:
            mock_dt.now.return_value.date.return_value = fixed_nzt_today
            result = get_tomorrows_collections(events)

        assert len(result) == 1
        assert result[0].collection_type == "recycle"
        assert result[0].collection_date == fixed_nzt_tomorrow

    def test_returns_empty_when_no_tomorrow_events(self):
        """Given no events tomorrow (NZT), returns empty list."""
        fixed_nzt_today = date(2026, 4, 21)
        events = [CollectionEvent(collection_type="rubbish", collection_date=fixed_nzt_today)]

        with patch("src.main.datetime") as mock_dt:
            mock_dt.now.return_value.date.return_value = fixed_nzt_today
            result = get_tomorrows_collections(events)

        assert result == []
