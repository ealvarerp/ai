import re
from dataclasses import dataclass

import tiktoken


@dataclass
class Chunk:
    text: str
    chunk_index: int
    token_count: int


class SemanticChunker:
    def __init__(self, max_tokens: int = 800):
        self.max_tokens = max_tokens

        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoder = None

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0

        if self.encoder:
            return len(self.encoder.encode(text))

        # Rough fallback: 1 token ~= 4 characters.
        return len(text) // 4

    def _split_sentences(self, text: str) -> list[str]:
        return re.split(r"(?<=[.!?])\s+", text)

    def _split_long_text(self, text: str) -> list[str]:
        max_chars = max(self.max_tokens * 4, 800)
        parts = []

        while len(text) > max_chars:
            parts.append(text[:max_chars])
            text = text[max_chars:]

        if text:
            parts.append(text)

        return parts

    def chunk(self, text: str) -> list[Chunk]:
        if not text or not text.strip():
            return []

        chunks: list[Chunk] = []
        current_parts: list[str] = []
        current_tokens = 0
        chunk_index = 0

        def flush():
            nonlocal current_parts, current_tokens, chunk_index

            if current_parts:
                chunk_text = "\n\n".join(current_parts).strip()
                if chunk_text:
                    chunks.append(
                        Chunk(
                            text=chunk_text,
                            chunk_index=chunk_index,
                            token_count=current_tokens,
                        )
                    )
                    chunk_index += 1

            current_parts = []
            current_tokens = 0

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

        for paragraph in paragraphs:
            paragraph_tokens = self.count_tokens(paragraph)

            if paragraph_tokens <= self.max_tokens:
                if current_tokens + paragraph_tokens > self.max_tokens:
                    flush()

                current_parts.append(paragraph)
                current_tokens += paragraph_tokens
            else:
                flush()

                sentences = self._split_sentences(paragraph)

                for sentence in sentences:
                    sentence_tokens = self.count_tokens(sentence)

                    if sentence_tokens > self.max_tokens:
                        flush()

                        for part in self._split_long_text(sentence):
                            chunks.append(
                                Chunk(
                                    text=part.strip(),
                                    chunk_index=chunk_index,
                                    token_count=self.count_tokens(part),
                                )
                            )
                            chunk_index += 1
                    else:
                        if current_tokens + sentence_tokens > self.max_tokens:
                            flush()

                        current_parts.append(sentence)
                        current_tokens += sentence_tokens

        flush()

        return chunks
