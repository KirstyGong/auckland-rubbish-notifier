# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run single test
pytest tests/test_scraper.py::TestParseCollectionDates::test_parses_rubbish_collection -v

# Run locally
export USERS_CONFIG='test|123 Queen Street, Auckland|test-topic'
python -m src.main
```

## Architecture

Three-module pipeline orchestrated by GitHub Actions (`.github/workflows/notify.yml`):

1. **scraper.py** - Fetches collection dates from Auckland Council
   - `lookup_address(street)` -> area_id via council API
   - `fetch_collection_page(area_id)` -> HTML
   - `parse_collection_dates(html)` -> `List[CollectionEvent]`

2. **notifier.py** - Sends push notifications via ntfy.sh
   - `send_notification(title, message, topic)`

3. **main.py** - Orchestrator
   - Checks if current NZT hour matches `NOTIFY_HOUR`
   - Filters events to today's date
   - Sends notification if collection day

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `USERS_CONFIG` | Yes | Pipe-delimited users: `name\|street\|topic\|hour` (see README) |
| `TEST_MODE` | No | Set "true" to bypass date check |

## External APIs

- **Auckland Council Property API**: `experience.aucklandcouncil.govt.nz/nextapi/property`
- **Collection Page**: `aucklandcouncil.govt.nz/.../rubbish-recycling-collection-days/{area_id}.html`
- **ntfy.sh**: `ntfy.sh/{topic}` for push notifications
