"""
Cloud storage utilities for handling file uploads.
Supports GCP Cloud Storage and local filesystem fallback.
"""
import os
import json
from typing import Optional, BinaryIO
from io import BytesIO
import hashlib

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class StorageClient:
    """Abstract storage client interface."""

    def __init__(self):
        self.provider = self._detect_provider()
        logger.info("Storage provider initialized", provider=self.provider)

    def _detect_provider(self) -> str:
        """Detect which storage provider to use."""
        if settings.gcp_bucket_name and settings.gcs_credentials_json:
            return "gcs"
        return "local"

    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        user_id: Optional[int] = None
    ) -> str:
        """
        Upload file to storage and return the storage path/URL.

        Args:
            file_content: File content as bytes
            filename: Original filename
            content_type: MIME type
            user_id: Optional user ID for organizing files

        Returns:
            Storage path or public URL
        """
        if self.provider == "gcs":
            return self._upload_to_gcs(file_content, filename, content_type, user_id)
        return self._upload_to_local(file_content, filename, user_id)

    def download_file(self, file_path: str) -> bytes:
        """
        Download file from storage.

        Args:
            file_path: Storage path or URL

        Returns:
            File content as bytes
        """
        if self.provider == "gcs":
            return self._download_from_gcs(file_path)
        return self._download_from_local(file_path)

    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_path: Storage path or URL

        Returns:
            True if successful
        """
        if self.provider == "gcs":
            return self._delete_from_gcs(file_path)
        return self._delete_from_local(file_path)

    def get_public_url(self, file_path: str) -> str:
        """
        Get public URL for a file.

        Args:
            file_path: Storage path

        Returns:
            Public URL
        """
        if self.provider == "gcs":
            return f"https://storage.googleapis.com/{settings.gcp_bucket_name}/{file_path}"
        return f"/files/{file_path}"

    # GCS Implementation
    def _upload_to_gcs(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        user_id: Optional[int]
    ) -> str:
        """Upload file to Google Cloud Storage."""
        try:
            from google.cloud import storage
            from google.oauth2 import service_account

            # Parse credentials - handle both raw JSON and escaped JSON
            creds_json = settings.gcs_credentials_json

            # If credentials are wrapped in quotes, remove them
            if creds_json.startswith('"') and creds_json.endswith('"'):
                creds_json = creds_json[1:-1]

            # Replace escaped newlines with actual newlines
            creds_json = creds_json.replace('\\n', '\n')

            try:
                credentials_dict = json.loads(creds_json)
            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to parse GCS credentials JSON",
                    error=str(e),
                    credentials_preview=creds_json[:100] if creds_json else "empty"
                )
                raise

            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict
            )

            # Create client
            client = storage.Client(
                credentials=credentials,
                project=settings.gcp_project_id
            )
            bucket = client.bucket(settings.gcp_bucket_name)

            # Generate unique path
            file_hash = hashlib.sha256(file_content).hexdigest()[:16]
            user_prefix = f"user_{user_id}" if user_id else "uploads"
            blob_name = f"{user_prefix}/{file_hash}_{filename}"

            # Upload
            blob = bucket.blob(blob_name)
            blob.upload_from_string(
                file_content,
                content_type=content_type
            )

            # Make public (optional - depends on your bucket settings)
            # blob.make_public()

            logger.info(
                "File uploaded to GCS",
                filename=filename,
                blob_name=blob_name,
                size=len(file_content)
            )

            return blob_name

        except Exception as e:
            logger.error("GCS upload failed", error=str(e), filename=filename)
            raise RuntimeError(f"Failed to upload to cloud storage: {str(e)}")

    def _download_from_gcs(self, blob_name: str) -> bytes:
        """Download file from Google Cloud Storage."""
        try:
            from google.cloud import storage
            from google.oauth2 import service_account

            # Parse credentials
            creds_json = settings.gcs_credentials_json
            if creds_json.startswith('"') and creds_json.endswith('"'):
                creds_json = creds_json[1:-1]
            creds_json = creds_json.replace('\\n', '\n')

            credentials_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict
            )

            client = storage.Client(
                credentials=credentials,
                project=settings.gcp_project_id
            )
            bucket = client.bucket(settings.gcp_bucket_name)
            blob = bucket.blob(blob_name)

            content = blob.download_as_bytes()
            logger.info("File downloaded from GCS", blob_name=blob_name)
            return content

        except Exception as e:
            logger.error("GCS download failed", error=str(e), blob_name=blob_name)
            raise RuntimeError(f"Failed to download from cloud storage: {str(e)}")

    def _delete_from_gcs(self, blob_name: str) -> bool:
        """Delete file from Google Cloud Storage."""
        try:
            from google.cloud import storage
            from google.oauth2 import service_account

            # Parse credentials
            creds_json = settings.gcs_credentials_json
            if creds_json.startswith('"') and creds_json.endswith('"'):
                creds_json = creds_json[1:-1]
            creds_json = creds_json.replace('\\n', '\n')

            credentials_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict
            )

            client = storage.Client(
                credentials=credentials,
                project=settings.gcp_project_id
            )
            bucket = client.bucket(settings.gcp_bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()

            logger.info("File deleted from GCS", blob_name=blob_name)
            return True

        except Exception as e:
            logger.error("GCS deletion failed", error=str(e), blob_name=blob_name)
            return False

    # Local Filesystem Implementation (Fallback)
    def _upload_to_local(
        self,
        file_content: bytes,
        filename: str,
        user_id: Optional[int]
    ) -> str:
        """Upload file to local filesystem."""
        # Create uploads directory
        upload_dir = os.path.join(os.getcwd(), "uploads")
        if user_id:
            upload_dir = os.path.join(upload_dir, f"user_{user_id}")

        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        file_hash = hashlib.sha256(file_content).hexdigest()[:16]
        unique_filename = f"{file_hash}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)

        # Write file
        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(
            "File uploaded to local storage",
            filename=filename,
            path=file_path
        )

        # Return relative path
        relative_path = os.path.join(
            f"user_{user_id}" if user_id else "uploads",
            unique_filename
        )
        return relative_path

    def _download_from_local(self, file_path: str) -> bytes:
        """Download file from local filesystem."""
        full_path = os.path.join(os.getcwd(), "uploads", file_path)
        with open(full_path, "rb") as f:
            content = f.read()

        logger.info("File downloaded from local storage", path=file_path)
        return content

    def _delete_from_local(self, file_path: str) -> bool:
        """Delete file from local filesystem."""
        try:
            full_path = os.path.join(os.getcwd(), "uploads", file_path)
            os.remove(full_path)
            logger.info("File deleted from local storage", path=file_path)
            return True
        except Exception as e:
            logger.error("Local deletion failed", error=str(e), path=file_path)
            return False


# Singleton instance
_storage_client: Optional[StorageClient] = None


def get_storage_client() -> StorageClient:
    """Get or create storage client singleton."""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client
