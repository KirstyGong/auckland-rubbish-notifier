# Auckland Rubbish Collection Notifier

Automated push notifications for Auckland Council rubbish/recycling collection days.

## How It Works

1. GitHub Actions runs daily at 5pm NZT
2. Scrapes Auckland Council website for your collection dates
3. If today is a collection day, sends push notification via ntfy.sh

## Setup

### 1. Install ntfy app

- **iOS**: [App Store](https://apps.apple.com/app/ntfy/id1625396347)
- **Android**: [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy)

Subscribe to a secret topic name (e.g., `my-rubbish-x7k9m`).

### 2. Fork this repository

Fork to your own GitHub account.

### 3. Add secrets

Go to Settings > Secrets and variables > Actions > New repository secret:

| Secret | Description | Example |
|--------|-------------|---------|
| `AUCKLAND_STREET` | Your street + suburb (no house number) | `Queen Street, Ponsonby` |
| `NTFY_TOPIC` | Your ntfy.sh topic name | `my-rubbish-x7k9m` |

### 4. Test

Go to Actions > "Rubbish Collection Notifier" > Run workflow.

Check your phone for the notification.

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Test locally (set env vars first)
export AUCKLAND_STREET="Queen Street, Auckland"
export NTFY_TOPIC="test-topic"
python -m src.main
```

## Privacy

- Your street name is stored encrypted in GitHub Secrets
- No house number required (all houses on same street share collection day)
- ntfy.sh topic name acts as a password (make it unguessable)
