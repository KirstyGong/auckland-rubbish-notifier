"""Tests for Auckland Council rubbish collection scraper."""
import pytest
from datetime import date
from unittest.mock import patch, Mock
from src.scraper import (
    lookup_address,
    fetch_collection_page,
    parse_collection_dates,
    CollectionEvent,
)


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
            result = lookup_address("Queen Street, Auckland")

        assert result == "12342478585"
        mock_get.assert_called_once()
        assert "Queen Street, Auckland" in mock_get.call_args[0][0]

    def test_raises_error_when_no_matches(self):
        """Raises ValueError when no addresses match."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = Mock()

        with patch("src.scraper.requests.get", return_value=mock_response):
            with pytest.raises(ValueError, match="No addresses found"):
                lookup_address("Nonexistent Street")


class TestParseCollectionDates:
    """Tests for parsing collection dates from HTML."""

    SAMPLE_HTML = """
    <html>
    <body>
        <div class="acpl-schedule-card">
            <p class="mb-0 lead">
                <span class="acpl-icon-with-attribute left">
                    <i class="acpl-icon rubbish"></i>
                    <span>Rubbish: <b>Monday, 14 April</b></span>
                </span>
            </p>
            <p class="mb-0 lead">
                <span class="acpl-icon-with-attribute left">
                    <i class="acpl-icon recycle"></i>
                    <span>Recycling: <b>Monday, 21 April</b></span>
                </span>
            </p>
            <p class="mb-0 lead">
                <span class="acpl-icon-with-attribute left">
                    <i class="acpl-icon food-waste"></i>
                    <span>Food scraps: <b>Monday, 14 April</b></span>
                </span>
            </p>
        </div>
    </body>
    </html>
    """

    def test_parses_rubbish_collection(self):
        """Extracts rubbish collection date."""
        events = parse_collection_dates(self.SAMPLE_HTML, year=2026)
        rubbish_events = [e for e in events if e.collection_type == "rubbish"]

        assert len(rubbish_events) == 1
        assert rubbish_events[0].collection_date == date(2026, 4, 14)

    def test_parses_recycling_collection(self):
        """Extracts recycling collection date."""
        events = parse_collection_dates(self.SAMPLE_HTML, year=2026)
        recycle_events = [e for e in events if e.collection_type == "recycle"]

        assert len(recycle_events) == 1
        assert recycle_events[0].collection_date == date(2026, 4, 21)

    def test_parses_food_waste_collection(self):
        """Extracts food waste collection date."""
        events = parse_collection_dates(self.SAMPLE_HTML, year=2026)
        food_events = [e for e in events if e.collection_type == "food-waste"]

        assert len(food_events) == 1
        assert food_events[0].collection_date == date(2026, 4, 14)

    def test_returns_empty_list_for_empty_html(self):
        """Returns empty list when no collection info found."""
        events = parse_collection_dates("<html></html>")
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
