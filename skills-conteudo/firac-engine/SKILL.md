---
name: firac-engine
description: "Motor de análise jurídica avançada usando a metodologia FIRAC. Use quando o usuário pedir para analisar um caso, gerar uma minuta, ou estruturar argumentos legais de forma objetiva e em compliance com o CNJ."
version: 1.0.0
author: Lex Intelligentia
metadata:
  hermes:
    tags: [juridico, analise, firac, cnj]
    category: legal-intelligence
    config:
      - key: firac.strict_compliance
        description: "Forçar compliance rigoroso com Resoluções CNJ 332/2020 e 615/2025"
        default: "true"
        prompt: "Ativar compliance rigoroso do CNJ?"
---

# Motor de Análise FIRAC (Enterprise V3)

Este motor processa fatos, documentos e pedidos utilizando a metodologia FIRAC estruturada, garantindo análises jurídicas lógicas, rastreáveis e em conformidade com as diretrizes do Conselho Nacional de Justiça (CNJ).

## When to Use

Use esta skill quando:
- O usuário solicitar a análise de um caso concreto ou conjunto de fatos.
- For necessário gerar o esqueleto ou a fundamentação para uma minuta de decisão, despacho ou petição.
- O usuário pedir para "aplicar o FIRAC" ou "estruturar juridicamente" uma situação.
- O contexto envolver a necessidade de justificar uma decisão com base em regras e precedentes.

## Quick Reference

- **Metodologia Completa:** `skill_view("firac-engine", "references/metodologia-firac.md")`
- **Regras de Compliance CNJ:** `skill_view("firac-engine", "references/compliance-cnj.md")`

## Procedure

1. **Revisão de Metodologia e Compliance:** Se você ainda não carregou nesta sessão, use `skill_view` para ler `references/metodologia-firac.md` e `references/compliance-cnj.md`. Compreenda as restrições antes de iniciar a análise.
2. **Coleta de Fatos:** Analise os documentos fornecidos ou a descrição do usuário. Se o usuário fornecer um arquivo PDF, use o script de extração local executando `!/home/ubuntu/lex-intelligentia/skills-conteudo/firac-engine/scripts/extract_pdf.py <caminho_do_pdf>` no terminal para obter o texto estruturado. Em seguida, extraia os Fatos (F) de forma objetiva, sem valoração jurídica.
3. **Identificação de Questões:** Formule as Questões (I - Issues) jurídicas centrais que precisam ser respondidas.
4. **Mapeamento de Regras:** Identifique as Regras (R) aplicáveis (Leis, Súmulas, Precedentes Qualificados). **NUNCA** invente jurisprudência. Se necessário, solicite ao usuário que forneça as regras ou use ferramentas de busca na web, se disponíveis.
5. **Aplicação (Chain of Thought):** Para cada Questão, conecte a Regra aos Fatos (A - Application). Demonstre o raciocínio lógico passo a passo. Aplique a verificação de *distinguishing* ou *overruling* se estiver usando precedentes.
6. **Conclusão:** Forneça a Conclusão (C) direta e objetiva para cada Questão.
7. **Formatação da Saída:** Apresente o resultado final estruturado com os cabeçalhos: **1. Fatos**, **2. Questões**, **3. Regras Aplicáveis**, **4. Análise (Aplicação)** e **5. Conclusão**.

## Pitfalls

- **Alucinação de Jurisprudência:** O erro mais crítico. Se não tiver certeza de uma Súmula ou artigo de lei, declare a incerteza ou peça confirmação.
- **Misturar Fatos e Análise:** A seção de Fatos deve ser puramente descritiva. Guarde os adjetivos e julgamentos de valor para a seção de Aplicação.
- **Ignorar o Compliance CNJ:** Falhar em justificar o raciocínio na seção de Aplicação viola a diretriz de explicabilidade (Res. 332/2020).

## Verification

A análise foi bem-sucedida se:
1. A saída segue estritamente os 5 cabeçalhos do FIRAC.
2. Nenhuma regra jurídica foi inventada.
3. A conclusão responde diretamente às questões levantadas.
4. O raciocínio na seção de Aplicação é lógico e rastreável.
