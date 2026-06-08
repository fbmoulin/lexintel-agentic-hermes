# Catálogo de Skills e Agentes

O catálogo local conecta as skills Markdown versionadas em `app/skills/` às capacidades agenticas do Lex Kratos Agentic Core.

Ele é apenas um mecanismo local de auditoria e descoberta. Não carrega LLMs, não executa integrações reais e não usa serviços externos.

## Endpoints

```text
GET /catalog/skills
GET /catalog/skills/{skill_name}
GET /catalog/agents
```

## Skills

Cada skill é um arquivo local `SKILL_*.md`. O loader:

- usa caminho absoluto derivado do pacote `app`;
- rejeita nomes com diretórios;
- aceita apenas arquivos no padrão `SKILL_*.md`;
- extrai título, seções, número de linhas e número de caracteres.

## Agentes

O registry registra 12 capacidades:

- `IntakeAgent` — implementado.
- `SecurityAgent` — implementado.
- `ExtractionAgent` — implementado.
- `LegalNormalizerAgent` — implementado.
- `MetadataAgent` — implementado.
- `IndexingAgent` — implementado.
- `HybridRetrievalAgent` — planejado.
- `FIRACAgent` — implementado.
- `JurisprudenceAgent` — planejado.
- `DraftingAgent` — planejado.
- `ValidatorAgent` — implementado.
- `EvaluationAgent` — planejado como agente; avaliação mockada existe em `app.evals`.

## Regras

- Agentes implementados devem ter classe importável.
- Toda capacidade deve apontar para uma skill existente.
- Toda skill versionada deve estar mapeada no registry.
- Fases de análise FIRAC, validação jurisprudencial, minuta e validação judicial exigem `requires_human_review`.
- Agentes planejados permanecem explicitamente marcados como `planned`.
- Testes continuam locais e determinísticos.
