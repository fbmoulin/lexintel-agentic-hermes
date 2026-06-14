# Real Qdrant Retrieval (MVP) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the stubbed `QdrantVectorStore` with a working local-only vector backend (fastembed embeddings + Qdrant), reachable through the existing `LEX_KRATOS_ENABLE_QDRANT` flag, and verify it live.

**Architecture:** A new `embeddings.py` isolates a local multilingual sentence-transformer (`paraphrase-multilingual-MiniLM-L12-v2`, 384-dim, symmetric — no e5 prefixes). `QdrantVectorStore` takes injectable `client`/`embedder` (mirroring `IndexingAgent(vector_store=...)`), ensures its collection, upserts full-chunk payloads under deterministic `uuid5` ids, and maps Qdrant hits back to the **same `RetrievedContext` dict shape the mock emits** — so `app/api/rag.py` and downstream agents are untouched. The mock path, the eval (`run_eval.py`, mock-only), and CI behavior are unchanged when the flag is off.

**Tech Stack:** Python 3.12, fastembed 0.7.x, qdrant-client 1.14.3, Qdrant v1.14.3 (docker), pytest.

**Spec:** `docs/superpowers/specs/2026-06-14-qdrant-real-retrieval-design.md`

**Confirmed facts (already verified against the live venv):**
- `intfloat/multilingual-e5-small` is **NOT** in fastembed 0.7.4 — spec's pre-authorized fallback used.
- `paraphrase-multilingual-MiniLM-L12-v2`: dim **384**, ~0.22 GB, symmetric. Portuguese paraphrase sanity: passage↔paraphrase-query cosine **0.585**, passage↔distractor **0.179** (mock token-overlap would score the paraphrase ~0).
- qdrant-client 1.14.3 API confirmed present: `collection_exists`, `create_collection`, `upsert`, `query_points`, `get_collection`, `count`; `models.VectorParams`, `Distance.COSINE`, `PointStruct`, `Filter`, `FieldCondition`, `MatchValue`.

---

## File Structure

| File | Responsibility |
|------|----------------|
| **Create** `app/services/embeddings.py` | Local embedder wrapper; lazy fastembed singleton; dim read from model |
| **Modify** `app/services/vector_store.py` | Fill `QdrantVectorStore.__init__/upsert/search` (+ private helpers); replaces the two `raise`s |
| **Create** `tests/test_qdrant_vector_store_unit.py` | Offline unit tests with fake client+embedder (default suite) |
| **Create** `tests/integration/__init__.py` | Marks the gated integration package |
| **Create** `tests/integration/test_qdrant_retrieval.py` | Gated end-to-end test (real model + live Qdrant) |
| **Modify** `requirements-qdrant.txt` | Add `fastembed` pin |
| **Modify** `.env.example` | Add flag + ports + optional model override |
| **Modify** `docker-compose.yml` | Parameterize host port (`${QDRANT_HOST_PORT:-6533}:6333`) |
| **Modify** `CHANGELOG.md`, `README.md` | Document the optional real-retrieval path + run-note |

---

> **⚠️ Supersedes spec D1/D2:** the spec named `intfloat/multilingual-e5-small` with `"query:"/"passage:"` prefixes. That model is **not** in fastembed 0.7.4 (spec D1's pre-authorized fallback applies). This plan uses the **symmetric** `paraphrase-multilingual-MiniLM-L12-v2` — **do NOT add e5 prefixes**; queries and documents are embedded identically. (Empirically verified: PT paraphrase cosine 0.585 vs distractor 0.179.)

## Task 1: Embedding module

**Files:**
- Create: `app/services/embeddings.py`
- (No default-suite test — it requires the model weights; exercised by the Task 3 gated integration test. The wrapper is thin and the unit tests in Task 2 stub it.)

- [ ] **Step 1: Write `app/services/embeddings.py`**

```python
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

        self.model_name = model_name or os.getenv(
            "LEX_KRATOS_EMBEDDING_MODEL", DEFAULT_MODEL
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
```

- [ ] **Step 2: Sanity-import without loading the model**

Run: `.venv/bin/python -c "import app.services.embeddings as e; print(e.DEFAULT_MODEL)"`
Expected: prints the model name, no weight download (lazy import means construction is deferred).

- [ ] **Step 3: Lint**

Run: `.venv/bin/ruff check app/services/embeddings.py && .venv/bin/ruff format app/services/embeddings.py`
Expected: clean.

- [ ] **Step 4: Commit**

```bash
git add app/services/embeddings.py
git commit -m "feat(rag): local multilingual embedder (fastembed) for real retrieval"
```

---

## Task 2: QdrantVectorStore body (offline-unit-tested)

**Files:**
- Modify: `app/services/vector_store.py` (replace the `QdrantVectorStore` class, lines ~159-175; add `import os`, `import uuid`, and the embeddings import)
- Test: `tests/test_qdrant_vector_store_unit.py`

- [ ] **Step 1: Write the failing unit test** (`tests/test_qdrant_vector_store_unit.py`)

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_qdrant_vector_store_unit.py -v`
Expected: FAIL — current `QdrantVectorStore.__init__` takes no args / `upsert` raises `RuntimeError`.

- [ ] **Step 3: Replace the `QdrantVectorStore` class in `app/services/vector_store.py`**

First, replace the **entire existing import block** (lines 1-7) with this already-sorted block (ruff `I` / isort-clean — `os`/`uuid` grouped with stdlib, the `qdrant_service` line *merged* not duplicated, so it won't trip `I001`):

```python
import os
import re
import unicodedata
import uuid
from copy import deepcopy
from typing import Protocol

from app.schemas.case import LegalChunk, RetrievedContext
from app.services.embeddings import Embedder, get_embedder
from app.services.qdrant_service import get_qdrant_client, is_qdrant_enabled
```

Replace the entire stub class (the `class QdrantVectorStore:` block that currently raises) with:

```python
class QdrantVectorStore:
    """Real vector retrieval backed by Qdrant + local fastembed embeddings.

    Client and embedder are injectable (mirrors IndexingAgent(vector_store=...)),
    so the mapping/id logic is unit-testable without a live server or model.
    Emits the SAME RetrievedContext dict shape as MockVectorStore -> rag.py and
    downstream agents need no change.
    """

    backend_name = "qdrant"

    def __init__(
        self,
        client=None,
        embedder: Embedder | None = None,
        collection_name: str | None = None,
    ):
        self._client = client if client is not None else get_qdrant_client()
        self._embedder = embedder if embedder is not None else get_embedder()
        self._collection = collection_name or os.getenv(
            "QDRANT_COLLECTION", "lex_kratos_chunks"
        )
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        from qdrant_client import models

        dim = self._embedder.dimension
        if not self._client.collection_exists(self._collection):
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=models.VectorParams(
                    size=dim, distance=models.Distance.COSINE
                ),
            )
            return
        existing = self._client.get_collection(self._collection)
        existing_dim = existing.config.params.vectors.size
        if existing_dim != dim:
            raise RuntimeError(
                f"Coleção Qdrant '{self._collection}' tem dim={existing_dim}, "
                f"mas o modelo de embedding produz dim={dim}. Recrie a coleção."
            )

    @staticmethod
    def _point_id(chunk_id: str) -> str:
        # Deterministic id => re-indexing the same chunk upserts (replaces),
        # mirroring MockVectorStore's existing_ids de-dup.
        return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))

    def upsert(self, chunks: list[dict]) -> dict:
        from qdrant_client import models

        validated = [
            LegalChunk.model_validate(chunk).model_dump() for chunk in chunks
        ]
        if validated:
            vectors = self._embedder.embed_texts([c["text"] for c in validated])
            points = [
                models.PointStruct(
                    id=self._point_id(chunk["chunk_id"]),
                    vector=vector,
                    payload=chunk,
                )
                for chunk, vector in zip(validated, vectors)
            ]
            self._client.upsert(collection_name=self._collection, points=points)
        return {
            "vector_backend": self.backend_name,
            "indexed_count": len(validated),
            "stored_count": self._client.count(self._collection, exact=True).count,
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[dict]:
        query_vector = self._embedder.embed_query(query)
        response = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=top_k,
            query_filter=self._build_filter(filters),
            with_payload=True,
        )
        return [self._point_to_context(point) for point in response.points]

    @staticmethod
    def _build_filter(filters: dict | None):
        if not filters:
            return None
        from qdrant_client import models

        # Filters target chunk metadata (mirrors MockVectorStore._matches_filters);
        # payload stores the full chunk, so metadata is nested under "metadata.*".
        return models.Filter(
            must=[
                models.FieldCondition(
                    key=f"metadata.{key}", match=models.MatchValue(value=value)
                )
                for key, value in filters.items()
            ]
        )

    @staticmethod
    def _point_to_context(point) -> dict:
        payload = point.payload or {}
        metadata = dict(payload.get("metadata", {}))
        metadata.update(
            {
                "case_id": payload.get("case_id"),
                "unit_type": payload.get("unit_type"),
                "retrieval_method": "qdrant",
            }
        )
        context = RetrievedContext(
            chunk_id=payload["chunk_id"],
            doc_id=payload["doc_id"],
            score=round(point.score, 4),
            text=payload["text"],
            source=payload.get("source"),
            page_start=payload.get("page_start"),
            page_end=payload.get("page_end"),
            metadata=metadata,
        )
        return context.model_dump()
```

> **Note on `get_vector_store()`** (lines ~187-193): unchanged. It already returns `QdrantVectorStore()` when `is_qdrant_enabled()`. With the new `__init__`, that call now resolves the real client+embedder and ensures the collection — exactly what we want.

- [ ] **Step 4: Run the unit tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_qdrant_vector_store_unit.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Run the FULL default suite — nothing regressed, still offline**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS, same count as before + 4 new. No network. (`test_qdrant_optional.py` still green — it never instantiates `QdrantVectorStore`.)

- [ ] **Step 6: Lint + type-check touched files**

Run: `.venv/bin/ruff check --fix app/services/vector_store.py tests/test_qdrant_vector_store_unit.py && .venv/bin/ruff format app/services/vector_store.py tests/test_qdrant_vector_store_unit.py && .venv/bin/mypy app/services/vector_store.py`
Expected: clean (the `--fix` auto-sorts imports if Step 3's block was pasted out of order).

- [ ] **Step 7: Commit**

```bash
git add app/services/vector_store.py tests/test_qdrant_vector_store_unit.py
git commit -m "feat(rag): implement QdrantVectorStore (upsert/search) with offline unit tests"
```

---

## Task 3: Gated end-to-end integration test

**Files:**
- Create: `tests/integration/__init__.py` (empty)
- Create: `tests/integration/test_qdrant_retrieval.py`

- [ ] **Step 1: Create the package marker**

`tests/integration/__init__.py` → empty file.

- [ ] **Step 2: Write the gated integration test** (`tests/integration/test_qdrant_retrieval.py`)

```python
"""End-to-end retrieval against a LIVE Qdrant with REAL embeddings.

Skipped by default. Runs only when ALL hold:
  - LEX_KRATOS_ENABLE_QDRANT=true
  - fastembed + qdrant-client importable
  - a Qdrant reachable at QDRANT_HOST:QDRANT_PORT (default localhost:6533)

This proves the value over the token-overlap mock: a paraphrased query with no
shared content words still retrieves the right chunk.
"""

import os
import socket
import uuid

import pytest


def _should_run() -> bool:
    if os.getenv("LEX_KRATOS_ENABLE_QDRANT", "false").lower() != "true":
        return False
    try:
        import fastembed  # noqa: F401
        import qdrant_client  # noqa: F401
    except ImportError:
        return False
    host = os.getenv("QDRANT_HOST", "localhost")
    port_env = os.getenv("QDRANT_PORT", "6533")
    port = int(port_env) if port_env.isdigit() else 6533
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _should_run(),
    reason="needs LEX_KRATOS_ENABLE_QDRANT=true, fastembed+qdrant-client, live Qdrant",
)

CHUNK = {
    "chunk_id": "chunk_it_bancario_p1_tese",
    "case_id": "caso_integracao",
    "doc_id": "doc_bancario",
    "unit_type": "tese",
    "text": "Responsabilidade objetiva de banco por fraude praticada por terceiro.",
    "page_start": 1,
    "page_end": 1,
    "source": "seed.pdf",
    "metadata": {"doc_type": "precedente", "source_ref": "Súmula 479/STJ"},
}


@pytest.fixture
def store():
    from app.services.vector_store import QdrantVectorStore

    # Unique collection per run so the test is isolated and self-cleaning.
    name = f"lex_it_{uuid.uuid4().hex[:8]}"
    s = QdrantVectorStore(collection_name=name)
    yield s
    s._client.delete_collection(name)


def test_paraphrase_query_retrieves_semantically(store):
    store.upsert([CHUNK])
    # Paraphrase with NO shared content words vs the chunk — mock would miss it.
    results = store.search(
        "instituição financeira responde por golpe aplicado por estranho", top_k=3
    )
    assert results, "expected at least one semantic hit"
    assert results[0]["chunk_id"] == CHUNK["chunk_id"]
    assert results[0]["metadata"]["retrieval_method"] == "qdrant"
    assert results[0]["metadata"]["source_ref"] == "Súmula 479/STJ"


def test_reindex_is_idempotent(store):
    store.upsert([CHUNK])
    second = store.upsert([CHUNK])  # same chunk_id -> uuid5 -> replace, not duplicate
    assert second["stored_count"] == 1
```

- [ ] **Step 3: Confirm it SKIPS by default (flag off)**

Run: `.venv/bin/python -m pytest tests/integration -v`
Expected: 2 skipped (flag off).

- [ ] **Step 4: Lint**

Run: `.venv/bin/ruff check tests/integration && .venv/bin/ruff format tests/integration`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add tests/integration/
git commit -m "test(rag): gated end-to-end Qdrant retrieval (skipped without live server)"
```

---

## Task 4: Config, dependencies, compose

**Files:**
- Modify: `requirements-qdrant.txt`, `.env.example`, `docker-compose.yml`

- [ ] **Step 1: Add fastembed to `requirements-qdrant.txt`**

Append:

```
# Local multilingual embeddings for real retrieval (paraphrase-multilingual-MiniLM-L12-v2).
fastembed==0.7.4
```

- [ ] **Step 2: Update `.env.example`** — replace the Qdrant block with:

```
# Real retrieval is OFF by default. Turn on ONLY for an explicit Qdrant task.
LEX_KRATOS_ENABLE_QDRANT=false
# Client connect port AND compose host bind must match (see docs/.../specs).
# 6533 avoids a foreign Qdrant that may already hold :6333.
QDRANT_HOST=localhost
QDRANT_PORT=6533
QDRANT_HOST_PORT=6533
QDRANT_COLLECTION=lex_kratos_chunks
# Optional override; default = sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384-dim).
LEX_KRATOS_EMBEDDING_MODEL=
```

- [ ] **Step 3: Parameterize the compose host port** in `docker-compose.yml`

Change the `qdrant` service `ports:` from `- "6333:6333"` to:

```yaml
    ports:
      - "${QDRANT_HOST_PORT:-6533}:6333"
      - "${QDRANT_GRPC_HOST_PORT:-6534}:6334"
```

- [ ] **Step 4: Verify compose still parses**

Run: `QDRANT_HOST_PORT=6533 docker compose config | grep -A3 ports`
Expected: shows host `6533` mapped to container `6333`.

- [ ] **Step 5: Commit**

```bash
git add requirements-qdrant.txt .env.example docker-compose.yml
git commit -m "chore(rag): pin fastembed; env + compose for Qdrant on port 6533"
```

---

## Task 5: Docs

**Files:**
- Modify: `CHANGELOG.md`, `README.md`

- [ ] **Step 1: Add a CHANGELOG entry** (top of the Unreleased/Added section) noting: optional real Qdrant retrieval behind `LEX_KRATOS_ENABLE_QDRANT`; local fastembed multilingual embeddings; eval stays mock-only; runs on port 6533.

- [ ] **Step 2: Add a README run-note** — a short "Real retrieval (optional)" subsection with the exact sequence from Task 6 (install extra, bring up Qdrant on 6533, set flag, restart app). State the ~0.22 GB first-run model download.

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md README.md
git commit -m "docs(rag): document optional real Qdrant retrieval path"
```

---

## Task 6: Live verification (options 1 & 3) — manual acceptance

> Not TDD; this is the live go/no-go. Run from the repo root with the venv.

- [ ] **Step 1 — Option 1 baseline (mock):** Start the app: `.venv/bin/uvicorn app.main:app --port 8000` (background). Confirm health: `curl -s localhost:8000/health`. Copy plugin: `cp -r integrations/hermes/lex_kratos ~/.hermes/plugins/lex_kratos`. In `hermes`, `/plugins` lists `lex_kratos`; run `lex_run_pipeline` with a manual case → returns a pipeline result. `curl -s -XPOST localhost:8000/rag/search -H 'content-type: application/json' -d '{"query":"fraude bancária","top_k":3}'` → `vector_backend":"mock"`. **Baseline confirmed.**

- [ ] **Step 2 — Bring up pinned Qdrant on 6533:** `QDRANT_HOST_PORT=6533 docker compose up -d qdrant`. Confirm: `curl -s localhost:6533/ | grep -o '"version":"[^"]*"'` → `1.14.x` (NOT the foreign 1.7.4 on 6333).

- [ ] **Step 3 — Install the extra + restart app with the flag:** `.venv/bin/pip install -r requirements-qdrant.txt`. Stop the mock uvicorn; restart with env: `LEX_KRATOS_ENABLE_QDRANT=true QDRANT_PORT=6533 .venv/bin/uvicorn app.main:app --port 8000` (first call triggers the ~0.22 GB model download).

- [ ] **Step 4 — Index via the plugin, then search:** Run `lex_run_pipeline` again (now indexes into Qdrant). Then `curl -s -XPOST localhost:8000/rag/search -H 'content-type: application/json' -d '{"query":"fraude bancária","top_k":3}'` → `"vector_backend":"qdrant"`, `"status":"success"`, each hit `"retrieval_method":"qdrant"`.

- [ ] **Step 5 — Prove semantic retrieval:** issue a paraphrased query with no token overlap and confirm a sensible hit still returns (the core win over the mock). Record the observed `vector_backend`, hit count, and top score.

- [ ] **Step 6 — Run the gated integration tests against the live server:**

Run: `LEX_KRATOS_ENABLE_QDRANT=true QDRANT_PORT=6533 .venv/bin/python -m pytest tests/integration -v`
Expected: 2 passed.

- [ ] **Step 7 — Confirm flag-off still defaults to mock** (no regression): stop the flagged app; `.venv/bin/python -m pytest -q` → full suite green, integration skipped.

---

## Done criteria (from spec §8)
- Pipeline via the `lex_kratos` plugin indexes into Qdrant without error (flag on, server up).
- `/rag/search` returns `vector_backend=qdrant`, `status=success`, each hit `retrieval_method=qdrant`, `RetrievedContext` shape.
- A paraphrased (no token-overlap) query returns the semantically-correct chunk.
- Default `pytest` passes unchanged & offline; integration tests skip cleanly when Qdrant/fastembed absent.
- `ruff check` + `ruff format` clean; mypy clean on touched files.
- Mock path, eval, and CI behavior unchanged when the flag is off.
