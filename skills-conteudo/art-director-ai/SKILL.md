---
name: art-director-ai
description: Diretor de Arte AI para garantir que todos os assets visuais, carrosséis, vídeos e posts sigam rigorosamente o branding da Lex Intelligentia.
metadata:
  hermes:
    tags: [design, visual, branding, gate]
    related_skills: [assets-marca, gerador-imagens]
---

# Art Director AI

## When to Use
Use esta skill como um *gate* visual SEMPRE que for gerar um output que tenha componente gráfico (Roteiros de Vídeo, Carrosséis, Prompts de Imagem, Thumbnails). O Art Director valida se a identidade visual está sendo aplicada corretamente antes da geração final.

## Procedure
1. Receba o conteúdo textual ou roteiro a ser validado.
2. Inspecione o conteúdo contra as regras do `assets-marca` (Fundo Preto/Carvão, Laranja Lex #F97316, Montserrat/Inter).
3. Rejeite qualquer instrução visual que sugira cores fora da paleta (ex: azul, verde, branco de fundo).
4. Para vídeos *Faceless*, garanta que a descrição visual foca em UI abstrata, tipografia cinética e elementos de tecnologia/direito.
5. Se aprovado, retorne o conteúdo com um selo de [APPROVED BY ART DIRECTOR]. Se rejeitado, retorne a lista de correções visuais necessárias.

## Pitfalls
- Não permita fundos claros. O projeto é *dark mode first*.
- Evite elementos visuais genéricos de banco de imagens (ex: juiz com martelo de madeira antigo). Substitua por versões modernas (tecnologia, redes neurais, balança minimalista).
- Nunca ignore a tipografia: Títulos devem ser explicitamente marcados como Montserrat SemiBold.
