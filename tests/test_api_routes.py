from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_rag_search_returns_mock_result():
    response = client.post(
        "/rag/search",
        json={"query": "responsabilidade de banco", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "responsabilidade de banco"
    assert data["top_k"] == 3
    assert data["results"][0]["retrieval_method"] == "mock"


def test_rag_search_rejects_invalid_top_k():
    response = client.post(
        "/rag/search",
        json={"query": "responsabilidade de banco", "top_k": 0},
    )

    assert response.status_code == 422


def test_eval_endpoint_runs():
    response = client.get("/eval/run")

    assert response.status_code == 200
    data = response.json()
    assert data["dataset_size"] == 4
    assert "average_recall" in data


def test_full_mock_pipeline_runs_all_available_agents():
    payload = {
        "case_id": "caso_full_mock_001",
        "source_type": "manual",
        "user_goal": "analise",
        "files": ["peticao_inicial.pdf", "sentenca.pdf"],
    }

    response = client.post("/cases/run-full-mock", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "caso_full_mock_001"
    assert data["status"] == "success"
    assert data["mock_draft"]["relatorio"] == "Relatório simulado."

    agent_names = [entry["agent_name"] for entry in data["trace"]]
    assert agent_names == [
        "IntakeAgent",
        "SecurityAgent",
        "ExtractionAgent",
        "LegalNormalizerAgent",
        "MetadataAgent",
        "FIRACAgent",
        "ValidatorAgent",
    ]


def test_invalid_case_payload_is_rejected():
    response = client.post(
        "/cases/intake",
        json={
            "case_id": "caso_invalido_001",
            "source_type": "legacy_repo",
            "user_goal": "minuta",
            "files": [],
        },
    )

    assert response.status_code == 422
