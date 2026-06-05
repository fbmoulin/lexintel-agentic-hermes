#!/usr/bin/env python3
"""
Wrapper para o pipeline de extração de PDF do Kratos.
Este script serve como ponte entre o Hermes Agent e a biblioteca de extração de PDF.
Ele recebe um caminho de arquivo PDF, executa a extração e retorna o Markdown limpo.
"""

import sys
import os
import json
import argparse

# Configuração de caminhos (simulando a integração com o Kratos)
KRATOS_PATH = "/home/ubuntu/lex-intelligentia/kratos-manus"
if os.path.exists(KRATOS_PATH):
    sys.path.append(KRATOS_PATH)

def extract_pdf(pdf_path: str, output_format: str = "markdown") -> str:
    """
    Simula a chamada ao pipeline de extração híbrido (Docling + pdfplumber).
    Na versão final, isso importaria e executaria o pipeline.py do Kratos.
    """
    if not os.path.exists(pdf_path):
        return f"ERRO: Arquivo não encontrado: {pdf_path}"
        
    try:
        # Placeholder para a integração real com o pipeline do Kratos
        # Em produção:
        # from workers.pdf_worker.src.pipeline import DocumentExtractionPipeline
        # pipeline = DocumentExtractionPipeline(...)
        # result = pipeline.process(pdf_path)
        
        # Simulação de sucesso para fins de teste do agente
        file_name = os.path.basename(pdf_path)
        
        if output_format == "json":
            return json.dumps({
                "status": "success",
                "document": file_name,
                "metadata": {
                    "pages": 10,
                    "extraction_method": "HYBRID"
                },
                "content": f"# Documento Extraído: {file_name}\n\nConteúdo simulado do PDF."
            })
            
        return f"""# Documento: {file_name}
> Extração via Pipeline Kratos (Híbrido)

## 1. Metadados do Processo
- **Arquivo:** {file_name}
- **Páginas:** [Simulado]

## 2. Conteúdo Extraído
(O conteúdo real do PDF seria inserido aqui após o processamento pelo Docling/pdfplumber)
"""
    except Exception as e:
        return f"ERRO na extração: {str(e)}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrai texto e estrutura de PDFs jurídicos.")
    parser.add_argument("pdf_path", help="Caminho para o arquivo PDF")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Formato de saída")
    
    args = parser.parse_args()
    
    resultado = extract_pdf(args.pdf_path, args.format)
    print(resultado)
