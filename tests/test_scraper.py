"""Tests for Auckland Council rubbish collection scraper."""
import pytest
from datetime import date
from unittest.mock import patch, Mock
from src.scraper import (
    fetch_session_token,
    lookup_address,
    fetch_collection_page,
    parse_collection_dates,
    CollectionEvent,
)


class TestFetchSessionToken:
    """Tests for session token acquisition."""

    def test_returns_jwt_from_server_action_response(self):
        """POSTs to server action endpoint and extracts JWT from RSC response."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = (
            '0:{"a":"$@1","f":"","b":"jZ04MegWDlhxOvfmuNvpN"}\n'
            '1:"eyJhbGciOiJIUzI1NiJ9.eyJzZXNzaW9uSWQiOiJhYmMxMjMiLCJleHAiOjk5OTk5OTk5OTl9.signature"\n'
        )

        with patch("src.scraper.requests.post", return_value=mock_response) as mock_post:
            token = fetch_session_token()

        assert token == "eyJhbGciOiJIUzI1NiJ9.eyJzZXNzaW9uSWQiOiJhYmMxMjMiLCJleHAiOjk5OTk5OTk5OTl9.signature"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "Next-Action" in call_kwargs[1]["headers"]

    def test_raises_on_failed_response(self):
        """Raises RuntimeError when server action fails."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500

        with patch("src.scraper.requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="Failed to fetch session token"):
                fetch_session_token()

    def test_raises_when_no_token_in_response(self):
        """Raises RuntimeError when response doesn't contain a JWT."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = '0:{"a":"$@1","f":"","b":"abc"}\n'

        with patch("src.scraper.requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="No token found"):
                fetch_session_token()


class TestLookupAddress:
    """Tests for address lookup API."""

    def test_returns_area_id_for_valid_street(self):
        """Given a street name, returns the area_id from first match."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {"id": "12342478585", "address": "1 Queen Street, Auckland Central"},
                {"id": "12342478586", "address": "2 Queen Street, Auckland Central"},
            ]
        }
        mock_response.raise_for_status = Mock()

        with patch("src.scraper.requests.get", return_value=mock_response) as mock_get:
            result = lookup_address("Queen Street, Auckland", "fake-token")

        assert result == "12342478585"
        mock_get.assert_called_once()
        assert "Queen Street, Auckland" in mock_get.call_args[0][0]
        assert "Bearer fake-token" in mock_get.call_args[1]["headers"]["Authorization"]

    def test_raises_error_when_no_matches(self):
        """Raises ValueError when no addresses match."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = Mock()

        with patch("src.scraper.requests.get", return_value=mock_response):
            with pytest.raises(ValueError, match="No addresses found"):
                lookup_address("Nonexistent Street", "fake-token")


class TestParseCollectionDates:
    """Tests for parsing collection dates from RSC payload."""

    SAMPLE_RSC = (
        '1e:[["$","$L2d",null,{"heading":"1 Queen Street"}],'
        '["$","$L30",null,{"icon":{"icon":"rubbish"},"children":["Rubbish: ",["$","b",null,{"children":"Monday, 14 April"}]]}],'
        '["$","$L30",null,{"icon":{"icon":"recycle"},"children":["Recycling: ",["$","b",null,{"children":"Monday, 21 April"}]]}],'
        '["$","$L30",null,{"icon":{"icon":"food-waste"},"children":["Food scraps: ",["$","b",null,{"children":"Monday, 14 April"}]]}]]'
    )

    def test_parses_rubbish_collection(self):
        """Extracts rubbish collection date."""
        events = parse_collection_dates(self.SAMPLE_RSC, year=2026)
        rubbish_events = [e for e in events if e.collection_type == "rubbish"]

        assert len(rubbish_events) == 1
        assert rubbish_events[0].collection_date == date(2026, 4, 14)

    def test_parses_recycling_collection(self):
        """Extracts recycling collection date."""
        events = parse_collection_dates(self.SAMPLE_RSC, year=2026)
        recycle_events = [e for e in events if e.collection_type == "recycle"]

        assert len(recycle_events) == 1
        assert recycle_events[0].collection_date == date(2026, 4, 21)

    def test_parses_food_waste_collection(self):
        """Extracts food waste collection date."""
        events = parse_collection_dates(self.SAMPLE_RSC, year=2026)
        food_events = [e for e in events if e.collection_type == "food-waste"]

        assert len(food_events) == 1
        assert food_events[0].collection_date == date(2026, 4, 14)

    def test_returns_empty_list_for_empty_payload(self):
        """Returns empty list when no collection info found."""
        events = parse_collection_dates("")
        assert events == []


class TestCollectionEvent:
    """Tests for CollectionEvent dataclass."""

    def test_collection_event_creation(self):
        """Can create a CollectionEvent with type and date."""
        event = CollectionEvent(
            collection_type="rubbish",
            collection_date=date(2026, 4, 14)
        )
        assert event.collection_type == "rubbish"
        assert event.collection_date == date(2026, 4, 14)
