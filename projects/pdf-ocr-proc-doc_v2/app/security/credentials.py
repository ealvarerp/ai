from azure.core.credentials import AzureKeyCredential
from azure.identity import ClientSecretCredential, DefaultAzureCredential

from app.config import Settings


def get_azure_token_credential(settings: Settings):
    if settings.azure_tenant_id and settings.azure_client_id and settings.azure_client_secret:
        return ClientSecretCredential(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )

    return DefaultAzureCredential()


def get_key_or_token_credential(settings: Settings, key: str | None):
    if key:
        return AzureKeyCredential(key)

    return get_azure_token_credential(settings)
