from typing import Protocol

from pydantic import BaseModel, Field

_MARKER_TEMPLATES: dict[str, str] = {
    "peticao_inicial": (
        "DOS FATOS\n"
        "O autor Consumidor Alfa sofreu fraude bancaria via pix realizada por terceiro.\n\n"
        "DO DIREITO\n"
        "A responsabilidade do fornecedor de servico e objetiva na forma do CDC.\n\n"
        "DOS PEDIDOS\n"
        "Requer a condenacao do reu ao pagamento de indenizacao por danos morais e materiais.\n"
    ),
    "contestacao": (
        "DAS PRELIMINARES\n"
        "O reu Banco Beta suscita a ausencia de interesse processual do autor.\n\n"
        "DO MERITO\n"
        "Sustenta a culpa exclusiva de terceiro e a inexistencia de falha na prestacao do servico.\n\n"
        "DOS PEDIDOS\n"
        "Requer a total improcedencia dos pedidos formulados na inicial.\n"
    ),
    "sentenca": (
        "RELATÓRIO\n"
        "Trata-se de acao de indenizacao proposta por Consumidor Alfa em face de Banco Beta.\n\n"
        "FUNDAMENTAÇÃO\n"
        "A responsabilidade do banco e objetiva conforme entendimento consolidado dos tribunais superiores.\n\n"
        "DISPOSITIVO\n"
        "Julgo parcialmente procedentes os pedidos para condenar o reu ao pagamento de danos morais.\n"
    ),
    "acordao": (
        "TRIBUNAL DE JUSTICA - QUARTA CAMARA CIVEL\n"
        "APELACAO CIVEL Nº 0001234-56.2026.8.08.0001\n"
        "RELATOR: Desembargador Fulano de Tal\n"
        "Publicado no DJe de 15/01/2026\n"
        "EMENTA\n"
        "Responsabilidade civil bancaria. Fraude praticada por terceiro. Responsabilidade objetiva.\n\n"
        "RELATÓRIO\n"
        "O banco apelou da sentenca que reconheceu a falha na prestacao do servico.\n\n"
        "VOTO\n"
        "A tese da culpa exclusiva de terceiro nao afasta a responsabilidade objetiva do banco.\n\n"
        "DISPOSITIVO\n"
        "Nego provimento ao recurso e mantenho a sentenca por seus proprios fundamentos.\n"
    ),
    "unknown": (
        "Documento nao classificado. Conteudo insuficiente para extracao juridica confiavel.\n"
    ),
}

_DOC_TYPES = ("peticao_inicial", "contestacao", "sentenca", "acordao")


class ExtractedDocument(BaseModel):
    text: str = Field(min_length=1)
    doc_type: str
    doc_id: str = "doc_unknown"
    file_path: str | None = None
    page_count: int = Field(default=1, ge=1)
    quality_score: float = Field(default=0.95, ge=0.0, le=1.0)
    extraction_method: str = "mock"
    metadata: dict = Field(default_factory=dict)


class Extractor(Protocol):
    def extract(
        self, file_path: str, doc_type: str | None = None
    ) -> ExtractedDocument: ...
    def supports(self, file_path: str) -> bool: ...


class MockExtractor:
    """Returns marker-rich structured text per doc_type (prepared interface; no real IO)."""

    def supports(self, file_path: str) -> bool:
        return str(file_path).lower().endswith((".pdf", ".txt"))

    def extract(self, file_path: str, doc_type: str | None = None) -> ExtractedDocument:
        resolved = doc_type or self._infer(file_path)
        text = _MARKER_TEMPLATES.get(resolved, _MARKER_TEMPLATES["unknown"])
        return ExtractedDocument(
            text=text,
            doc_type=resolved,
            file_path=file_path,
            extraction_method="mock",
        )

    @staticmethod
    def _infer(file_path: str) -> str:
        lowered = str(file_path).lower()
        for candidate in _DOC_TYPES:
            if candidate.split("_")[0] in lowered:
                return candidate
        return "unknown"
