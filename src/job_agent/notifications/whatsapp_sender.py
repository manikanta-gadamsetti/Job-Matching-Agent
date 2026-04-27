from __future__ import annotations

from twilio.rest import Client

from job_agent.models import JobDigest, WhatsAppNotificationConfig


def send_whatsapp_digest(
    config: WhatsAppNotificationConfig,
    account_sid: str,
    auth_token: str,
    digest: JobDigest,
) -> None:
    if not account_sid or not auth_token:
        raise ValueError("Missing Twilio credentials for WhatsApp delivery.")

    client = Client(account_sid, auth_token)
    for number in config.to_numbers:
        client.messages.create(
            from_=config.from_number,
            to=number,
            body=digest.message_text[:1500],
        )
