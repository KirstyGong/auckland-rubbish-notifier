"""ntfy.sh notification sender."""
import requests

NTFY_BASE_URL = "https://ntfy.sh"


def send_notification(title: str, message: str, topic: str) -> None:
    """
    Send a push notification via ntfy.sh.

    Args:
        title: Notification title
        message: Notification body text
        topic: ntfy.sh topic name (acts as the channel/password)

    Raises:
        Exception: If the request fails
    """
    url = f"{NTFY_BASE_URL}/{topic}"

    headers = {
        "Title": title,
        "Tags": "wastebasket",
        "Priority": "high",
    }

    response = requests.post(
        url,
        data=message,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
