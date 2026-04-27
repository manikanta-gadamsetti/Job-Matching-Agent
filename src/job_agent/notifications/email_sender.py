from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from job_agent.models import EmailNotificationConfig, JobDigest


def send_email_digest(config: EmailNotificationConfig, password: str, digest: JobDigest) -> None:
    if not password:
        raise ValueError(f"Missing SMTP password in env var {config.smtp_password_env}")

    message = MIMEMultipart("alternative")
    message["Subject"] = "New matching jobs for you"
    message["From"] = config.from_address
    message["To"] = ", ".join(config.to_addresses)
    message.attach(MIMEText(digest.message_text, "plain", "utf-8"))
    message.attach(MIMEText(digest.message_html, "html", "utf-8"))

    with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
        server.starttls()
        server.login(config.smtp_username, password)
        server.sendmail(config.from_address, config.to_addresses, message.as_string())
