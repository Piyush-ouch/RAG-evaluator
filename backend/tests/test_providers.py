"""
Unit Tests for AI and Vector Database Provider Adapters
"""

from app.providers.vectordb import VectorDBFactory, ChromaAdapter, PgVectorAdapter


def test_vector_db_factory():
    chroma = VectorDBFactory.create("chroma")
    assert isinstance(chroma, ChromaAdapter)

    pgvector = VectorDBFactory.create("pgvector")
    assert isinstance(pgvector, PgVectorAdapter)


def test_vector_db_factory_unknown():
    try:
        VectorDBFactory.create("unsupported_vector_db_type")
        assert False, "Should have raised ValueError"
    except ValueError:
        assert True
