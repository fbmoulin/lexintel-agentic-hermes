# Pacote de Conteúdo Completo — Teste End-to-End

## Tema: Prompt Injection e Shadow AI nos Tribunais

**Pipeline Executado:** Pesquisa → FIRAC → Pillar → Atomizador → Roteiro de Vídeo

---

## 1. Análise FIRAC

### Facts

A adoção institucional de IA generativa no Judiciário brasileiro ocorre sob a Resolução CNJ 615/2025, que revogou a Resolução 332/2020 e instituiu classificação de risco em três camadas (vedado, alto risco, baixo risco). O art. 19 autoriza o uso de LLMs como apoio (caráter auxiliar), vedando a tomada autônoma de decisões. A resolução proíbe o envio de dados sigilosos a sistemas externos sem anonimização, exige registro automático quando IA generativa for usada na redação de atos judiciais, e determina comunicação de evento adverso em até 72 horas. O CNIAJ (14 membros) possui competência para classificar e reclassificar soluções, e o prazo de adequação de 12 meses já expirou.

**Shadow AI:** Reportagens (JOTA, maio/2026) indicam uso não autorizado de IA generativa por magistrados e servidores, sem observância dos protocolos da Resolução 615/2025. Foi noticiada "publicação de prompt no Diário da Justiça", evidenciando falhas graves de governança e conformidade.

**Prompt Injection:** Estudos (SSRN, maio/2026) apontam injeção de comandos em peças processuais para manipular sistemas de IA dos tribunais, deslocando o processo para "nova zona de risco". A Manifestação Técnica CNIAJ 1/2026 (27/05/2026) trata formalmente do risco de injeção de comandos no Judiciário.

**Contexto operacional:** O A2J Lab (Harvard, maio/2026) destaca inovação sem avaliação adequada: sistemas que priorizam casos e redigem minutas sem validação robusta. Há mais de 100 milhões de processos pendentes, pressionando por automação.

### Issues

| Categoria | Questão Central |
| :--- | :--- |
| Conformidade e governança | O uso de IA fora dos protocolos (Shadow AI) viola a 615/2025? Quais as consequências? |
| Integridade processual | Prompt injection vicia a motivação e pode ensejar nulidade? |
| Segurança e proteção de dados | Envio de dados sigilosos a LLMs externos configura infração? |
| Responsabilização | Quem responde: advogado que injeta, administração que não controla, ou ambos? |
| Classificação de risco | Triagem e minutas com LLMs são "alto risco" que exige controles reforçados? |

### Rule

A Resolução CNJ 615/2025 admite IA generativa com função auxiliar, veda decisão autônoma, impõe transparência e accountability. O art. 19 permite que LLMs apoiem magistrados e servidores, desde que não substituam o juízo humano, com controles e validações adequadas. É vedado submeter dados sigilosos a sistemas externos sem anonimização prévia. O registro automático é obrigatório quando IA generativa for usada na redação de atos judiciais. A gestão de risco opera em classificação vedado/alto risco/baixo risco, e o CNIAJ pode classificar/reclassificar soluções e determinar salvaguardas. "Eventos adversos" devem ser comunicados em até 72 horas, com medidas corretivas.

### Application

**Shadow AI como violação direta:** O uso de LLMs por magistrados e servidores fora de soluções aprovadas e sem registro automático infringe a exigência de governança, transparência e accountability da 615/2025. Se dados sigilosos forem enviados a serviços externos sem anonimização, há infração expressa. A publicação de prompt no Diário da Justiça evidencia falhas de segregação e higiene operacional, caracterizando incidente de governança e segurança que exige comunicação em 72 horas.

**Prompt injection como evento adverso:** A injeção de comandos em petições é um ataque de input malicioso que busca reconfigurar o comportamento do LLM da corte. Em pipelines de alto risco, o desenho seguro deve presumir que "peças processuais são entrada não confiável". Se o sistema não isola instruções do usuário e não sanitiza conteúdo, a arquitetura é insegura e deve ser classificada/reclassificada pelo CNIAJ, corrigida ou suspensa.

**Responsabilização compartilhada:** A administração judiciária deve manter arquitetura "zero trust" para entradas externas. Magistrados e servidores devem evitar Shadow AI e registrar o uso de IA. Advogados que inserem comandos ocultos praticam ataque à integridade procedimental, sujeitando-se a medidas punitivas.

### Conclusion

Prompt injection e Shadow AI representam ameaça aguda à integridade, motivação e governança das decisões judiciais. Shadow AI é incompatível com o regime de governança; prompt injection é evento adverso de segurança que impõe notificação em 72 horas. Usos de LLMs em triagem e minutas são de alto risco e exigem guardrails robustos. Atos judiciais influenciados por outputs não auditáveis podem ser questionados por vício de motivação e anulados. O caminho recomendado: interromper Shadow AI, institucionalizar soluções aprovadas e auditáveis, tratar peças como entrada não confiável, implementar isolamento e sanitização, assegurar registro automático e revisão humana, e acionar o CNIAJ para classificação quando necessário.

---

## 2. Pillar da Semana (Artigo Denso)

Prompt injection e Shadow AI nos tribunais não são meros desvios operacionais: constituem ameaças diretas à governança, à motivação das decisões e à confiança pública. Sob a Resolução CNJ 615/2025, que revogou a 332/2020 e instituiu um regime de risco em três camadas, a IA generativa é admitida apenas com função auxiliar, vedada a decisão autônoma, com transparência, trilhas de auditoria e proteção de dados. O prazo de adequação de 12 meses já expirou; o CNIAJ, com competência para classificar e reclassificar soluções, é o guardião dessa arquitetura de conformidade.

Shadow AI — o uso não autorizado de LLMs por magistrados e servidores — afronta diretamente a 615/2025. Ao operar fora de soluções aprovadas, sem registro automático na redação de atos e sem os controles mínimos, quebra-se a accountability exigida. Mais grave: quando dados sigilosos são submetidos a sistemas externos sem anonimização, consuma-se uma infração expressa à resolução. Episódios como a "publicação de prompt no Diário da Justiça" revelam falhas de segregação e higiene operacional; são incidentes de governança e segurança que exigem comunicação em até 72 horas, correção de processos e, se necessário, reclassificação pelo CNIAJ.

Prompt injection eleva o risco a um novo patamar. A inserção de comandos maliciosos em petições para influenciar LLMs de triagem, priorização ou de redação de minutas é um ataque de input adversarial já formalmente reconhecido (Manifestação Técnica CNIAJ 1/2026). Se a arquitetura não trata "peças processuais" como entrada não confiável, não isola instruções do sistema, não sanitiza conteúdos e permite que comandos de partes escapem para o prompt de sistema, o desenho é inseguro. Em usos de alto risco, como priorização de casos e minutas, isso impõe reclassificação, correção ou suspensão da solução.

Do ponto de vista processual, a influência material de uma injeção de comandos que contamine minutas ou atos, aliada à ausência de registro automático e validação humana efetiva, vicia a motivação. O art. 19 exige controle humano significativo: a decisão não pode ser um endosso opaco ao output da IA. Sem auditabilidade e verificação independente, abrem-se vias para impugnação por ausência de fundamentação e por quebra de imparcialidade/isonomia, com risco de nulidade dependendo do impacto no mérito.

A responsabilidade é compartilhada. A administração judiciária deve adotar uma postura "zero trust" para entradas externas: isolamento rígido entre instruções de sistema e conteúdo das peças; sanitização/escapamento de tokens e marcações; bloqueio de tool-use sensível disparado por texto de partes; processamento read-only de documentos; logs completos; ambientes internos para dados sigilosos; e validação humana obrigatória.

A pressão de mais de 100 milhões de processos não legitima atalhos. Inovação sem avaliação amplia o risco sistêmico e expõe o Judiciário a erros em escala e captura por atores maliciosos. O caminho seguro existe: tratar peças como entradas não confiáveis; implementar isolamento e sanitização; operar LLMs de alto risco com guardrails robustos e validação humana; adotar registro automático; e acionar o CNIAJ para classificar e reclassificar soluções.

### ÁTOMOS MARCADOS (Para o Atomizador)

| Átomo | Conteúdo |
| :--- | :--- |
| Norma-chave | Resolução CNJ 615/2025 (art. 19: apoio, sem decisão autônoma; registro automático; vedação de envio de dados sigilosos sem anonimização) |
| Risco central | Shadow AI viola governança e accountability; prompt injection explora entradas não confiáveis para capturar LLMs |
| Evento adverso | Injeção de comandos e vazamento de prompts exigem notificação em até 72 horas |
| Integridade decisória | Outputs não auditáveis/validados viciam motivação; podem ensejar nulidade |
| Responsabilização | Advogado que insere comandos ocultos pratica manipulação sancionável; administração responde por falta de controles |
| Classificação de risco | Triagem, priorização e minutas com LLMs são alto risco |
| Controles mínimos | Isolamento de prompts; sanitização; bloqueio de tool-use; logs completos; processamento on-prem; validação humana |
| Ação imediata | Cessar Shadow AI; institucionalizar soluções aprovadas; ativar registro automático; red teaming; reavaliar pelo CNIAJ |

---

## 3. Conteúdo Atomizado

### 3.1 Carrossel Instagram (8 Slides)

| Slide | Conteúdo |
| :---: | :--- |
| 1 | **Shadow AI + prompt injection:** o atalho que pode derrubar decisões. Risco direto à governança e à confiança. |
| 2 | **Regra do jogo — Res. CNJ 615/2025.** IA só apoia (art. 19), não decide. Registro automático é obrigatório. Dado sigiloso fora? Só anonimizando. |
| 3 | **Shadow AI é infração.** Uso de LLMs fora das soluções aprovadas = sem trilha, sem controle, sem accountability. |
| 4 | **Prompt injection é ataque.** Comandos ocultos em petições podem capturar triagem, priorização e minutas se o sistema mistura conteúdo com instruções. |
| 5 | **Deu ruim? Proceda.** Notifique em até 72h, preserve evidências e logs, e reclassifique no CNIAJ se preciso. |
| 6 | **Integridade decisória.** Sem auditoria + validação humana real, a motivação é viciada: risco de impugnação e nulidade. |
| 7 | **Controles mínimos (zero trust).** Isolar prompts. Sanitizar/escapar conteúdo. Bloquear tool-use disparado por partes. Processar sigilosos on-prem. Logs completos + validação humana. |
| 8 | **Ação agora.** Cessar Shadow AI. Institucionalizar soluções aprovadas. Ativar registro automático. Fazer red teaming. Refazer atos contaminados. Reavaliar no CNIAJ. |

### 3.2 Roteiro de Reel (60s)

| Tempo | Áudio (Voz) | Visual (On-screen) |
| :---: | :--- | :--- |
| 0–3s | "Se a petição manda no seu LLM, a decisão já nasceu suspeita." | "Shadow AI + prompt injection = risco de nulidade" |
| 3–15s | "A 615/2025 é clara: IA generativa só auxilia. Registro automático é obrigatório. Dado sigiloso fora? Só anonimizando." | "Res. 615/2025 — IA só apoia (art. 19)" |
| 15–28s | "Usar LLM não aprovado — sem trilhas e sem controle — viola governança. Vazou prompt? É incidente: notifique em até 72 horas e preserve evidências." | "Shadow AI quebra governança" |
| 28–42s | "Comandos escondidos em petições podem capturar triagem, priorização e minutas. Em alto risco, a solução deve ser corrigida, reclassificada ou suspensa pelo CNIAJ." | "Prompt injection é ataque" |
| 42–52s | "Sem auditabilidade e validação humana significativa, a motivação fica viciada — abre caminho para impugnação e nulidade." | "Sem validação ≠ motivação" |
| 52–60s | "Implemente zero trust: isole prompts, sanitize conteúdo, bloqueie tool-use por partes, processe sigilosos on-prem e valide. Acione o CNIAJ. Envie este vídeo a quem ainda usa 'só um prompt'." | "Zero trust: isole, sanitize, bloqueie, on-prem, valide" |

### 3.3 Tip de Imagem Única

> **Frase na imagem:** "Petições não são confiáveis: separe o prompt do conteúdo."

**Legenda:** Triagem, priorização e minutas são alto risco: isole prompts, sanitize conteúdo, bloqueie tool-use disparado por partes, processe sigilosos on-prem e valide humanamente. A 615/2025 (art. 19) exige apoio, registro automático e notificação de incidentes em até 72h — acione o CNIAJ quando necessário.

---

## 4. Roteiro de Vídeo Faceless (Formato Tabela Completo)

| Tempo | Áudio | Visual |
| :---: | :--- | :--- |
| 0–3s | "Se a petição manda no seu LLM, a decisão já nasceu suspeita." | Fundo Carvão. Texto grande em Laranja Lex: "Shadow AI + prompt injection = risco de nulidade". Efeito glitch sutil + ícone de alerta minimalista. |
| 3–7s | "A 615/2025 é clara: IA generativa só auxilia." | Faixa superior Laranja Lex com título em Montserrat Bold: "Res. 615/2025 — IA só apoia (art. 19)". Fundo Carvão com UI abstrata de tribunal/IA. |
| 7–11s | "Registro automático é obrigatório." | Fundo Carvão. Checklist animado em Laranja Lex com check marcando: "Registro automático é obrigatório". Micro-zoom. |
| 11–15s | "Dado sigiloso fora? Só anonimizando." | Fundo Carvão. Documento borrado + cadeado Laranja Lex. Animação de blur/mascara. |
| 15–19s | "Usar LLM não aprovado — sem trilhas e sem controle — viola governança." | Cabeçalho em Laranja Lex: "Shadow AI quebra governança". Carimbo animado: "sem trilha / sem controle". Fundo Carvão com padrão de logs ausentes. |
| 19–23s | "Vazou prompt? É incidente: notifique em até 72 horas" | Fundo Carvão. Timer 72h em destaque Laranja Lex. Efeito de pulso. |
| 23–28s | "e preserve evidências." | Fundo Carvão. Animação de pasta de evidências + ícone de logs. Linha temporal surgindo. |
| 28–31s | "Comandos escondidos em petições" | Cabeçalho em Laranja Lex: "Prompt injection é ataque". Documento com trechos ocultos revelados por highlighter Laranja. |
| 31–35s | "podem capturar triagem, priorização e minutas." | Fluxo de trabalho estilizado sendo "sequestrado" por seta Laranja. Palavras: "triagem / priorização / minutas". |
| 35–39s | "Em alto risco," | Medidor de risco sobe até ALTO em Laranja Lex. Vibração sutil. |
| 39–42s | "a solução deve ser corrigida, reclassificada ou suspensa pelo CNIAJ." | Botões Laranja: "Corrigir / Reclassificar / Suspender". Selo CNIAJ em destaque. |
| 42–46s | "Sem auditabilidade e validação humana significativa," | Título em Laranja: "Sem validação ≠ motivação". Trilha de auditoria incompleta (tracejado). |
| 46–49s | "a motivação fica viciada —" | Carimbo em Laranja Lex: "Motivação viciada". Efeito de rachadura. |
| 49–52s | "abre caminho para impugnação e nulidade." | Texto em Montserrat: "Risco: impugnação e nulidade". Martelo de juiz estilizado rachando. |
| 52–56s | "Implemente zero trust: isole prompts, sanitize conteúdo, bloqueie tool-use por partes, processe sigilosos on-prem e valide." | Cabeçalho Laranja: "Zero trust". Lista com ícones: 1) Isolar prompts 2) Sanitizar 3) Bloquear tool-use 4) On-prem 5) Validação humana. Cada item "check" em sequência. |
| 56–60s | "Acione o CNIAJ. Envie este vídeo a quem ainda usa 'só um prompt'." | CTA em botão Laranja: "Acione o CNIAJ agora". Ícone de compartilhar. Barra final Laranja Lex com fundo Carvão. Fade out. |

---

## Metadados do Teste

| Etapa | Modelo | Tempo | Status |
| :--- | :--- | :--- | :--- |
| Pesquisa | Web Search | ~5s | Concluído |
| FIRAC | GPT-5 (sandbox) | ~30s | Concluído |
| Pillar | GPT-5 (sandbox) | ~30s | Concluído |
| Atomizador | GPT-5 (sandbox) | ~30s | Concluído |
| Roteiro Vídeo | GPT-5 (sandbox) | ~30s | Concluído |

**Observações:**
- O pipeline foi executado via scripts Python que chamam a API OpenAI (sandbox) simulando a execução das skills do Hermes.
- Em produção, o Hermes Agent orquestrará essas chamadas nativamente via `/content-day`.
- Todas as etapas respeitaram a identidade visual (Laranja Lex, Carvão, Montserrat/Inter) e o tom de voz da marca.
