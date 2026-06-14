---
name: legal-pdf-extraction
description: "Extrai texto juridicamente útil de PDFs e imagens via OCR."
version: 1.0.0
metadata:
  hermes:
    tags: [pdf, ocr, extracao]
    category: legal-br
---

# SKILL_LEGAL_PDF_EXTRACTION

## Objetivo
Extrair texto juridicamente útil de PDFs e imagens OCR.

## Procedimento
1. Extrair texto por página.
2. Preservar numeração de página.
3. Identificar cabeçalhos, rodapés e assinaturas.
4. Marcar trechos ilegíveis.
5. Calcular quality_score.
6. Bloquear automação quando quality_score < 0.70.
