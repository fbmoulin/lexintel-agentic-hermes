import os
from functools import lru_cache
from typing import Protocol, runtime_checkable

# MVP default: a symmetric multilingual sentence-transformer confirmed present in
# fastembed 0.7.x (intfloat/multilingual-e5-small is NOT). Symmetric => queries and
# documents are embedded identically; no e5 "query:"/"passage:" prefixes to get wrong.
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@runtime_checkable
class Embedder(Protocol):
    @property
    def dimension(self) -> int: ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class FastEmbedEmbedder:
    """Local multilingual sentence embeddings via fastembed.

    Weights download once on first use (~0.22 GB) and are cached by fastembed.
    fastembed is an optional extra (requirements-qdrant.txt), so it is imported
    lazily — the mocked v0.1 pipeline never touches this module.
    """

    def __init__(self, model_name: str | None = None):
        from fastembed import TextEmbedding  # lazy: optional extra

        self.model_name = (
            model_name or os.getenv("LEX_KRATOS_EMBEDDING_MODEL") or DEFAULT_MODEL
        )
        self._model = TextEmbedding(self.model_name)
        self._dimension: int | None = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # fastembed yields numpy arrays; normalize to plain lists for Qdrant.
        return [vector.tolist() for vector in self._model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    @property
    def dimension(self) -> int:
        # Derive dim from the model itself so model -> dim -> collection can never
        # drift (a hardcoded size silently corrupts retrieval if the model changes).
        if self._dimension is None:
            self._dimension = len(self.embed_query("probe"))
        return self._dimension


@lru_cache(maxsize=1)
def get_embedder() -> FastEmbedEmbedder:
    """Process-wide singleton — loading the model is expensive."""
    return FastEmbedEmbedder()
