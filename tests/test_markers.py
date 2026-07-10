from app.services.markers import detect_sections, extract_acordao_metadata

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
    assert [s.unit_type for s in sections] == [
        "relatorio",
        "fundamentos",
        "dispositivo",
    ]
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


def test_adjacent_markers_drop_empty_section_no_marker_leak():
    # M3: an empty section body between adjacent markers must be dropped, and no
    # marker text may leak into any body.
    text = (
        "DOS FATOS\nDO DIREITO\nconteudo do direito aqui.\nDOS PEDIDOS\npedido final.\n"
    )
    sections = detect_sections(text, "peticao_inicial")
    assert sections is not None
    assert "fatos" not in [s.unit_type for s in sections]  # empty section dropped
    assert all(s.text.strip() != "DO DIREITO" for s in sections)
    assert all(
        s.text.strip() not in {"DOS FATOS", "DO DIREITO", "DOS PEDIDOS"}
        for s in sections
    )
    direito = next(s for s in sections if s.unit_type == "direito")
    assert "conteudo do direito" in direito.text


ACORDAO_HEADER = (
    "TRIBUNAL DE JUSTICA - QUARTA CAMARA CIVEL\n"
    "APELACAO CIVEL Nº 0001234-56.2026.8.08.0001\n"
    "RELATOR: Desembargador Fulano de Tal\n"
    "Publicado no DJe de 15/01/2026\n"
    "EMENTA\n...\n"
)


def test_extract_acordao_metadata_pulls_header_fields():
    meta = extract_acordao_metadata(ACORDAO_HEADER)
    assert meta["orgao_julgador"] == "QUARTA CAMARA CIVEL"
    assert meta["numero"] == "0001234-56.2026.8.08.0001"
    assert meta["relator"] == "Desembargador Fulano de Tal"
    assert meta["tipo_recurso"] == "APELACAO"
    assert meta["data_publicacao"] == "15/01/2026"


def test_extract_acordao_metadata_missing_fields_are_none():
    meta = extract_acordao_metadata("texto sem cabecalho estruturado")
    assert all(meta[k] is None for k in meta)
