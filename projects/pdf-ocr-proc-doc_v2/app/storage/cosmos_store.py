from azure.cosmos import CosmosClient, PartitionKey

from app.config import Settings
from app.security.credentials import get_azure_token_credential


class CosmosStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        credential = get_azure_token_credential(settings)

        self.client = CosmosClient(
            url=settings.cosmos_endpoint,
            credential=credential,
        )

        self.database = self.client.create_database_if_not_exists(
            settings.cosmos_database
        )

        self.container = self.database.create_container_if_not_exists(
            id=settings.cosmos_container,
            partition_key=PartitionKey(path="/partition_key"),
        )

    def upsert_document_metadata(self, document: dict) -> None:
        if "id" not in document:
            raise ValueError("Cosmos document must contain an id field.")

        document = dict(document)

        if "partition_key" not in document:
            document["partition_key"] = document.get("parent_id") or document["id"]

        self.container.upsert_item(document)

    def get_document_metadata(self, document_id: str, partition_key: str | None = None) -> dict | None:
        try:
            return self.container.read_item(
                item=document_id,
                partition_key=partition_key or document_id,
            )
        except Exception:
            return None
