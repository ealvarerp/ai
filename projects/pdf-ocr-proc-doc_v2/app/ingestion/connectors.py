from abc import ABC, abstractmethod
from typing import Iterable

from azure.storage.blob import BlobServiceClient

from app.config import Settings
from app.models import IngestedDocument
from app.security.credentials import get_azure_token_credential


class IngestionConnector(ABC):
    source_name: str = "unknown"

    @abstractmethod
    def fetch_documents(self) -> Iterable[IngestedDocument]:
        raise NotImplementedError


class BlobIngestionConnector(IngestionConnector):
    source_name = "blob"

    def __init__(self, settings: Settings):
        self.settings = settings
        credential = get_azure_token_credential(settings)
        self.client = BlobServiceClient(
            account_url=settings.blob_account_url,
            credential=credential,
        )

    def fetch_documents(
        self,
        container: str | None = None,
        prefix: str | None = None,
    ) -> Iterable[IngestedDocument]:
        container_name = container or self.settings.blob_container
        container_client = self.client.get_container_client(container_name)

        for blob in container_client.list_blobs(name_starts_with=prefix):
            if not blob.name.lower().endswith(".pdf"):
                continue

            data = container_client.download_blob(blob.name).readall()

            yield IngestedDocument(
                name=blob.name,
                content=data,
                source=self.source_name,
                metadata={
                    "container": container_name,
                    "blob_name": blob.name,
                },
            )


class SharePointIngestionConnector(IngestionConnector):
    source_name = "sharepoint"

    def fetch_documents(self) -> Iterable[IngestedDocument]:
        # Production implementation should use Microsoft Graph API.
        # Example:
        # - Authenticate with MSAL
        # - GET /sites/{site-id}/drive/root/children
        # - Filter .pdf files
        # - Download file content
        raise NotImplementedError("SharePoint connector requires Microsoft Graph implementation.")


class EmailAttachmentIngestionConnector(IngestionConnector):
    source_name = "email"

    def fetch_documents(self) -> Iterable[IngestedDocument]:
        # Production implementation can use Microsoft Graph, IMAP, or Exchange.
        raise NotImplementedError("Email attachment connector requires external mail integration.")


class FtpIngestionConnector(IngestionConnector):
    source_name = "ftp"

    def fetch_documents(self) -> Iterable[IngestedDocument]:
        # Production implementation can use ftplib for FTP.
        raise NotImplementedError("FTP connector requires host, credentials, and directory configuration.")


class SftpIngestionConnector(IngestionConnector):
    source_name = "sftp"

    def fetch_documents(self) -> Iterable[IngestedDocument]:
        # Production implementation can use paramiko for SFTP.
        raise NotImplementedError("SFTP connector requires host, credentials, and directory configuration.")
