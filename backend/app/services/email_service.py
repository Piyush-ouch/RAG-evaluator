"""
Email Service Adapters

Protocol-based email service with support for:
- SMTP
- SendGrid
- AWS SES
- Resend
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import structlog

from app.config import get_settings
from app.core.constants import EmailProviderType

logger = structlog.get_logger(__name__)


@dataclass
class EmailMessage:
    to_email: str
    subject: str
    body_text: str
    body_html: str | None = None
    from_email: str | None = None
    from_name: str | None = None


class BaseEmailAdapter(ABC):
    @abstractmethod
    async def send_email(self, message: EmailMessage) -> bool:
        ...


class SmtpEmailAdapter(BaseEmailAdapter):
    """SMTP Email Provider."""

    async def send_email(self, message: EmailMessage) -> bool:
        settings = get_settings()
        import aiosmtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = message.subject
        msg["From"] = f"{message.from_name or settings.email_from_name} <{message.from_email or settings.email_from_address}>"
        msg["To"] = message.to_email

        msg.attach(MIMEText(message.body_text, "plain"))
        if message.body_html:
            msg.attach(MIMEText(message.body_html, "html"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username or None,
                password=settings.smtp_password or None,
                start_tls=settings.smtp_use_tls,
            )
            logger.info("smtp_email_sent", to=message.to_email, subject=message.subject)
            return True
        except Exception as e:
            logger.error("smtp_email_failed", error=str(e), to=message.to_email)
            return False


class SendGridEmailAdapter(BaseEmailAdapter):
    """SendGrid Email Provider."""

    async def send_email(self, message: EmailMessage) -> bool:
        settings = get_settings()
        import httpx

        if not settings.sendgrid_api_key:
            logger.error("sendgrid_key_missing")
            return False

        payload = {
            "personalizations": [{"to": [{"email": message.to_email}]}],
            "from": {
                "email": message.from_email or settings.email_from_address,
                "name": message.from_name or settings.email_from_name,
            },
            "subject": message.subject,
            "content": [
                {"type": "text/plain", "value": message.body_text},
            ],
        }
        if message.body_html:
            payload["content"].append({"type": "text/html", "value": message.body_html})

        headers = {
            "Authorization": f"Bearer {settings.sendgrid_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers=headers,
                )
                if resp.status_code in (200, 202):
                    logger.info("sendgrid_email_sent", to=message.to_email)
                    return True
                logger.error("sendgrid_error", status=resp.status_code, body=resp.text)
                return False
        except Exception as e:
            logger.error("sendgrid_exception", error=str(e))
            return False


class SesEmailAdapter(BaseEmailAdapter):
    """AWS SES Email Provider."""

    async def send_email(self, message: EmailMessage) -> bool:
        settings = get_settings()
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client(
            "ses",
            region_name=settings.ses_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
        )

        destination = {"ToAddresses": [message.to_email]}
        body = {"Text": {"Data": message.body_text, "Charset": "UTF-8"}}
        if message.body_html:
            body["Html"] = {"Data": message.body_html, "Charset": "UTF-8"}

        source = f"{message.from_name or settings.email_from_name} <{message.from_email or settings.email_from_address}>"

        try:
            client.send_email(
                Source=source,
                Destination=destination,
                Message={"Subject": {"Data": message.subject, "Charset": "UTF-8"}, "Body": body},
            )
            logger.info("ses_email_sent", to=message.to_email)
            return True
        except ClientError as e:
            logger.error("ses_email_failed", error=str(e))
            return False


class ResendEmailAdapter(BaseEmailAdapter):
    """Resend Email Provider."""

    async def send_email(self, message: EmailMessage) -> bool:
        settings = get_settings()
        import httpx

        if not settings.resend_api_key:
            logger.error("resend_key_missing")
            return False

        payload = {
            "from": f"{message.from_name or settings.email_from_name} <{message.from_email or settings.email_from_address}>",
            "to": [message.to_email],
            "subject": message.subject,
            "text": message.body_text,
            "html": message.body_html or message.body_text,
        }

        headers = {
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post("https://api.resend.com/emails", json=payload, headers=headers)
                if resp.status_code in (200, 201):
                    logger.info("resend_email_sent", to=message.to_email)
                    return True
                logger.error("resend_error", status=resp.status_code, body=resp.text)
                return False
        except Exception as e:
            logger.error("resend_exception", error=str(e))
            return False


class EmailServiceFactory:
    """Email Service Factory to instantiate configured adapter."""

    @classmethod
    def get_adapter(cls) -> BaseEmailAdapter:
        settings = get_settings()
        provider = settings.email_provider.lower()

        if provider == EmailProviderType.SENDGRID.value:
            return SendGridEmailAdapter()
        elif provider == EmailProviderType.SES.value:
            return SesEmailAdapter()
        elif provider == EmailProviderType.RESEND.value:
            return ResendEmailAdapter()
        else:
            return SmtpEmailAdapter()
