---
name: radar-pauta
description: Monitora tendências jurídicas, novas legislações e jurisprudências para alimentar o pipeline de conteúdo.
author: Manus AI
version: 1.0.0
---

# Radar de Pauta

Responsável por identificar temas quentes no ecossistema jurídico e tecnológico, sugerindo pautas relevantes para a produção de conteúdo (FIRAC e Pillar).

## Quando usar

- No início do ciclo de planejamento de conteúdo (ex: semanalmente).
- Para descobrir novas decisões do STJ/STF ou resoluções do CNJ relacionadas à tecnologia.
- Para buscar *trending topics* em plataformas jurídicas.

## Procedimento

1.  **Busca de Fontes:** Utilize ferramentas de busca (web search) ou acesse APIs de tribunais (se configurado via n8n/webhooks) para procurar por "tecnologia", "IA", "resolução", "jurisprudência STJ".
2.  **Filtragem:** Selecione apenas temas que tenham impacto real (não apenas notícias superficiais).
3.  **Sugestão:** Apresente 3 a 5 sugestões de pauta, incluindo:
    - Título sugerido.
    - Fonte principal (link ou número do processo/resolução).
    - Breve justificativa de relevância.
4.  **Integração:** As sugestões aprovadas devem ser passadas para o `firac-engine` para análise aprofundada.

## Armadilhas (Pitfalls)

- Não sugira temas genéricos (ex: "O que é IA"). Foque em aplicações práticas, decisões ou regulamentações.
- Certifique-se de que a fonte é confiável (sites oficiais de tribunais, portais jurídicos reconhecidos).
