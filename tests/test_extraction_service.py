from app.services.extraction import ExtractedDocument, MockExtractor
from app.services.markers import detect_sections


def test_mock_extractor_returns_extracted_document():
    doc = MockExtractor().extract("sentenca.pdf", "sentenca")
    assert isinstance(doc, ExtractedDocument)
    assert doc.doc_type == "sentenca"


def test_mock_extractor_sentenca_has_three_detectable_sections():
    doc = MockExtractor().extract("sentenca.pdf", "sentenca")
    sections = detect_sections(doc.text, "sentenca")
    assert [s.unit_type for s in sections] == [
        "relatorio",
        "fundamentos",
        "dispositivo",
    ]


def test_mock_extractor_acordao_has_four_sections_and_header():
    doc = MockExtractor().extract("acordao.pdf", "acordao")
    sections = detect_sections(doc.text, "acordao")
    assert len(sections) == 4
    assert "RELATOR" in doc.text and "DJe" in doc.text


def test_mock_extractor_infers_doc_type_from_filename():
    assert MockExtractor().extract("peticao_inicial.pdf").doc_type == "peticao_inicial"


def test_mock_extractor_unknown_has_no_sections():
    doc = MockExtractor().extract("random.pdf", "unknown")
    assert detect_sections(doc.text, "unknown") is None


def test_mock_extractor_supports_pdf():
    assert MockExtractor().supports("x.pdf") is True
