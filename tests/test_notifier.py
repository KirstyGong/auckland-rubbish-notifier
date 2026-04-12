"""Tests for ntfy.sh notifier."""
import pytest
from unittest.mock import patch, Mock
from src.notifier import send_notification


class TestSendNotification:
    """Tests for sending notifications via ntfy.sh."""

    def test_sends_post_request_to_ntfy(self):
        """Sends POST to correct ntfy.sh URL."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch("src.notifier.requests.post", return_value=mock_response) as mock_post:
            send_notification(
                title="Bin Day Today",
                message="Put out: Rubbish",
                topic="test-topic-123"
            )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://ntfy.sh/test-topic-123"

    def test_includes_title_in_headers(self):
        """Title is sent in request headers."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch("src.notifier.requests.post", return_value=mock_response) as mock_post:
            send_notification(
                title="Bin Day Today",
                message="Put out: Rubbish",
                topic="test-topic"
            )

        headers = mock_post.call_args[1]["headers"]
        assert headers["Title"] == "Bin Day Today"

    def test_includes_message_in_body(self):
        """Message is sent as request body."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch("src.notifier.requests.post", return_value=mock_response) as mock_post:
            send_notification(
                title="Bin Day",
                message="Put out: Rubbish, Recycling",
                topic="test-topic"
            )

        assert mock_post.call_args[1]["data"] == "Put out: Rubbish, Recycling"

    def test_includes_tags_for_emoji(self):
        """Includes wastebasket tag for emoji."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch("src.notifier.requests.post", return_value=mock_response) as mock_post:
            send_notification(
                title="Bin Day",
                message="Rubbish",
                topic="test-topic"
            )

        headers = mock_post.call_args[1]["headers"]
        assert "wastebasket" in headers["Tags"]

    def test_raises_on_request_failure(self):
        """Raises exception when ntfy.sh request fails."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Network error")

        with patch("src.notifier.requests.post", return_value=mock_response):
            with pytest.raises(Exception, match="Network error"):
                send_notification("Title", "Message", "topic")
