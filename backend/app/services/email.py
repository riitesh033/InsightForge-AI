import asyncio
import base64
import html
import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def build_password_reset_url(reset_token: str) -> str:
    """Build the frontend password-reset URL without logging the token."""
    frontend_url = urlsplit(settings.FRONTEND_URL)

    return urlunsplit(
        (
            frontend_url.scheme,
            frontend_url.netloc,
            f"{frontend_url.path.rstrip('/')}/reset-password",
            urlencode({"token": reset_token}),
            "",
        )
    )


class EmailService:
    """Transactional email service using the Brevo HTTPS API."""

    def __init__(self):
        self.api_key = settings.BREVO_API_KEY
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

        self.smtp_host = settings.SMTP_HOST.strip()
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME.strip()
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_configured = bool(
            self.smtp_host
            and self.smtp_username
            and self.smtp_password
            and self.from_email
        )

        self.missing_configuration = tuple(
            name
            for name, value in (
                ("BREVO_API_KEY", self.api_key),
                ("SMTP_FROM_EMAIL", self.from_email),
            )
            if not value
        )

        self.is_configured = bool(self.api_key and self.from_email) or self.smtp_configured

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> bool:
        """Send a transactional email through Brevo's HTTPS API."""

        recipient = to_email.strip().lower()

        if not recipient:
            logger.error("Email delivery skipped because recipient is empty.")
            return False

        if not self.api_key and self.smtp_configured:
            return await asyncio.to_thread(
                self._send_email_smtp,
                recipient,
                subject,
                html_content,
                text_content,
                attachments,
            )

        if not self.api_key or not self.from_email:
            logger.warning(
                "Email delivery skipped because neither Brevo nor SMTP "
                "is fully configured."
            )
            return False

        payload: dict = {
            "sender": {
                "name": self.from_name,
                "email": self.from_email,
            },
            "to": [
                {
                    "email": recipient,
                }
            ],
            "subject": subject,
            "htmlContent": html_content,
        }

        if text_content:
            payload["textContent"] = text_content

        if attachments:
            payload["attachment"] = [
                {
                    "name": filename,
                    "content": base64.b64encode(content).decode("ascii"),
                }
                for filename, content, _content_type in attachments
            ]

        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    BREVO_API_URL,
                    headers=headers,
                    json=payload,
                )

            if 200 <= response.status_code < 300:
                logger.info("Brevo email sent successfully.")
                return True

            logger.error(
                "Brevo email delivery failed with HTTP status %s.",
                response.status_code,
            )
            if self.smtp_configured:
                return await asyncio.to_thread(
                    self._send_email_smtp,
                    recipient,
                    subject,
                    html_content,
                    text_content,
                    attachments,
                )
            return False

        except Exception as error:
            # Never log API keys, passwords, reset tokens, or email bodies.
            logger.error(
                "Brevo email delivery failed (%s).",
                type(error).__name__,
            )
            if self.smtp_configured:
                return await asyncio.to_thread(
                    self._send_email_smtp,
                    recipient,
                    subject,
                    html_content,
                    text_content,
                    attachments,
                )
            return False

    def _send_email_smtp(
        self,
        recipient: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> bool:
        """Send email through configured SMTP when Brevo API is unavailable."""
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = recipient
        message.set_content(text_content or "Please view this message in an HTML-capable email client.")
        message.add_alternative(html_content, subtype="html")

        for filename, content, content_type in attachments or []:
            maintype, _, subtype = content_type.partition("/")
            message.add_attachment(
                content,
                maintype=maintype or "application",
                subtype=subtype or "octet-stream",
                filename=filename,
            )

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            logger.info("SMTP email sent successfully.")
            return True
        except Exception as error:
            logger.error("SMTP email delivery failed (%s).", type(error).__name__)
            return False

    async def send_registration_email(
        self,
        to_email: str,
        user_name: str,
    ) -> bool:
        """Send the account registration welcome email."""

        login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"

        html_content = (
            f"<h1>Welcome, {user_name}!</h1>"
            "<p>Your account was created successfully.</p>"
            f'<p><a href="{login_url}">Log in to InsightForge AI</a></p>'
            f"<p>If you did not create this account, contact "
            f"{settings.SUPPORT_EMAIL}.</p>"
        )

        text_content = (
            f"Welcome, {user_name}!\n\n"
            "Your account was created successfully.\n\n"
            f"Log in: {login_url}\n\n"
            f"Support: {settings.SUPPORT_EMAIL}"
        )

        return await self.send_email(
            to_email=to_email,
            subject="Welcome to InsightForge AI",
            html_content=html_content,
            text_content=text_content,
        )

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
    ) -> bool:
        """
        Send a password reset email through Brevo.

        Security:
        - Never logs the reset URL or token.
        - Never logs the API key.
        - Returns False instead of exposing delivery details.
        """

        recipient = to_email.strip().lower()

        if not recipient:
            logger.error(
                "Password reset email was not sent because "
                "the recipient email is empty."
            )
            return False

        if not self.is_configured:
            logger.warning(
                "Password reset email skipped because "
                "Brevo is not configured."
            )
            return False

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Password Reset</title>
</head>
<body
    style="
        font-family: Arial, sans-serif;
        line-height: 1.6;
        color: #333;
    "
>
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1>Reset Your Password</h1>

        <p>
            You requested a password reset for your InsightForge AI account.
        </p>

        <p>
            <a
                href="{reset_url}"
                style="
                    display: inline-block;
                    padding: 12px 24px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                "
            >
                Reset Password
            </a>
        </p>

        <p>
            This link expires in 1 hour.
        </p>

        <p>
            If you did not request this password reset,
            you can safely ignore this email.
        </p>

        <p>
            Best regards,<br>
            The InsightForge AI Team
        </p>
    </div>
</body>
</html>
"""

        text_content = (
            "You requested a password reset for your "
            "InsightForge AI account.\n\n"
            "Reset your password using this link:\n"
            f"{reset_url}\n\n"
            "This link expires in 1 hour.\n\n"
            "If you did not request this password reset, "
            "you can safely ignore this email."
        )

        return await self.send_email(
            to_email=recipient,
            subject="InsightForge AI — Password Reset",
            html_content=html_content,
            text_content=text_content,
        )

    async def send_student_verification_email(
        self,
        to_email: str,
        applicant_name: str,
        decision: str,
        reason: str | None = None,
    ) -> bool:
        """Notify a student of a review decision without attaching proof."""
        safe_name = html.escape(applicant_name)
        safe_reason = html.escape(reason or "")
        is_approved = decision == "approved"
        message = (
            "Your student verification was approved. "
            "Student Pro access is active for 365 days."
            if is_approved
            else "Your student verification application was not approved."
        )
        subject = (
            "Student verification approved"
            if is_approved
            else "Student verification update"
        )
        reason_markup = (
            f"<p>Review note: {safe_reason}</p>" if safe_reason else ""
        )
        html_content = (
            f"<p>Hello {safe_name},</p><p>{message}</p>{reason_markup}"
            "<p>Sign in to InsightForge AI to review your application status.</p>"
        )
        text_content = f"Hello {applicant_name},\n\n{message}"
        if reason:
            text_content += f"\n\nReview note: {reason}"
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

    async def send_purchase_confirmation(
        self,
        to_email: str,
        user_name: str,
        plan_type: str,
        amount: float,
        currency: str,
        transaction_id: str,
        purchase_date: str,
        features: list[str],
        attachment: tuple[str, bytes, str] | None = None,
    ) -> bool:
        """Send purchase confirmation with an optional PDF invoice."""

        recipient = to_email.strip().lower()

        subject = (
            f"Thank you for your "
            f"{plan_type.capitalize()} subscription!"
        )

        features_list = "".join(
            f"<li>{feature}</li>"
            for feature in features
        )

        dashboard_url = (
            f"{settings.FRONTEND_URL.rstrip('/')}/dashboard"
        )

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Purchase Confirmation</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }}

        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            background: linear-gradient(
                135deg,
                #667eea 0%,
                #764ba2 100%
            );
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}

        .content {{
            background: #f9f9f9;
            padding: 30px;
        }}

        .plan-box {{
            background: white;
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}

        .plan-name {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }}

        .features {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}

        .features ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}

        .features li {{
            margin: 8px 0;
        }}

        .details {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}

        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}

        .detail-row:last-child {{
            border-bottom: none;
        }}

        .button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 6px;
            margin-top: 20px;
        }}

        .footer {{
            background: #333;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 0 0 8px 8px;
            font-size: 14px;
        }}
    </style>
</head>

<body>
    <div class="container">

        <div class="header">
            <h1>🎉 Purchase Confirmed!</h1>
            <p>Thank you for subscribing to InsightForge AI</p>
        </div>

        <div class="content">

            <p>Dear {user_name},</p>

            <p>
                Thank you for your purchase!
                Your subscription has been successfully activated.
            </p>

            <div class="plan-box">
                <div class="plan-name">
                    {plan_type.capitalize()} Plan
                </div>

                <p>
                    Your subscription is now active and
                    you have access to all premium features.
                </p>
            </div>

            <div class="features">
                <h3>✨ Features Unlocked:</h3>
                <ul>
                    {features_list}
                </ul>
            </div>

            <div class="details">
                <h3>📋 Order Details:</h3>

                <div class="detail-row">
                    <span>
                        <strong>Amount Paid:</strong>
                    </span>
                    <span>
                        {currency} {amount:.2f}
                    </span>
                </div>

                <div class="detail-row">
                    <span>
                        <strong>Transaction ID:</strong>
                    </span>
                    <span>
                        {transaction_id}
                    </span>
                </div>

                <div class="detail-row">
                    <span>
                        <strong>Purchase Date:</strong>
                    </span>
                    <span>
                        {purchase_date}
                    </span>
                </div>

                <div class="detail-row">
                    <span>
                        <strong>Billing Email:</strong>
                    </span>
                    <span>
                        {recipient}
                    </span>
                </div>
            </div>

            <div style="text-align: center;">
                <a
                    href="{dashboard_url}"
                    class="button"
                >
                    Go to Dashboard
                </a>
            </div>

            <p style="margin-top: 30px;">
                <strong>What's Next?</strong>
            </p>

            <p>
                You can now access all premium features by visiting
                your dashboard.
            </p>

            <p style="margin-top: 20px;">
                If you have any questions or need assistance,
                please contact our support team at
                {settings.SUPPORT_EMAIL}.
            </p>

            <p>
                Best regards,<br>
                The InsightForge AI Team
            </p>

        </div>

        <div class="footer">
            <p>
                &copy; 2026 InsightForge AI. All rights reserved.
            </p>

            <p>
                This email was sent to {recipient}
            </p>
        </div>

    </div>
</body>
</html>
"""

        text_content = f"""
Thank you for your {plan_type.capitalize()} subscription!

Dear {user_name},

Thank you for your purchase!
Your subscription has been successfully activated.

Plan: {plan_type.capitalize()}
Amount Paid: {currency} {amount:.2f}
Transaction ID: {transaction_id}
Purchase Date: {purchase_date}

Features Unlocked:
{chr(10).join("- " + feature for feature in features)}

You can now access all premium features by visiting your dashboard.

If you have any questions, contact us at:
{settings.SUPPORT_EMAIL}

Best regards,
The InsightForge AI Team
"""

        return await self.send_email(
            to_email=recipient,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attachments=[attachment] if attachment else None,
        )


email_service = EmailService()