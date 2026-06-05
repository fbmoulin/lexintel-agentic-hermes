---
name: guardiao-politica
description: Atua como gatekeeper de compliance (Evaluator) em um loop Evaluator-Optimizer, validando a conformidade jurídica, tom de voz e aderência à marca de qualquer conteúdo gerado antes da publicação.
author: Manus AI
version: 1.0.0
---

# Guardião de Política

Atua como o "Juiz" em um padrão Evaluator-Optimizer. Valida a conformidade jurídica (ex: Resolução CNJ 615/2025), a aderência à marca Lex Intelligentia e o tom de voz do conteúdo.

## Quando usar

- ANTES de aprovar qualquer conteúdo para publicação.
- Como `evaluator` em um loop com o `firac-engine` ou `atomizador`.
- Para garantir que nenhuma afirmação legal seja feita sem base (prevenção de alucinação).

## Procedimento

1.  **Recepção:** Receba o conteúdo gerado (texto, roteiro, etc.).
2.  **Validação Jurídica:** Verifique se todas as afirmações legais possuem base normativa (ex: cita a lei/resolução correta). Se não, reprove e peça correção.
3.  **Validação de Marca:** Verifique se a paleta de cores (Laranja Lex, Carvão) e a tipografia estão sendo respeitadas (se aplicável).
4.  **Validação de Tom:** O tom deve ser técnico, direto e profissional, sem jargões desnecessários ou emojis excessivos.
5.  **Feedback:** Forneça um feedback específico e acionável. Se o conteúdo estiver perfeito, responda com `EXCELLENT`. Caso contrário, detalhe o que precisa ser ajustado.

## Armadilhas (Pitfalls)

- Não reescreva o texto. O papel do Guardião é avaliar e apontar erros, não gerar conteúdo novo.
- Seja objetivo no feedback para não confundir o gerador no loop.
