"""Auckland Council rubbish collection scraper."""
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import List

import requests
from bs4 import BeautifulSoup


@dataclass
class CollectionEvent:
    """Represents a single rubbish/recycling collection event."""
    collection_type: str
    collection_date: date


PROPERTY_API_URL = "https://experience.aucklandcouncil.govt.nz/nextapi/property"
COLLECTION_PAGE_URL = "https://www.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days/{area_id}.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-NZ,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}


def lookup_address(street: str) -> str:
    """
    Look up area_id from street name using Auckland Council API.

    Args:
        street: Street name and suburb (e.g., "Queen Street, Auckland")

    Returns:
        area_id: The property ID used for collection lookups

    Raises:
        ValueError: If no matching addresses found
    """
    url = f"{PROPERTY_API_URL}?query={street}&pageSize=10"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    data = response.json()
    items = data.get("items", [])

    if not items:
        raise ValueError(f"No addresses found for: {street}")

    return items[0]["id"]


def fetch_collection_page(area_id: str) -> str:
    """
    Fetch the collection page HTML for a given area_id.

    Args:
        area_id: The property ID from lookup_address

    Returns:
        Raw HTML string of the collection page
    """
    url = COLLECTION_PAGE_URL.format(area_id=area_id)
    response = requests.get(url, headers=HEADERS, timeout=30)
    if not response.ok:
        print(f"HTTP {response.status_code} from collection page")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body (first 500 chars): {response.text[:500]}")
    response.raise_for_status()
    return response.text


def parse_collection_dates(html: str, year: int = None) -> List[CollectionEvent]:
    """
    Parse collection dates from Auckland Council HTML.

    Args:
        html: Raw HTML from fetch_collection_page
        year: Year for date parsing (defaults to current year)

    Returns:
        List of CollectionEvent objects
    """
    if year is None:
        year = datetime.now().year

    soup = BeautifulSoup(html, "html.parser")
    events = []

    # Find all collection entries
    for p in soup.find_all("p", class_="mb-0 lead"):
        # Find the icon element (i tag with acpl-icon class)
        icon = p.find("i", class_="acpl-icon")
        date_elem = p.find("b")

        if not icon or not date_elem:
            continue

        # Extract collection type from class
        classes = icon.get("class", [])
        collection_type = None
        for cls in classes:
            if cls in ("rubbish", "recycle", "food-waste"):
                collection_type = cls
                break

        if not collection_type:
            continue

        # Parse date from format "Monday, 14 April"
        date_text = date_elem.get_text(strip=True)
        try:
            # Remove day name, parse "14 April"
            date_part = date_text.split(", ", 1)[1] if ", " in date_text else date_text
            parsed_date = datetime.strptime(f"{date_part} {year}", "%d %B %Y").date()

            events.append(CollectionEvent(
                collection_type=collection_type,
                collection_date=parsed_date
            ))
        except (ValueError, IndexError):
            continue

    return events


def get_collections_for_street(street: str) -> List[CollectionEvent]:
    """
    Convenience function: look up street and get collection dates.

    Args:
        street: Street name and suburb

    Returns:
        List of upcoming CollectionEvent objects
    """
    area_id = lookup_address(street)
    html = fetch_collection_page(area_id)
    return parse_collection_dates(html)
