"""
Vector Database Adapters

Protocol-based adapters for supported vector databases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


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
    """Protocol for vector database adapters."""

    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[Chunk]: ...
    async def health_check(self) -> bool: ...


class ChromaAdapter:
    """ChromaDB adapter."""

    def __init__(self, collection_name: str = "default", **kwargs: Any):
        import chromadb
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)

    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[Chunk]:
        results = self.collection.query(query_texts=[query], n_results=top_k)
        chunks = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                chunks.append(Chunk(
                    id=results["ids"][0][i] if results["ids"] else str(i),
                    content=doc,
                    score=1.0 - (results["distances"][0][i] if results.get("distances") else 0.0),
                    metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
                ))
        return chunks

    async def health_check(self) -> bool:
        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False


class FAISSAdapter:
    """FAISS adapter for local vector search."""

    def __init__(self, index_path: str | None = None, dimension: int = 1536, **kwargs: Any):
        self.dimension = dimension
        self.documents: list[str] = []
        self.metadatas: list[dict] = []

    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[Chunk]:
        # FAISS requires embeddings — return empty for now
        # Real implementation would embed the query and search
        return []

    async def health_check(self) -> bool:
        return True


class VectorDBFactory:
    """Creates vector database adapter instances."""

    _ADAPTERS: dict[str, type] = {
        "chroma": ChromaAdapter,
        "faiss": FAISSAdapter,
    }

    @classmethod
    def create(cls, provider_type: str, **kwargs: Any) -> VectorDBProvider:
        adapter_class = cls._ADAPTERS.get(provider_type)
        if not adapter_class:
            raise ValueError(f"Unknown vector DB: '{provider_type}'.")
        return adapter_class(**kwargs)
