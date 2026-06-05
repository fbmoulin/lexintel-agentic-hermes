---
name: analista-desempenho
description: Analisa métricas de engajamento de conteúdos publicados e gera insights para otimização das skills de produção (Feedback Loop).
author: Manus AI
version: 1.0.0
---

# Analista de Desempenho

Atua no fim do pipeline, coletando dados de engajamento (likes, saves, comentários) das publicações e retroalimentando o sistema para melhorar os prompts de geração.

## Quando usar

- Após a publicação de um ciclo de conteúdo (ex: semanalmente).
- Quando houver necessidade de ajustar o tom de voz baseado no que a audiência mais engajou.

## Procedimento

1.  **Coleta de Dados:** Receba os dados de engajamento das plataformas (pode ser via webhook do n8n ou input manual).
2.  **Análise Comparativa:** Compare os posts de alta performance com os de baixa performance.
3.  **Extração de Padrões:** Identifique quais formatos (carrossel vs reel), temas ou estilos de gancho (hook) funcionaram melhor.
4.  **Feedback Loop:** Gere recomendações claras de ajuste para as skills `atomizador` e `apresentador-video`.
    - *Exemplo:* "A audiência respondeu 40% melhor a ganchos que começam com uma pergunta. Atualizar o prompt do atomizador para priorizar este formato."

## Armadilhas (Pitfalls)

- Não analise métricas de vaidade isoladas. Foque em métricas de retenção (saves, watch time).
- As recomendações devem ser acionáveis, ou seja, instruções claras de como alterar o prompt da skill geradora.
