import os
from openai import OpenAI

client = OpenAI()

with open('/home/ubuntu/lex-intelligentia/tests/output_pillar.md', 'r') as f:
    pillar_content = f.read()

prompt = f"""
Atue como a skill atomizador da Lex Intelligentia.
Sua tarefa é ler o artigo Pillar abaixo (especialmente a seção ÁTOMOS MARCADOS) e gerar:
1. Um Carrossel de 8 slides para o Instagram (textos enxutos, focados no mobile).
2. Um roteiro de Reel de 15-60s (focado em compartilhamento via DM).
3. Um Tip de imagem única (uma frase de impacto + legenda).

Não copie o texto literalmente. Adapte para cada formato.
Não inclua introduções, saudações ou explicações. Apenas os conteúdos atomizados.

PILLAR BASE:
{pillar_content}
"""

response = client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

with open('/home/ubuntu/lex-intelligentia/tests/output_atomizado.md', 'w') as f:
    f.write(response.choices[0].message.content)
print("Conteúdo atomizado gerado com sucesso via OpenAI API.")
