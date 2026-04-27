"""Auckland Council rubbish collection scraper."""
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import List

import requests


@dataclass
class CollectionEvent:
    """Represents a single rubbish/recycling collection event."""
    collection_type: str
    collection_date: date


PROPERTY_API_URL = "https://experience.aucklandcouncil.govt.nz/nextapi/property"
COLLECTION_PAGE_URL = "https://experience.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days/{area_id}.html"

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-NZ,en;q=0.9",
}

RSC_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/x-component",
    "Accept-Language": "en-NZ,en;q=0.9",
    "RSC": "1",
    "Next-Router-State-Tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
}

_COLLECTION_TYPES = {"rubbish", "recycle", "food-waste"}
_RSC_DATE_PATTERN = re.compile(
    r'"icon":\{"icon":"(rubbish|recycle|food-waste)"\}[^}]*?"children":"([^"]+)"'
)


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
    response = requests.get(url, headers=API_HEADERS, timeout=30)
    response.raise_for_status()

    data = response.json()
    items = data.get("items", [])

    if not items:
        raise ValueError(f"No addresses found for: {street}")

    return items[0]["id"]


def fetch_collection_page(area_id: str) -> str:
    """
    Fetch the collection page RSC payload for a given area_id.

    Args:
        area_id: The property ID from lookup_address

    Returns:
        Raw RSC text payload of the collection page
    """
    url = COLLECTION_PAGE_URL.format(area_id=area_id)
    response = requests.get(url, headers=RSC_HEADERS, timeout=30)
    if not response.ok:
        print(f"HTTP {response.status_code} from collection page")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body (first 500 chars): {response.text[:500]}")
    response.raise_for_status()
    return response.text


def parse_collection_dates(rsc_text: str, year: int = None) -> List[CollectionEvent]:
    """
    Parse collection dates from Auckland Council RSC payload.

    Args:
        rsc_text: RSC text/x-component payload from fetch_collection_page
        year: Year for date parsing (defaults to current year)

    Returns:
        List of CollectionEvent objects
    """
    if year is None:
        year = datetime.now().year

    seen = set()
    events = []

    for collection_type, date_text in _RSC_DATE_PATTERN.findall(rsc_text):
        key = (collection_type, date_text)
        if key in seen:
            continue
        seen.add(key)

        try:
            date_part = date_text.split(", ", 1)[1] if ", " in date_text else date_text
            parsed_date = datetime.strptime(f"{date_part} {year}", "%d %B %Y").date()
            events.append(CollectionEvent(
                collection_type=collection_type,
                collection_date=parsed_date,
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
    rsc_text = fetch_collection_page(area_id)
    return parse_collection_dates(rsc_text)
