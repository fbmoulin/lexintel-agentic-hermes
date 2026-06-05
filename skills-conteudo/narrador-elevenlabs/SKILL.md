---
name: narrador-elevenlabs
description: Diretor de Locução. Prepara roteiros de vídeo para síntese de voz no ElevenLabs, inserindo pausas e ênfases para um tom professoral e autoritativo.
metadata:
  hermes:
    tags: [audio, video, elevenlabs, voz]
    related_skills: [apresentador-video, voz-marca-lex]
---

# Narrador ElevenLabs

## When to Use
Use esta skill após gerar um roteiro de vídeo (`apresentador-video`) para formatar a coluna de "Áudio" com a sintaxe (SSML/tags) suportada pelo ElevenLabs, garantindo que a voz soe natural, pausada e didática.

## Procedure
1. Receba a coluna de "Áudio" do roteiro de vídeo.
2. Aplique as regras de `voz-marca-lex`: Tom autoritativo, ritmo pausado (professoral).
3. Insira tags de pausa explícitas onde houver vírgulas longas ou mudanças de slide. Exemplo: `<break time="0.5s" />`.
4. Para ênfase em conceitos jurídicos (ex: "Shadow AI", "Resolução 615"), use aspas duplas ou reescreva foneticamente se a pronúncia em inglês/português for confusa.
5. Remova emojis e marcações de cena (ex: `[0-3s] Voz:`). O output deve ser apenas o texto limpo e tagueado pronto para a API.
6. (Opcional) Sugira o `voice_id` ideal para o projeto (ex: uma voz masculina, grave, sotaque neutro brasileiro).

## Pitfalls
- Não envie o roteiro inteiro (com a coluna visual) para a API de áudio, pois ela lerá as instruções visuais em voz alta. Extraia apenas a fala.
- Cuidado com siglas jurídicas (CNJ, STF). Escreva-as com hífens se o modelo errar a pronúncia: "Cê-Ene-Jota".
