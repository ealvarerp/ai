from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

from app.config import Settings
from app.models import RetrievedChunk
from app.security.credentials import get_key_or_token_credential


class SearchStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        credential = get_key_or_token_credential(settings, settings.search_api_key)

        self.index_client = SearchIndexClient(
            endpoint=settings.search_endpoint,
            credential=credential,
        )

        self.search_client = SearchClient(
            endpoint=settings.search_endpoint,
            index_name=settings.search_index,
            credential=credential,
        )

    def ensure_index(self) -> None:
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="parent_id", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SimpleField(name="chunk_index", type=SearchFieldDataType.Int32, filterable=True),
            SimpleField(name="language", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="metadata", type=SearchFieldDataType.String),
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="default",
            ),
        ]

        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(name="hnsw-config"),
            ],
            profiles=[
                VectorSearchProfile(
                    name="default",
                    algorithm_configuration_name="hnsw-config",
                ),
            ],
        )

        index = SearchIndex(
            name=self.settings.search_index,
            fields=fields,
            vector_search=vector_search,
        )

        self.index_client.create_or_update_index(index)

    def upload_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            return

        documents = []
        for chunk in chunks:
            documents.append(
                {
                    "@search.action": "upload",
                    **chunk,
                }
            )

        self.search_client.upload_documents(documents=documents)

    def search(
        self,
        query: str,
        query_embedding: list[float],
        top: int = 8,
    ) -> list[RetrievedChunk]:
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=50,
            fields="embedding",
        )

        results = self.search_client.search(
            search_text=query or "*",
            vector_queries=[vector_query],
            top=top,
            select="id,parent_id,source,title,content,chunk_index",
        )

        output: list[RetrievedChunk] = []

        for item in results:
            output.append(
                RetrievedChunk(
                    id=item.get("id"),
                    parent_id=item.get("parent_id"),
                    source=item.get("source"),
                    title=item.get("title"),
                    content=item.get("content", ""),
                    chunk_index=item.get("chunk_index"),
                    score=item.get("@search.score"),
                )
            )

        return output
