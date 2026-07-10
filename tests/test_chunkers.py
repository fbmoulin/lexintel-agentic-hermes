import pytest
from pydantic import ValidationError

from app.schemas.case import LegalChunk
from app.services.chunking import (
    ParagraphChunker,
    StructuralChunker,
    build_chunks,
    estimate_tokens,
    get_chunker,
    split_sentences,
)
from tests.test_markers import ACORDAO_HEADER, SENTENCA


@pytest.mark.parametrize("unit_type", ["fatos", "direito", "preliminares", "merito"])
def test_legal_chunk_accepts_new_structural_unit_types(unit_type):
    chunk = LegalChunk(
        chunk_id="c1",
        case_id="caso",
        doc_id="doc_1",
        unit_type=unit_type,
        text="x",
        page_start=1,
        page_end=1,
    )
    assert chunk.unit_type == unit_type


def test_legal_chunk_rejects_unknown_unit_type():
    with pytest.raises(ValidationError):
        LegalChunk(
            chunk_id="c1",
            case_id="caso",
            doc_id="doc_1",
            unit_type="nao_existe",
            text="x",
            page_start=1,
            page_end=1,
        )


def test_estimate_tokens_counts_words():
    assert estimate_tokens("um dois tres quatro") == 4
    assert estimate_tokens("   ") == 0


def test_split_sentences_keeps_terminators_and_ignores_trailing_space():
    text = "Primeira frase. Segunda frase! Terceira frase?"
    assert split_sentences(text) == [
        "Primeira frase.",
        "Segunda frase!",
        "Terceira frase?",
    ]


def test_split_sentences_single_sentence_without_terminator():
    assert split_sentences("sem ponto final") == ["sem ponto final"]


def test_paragraph_chunker_single_small_text_one_chunk():
    chunks = ParagraphChunker().chunk("texto curto de teste", unit_type="documento")
    assert len(chunks) == 1
    assert chunks[0]["unit_type"] == "documento"
    assert chunks[0]["metadata"]["chunking_strategy"] == "paragraph_v0.2"
    assert chunks[0]["text"] == "texto curto de teste"


def test_paragraph_chunker_respects_unit_type_param():
    chunks = ParagraphChunker().chunk("conteudo", unit_type="fundamentos")
    assert chunks[0]["unit_type"] == "fundamentos"


def test_paragraph_chunker_splits_oversized_text_with_overlap():
    # 900 one-word "sentences." -> exceeds max_tokens=800 -> splits; overlap marker present.
    sentence = "palavra."
    big = " ".join([sentence] * 900)
    chunks = ParagraphChunker(max_tokens=800).chunk(big, unit_type="documento")
    assert len(chunks) >= 2
    assert all(c["unit_type"] == "documento" for c in chunks)
    assert chunks[1]["text"].startswith("[...]")


def test_paragraph_chunker_empty_text_returns_empty():
    assert ParagraphChunker().chunk("   ", unit_type="documento") == []


def test_structural_chunker_sentenca_three_sections():
    chunks = StructuralChunker().chunk(SENTENCA, "sentenca")
    assert [c["unit_type"] for c in chunks] == [
        "relatorio",
        "fundamentos",
        "dispositivo",
    ]
    assert all(c["metadata"]["chunking_strategy"] == "structural_v0.2" for c in chunks)


def test_structural_chunker_acordao_attaches_metadata_to_all_chunks():
    acordao = (
        ACORDAO_HEADER
        + "Corpo da ementa.\n\nVOTO\nCorpo do voto.\n\nDISPOSITIVO\nNego provimento.\n"
    )
    chunks = StructuralChunker().chunk(acordao, "acordao")
    assert len(chunks) >= 2
    assert all(
        c["metadata"]["acordao"]["relator"] == "Desembargador Fulano de Tal"
        for c in chunks
    )


def test_get_chunker_returns_structural_when_markers_present():
    assert isinstance(get_chunker(SENTENCA, "sentenca"), StructuralChunker)


def test_get_chunker_returns_paragraph_without_markers():
    assert isinstance(
        get_chunker("texto plano sem cabecalhos", "sentenca"), ParagraphChunker
    )


def test_get_chunker_paragraph_for_unknown_doc_type():
    assert isinstance(get_chunker(SENTENCA, "algo"), ParagraphChunker)


def _item(doc_id, doc_type, text, page=1):
    return {
        "doc_id": doc_id,
        "doc_type": doc_type,
        "text": text,
        "file_path": f"{doc_id}.pdf",
        "page": page,
        "quality_score": 0.9,
    }


def test_build_chunks_single_chunk_keeps_bare_id():
    # marker-free short text -> paragraph -> one chunk -> id has NO ordinal suffix.
    chunks = build_chunks("caso", [_item("doc_1", "peticao_inicial", "texto curto")])
    assert chunks[0]["chunk_id"] == "chunk_caso_doc_1_p1_pedido"
    assert chunks[0]["unit_type"] == "pedido"


def test_build_chunks_multichunk_section_gets_unique_ordinal_ids(monkeypatch):
    # Force an oversized single section so one (doc,page,unit) yields >1 chunk.
    big = "palavra. " * 2000
    text = f"RELATÓRIO\n{big}\n\nDISPOSITIVO\nfim.\n"
    chunks = build_chunks("caso", [_item("doc_1", "sentenca", text)])
    relatorio_ids = [c["chunk_id"] for c in chunks if c["unit_type"] == "relatorio"]
    assert len(relatorio_ids) >= 2
    assert len(set(relatorio_ids)) == len(relatorio_ids)  # no collisions
    assert relatorio_ids[0].endswith("_relatorio_0")


def test_build_chunks_skips_empty_text():
    assert build_chunks("caso", [_item("doc_1", "sentenca", "   ")]) == []
