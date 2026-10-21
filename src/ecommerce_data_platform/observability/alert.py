import httpx


def send_webhook_alert(webhook_url: str, message: str, timeout: int = 10):

    response = httpx.post(
        webhook_url,
        json={"text": message},
        timeout=timeout,
    )
    response.raise_for_status()