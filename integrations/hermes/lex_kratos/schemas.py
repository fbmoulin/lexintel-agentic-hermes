"""LLM-facing tool schemas for the lex_kratos Hermes plugin."""

_CASE_PROPERTIES = {
    "case_id": {
        "type": "string",
        "description": "Identificador do caso (ex.: 'caso-2026-001').",
    },
    "source_type": {
        "type": "string",
        "enum": ["pdf", "datajud", "manual", "drive", "pje_export"],
        "description": "Origem do caso. Default: manual.",
    },
    "user_goal": {
        "type": "string",
        "enum": ["minuta", "analise", "triagem", "jurimetria", "relatorio"],
        "description": "Objetivo do usuário. Default: analise.",
    },
    "files": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Nomes/caminhos dos documentos do caso (ex.: 'peticao_inicial.pdf').",
    },
}

LEX_INTAKE = {
    "name": "lex_intake",
    "description": (
        "Roda apenas intake + segurança do pipeline jurídico Lex Kratos (mock "
        "v0.1) sobre um caso. Use para triagem rápida e detecção de prompt "
        "injection. Retorna trace auditável; nunca para uso externo sem revisão."
    ),
    "parameters": {
        "type": "object",
        "properties": _CASE_PROPERTIES,
        "required": ["case_id"],
    },
}

LEX_RUN_PIPELINE = {
    "name": "lex_run_pipeline",
    "description": (
        "Roda o pipeline jurídico Lex Kratos completo (mock v0.1): intake, "
        "segurança, extração, normalização, metadados, indexação, FIRAC+ e "
        "validação. Retorna trace auditável com flags de revisão humana. "
        "Saída SEMPRE requer revisão humana e não é para uso externo."
    ),
    "parameters": {
        "type": "object",
        "properties": _CASE_PROPERTIES,
        "required": ["case_id"],
    },
}
