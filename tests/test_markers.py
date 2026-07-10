from app.services.markers import detect_sections

SENTENCA = (
    "RELATÓRIO\n"
    "Trata-se de acao de indenizacao.\n\n"
    "FUNDAMENTAÇÃO\n"
    "A responsabilidade do banco e objetiva.\n\n"
    "DISPOSITIVO\n"
    "Julgo parcialmente procedentes os pedidos.\n"
)


def test_detects_three_sections_in_sentenca():
    sections = detect_sections(SENTENCA, "sentenca")
    assert [s.unit_type for s in sections] == ["relatorio", "fundamentos", "dispositivo"]
    assert "Trata-se" in sections[0].text
    assert "objetiva" in sections[1].text


def test_returns_none_without_markers():
    assert detect_sections("um paragrafo qualquer sem cabecalhos", "sentenca") is None


def test_returns_none_with_single_marker():
    assert detect_sections("RELATÓRIO\nso um cabecalho aqui", "sentenca") is None


def test_unknown_doc_type_returns_none():
    assert detect_sections(SENTENCA, "algo_desconhecido") is None


def test_marker_mid_line_not_detected():
    # "RELATÓRIO" must be its own line (^\s*...\s*$), not embedded.
    text = "no meio do RELATÓRIO texto\noutra linha DISPOSITIVO aqui"
    assert detect_sections(text, "sentenca") is None
