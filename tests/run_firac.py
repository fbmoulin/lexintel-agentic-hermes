import os
from openai import OpenAI

client = OpenAI()

with open('/home/ubuntu/lex-intelligentia/tests/pesquisa_tema_teste.md', 'r') as f:
    context = f.read()

prompt = f"""
Atue como o firac-engine da Lex Intelligentia. 
Sua tarefa é ler o contexto abaixo e gerar uma análise FIRAC (Facts, Issues, Rule, Application, Conclusion) completa e profunda sobre 'Prompt Injection e Shadow AI nos Tribunais'.
O output deve ser APENAS a análise FIRAC em markdown, sem introduções ou saudações.

CONTEXTO:
{context}
"""

response = client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

with open('/home/ubuntu/lex-intelligentia/tests/output_firac.md', 'w') as f:
    f.write(response.choices[0].message.content)
print("FIRAC gerado com sucesso via OpenAI API.")
