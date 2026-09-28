import base64
import logging
from typing import Optional
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def build_password_reset_url(reset_token: str) -> str:
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
    """Transactional email service using the Brevo HTTPS API.

    The Brevo API key is loaded from BREVO_API_KEY.
    SMTP credentials are not used for email delivery.
    """

    def __init__(self):
        self.api_key = settings.BREVO_API_KEY
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

        self.missing_configuration = tuple(
            name
            for name, value in (
                ("BREVO_API_KEY", self.api_key),
                ("SMTP_FROM_EMAIL", self.from_email),
            )
            if not value
        )

        self.is_configured = not self.missing_configuration

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> bool:
        """Send a transactional email through Brevo's HTTPS API."""

        if not self.is_configured:
            logger.warning(
                "Brevo email skipped; missing configuration: %s",
                ", ".join(self.missing_configuration),
            )
            return False

        payload: dict = {
            "sender": {
                "name": self.from_name,
                "email": self.from_email,
            },
            "to": [
                {
                    "email": to_email,
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

            # Do not log the response body because it could contain
            # information that should not appear in application logs.
            logger.error(
                "Brevo email delivery failed with HTTP status %s.",
                response.status_code,
            )
            return False

        except Exception as error:
            # Never log the API key, password, reset token, or email body.
            logger.error(
                "Brevo email delivery failed (%s).",
                type(error).__name__,
            )
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
    ) -> None:
        """Send password reset email.

        The reset URL is sent to the recipient but is never written to logs.
        """

        if not self.is_configured:
            logger.warning(
                "Brevo password-reset email skipped; missing configuration: %s",
                ", ".join(self.missing_configuration),
            )
            return

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Password Reset</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h1>Reset Your Password</h1>

    <p>You requested a password reset for your InsightForge AI account.</p>

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

    <p>This link expires in 1 hour.</p>

    <p>
        If you did not request this password reset,
        you can safely ignore this email.
    </p>
</body>
</html>
"""

        text_content = (
            "You requested a password reset for your InsightForge AI account.\n\n"
            f"Reset your password using this link:\n{reset_url}\n\n"
            "This link expires in 1 hour.\n\n"
            "If you did not request this password reset, "
            "you can safely ignore this email."
        )

        delivered = await self.send_email(
            to_email=to_email,
            subject="InsightForge AI — Password Reset",
            html_content=html_content,
            text_content=text_content,
        )

        if not delivered:
            raise RuntimeError("Password reset email delivery failed.")

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
        """Send purchase confirmation with optional PDF invoice attachment."""

        subject = (
            f"Thank you for your {plan_type.capitalize()} subscription!"
        )

        features_list = "".join(
            f"<li>{feature}</li>"
            for feature in features
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
                        {to_email}
                    </span>
                </div>
            </div>

            <div style="text-align: center;">
                <a
                    href="{settings.FRONTEND_URL.rstrip('/')}/dashboard"
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
                This email was sent to {to_email}
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
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attachments=[attachment] if attachment else None,
        )

    async def send_password_reset(
        self,
        to_email: str,
        user_name: str,
        reset_token: str,
    ) -> bool:
        """Send password reset email."""

        reset_link = build_password_reset_url(reset_token)

        subject = "Reset Your Password - InsightForge AI"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Password Reset</title>

    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
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

        .button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
        }}

        .warning {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
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
            <h1>🔐 Password Reset Request</h1>
        </div>

        <div class="content">

            <p>Dear {user_name},</p>

            <p>
                We received a request to reset your password.
                Click the button below to reset it:
            </p>

            <div style="text-align: center;">
                <a href="{reset_link}" class="button">
                    Reset Password
                </a>
            </div>

            <p>
                Or copy and paste this link into your browser:
            </p>

            <p style="word-break: break-all; color: #667eea;">
                {reset_link}
            </p>

            <div class="warning">
                <strong>⚠️ Important:</strong>
                This link will expire in 1 hour.
                If you did not request this password reset,
                please ignore this email.
            </div>

            <p>
                Best regards,<br>
                The InsightForge AI Team
            </p>

        </div>

        <div class="footer">
            <p>
                &copy; 2026 InsightForge AI. All rights reserved.
            </p>
        </div>

    </div>
</body>
</html>
"""

        text_content = f"""
Password Reset Request

Dear {user_name},

We received a request to reset your password.

Visit the link below to reset your password:

{reset_link}

This link will expire in 1 hour.

If you did not request this password reset,
please ignore this email.

Best regards,
The InsightForge AI Team
"""

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )


# Global email service instance
email_service = EmailService()