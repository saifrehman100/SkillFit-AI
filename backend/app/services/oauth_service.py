"""
OAuth service for third-party authentication (Google, GitHub, etc.).
"""
from typing import Dict, Optional
import httpx

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class OAuthService:
    """Service for OAuth authentication."""

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(
        self,
        google_client_id: Optional[str] = None,
        google_client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ):
        self.google_client_id = google_client_id
        self.google_client_secret = google_client_secret
        self.redirect_uri = redirect_uri

    async def exchange_google_code(self, code: str) -> Dict:
        """
        Exchange Google authorization code for access token.

        Args:
            code: Authorization code from Google OAuth callback

        Returns:
            Dictionary with access_token and other OAuth data

        Raises:
            Exception if token exchange fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.GOOGLE_TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": self.google_client_id,
                        "client_secret": self.google_client_secret,
                        "redirect_uri": self.redirect_uri,
                        "grant_type": "authorization_code"
                    }
                )

                if response.status_code != 200:
                    error_data = response.json()
                    raise Exception(f"Token exchange failed: {error_data}")

                return response.json()

        except Exception as e:
            logger.error("Google token exchange failed", error=str(e))
            raise

    async def get_google_user_info(self, access_token: str) -> Dict:
        """
        Get user information from Google.

        Args:
            access_token: Google access token

        Returns:
            Dictionary with user data (email, name, picture, etc.)

        Raises:
            Exception if API call fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if response.status_code != 200:
                    raise Exception(f"Failed to get user info: {response.text}")

                user_info = response.json()
                logger.info("Got Google user info", email=user_info.get("email"))

                return user_info

        except Exception as e:
            logger.error("Failed to get Google user info", error=str(e))
            raise

    async def authenticate_with_google(self, code: str) -> Dict:
        """
        Complete Google OAuth flow: exchange code and get user info.

        Args:
            code: Authorization code from Google

        Returns:
            Dictionary with user information

        Raises:
            Exception if authentication fails
        """
        # Exchange code for token
        token_data = await self.exchange_google_code(code)
        access_token = token_data.get("access_token")

        if not access_token:
            raise Exception("No access token received from Google")

        # Get user info
        user_info = await self.get_google_user_info(access_token)

        return {
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "email_verified": user_info.get("verified_email", False),
            "google_id": user_info.get("id")
        }
