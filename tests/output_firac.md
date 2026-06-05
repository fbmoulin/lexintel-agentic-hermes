# Facts

- Adoção institucional de IA generativa no Judiciário brasileiro ocorre sob a Resolução CNJ 615/2025, que:
  - Revogou a Resolução 332/2020 e instituiu classificação de risco em três camadas (vedado, alto risco, baixo risco).
  - No art. 19, autoriza o uso de LLMs como apoio (caráter auxiliar), vedando a tomada autônoma de decisões.
  - Proíbe o envio de dados sigilosos a sistemas externos sem anonimização.
  - Exige registro automático quando IA generativa for usada na redação de atos judiciais (trilha de auditoria/identificação do uso).
  - Determina comunicação de evento adverso em até 72 horas e atribui ao CNIAJ (14 membros) competência para classificar/reclassificar soluções.
  - Estabeleceu prazo de adequação de 12 meses, já expirado.
- Shadow AI:
  - Reportagens (JOTA, maio/2026) indicam uso não autorizado de IA generativa por magistrados/servidores, sem observância dos protocolos da Resolução 615/2025.
  - Foi noticiada “publicação de prompt no Diário da Justiça”, evidenciando falhas graves de governança e conformidade.
- Prompt Injection:
  - Estudos (SSRN, maio/2026) apontam injeção de comandos em peças processuais para manipular sistemas de IA dos tribunais, deslocando o processo para “nova zona de risco”.
  - Manifestação Técnica CNIAJ 1/2026 (27/05/2026) trata formalmente do risco de injeção de comandos no Judiciário.
- Contexto operacional:
  - A2J Lab (Harvard, maio/2026) destaca inovação sem avaliação adequada: sistemas que priorizam casos e redigem minutas sem validação robusta.
  - Há mais de 100 milhões de processos pendentes, pressionando por automação.
  
# Issues

1. Conformidade e governança:
   - O uso de IA generativa fora dos protocolos (Shadow AI) viola a Resolução 615/2025? Quais as consequências administrativas e processuais?
   - A ausência de registro automático do uso de IA na redação de atos compromete transparência e auditabilidade?

2. Integridade processual e nulidade:
   - A influência de prompt injection em minutas/atos judiciais vicia a motivação e pode ensejar nulidade por ausência de fundamentação independente e por quebra de imparcialidade?
   - Em que medida decisões impactadas por outputs não auditáveis/indiscriminados de LLMs carecem de validação humana exigida pelo art. 19?

3. Segurança e proteção de dados:
   - O envio de peças com dados sigilosos a LLMs externos, sem anonimização, por magistrados/servidores (Shadow AI) configura infração à Resolução 615/2025?
   - A injeção de comandos em peças pode ser classificada como “evento adverso” de segurança da informação, exigindo notificação em 72 horas?

4. Responsabilização e sanções:
   - Quem responde por efeitos de prompt injection: o advogado que insere comandos ocultos, a unidade judiciária que não implementa controles, ou ambos?
   - Em que hipóteses a conduta do advogado configura comportamento sancionável (fraude processual/manipulação dolosa de sistema), e a da administração, falta de governança?

5. Classificação de risco e continuidade de negócios:
   - O uso de LLMs em triagem, priorização e redação de minutas é “alto risco” que exige controles reforçados? Quais salvaguardas mínimas?
   - Em que casos a arquitetura que permite execução de instruções oriundas de peças deve ser reclassificada/vedada pelo CNIAJ?

# Rule

- Resolução CNJ 615/2025:
  - Princípios e escopo: Admite IA generativa com função auxiliar, veda decisão autônoma, impõe transparência e accountability.
  - Art. 19: LLMs podem apoiar magistrados/servidores, desde que não substituam o juízo humano, e com controles e validações adequadas.
  - Dados sigilosos: É vedado submetê-los a sistemas externos sem anonimização prévia.
  - Registro automático: Obrigatório quando IA generativa for usada na redação de atos judiciais; viabiliza rastreabilidade, auditoria e accountability.
  - Gestão de risco: Classificação em vedado/alto risco/baixo risco; o CNIAJ pode classificar/reclassificar soluções e determinar salvaguardas.
  - Incidentes: “Eventos adversos” devem ser comunicados em até 72 horas, com medidas corretivas.
- Diretrizes implícitas de devida motivação e controle humano:
  - A decisão judicial deve ser motivada com base em apreciação humana independente; textos de IA são apoio e não podem substituir o convencimento motivado do julgador.
  - Sistemas de apoio de alto risco requerem salvaguardas técnicas e organizacionais (governança, validação humana, logs, segregação de ambientes, controles de segurança).
- Padrões de governança algorítmica no Judiciário:
  - Soluções só podem operar em conformidade com o ciclo de vida de risco estabelecido pela 615/2025 e sob supervisão do CNIAJ.
  - Inovações que afetem priorização e minutas sem avaliação apropriada contrariam o dever de diligência e a classificação de risco adequada.

# Application

1. Shadow AI como violação direta da 615/2025:
   - Uso de LLMs por magistrados/servidores fora de soluções aprovadas e sem registro automático infringe a exigência de governança, transparência e accountability da 615/2025.
   - Se, no Shadow AI, dados sigilosos (p. ex., autos em segredo de justiça) forem enviados a serviços externos sem anonimização, há infração expressa.
   - Publicação de prompt no Diário da Justiça evidencia falhas de segregação e de higiene operacional: prompts e contextos de trabalho não devem vazar para atos oficiais. Tal evento caracteriza incidente de governança e segurança, exigindo comunicação em 72 horas, revisão de processos e correções estruturais.

2. Prompt injection como evento adverso de segurança e integridade:
   - A injeção de comandos em petições é um ataque de input malicioso que busca reconfigurar o comportamento do LLM da corte (p. ex., induzir priorização indevida, suprimir citações desfavoráveis, ou gerar rascunho pró-parte).
   - Em pipelines de alto risco (triagem/priorização/redação de minutas), o desenho seguro deve presumir que “peças processuais são entrada não confiável”. Se o sistema não isola instruções do usuário, não sanitiza conteúdo e permite que instruções escapem para o “sistema prompt”, a arquitetura é insegura e deve ser: (i) classificada/reclassificada pelo CNIAJ, e (ii) corrigida ou suspensa (quando necessário).
   - Ocorrendo influência material de injeção de comandos no texto de uma minuta/ato: 
     - Há quebra do requisito de controle humano efetivo (art. 19) se o magistrado não reconduzir o conteúdo à sua motivação própria e verificar a fidedignidade.
     - Falta de registro automático do uso de IA na redação impede auditoria; decisões assim ficam vulneráveis a questionamento por vício de fundamentação e por desvio do fluxo de conformidade.
   - Consequências processuais: atos redigidos com apoio de IA sob influência de prompt injection e sem validação/registro podem ser impugnados. A depender do impacto (p. ex., decisão baseada em trecho contaminado e não verificado), pode-se reconhecer nulidade por ausência de motivação adequada e quebra de imparcialidade/isonomia.

3. Responsabilização e deveres correlatos:
   - Administração judiciária:
     - Deve manter arquitetura “zero trust” para entradas externas, com controles como: isolamento rígido entre instruções do sistema e conteúdo de peças; filtros e remoção de marcações/instruções; bloqueio de tool-use sensível disparado por texto de partes; validação humana obrigatória; logs completos; e uso de ambientes internos (on-prem/privados) para dados sigilosos.
     - Diante de incidente (e.g., prompt injection com efeito), incide o dever de comunicar em até 72 horas, preservar evidências (logs), realizar análise de causa-raiz, reexecutar decisões com revisão humana e atualizar salvaguardas. Falhas reiteradas ou graves podem ensejar intervenção do CNIAJ (reclassificação/suspensão).
   - Magistrados/servidores:
     - Devem evitar Shadow AI. O uso de LLM externo sem anonimização ou fora das soluções aprovadas viola a 615/2025 e rompe a trilha de responsabilidade exigida.
     - Na redação assistida, devem registrar o uso de IA e produzir decisão final com motivação independente, não meramente endossar o texto gerado.
   - Partes/advogados:
     - Inserir comandos ocultos para manipular sistemas do tribunal caracteriza ataque à integridade procedimental. Tal conduta é compatível com a noção de comportamento sancionável por tentativa de manipulação do processo, sujeitando o advogado/parte a medidas punitivas cabíveis e comunicação aos órgãos competentes.
     - Mesmo sem sanção específica tecnológica, o resultado é tratado como evento adverso; o tribunal deve neutralizar a injeção, reconstruir atos e notificar.

4. Classificação de risco e desenho de controles:
   - Triagem e priorização automatizadas e redação de minutas com LLMs são típicos usos de alto risco. Exigem:
     - Guardrails técnicos: separação de canais (sistema prompt imutável); instruções de “não executar” para conteúdo de partes; sanitização (remoção/escapamento de tokens/instruções); filtros de segurança; content moderation; limitação de ferramentas; e “read-only” ao processar peças.
     - Guardrails organizacionais: aprovação prévia pelo CNIAJ ou instância competente; Mapa de riscos; testes/red teaming com casos adversariais; auditorias periódicas; registro automático do uso; e treinamento de usuários.
     - Proteção de dados: processamento local quando houver dados sensíveis; anonimização para qualquer interação externa; políticas de retenção/expurgo; segregação de ambientes.
   - Usos vedados: qualquer arranjo que implique decisão autônoma (sem validação humana), ou transferência de dados sigilosos a serviços externos sem anonimização, deve ser interrompido e reportado.

5. Continuidade operacional sob pressão do backlog:
   - A pressão de 100+ milhões de processos não autoriza atalhos de governança. “Inovação sem avaliação” amplia risco sistêmico: erros em escala, vieses e captura por atores maliciosos.
   - A implementação correta reduz risco e aumenta legitimidade: LLMs como apoio, com verificação humana e trilhas de auditoria, permitem ganhos sem sacrificar a integridade processual.

# Conclusion

- Prompt injection e Shadow AI, combinados, representam uma ameaça aguda à integridade, à motivação e à governança das decisões judiciais. À luz da Resolução 615/2025:
  - Shadow AI é incompatível com o regime de governança, especialmente quando envolve envio de dados sigilosos a serviços externos e ausência de registro automático; deve ser cessado e substituído por soluções conformes.
  - Prompt injection em peças é evento adverso de segurança; sua ocorrência impõe notificação em até 72 horas, investigação, recomposição de atos potencialmente viciados e reforço de controles técnicos/organizacionais.
  - Usos de LLMs em triagem, priorização e redação de minutas são de alto risco e exigem guardrails robustos e validação humana efetiva. A falta desses controles desloca a solução para classificação mais restritiva, inclusive vedação temporária, a critério do CNIAJ.
  - Atos judiciais substancialmente influenciados por outputs não auditáveis e não validados podem ser questionados por vício de motivação e, conforme o caso, anulados. A responsabilidade recai tanto sobre quem explora vulnerabilidades (advogados/partes) quanto sobre a administração que negligencia salvaguardas.
- Caminho recomendado: interromper Shadow AI; institucionalizar soluções aprovadas e auditáveis; tratar peças como entrada não confiável; implementar isolamento e sanitização contra injeções; assegurar registro automático e revisão humana; acionar o CNIAJ para classificação e reclassificação quando necessário. Com isso, os tribunais preservam celeridade sem sacrificar legalidade, transparência e confiança pública.