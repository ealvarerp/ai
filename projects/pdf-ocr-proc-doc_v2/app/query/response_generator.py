from app.genai.azure_openai import ChatService
from app.models import Citation, RetrievedChunk


class ResponseGenerator:
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    def generate(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> tuple[str, list[Citation]]:
        if not chunks:
            return "No supporting documents were found.", []

        context_parts = []

        for i, chunk in enumerate(chunks, start=1):
            context_parts.append(
                f"[{i}] Source: {chunk.source or 'unknown'}\n"
                f"Title: {chunk.title or 'Untitled'}\n"
                f"Content:\n{chunk.content[:1800]}"
            )

        context = "\n\n".join(context_parts)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an enterprise RAG assistant. "
                    "Answer only using the provided sources. "
                    "If the answer is not contained in the sources, say that you do not know. "
                    "Cite sources using bracketed numbers like [1], [2], [3]."
                ),
            },
            {
                "role": "user",
                "content": f"Question:\n{query}\n\nSources:\n{context}",
            },
        ]

        answer = self.chat_service.complete(messages, temperature=0.2)

        citations = [
            Citation(
                chunk_id=chunk.id,
                source=chunk.source,
                title=chunk.title,
                snippet=chunk.content[:300],
            )
            for chunk in chunks
        ]

        return answer, citations
