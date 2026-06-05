import os
from openai import OpenAI

client = OpenAI()

with open('/home/ubuntu/lex-intelligentia/tests/output_atomizado.md', 'r') as f:
    atomizado_content = f.read()

prompt = f"""
Atue como a skill apresentador-video da Lex Intelligentia.
Sua tarefa é ler o conteúdo atomizado abaixo e pegar especificamente o roteiro de 'Reel' gerado.
A partir dele, gere um Roteiro de Vídeo Faceless no formato Tabela (Áudio | Visual), aplicando rigorosamente as instruções da skill assets-marca (cores Laranja Lex/Carvão, fontes Montserrat/Inter).
O vídeo deve ter cortes dinâmicos a cada 3-5 segundos.
Não inclua introduções, saudações ou explicações. Apenas o roteiro em formato de tabela.

CONTEÚDO ATOMIZADO:
{atomizado_content}
"""

response = client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

with open('/home/ubuntu/lex-intelligentia/tests/output_video.md', 'w') as f:
    f.write(response.choices[0].message.content)
print("Roteiro de vídeo gerado com sucesso via OpenAI API.")
