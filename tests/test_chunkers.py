import pytest
from pydantic import ValidationError

from app.schemas.case import LegalChunk
from app.services.chunking import (
    ParagraphChunker,
    estimate_tokens,
    split_sentences,
)


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
