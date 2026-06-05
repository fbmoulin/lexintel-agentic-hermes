---
name: pillar-semana
description: Cria artigos densos (400-700 palavras) sobre IA e Direito, servindo como base (fonte da verdade) para toda a atomização de conteúdo da semana.
version: 1.1.0
author: Manus AI
metadata:
  hermes:
    tags: [conteudo, pillar, artigo, estrategia]
    category: producao
    related_skills: [atomizador, voz-marca-lex, firac-engine]
---

# Pillar da Semana

O Pillar é a peça-fonte do ecossistema de conteúdo da Lex Intelligentia. Ele é um artigo profundo, estruturado e ancorado em fatos reais, do qual todos os outros formatos (redes sociais, vídeos) derivarão.

## When to Use

Invoque o Pillar SEMPRE que:
* For solicitado a criar o "conteúdo da semana" ou o "tema principal".
* O usuário fornecer uma pauta ou decisão recente (ex: "Escreva sobre a nova Resolução do CNJ").
* For necessário aprofundar um tema jurídico-tecnológico para criar autoridade.

## Quick Reference

| Requisito | Detalhe |
| :--- | :--- |
| Tamanho | 400 a 700 palavras |
| Formato | Texto corrido (PT-BR), sem travessões, Markdown |
| Grounding | Obrigatório ancorar em fonte real (Lei, Jurisprudência, CNJ) |
| Output Fixo | O texto DEVE terminar com a seção "ÁTOMOS MARCADOS" |

## Procedure

Ao escrever o Pillar da semana, siga a estrutura abaixo rigorosamente:

1.  **Gancho Inicial:** A tensão, o erro comum ou a pergunta que prende o leitor.
2.  **O Que Está em Jogo:** Por que isso importa para o advogado, juiz ou estudante agora.
3.  **O Núcleo (Grounding):** Explique o tema com clareza, citando a base legal (norma, decisão, fonte). Se o tema vier do `firac-engine`, use a análise gerada lá.
4.  **Aplicação Prática:** O que fazer com essa informação no dia a dia do escritório ou tribunal.
5.  **Síntese:** A frase de impacto que a pessoa leva consigo.
6.  **Geração dos Átomos:** Ao final do texto, você DEVE gerar uma seção separada para facilitar o trabalho do `atomizador`.

### Formato Obrigatório dos Átomos Marcados

Copie e preencha este bloco exato no final do seu output:

```markdown
### ÁTOMOS MARCADOS (Para o Atomizador):
- **Gancho:** [1 frase de impacto]
- **3 Pontos-chave:** 
  1. [Ponto 1]
  2. [Ponto 2]
  3. [Ponto 3]
- **Exemplo Concreto:** [Resumo de 1-2 frases de uma aplicação prática]
- **1 Número/Estatística:** [Ex: 73% dos processos...]
- **1 Checklist:** 
  - [ ] Passo 1
  - [ ] Passo 2
  - [ ] Passo 3
```

## Pitfalls

*   **Superficialidade:** Escrever um texto que parece gerado por IA genérica (cheio de jargões vazios como "no dinâmico mundo de hoje"). Vá direto ao ponto.
*   **Falta de Base Legal:** Falar de Direito sem citar a norma, resolução ou precedente.
*   **Esquecer os Átomos:** Terminar o texto sem a seção "ÁTOMOS MARCADOS" quebra o fluxo de automação para a próxima skill.

## Verification

Antes de entregar o Pillar:
1. O texto tem entre 400 e 700 palavras?
2. A voz da marca (`voz-marca-lex`) foi aplicada?
3. Existe uma citação de fonte real (CNJ, Lei, STJ)?
4. A seção "ÁTOMOS MARCADOS" está presente no final, formatada corretamente?
Se sim, o Pillar está validado e pronto para o `atomizador`.
