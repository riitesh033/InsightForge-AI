import logging
import asyncio
from typing import Optional
from urllib.parse import urlencode, urlsplit, urlunsplit

from app.core.config import settings

logger = logging.getLogger(__name__)


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
    """Email service for sending transactional emails.

    Configuration comes exclusively from the application settings
    (Pydantic BaseSettings backed by environment variables / .env).
    No credentials are ever hard-coded.
    """

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.missing_configuration = tuple(
            name
            for name, value in (
                ("SMTP_HOST", self.smtp_host),
                ("SMTP_USERNAME", self.smtp_user),
                ("SMTP_PASSWORD", self.smtp_password),
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
        """Send an email to the specified recipient."""
        if not self.is_configured:
            logger.warning(
                "SMTP email skipped; missing configuration: %s",
                ", ".join(self.missing_configuration),
            )
            return False

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        if text_content:
            msg.attach(MIMEText(text_content, "plain"))

        msg.attach(MIMEText(html_content, "html"))
        if attachments:
            from email.mime.base import MIMEBase
            from email import encoders
            for filename, content, content_type in attachments:
                maintype, subtype = content_type.split("/", 1)
                part = MIMEBase(maintype, subtype)
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition", "attachment", filename=filename
                )
                msg.attach(part)

        return await asyncio.to_thread(self._send_message, msg)

    def _send_message(self, message) -> bool:
        import smtplib

        try:
            with smtplib.SMTP(
                self.smtp_host,
                self.smtp_port,
                timeout=10,
            ) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            return True
        except Exception as error:
            logger.error(
                "SMTP email delivery failed (%s)",
                type(error).__name__,
            )
            return False

    async def send_registration_email(self, to_email: str, user_name: str) -> bool:
        login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
        return await self.send_email(
            to_email,
            "Welcome to InsightForge AI",
            f"<h1>Welcome, {user_name}!</h1><p>Your account was created successfully.</p>"
            f'<p><a href="{login_url}">Log in to InsightForge AI</a></p>'
            f"<p>If you did not create this account, contact {settings.SUPPORT_EMAIL}.</p>",
            f"Welcome, {user_name}!\n\nYour account was created successfully.\n"
            f"Log in: {login_url}\n\nSupport: {settings.SUPPORT_EMAIL}",
        )

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
    ) -> None:
        """Send a password reset email. No-op if SMTP is not configured.

        Raises on SMTP transport failure so callers can log it; the reset
        URL/token itself is never logged.
        """
        if not self.is_configured:
            logger.warning(
                "SMTP password-reset email skipped; missing configuration: %s",
                ", ".join(self.missing_configuration),
            )
            return

        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = "InsightForge AI — Password Reset"
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email
        msg.set_content(
            f"Hello,\n\nYou requested a password reset.\n\n"
            f"Open this link to reset your password:\n{reset_url}\n\n"
            f"This link expires in 1 hour.\n"
            f"If you did not request this, ignore this email.\n"
        )

        delivered = await asyncio.to_thread(self._send_message, msg)
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
        """Send purchase confirmation email."""
        subject = f"Thank you for your {plan_type.capitalize()} subscription!"

        features_list = "".join([f"<li>{feature}</li>" for feature in features])

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; }}
        .plan-box {{ background: white; border: 2px solid #667eea; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .plan-name {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .features {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .features ul {{ margin: 10px 0; padding-left: 20px; }}
        .features li {{ margin: 8px 0; }}
        .details {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .detail-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
        .detail-row:last-child {{ border-bottom: none; }}
        .footer {{ background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; font-size: 14px; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
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
            
            <p>Thank you for your purchase! Your subscription has been successfully activated.</p>
            
            <div class="plan-box">
                <div class="plan-name">{plan_type.capitalize()} Plan</div>
                <p>Your subscription is now active and you have access to all premium features.</p>
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
                    <span><strong>Amount Paid:</strong></span>
                    <span>{currency} {amount:.2f}</span>
                </div>
                <div class="detail-row">
                    <span><strong>Transaction ID:</strong></span>
                    <span>{transaction_id}</span>
                </div>
                <div class="detail-row">
                    <span><strong>Purchase Date:</strong></span>
                    <span>{purchase_date}</span>
                </div>
                <div class="detail-row">
                    <span><strong>Billing Email:</strong></span>
                    <span>{to_email}</span>
                </div>
            </div>
            
            <div style="text-align: center;">
                <a href="{settings.FRONTEND_URL}/dashboard" class="button">Go to Dashboard</a>
            </div>
            
            <p style="margin-top: 30px;"><strong>What's Next?</strong></p>
            <p>You can now access all premium features by visiting your dashboard. Start by uploading a dataset or exploring the advanced analytics tools.</p>
            
            <p style="margin-top: 20px;">If you have any questions or need assistance, please don't hesitate to contact our support team at <a href="mailto:support@insightforge.ai">support@insightforge.ai</a>.</p>
            
            <p>Best regards,<br>The InsightForge AI Team</p>
        </div>
        
        <div class="footer">
            <p>&copy; 2024 InsightForge AI. All rights reserved.</p>
            <p>This email was sent to {to_email}</p>
        </div>
    </div>
</body>
</html>
        """

        text_content = f"""
Thank you for your {plan_type.capitalize()} subscription!

Dear {user_name},

Thank you for your purchase! Your subscription has been successfully activated.

Plan: {plan_type.capitalize()}
Amount Paid: {currency} {amount:.2f}
Transaction ID: {transaction_id}
Purchase Date: {purchase_date}

Features Unlocked:
{chr(10).join(['- ' + feature for feature in features])}

You can now access all premium features by visiting your dashboard.

If you have any questions, contact us at support@insightforge.ai.

Best regards,
The InsightForge AI Team
        """

        return await self.send_email(
            to_email, subject, html_content, text_content,
            [attachment] if attachment else None,
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
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .footer {{ background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; font-size: 14px; }}
        .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 6px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Password Reset Request</h1>
        </div>
        
        <div class="content">
            <p>Dear {user_name},</p>
            
            <p>We received a request to reset your password. Click the button below to reset it:</p>
            
            <div style="text-align: center;">
                <a href="{reset_link}" class="button">Reset Password</a>
            </div>
            
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #667eea;">{reset_link}</p>
            
            <div class="warning">
                <strong>⚠️ Important:</strong> This link will expire in 1 hour. If you didn't request this password reset, please ignore this email.
            </div>
            
            <p>Best regards,<br>The InsightForge AI Team</p>
        </div>
        
        <div class="footer">
            <p>&copy; 2024 InsightForge AI. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

        text_content = f"""
Password Reset Request

Dear {user_name},

We received a request to reset your password. Visit the link below to reset it:

{reset_link}

This link will expire in 1 hour. If you didn't request this password reset, please ignore this email.

Best regards,
The InsightForge AI Team
        """

        return await self.send_email(to_email, subject, html_content, text_content)


# Global instance
email_service = EmailService()
