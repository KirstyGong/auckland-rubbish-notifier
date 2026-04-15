# Auckland Rubbish Collection Notifier

Automated push notifications for Auckland Council rubbish/recycling collection days.

## How It Works

1. GitHub Actions runs hourly (7am-10pm NZT window), notifies at your configured hour (default: 5pm)
2. Scrapes Auckland Council website for your collection dates
3. If tomorrow is a collection day, sends "Bin Day Tomorrow" notification via ntfy.sh

## Setup

### 1. Install ntfy app

- **iOS**: [App Store](https://apps.apple.com/app/ntfy/id1625396347)
- **Android**: [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy)

Subscribe to a secret topic name (e.g., `my-rubbish-x7k9m`).

### 2. Fork this repository

Fork to your own GitHub account.

### 3. Add secret

Go to Settings > Secrets and variables > Actions > New repository secret:

| Secret | Description |
|--------|-------------|
| `USERS_CONFIG` | JSON array of users (see below) |

**USERS_CONFIG format:**

```json
[
  {"name": "me", "street": "Queen Street, Ponsonby", "topic": "my-bins-xyz"},
  {"name": "friend", "street": "Victoria Road, Devonport", "topic": "friend-bins-abc", "notify_hour": 18}
]
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Identifier for logging |
| `street` | Yes | Street + suburb (no house number) |
| `topic` | Yes | ntfy.sh topic name |
| `notify_hour` | No | Hour to notify in NZT (default: 17 / 5pm) |

### 4. Test

Go to Actions > "Rubbish Collection Notifier" > Run workflow.

Check your phone for the notification.

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Test locally
export USERS_CONFIG='[{"name": "test", "street": "Queen Street, Auckland", "topic": "test-topic"}]'
python -m src.main
```

## Privacy

- Your street name is stored encrypted in GitHub Secrets
- No house number required (all houses on same street share collection day)
- ntfy.sh topic name acts as a password (make it unguessable)
