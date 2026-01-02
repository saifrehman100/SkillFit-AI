"""
Email service for sending transactional emails.
Currently supports password reset emails.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        from_email: str = None
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.from_email = from_email or os.getenv("FROM_EMAIL", self.smtp_user)

    def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        frontend_url: str
    ) -> bool:
        """
        Send password reset email.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            frontend_url: Frontend base URL

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            reset_link = f"{frontend_url}/reset-password?token={reset_token}"

            subject = "SkillFit AI - Password Reset Request"

            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <h2 style="color: #1f4e78;">Password Reset Request</h2>

                  <p>Hello,</p>

                  <p>We received a request to reset your password for your SkillFit AI account.</p>

                  <p>Click the button below to reset your password:</p>

                  <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}"
                       style="background-color: #1f4e78; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                      Reset Password
                    </a>
                  </div>

                  <p>Or copy and paste this link into your browser:</p>
                  <p style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {reset_link}
                  </p>

                  <p><strong>This link will expire in 1 hour.</strong></p>

                  <p>If you didn't request this password reset, please ignore this email.
                     Your password will remain unchanged.</p>

                  <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                  <p style="font-size: 12px; color: #666;">
                    SkillFit AI - AI-Powered Resume & Job Matcher<br>
                    <a href="{frontend_url}" style="color: #1f4e78;">Visit our website</a>
                  </p>
                </div>
              </body>
            </html>
            """

            text_body = f"""
            Password Reset Request

            Hello,

            We received a request to reset your password for your SkillFit AI account.

            Click the link below to reset your password:
            {reset_link}

            This link will expire in 1 hour.

            If you didn't request this password reset, please ignore this email.
            Your password will remain unchanged.

            ---
            SkillFit AI - AI-Powered Resume & Job Matcher
            {frontend_url}
            """

            return self._send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )

        except Exception as e:
            logger.error("Failed to send password reset email", error=str(e))
            return False

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Check if SMTP is configured
            if not self.smtp_user or not self.smtp_password:
                logger.warning(
                    "SMTP not configured, skipping email send. "
                    "Set SMTP_USER and SMTP_PASSWORD environment variables."
                )
                # In development, log the token instead
                if "reset" in subject.lower():
                    logger.info(
                        "Password reset email would be sent",
                        to_email=to_email,
                        html_contains_token=True
                    )
                return False

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            # Add text and HTML parts
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")

            message.attach(part1)
            message.attach(part2)

            # Send email with timeout
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)

            logger.info("Email sent successfully", to_email=to_email, subject=subject)
            return True

        except Exception as e:
            logger.error("Failed to send email", error=str(e), to_email=to_email)
            return False


# Global email service instance
email_service = EmailService()
