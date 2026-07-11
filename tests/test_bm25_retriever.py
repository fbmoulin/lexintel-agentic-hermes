from app.services.bm25 import BM25Retriever

CHUNKS = [
    {
        "chunk_id": "banco", "case_id": "seed", "doc_id": "d1", "unit_type": "tese",
        "text": "Responsabilidade objetiva do banco por fraude de terceiro.",
        "page_start": 1, "page_end": 1, "source": "seed",
        "metadata": {"source_ref": "Súmula 479/STJ"},
    },
    {
        "chunk_id": "saude", "case_id": "seed", "doc_id": "d2", "unit_type": "tese",
        "text": "Plano de saúde e rol da ANS, Tema 1082.",
        "page_start": 1, "page_end": 1, "source": "seed",
        "metadata": {"source_ref": "Tema 1082/STJ", "area": "saude"},
    },
    {
        "chunk_id": "tutela", "case_id": "seed", "doc_id": "d3", "unit_type": "fundamentos",
        "text": "Tutela de urgência exige probabilidade do direito, art. 300 CPC.",
        "page_start": 1, "page_end": 1, "source": "seed",
        "metadata": {"source_ref": "art. 300 CPC"},
    },
]


def test_ranks_most_relevant_first():
    retriever = BM25Retriever(CHUNKS)
    results = retriever.search("fraude no banco", top_k=3)
    assert results[0]["chunk_id"] == "banco"
    assert results[0]["metadata"]["retrieval_method"] == "bm25"


def test_accent_folding_matches():
    retriever = BM25Retriever(CHUNKS)
    results = retriever.search("saude ans", top_k=1)
    assert results[0]["chunk_id"] == "saude"


def test_applies_metadata_filters():
    retriever = BM25Retriever(CHUNKS)
    results = retriever.search("rol", top_k=3, filters={"area": "saude"})
    assert [r["chunk_id"] for r in results] == ["saude"]


def test_deterministic_tie_break_by_chunk_id():
    tied = [
        {**CHUNKS[0], "chunk_id": "b_id", "text": "termo comum unico"},
        {**CHUNKS[0], "chunk_id": "a_id", "text": "termo comum unico"},
    ]
    retriever = BM25Retriever(tied)
    results = retriever.search("termo comum unico", top_k=2)
    assert [r["chunk_id"] for r in results] == ["a_id", "b_id"]


def test_no_match_returns_empty():
    retriever = BM25Retriever(CHUNKS)
    assert retriever.search("xyzxyz inexistente", top_k=3) == []


def test_empty_corpus_returns_empty_and_does_not_crash():
    # build_default_hybrid_agent builds BM25 from snapshot_chunks(), which can be
    # empty (e.g. a fresh store); the avgdl guard must hold.
    retriever = BM25Retriever([])
    assert retriever.search("qualquer coisa", top_k=3) == []


def test_top_k_truncates_results():
    retriever = BM25Retriever(CHUNKS)
    # "de" appears across chunks; request fewer than the number of positive matches.
    results = retriever.search("banco saude tutela urgencia fraude", top_k=1)
    assert len(results) == 1
