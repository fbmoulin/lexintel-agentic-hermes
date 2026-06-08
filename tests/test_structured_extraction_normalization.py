from fastapi.testclient import TestClient

from app.agents.extraction_agent import ExtractionAgent
from app.agents.normalizer_agent import LegalNormalizerAgent
from app.main import app
from app.schemas.case import ExtractedText, NormalizedCase


client = TestClient(app)


def test_extraction_agent_returns_pydantic_validated_records():
    documents = [
        {
            "doc_id": "doc_1",
            "file_path": "peticao_inicial.pdf",
            "doc_type": "peticao_inicial",
        },
        {
            "doc_id": "doc_2",
            "file_path": "contestacao.pdf",
            "doc_type": "contestacao",
        },
        {
            "doc_id": "doc_3",
            "file_path": "sentenca.pdf",
            "doc_type": "sentenca",
        },
        {
            "doc_id": "doc_4",
            "file_path": "acordao.pdf",
            "doc_type": "acordao",
        },
    ]

    result = ExtractionAgent().run("caso_extracao_001", documents)

    assert result.status == "success"
    assert result.output["extraction_schema_version"] == "extraction-mock-v0.1"
    assert result.output["quality_summary"] == {
        "document_count": 4,
        "page_count": 4,
        "min_quality_score": 0.92,
        "average_quality_score": 0.92,
        "low_quality_pages": [],
        "automation_allowed": True,
    }

    extracted_text = result.output["extracted_text"]
    assert [item["doc_type"] for item in extracted_text] == [
        "peticao_inicial",
        "contestacao",
        "sentenca",
        "acordao",
    ]
    assert all(ExtractedText.model_validate(item) for item in extracted_text)
    assert all(item["page"] == 1 for item in extracted_text)
    assert all(item["quality_score"] == 0.92 for item in extracted_text)


def test_extraction_agent_marks_unknown_document_as_low_quality():
    result = ExtractionAgent().run(
        "caso_extracao_unknown_001",
        [{
            "doc_id": "doc_1",
            "file_path": "documento_generico.pdf",
            "doc_type": "unknown",
        }],
    )

    assert result.status == "warning"
    assert result.requires_human_review is True
    assert result.output["quality_summary"]["automation_allowed"] is False
    assert result.output["quality_summary"]["low_quality_pages"] == ["doc_1:p1"]
    assert result.output["extracted_text"][0]["quality_score"] == 0.68


def test_extraction_agent_marks_empty_document_list_for_review():
    result = ExtractionAgent().run("caso_sem_documentos_001", [])

    assert result.status == "warning"
    assert result.requires_human_review is True
    assert result.output["quality_summary"] == {
        "document_count": 0,
        "page_count": 0,
        "min_quality_score": 0.0,
        "average_quality_score": 0.0,
        "low_quality_pages": [],
        "automation_allowed": False,
    }


def test_normalizer_agent_extracts_structured_legal_fields():
    extracted = ExtractionAgent().run(
        "caso_normalizacao_001",
        [
            {
                "doc_id": "doc_1",
                "file_path": "peticao_inicial.pdf",
                "doc_type": "peticao_inicial",
            },
            {
                "doc_id": "doc_2",
                "file_path": "contestacao.pdf",
                "doc_type": "contestacao",
            },
            {
                "doc_id": "doc_3",
                "file_path": "sentenca.pdf",
                "doc_type": "sentenca",
            },
            {
                "doc_id": "doc_4",
                "file_path": "acordao.pdf",
                "doc_type": "acordao",
            },
        ],
    )

    result = LegalNormalizerAgent().run(
        "caso_normalizacao_001",
        extracted.output["extracted_text"],
    )

    normalized = NormalizedCase.model_validate(result.output)
    assert result.status == "success"
    assert normalized.document_types == [
        "acordao",
        "contestacao",
        "peticao_inicial",
        "sentenca",
    ]
    assert {party.role for party in normalized.parties} == {"author", "defendant"}
    assert normalized.claims[0].claim_type == "indenizacao_dano_moral_material"
    assert normalized.defenses[0].defense_type == "culpa_exclusiva_terceiro"
    assert {event.event_type for event in normalized.procedural_events} == {
        "sentenca_publicada",
        "julgamento_colegiado",
    }
    assert normalized.legal_issues[0].issue_type == "responsabilidade_bancaria_fraude"


def test_full_mock_pipeline_exposes_structured_extraction_and_metadata():
    response = client.post(
        "/cases/run-full-mock",
        json={
            "case_id": "caso_pipeline_estruturado_001",
            "source_type": "manual",
            "user_goal": "analise",
            "files": [
                "peticao_inicial.pdf",
                "contestacao.pdf",
                "sentenca.pdf",
                "acordao.pdf",
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    extraction_output = data["trace"][2]["output"]
    normalization_output = data["trace"][3]["output"]
    metadata_output = data["trace"][4]["output"]

    assert extraction_output["quality_summary"]["automation_allowed"] is True
    assert len(extraction_output["extracted_text"]) == 4
    assert normalization_output["normalization_schema_version"] == (
        "normalization-mock-v0.1"
    )
    assert metadata_output["metadata_schema_version"] == "metadata-mock-v0.1"
    assert metadata_output["document_count"] == 4
    assert metadata_output["has_petition"] is True
    assert metadata_output["has_defense"] is True
    assert metadata_output["has_decision"] is True
    assert metadata_output["has_appeal_decision"] is True
