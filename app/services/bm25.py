import math
from collections import Counter

from app.services.vector_store import (
    LegalChunk,
    _tokenize,
    build_retrieved_context,
)


class BM25Retriever:
    """Okapi BM25 over LegalChunk text — sparse, deterministic, pure Python.

    Shares _tokenize (accent-fold) with the lexical store so both sides of the
    offline ensemble see the same terms. Emits the same RetrievedContext shape
    as MockVectorStore / QdrantVectorStore.
    """

    backend_name = "bm25"

    def __init__(self, chunks: list[dict], k1: float = 1.5, b: float = 0.75):
        self._k1 = k1
        self._b = b
        self._chunks = [
            LegalChunk.model_validate(chunk).model_dump() for chunk in chunks
        ]
        self._doc_tokens = [Counter(_tokenize(chunk["text"])) for chunk in self._chunks]
        self._doc_len = [sum(counter.values()) for counter in self._doc_tokens]
        self._avgdl = (
            (sum(self._doc_len) / len(self._doc_len)) if self._doc_len else 0.0
        )
        self._idf = self._compute_idf()

    def _compute_idf(self) -> dict[str, float]:
        n = len(self._chunks)
        df: Counter = Counter()
        for counter in self._doc_tokens:
            df.update(counter.keys())
        # ln(1 + (N - df + 0.5)/(df + 0.5)) keeps idf non-negative (Okapi/BM25+ variant).
        return {
            term: math.log(1 + (n - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }

    def _score(self, query_tokens: list[str], index: int) -> float:
        counter = self._doc_tokens[index]
        length = self._doc_len[index]
        score = 0.0
        for term in query_tokens:
            tf = counter.get(term, 0)
            if tf == 0:
                continue
            idf = self._idf.get(term, 0.0)
            denom = tf + self._k1 * (
                1 - self._b + self._b * length / (self._avgdl or 1)
            )
            score += idf * (tf * (self._k1 + 1)) / denom
        return score

    @staticmethod
    def _matches_filters(chunk: dict, filters: dict) -> bool:
        return all(
            chunk["metadata"].get(key) == value for key, value in filters.items()
        )

    def search(
        self, query: str, top_k: int = 5, filters: dict | None = None
    ) -> list[dict]:
        query_tokens = list(_tokenize(query))
        scored = []
        for index, chunk in enumerate(self._chunks):
            if filters and not self._matches_filters(chunk, filters):
                continue
            score = self._score(query_tokens, index)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1]["chunk_id"]))
        return [
            build_retrieved_context(chunk, score, "bm25")
            for score, chunk in scored[:top_k]
        ]
