from __future__ import annotations

import os

from job_agent.models import JobDigest, NotificationConfig
from job_agent.notifications.email_sender import send_email_digest
from job_agent.notifications.whatsapp_sender import send_whatsapp_digest


class NotificationDispatcher:
    def __init__(self, config: NotificationConfig) -> None:
        self.config = config

    def send(self, digest: JobDigest) -> None:
        if self.config.email.enabled:
            password = os.environ.get(self.config.email.smtp_password_env, "")
            send_email_digest(self.config.email, password, digest)

        if self.config.whatsapp.enabled:
            account_sid = os.environ.get(self.config.whatsapp.account_sid_env, "")
            auth_token = os.environ.get(self.config.whatsapp.auth_token_env, "")
            send_whatsapp_digest(self.config.whatsapp, account_sid, auth_token, digest)
