"""
Email service for sending transactional emails via Brevo.
Currently supports password reset emails.
"""
import os
from typing import Optional
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EmailService:
    """Service for sending emails via Brevo API."""

    def __init__(
        self,
        brevo_api_key: str = None,
        sender_email: str = None,
        sender_name: str = None
    ):
        self.brevo_api_key = brevo_api_key or os.getenv("BREVO_API_KEY", "")
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL", "noreply@careeralign.ai")
        self.sender_name = sender_name or os.getenv("SENDER_NAME", "CareerAlign.ai")

    def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        frontend_url: str
    ) -> bool:
        """
        Send password reset email via Brevo.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            frontend_url: Frontend base URL

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            reset_link = f"{frontend_url}/reset-password?token={reset_token}"

            subject = "CareerAlign.ai - Password Reset Request"

            html_content = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <h2 style="color: #1f4e78;">Password Reset Request</h2>

                  <p>Hello,</p>

                  <p>We received a request to reset your password for your CareerAlign.ai account.</p>

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
                    CareerAlign.ai - AI-Powered Resume & Job Matcher<br>
                    <a href="{frontend_url}" style="color: #1f4e78;">Visit our website</a>
                  </p>
                </div>
              </body>
            </html>
            """

            return self._send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error("Failed to send password reset email", error=str(e))
            return False

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        """
        Send transactional email via Brevo.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email

        Returns:
            True if sent successfully, False otherwise

        Raises:
            ApiException: If email sending fails
        """
        logger.info(f"Sending email to: {to_email} with subject: '{subject}'")

        # Check if Brevo API key is configured
        if not self.brevo_api_key:
            logger.warning(
                "Brevo API key not configured, skipping email send. "
                "Set BREVO_API_KEY environment variable."
            )
            # In development, log that email would be sent
            if "reset" in subject.lower():
                logger.info(
                    "Password reset email would be sent",
                    to_email=to_email,
                    subject=subject
                )
            return False

        try:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.brevo_api_key

            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email}],
                sender={
                    "name": self.sender_name,
                    "email": self.sender_email
                },
                subject=subject,
                html_content=html_content
            )

            api_response = api_instance.send_transac_email(send_smtp_email)
            logger.info(
                f"Email sent successfully to {to_email} (Message ID: {api_response.message_id})"
            )
            return True

        except ApiException as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {str(e)}", exc_info=True)
            return False


# Global email service instance
email_service = EmailService()
