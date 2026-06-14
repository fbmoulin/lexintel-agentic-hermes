"""Offline unit tests for QdrantVectorStore.

No live Qdrant, no model download: a fake client and a fake embedder exercise
id derivation, payload construction, the dim-mismatch guard, and the
hit -> RetrievedContext mapping (incl. the retrieval_method="qdrant" stamp).
"""

import uuid
from types import SimpleNamespace

import pytest

from app.services.vector_store import QdrantVectorStore


class _FakeEmbedder:
    dimension = 4

    def embed_texts(self, texts):
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]

    def embed_query(self, text):
        return [0.1, 0.2, 0.3, 0.4]


class _FakeClient:
    def __init__(self, exists=False, existing_dim=4):
        self._exists = exists
        self._existing_dim = existing_dim
        self.created = None
        self.upserted = []
        self.query_response = SimpleNamespace(points=[])

    def collection_exists(self, collection_name):
        return self._exists

    def create_collection(self, collection_name, vectors_config):
        self.created = (collection_name, vectors_config.size, vectors_config.distance)
        self._exists = True

    def get_collection(self, collection_name):
        vectors = SimpleNamespace(size=self._existing_dim)
        params = SimpleNamespace(vectors=vectors)
        return SimpleNamespace(config=SimpleNamespace(params=params))

    def upsert(self, collection_name, points):
        self.upserted = points

    def count(self, collection_name, exact=True):
        return SimpleNamespace(count=len(self.upserted))

    def query_points(self, **kwargs):
        return self.query_response


CHUNK = {
    "chunk_id": "chunk_caso_1_doc_1_p1_pedido",
    "case_id": "caso_1",
    "doc_id": "doc_1",
    "unit_type": "pedido",
    "text": "Pedido de indenização por fraude bancária.",
    "page_start": 1,
    "page_end": 1,
    "source": "peticao.pdf",
    "metadata": {"doc_type": "peticao_inicial", "source_ref": "CDC art. 14"},
}


def _store(client):
    return QdrantVectorStore(
        client=client, embedder=_FakeEmbedder(), collection_name="test_coll"
    )


def test_creates_collection_with_model_dimension():
    client = _FakeClient(exists=False)
    _store(client)
    assert client.created[0] == "test_coll"
    assert client.created[1] == 4  # dim from embedder, not hardcoded


def test_dim_mismatch_raises_loud():
    client = _FakeClient(exists=True, existing_dim=999)
    with pytest.raises(RuntimeError, match="dim"):
        _store(client)


def test_upsert_uses_deterministic_uuid5_id_and_full_payload():
    client = _FakeClient(exists=True, existing_dim=4)
    result = _store(client).upsert([CHUNK])
    assert result["vector_backend"] == "qdrant"
    assert result["indexed_count"] == 1
    point = client.upserted[0]
    expected_id = str(uuid.uuid5(uuid.NAMESPACE_URL, CHUNK["chunk_id"]))
    assert point.id == expected_id  # idempotent re-index
    assert point.payload["chunk_id"] == CHUNK["chunk_id"]
    assert point.payload["metadata"]["source_ref"] == "CDC art. 14"


def test_search_maps_hit_to_retrieved_context_and_stamps_method():
    client = _FakeClient(exists=True, existing_dim=4)
    client.query_response = SimpleNamespace(
        points=[SimpleNamespace(id="x", score=0.87654, payload=CHUNK)]
    )
    results = _store(client).search("fraude", top_k=3)
    assert len(results) == 1
    hit = results[0]
    assert hit["chunk_id"] == CHUNK["chunk_id"]
    assert hit["doc_id"] == "doc_1"
    assert hit["score"] == 0.8765  # rounded to 4
    assert hit["metadata"]["retrieval_method"] == "qdrant"  # stamped, not stored
    assert hit["metadata"]["case_id"] == "caso_1"
    assert hit["metadata"]["unit_type"] == "pedido"
    assert hit["metadata"]["source_ref"] == "CDC art. 14"
