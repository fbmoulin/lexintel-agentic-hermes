import os
from openai import OpenAI

client = OpenAI()

with open('/home/ubuntu/lex-intelligentia/tests/output_firac.md', 'r') as f:
    firac_content = f.read()

prompt = f"""
Atue como a skill pillar-semana da Lex Intelligentia.
Sua tarefa é escrever um artigo denso (400 a 700 palavras) sobre 'Prompt Injection e Shadow AI nos Tribunais'.
Use a análise FIRAC abaixo como sua base de conhecimento (grounding).
O texto deve terminar OBRIGATORIAMENTE com a seção 'ÁTOMOS MARCADOS' conforme o template da skill.
Não inclua introduções, saudações ou explicações. Apenas o artigo final.

ANÁLISE FIRAC BASE:
{firac_content}
"""

response = client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

with open('/home/ubuntu/lex-intelligentia/tests/output_pillar.md', 'w') as f:
    f.write(response.choices[0].message.content)
print("Pillar gerado com sucesso via OpenAI API.")
