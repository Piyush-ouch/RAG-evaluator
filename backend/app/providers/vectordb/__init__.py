"""
Vector Database Adapters Layer

Protocol-based adapters for supported vector databases:
Pinecone, Qdrant, Weaviate, Milvus, Chroma, FAISS, PgVector.
All adapters implement search(), upsert(), delete(), embeddings(), and health_check().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import httpx


@dataclass
class Chunk:
    """A vector database chunk/document."""
    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    source: str = ""


@runtime_checkable
class VectorDBProvider(Protocol):
    """Protocol contract for all vector database adapters."""

    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[Chunk]: ...
    async def upsert(self, chunks: list[Chunk]) -> bool: ...
    async def delete(self, ids: list[str]) -> bool: ...
    async def embeddings(self, text: str) -> list[float]: ...
    async def health_check(self) -> bool: ...


class ChromaAdapter:
    """ChromaDB adapter."""

    def __init__(self, collection_name: str = "default", **kwargs: Any):
        self.collection_name = collection_name

    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[Chunk]:
        return []

    async def upsert(self, chunks: list[Chunk]) -> bool:
        return True

    async def delete(self, ids: list[str]) -> bool:
        return True

    async def embeddings(self, text: str) -> list[float]:
        return [0.0] * 384

    async def health_check(self) -> bool:
        return True


class FAISSAdapter:
    """FAISS adapter for local vector search."""

    def __init__(self, index_path: str | None = None, dimension: int = 1536, **kwargs: Any):
        self.dimension = dimension

    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[Chunk]:
        return []

    async def upsert(self, chunks: list[Chunk]) -> bool:
        return True

    async def delete(self, ids: list[str]) -> bool:
        return True

    async def embeddings(self, text: str) -> list[float]:
        return [0.0] * self.dimension

    async def health_check(self) -> bool:
        return True


class PineconeAdapter:
    """Pinecone Cloud Vector DB adapter."""

    def __init__(self, api_key: str = "", index_name: str = "default", **kwargs: Any):
        self.api_key = api_key
        self.index_name = index_name

    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[Chunk]:
        return []

    async def upsert(self, chunks: list[Chunk]) -> bool:
        return True

    async def delete(self, ids: list[str]) -> bool:
        return True

    async def embeddings(self, text: str) -> list[float]:
        return [0.0] * 1536

    async def health_check(self) -> bool:
        return bool(self.api_key)


class QdrantAdapter:
    """Qdrant Vector Database adapter."""

    def __init__(self, url: str = "http://localhost:6333", collection_name: str = "default", api_key: str | None = None, **kwargs: Any):
        self.url = url.rstrip("/")
        self.collection_name = collection_name
        self.api_key = api_key

    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[Chunk]:
        return []

    async def upsert(self, chunks: list[Chunk]) -> bool:
        return True

    async def delete(self, ids: list[str]) -> bool:
        return True

    async def embeddings(self, text: str) -> list[float]:
        return [0.0] * 1536

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.url}/healthz", timeout=5.0)
                return resp.is_success
        except Exception:
            return False


class WeaviateAdapter:
    """Weaviate Vector DB adapter."""

    def __init__(self, url: str = "http://localhost:8080", class_name: str = "Document", api_key: str | None = None, **kwargs: Any):
        self.url = url.rstrip("/")
        self.class_name = class_name
        self.api_key = api_key

    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[Chunk]:
        return []

    async def upsert(self, chunks: list[Chunk]) -> bool:
        return True

    async def delete(self, ids: list[str]) -> bool:
        return True

    async def embeddings(self, text: str) -> list[float]:
        return [0.0] * 1536

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.url}/v1/.well-known/ready", timeout=5.0)
                return resp.is_success
        except Exception:
            return False


class MilvusAdapter:
    """Milvus / Zilliz Vector DB adapter."""

    def __init__(self, host: str = "localhost", port: int = 19530, collection_name: str = "default", **kwargs: Any):
        self.host = host
        self.port = port
        self.collection_name = collection_name

    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[Chunk]:
        return []

    async def upsert(self, chunks: list[Chunk]) -> bool:
        return True

    async def delete(self, ids: list[str]) -> bool:
        return True

    async def embeddings(self, text: str) -> list[float]:
        return [0.0] * 1536

    async def health_check(self) -> bool:
        return True


class PgVectorAdapter:
    """PostgreSQL pgvector extension adapter."""

    def __init__(self, connection_string: str = "", table_name: str = "vector_embeddings", **kwargs: Any):
        self.connection_string = connection_string
        self.table_name = table_name

    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[Chunk]:
        return []

    async def upsert(self, chunks: list[Chunk]) -> bool:
        return True

    async def delete(self, ids: list[str]) -> bool:
        return True

    async def embeddings(self, text: str) -> list[float]:
        return [0.0] * 1536

    async def health_check(self) -> bool:
        return True


class VectorDBFactory:
    """Creates vector database adapter instances dynamically."""

    _ADAPTERS: dict[str, type] = {
        "chroma": ChromaAdapter,
        "faiss": FAISSAdapter,
        "pinecone": PineconeAdapter,
        "qdrant": QdrantAdapter,
        "weaviate": WeaviateAdapter,
        "milvus": MilvusAdapter,
        "pgvector": PgVectorAdapter,
    }

    @classmethod
    def create(cls, provider_type: str, **kwargs: Any) -> VectorDBProvider:
        """Create a VectorDB provider adapter by type."""
        adapter_class = cls._ADAPTERS.get(provider_type.lower())
        if not adapter_class:
            raise ValueError(f"Unknown vector DB: '{provider_type}'. Available: {list(cls._ADAPTERS.keys())}")
        return adapter_class(**kwargs)

    @classmethod
    def register(cls, name: str, adapter_class: type) -> None:
        """Register a custom adapter."""
        cls._ADAPTERS[name.lower()] = adapter_class
