from openai import AzureOpenAI

from app.config import Settings
from app.security.credentials import get_azure_token_credential


def create_openai_client(settings: Settings) -> AzureOpenAI:
    if settings.openai_api_key:
        return AzureOpenAI(
            azure_endpoint=settings.openai_endpoint,
            api_key=settings.openai_api_key,
            api_version=settings.openai_api_version,
        )

    credential = get_azure_token_credential(settings)

    def azure_ad_token_provider() -> str:
        return credential.get_token("https://cognitiveservices.azure.com/.default").token

    return AzureOpenAI(
        azure_endpoint=settings.openai_endpoint,
        azure_ad_token_provider=azure_ad_token_provider,
        api_version=settings.openai_api_version,
    )


class EmbeddingService:
    def __init__(self, client: AzureOpenAI, settings: Settings):
        self.client = client
        self.settings = settings

    def embed_text(self, text: str) -> list[float]:
        embeddings = self.embed_texts([text])
        return embeddings[0]

    def embed_texts(self, texts: list[str], batch_size: int = 16) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch = [item if item.strip() else " " for item in batch]

            response = self.client.embeddings.create(
                input=batch,
                model=self.settings.embedding_deployment,
            )

            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

        return embeddings


class ChatService:
    def __init__(self, client: AzureOpenAI, settings: Settings):
        self.client = client
        self.settings = settings

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.settings.chat_deployment,
            messages=messages,
            temperature=temperature,
        )

        return response.choices[0].message.content or ""
