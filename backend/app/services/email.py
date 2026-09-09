import os
from typing import Optional

from fastapi import HTTPException


class EmailService:
    """Email service for sending transactional emails."""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@insightforge.ai")
        self.from_name = os.getenv("FROM_NAME", "InsightForge AI")
        self.is_configured = all([
            self.smtp_host,
            self.smtp_user,
            self.smtp_password,
        ])

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email to the specified recipient."""
        if not self.is_configured:
            # Log warning but don't fail - allow development without email
            print(f"Email not configured. Would send to {to_email}: {subject}")
            return True

        try:
            # Import here to avoid requiring aiosmtpd in production if not using email
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain"))

            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")
            return False

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
                <a href="{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/dashboard" class="button">Go to Dashboard</a>
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

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_password_reset(
        self,
        to_email: str,
        user_name: str,
        reset_token: str,
    ) -> bool:
        """Send password reset email."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

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
