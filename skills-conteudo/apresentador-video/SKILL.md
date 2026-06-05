---
name: apresentador-video
description: Gera roteiros e prompts de imagem/áudio para vídeos institucionais (Faceless) ou com Avatar, garantindo conformidade visual e retenção.
version: 1.1.0
author: Manus AI
metadata:
  hermes:
    tags: [conteudo, video, roteiro, faceless, heygen]
    category: producao
    related_skills: [atomizador, voz-marca-lex, assets-marca, guardiao-politica]
---

# Apresentador de Vídeo

Esta skill é responsável por transformar textos em roteiros audiovisuais otimizados para retenção (Shorts/Reels/TikTok) e gerar as instruções para a produção do vídeo (seja via edição faceless ou via IA de Avatar como HeyGen).

## When to Use

Invoque esta skill SEMPRE que:
* For solicitado a criar um "roteiro de vídeo" ou "roteiro para YouTube/Reels".
* Um conteúdo do `atomizador` (Reel) precisar ser detalhado com instruções visuais (B-roll, letreiros).
* For necessário gerar um vídeo usando o "Gêmeo Digital" (Avatar).

## Quick Reference

| Modo de Vídeo | Descrição | Uso Recomendado |
| :--- | :--- | :--- |
| **Modo A (Faceless)** | Voz off + Imagens de Banco (B-roll) + Textos dinâmicos | Institucional, tutoriais rápidos, temas sensíveis. |
| **Modo B (Avatar)** | Gêmeo Digital (HeyGen) falando para a câmera | Conteúdo de volume, dicas rápidas, onde a presença humana gera conexão. |

## Procedure

### 1. Definir o Modo
Pergunte ao usuário ou leia o contexto para definir se o vídeo será **Faceless** ou **Avatar**. Se não houver instrução, assuma **Faceless** por padrão (mais seguro).

### 2. Estruturar o Roteiro (Formato Tabela)
Crie o roteiro dividindo a tela em duas colunas: Áudio (o que é falado) e Visual (o que aparece na tela).

**Regras de Roteiro:**
*   **Segundos 0-3:** Gancho visual e sonoro forte. Ação rápida na tela.
*   **Tempo total:** Máximo de 60 segundos (cerca de 120-150 palavras faladas).
*   **Cortes:** Indique cortes de câmera ou mudança de B-roll a cada 3 a 5 segundos para manter a retenção.

### 3. Instruções Visuais (Assets Marca)
Na coluna "Visual", você DEVE aplicar as regras da skill `assets-marca`:
*   Indique que os letreiros (legendas) devem usar a fonte **Montserrat/Inter**.
*   Indique que elementos gráficos devem usar o **Laranja Lex (#F97316)**.
*   O fundo ou paleta geral do vídeo deve tender ao escuro (**Carvão/Grafite**).

### 4. Modo Avatar (Regras Especiais)
Se o Modo B (Avatar) for selecionado, você DEVE incluir este aviso no topo do output:
> ⚠️ **COMPLIANCE AVATAR:** Certifique-se de que o consentimento de uso de imagem/voz está registrado antes de gerar este vídeo no HeyGen ou ferramenta similar.

## Pitfalls

*   **Roteiros Longos:** Textos de 300 palavras não cabem em um Short/Reel de 1 minuto. O roteiro falhará na produção.
*   **Falta de Direção Visual:** Escrever apenas o texto falado e esquecer de indicar o B-roll ou o texto que aparece na tela. O editor de vídeo precisa saber o que mostrar.
*   **Tom Robótico:** O texto falado deve ser coloquial e respirável, diferente de um artigo de blog.

## Verification

Antes de entregar o roteiro:
1. O roteiro está no formato de tabela (Áudio | Visual)?
2. O tempo estimado de fala é inferior a 60 segundos?
3. Há instruções visuais para aplicar a identidade da Lex Intelligentia (cores/fontes)?
4. Se for Avatar, o aviso de compliance está presente?
Se sim, o roteiro está pronto.
