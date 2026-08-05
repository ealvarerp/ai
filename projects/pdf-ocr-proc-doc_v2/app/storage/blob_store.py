from azure.storage.blob import BlobServiceClient

from app.config import Settings
from app.security.credentials import get_azure_token_credential


class BlobStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        credential = get_azure_token_credential(settings)
        self.client = BlobServiceClient(
            account_url=settings.blob_account_url,
            credential=credential,
        )
        self.container_client = self.client.get_container_client(settings.blob_container)

    def ensure_container(self) -> None:
        try:
            self.container_client.create_container()
        except Exception:
            # Already exists or unauthorized in limited permissions environments.
            pass

    def upload_bytes(
        self,
        blob_name: str,
        data: bytes,
        content_type: str = "application/pdf",
    ) -> str:
        self.container_client.upload_blob(
            name=blob_name,
            data=data,
            overwrite=True,
            content_type=content_type,
        )
        return blob_name

    def download_bytes(self, blob_name: str) -> bytes:
        return self.container_client.download_blob(blob_name).readall()

    def exists(self, blob_name: str) -> bool:
        return self.container_client.get_blob_client(blob_name).exists()
