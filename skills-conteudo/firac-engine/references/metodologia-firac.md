# Metodologia FIRAC - Enterprise V3

A metodologia FIRAC (Fatos, Questões, Regras, Aplicação, Conclusão) é o padrão ouro para análise jurídica estruturada. Esta versão "Enterprise V3" foi otimizada para processamento por agentes de IA, garantindo compliance com as resoluções do CNJ.

## 1. Fatos (Facts)
- **Objetivo:** Extrair a narrativa factual livre de valorações jurídicas.
- **O que buscar:** Quem fez o quê, a quem, quando, onde e por quê. Identificar as partes (autor, réu), datas críticas, valores envolvidos e a cronologia dos eventos.
- **Restrição:** Não incluir argumentos legais nesta seção. Apenas o que aconteceu no mundo real.

## 2. Questões (Issues)
- **Objetivo:** Identificar os pontos de controvérsia jurídica que precisam ser resolvidos.
- **Formato:** Formular como perguntas fechadas (Sim/Não) ou perguntas abertas focadas na aplicação da lei aos fatos.
- **Exemplo:** "A conduta do réu configura dano moral indenizável sob a ótica do Código de Defesa do Consumidor?"

## 3. Regras (Rules)
- **Objetivo:** Mapear o arcabouço normativo aplicável às questões identificadas.
- **O que incluir:** Legislação (Constituição, Códigos, Leis Especiais), Jurisprudência (Súmulas vinculantes e persuasivas do STF/STJ), e Doutrina majoritária.
- **Compliance CNJ:** Priorizar precedentes qualificados (Súmulas, Recursos Repetitivos, IRDR).

## 4. Aplicação (Application/Analysis)
- **Objetivo:** Conectar as Regras aos Fatos para responder às Questões.
- **Método:** É a parte mais importante. Exige raciocínio lógico (chain-of-thought). Para cada questão, aplique a regra ao fato específico. Argumente os dois lados se houver controvérsia, mas defina a posição que prevalece com base nas regras.
- **Estrutura:** "Como a regra X diz Y, e o fato Z ocorreu, então o resultado deve ser W."

## 5. Conclusão (Conclusion)
- **Objetivo:** Fornecer a resposta final e direta para cada Questão.
- **Formato:** Respostas claras, sem introduzir novos fatos ou regras. Deve derivar logicamente da seção de Aplicação.
- **Saída:** O veredito ou a recomendação de ação (ex: procedência do pedido, improcedência, valor da indenização).

---
*Nota para o Agente:* Ao aplicar esta metodologia, utilize o framework de extração de dados para garantir que nenhum fato material seja ignorado durante a leitura dos documentos do caso.
