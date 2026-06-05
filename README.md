# Lex Intelligentia: Ecossistema de Agentes de IA para Conteúdo Jurídico

Este repositório contém o ecossistema de agentes de Inteligência Artificial para a produção de conteúdo jurídico do projeto Lex Intelligentia. O objetivo é automatizar e otimizar a criação de conteúdo, garantindo alta qualidade, conformidade regulatória e relevância jurídica, com supervisão humana estratégica.

## Estrutura do Repositório

*   `skills-conteudo/`: Definições das skills para cada agente (voz-marca, voz-pessoal, radar, pillar, atomizador, apresentador-video, guardiao, analista, etc.).
*   `runbook/`: Rotinas semanais e critérios de aprovação do ciclo de conteúdo.
*   `assets-marca/`: Identidade visual e ativos de marca.
*   `tests/`: Testes automatizados para as skills e o fluxo de trabalho.
*   `docs/`: Documentação técnica e especificações do projeto.
*   `memory/`: Memória local do orquestrador Hermes (SQLite).
*   `CLAUDE.md`: Regras de governança e padrões para o agente Claude Code.

## Visão Geral do Fluxo de Trabalho

O projeto opera com um ciclo de produção de conteúdo otimizado, envolvendo agentes especializados e gates humanos. Este ciclo garante que o conteúdo passe por etapas de ideação, criação, validação, aprovação e análise de desempenho.

## Agentes Chave

*   **Hermes:** Orquestrador central dos agentes e do ciclo de conteúdo.
*   **Claude Code:** Construtor e mantenedor do repositório e das skills.
*   **Agentes Especialistas:** `Radar Preditivo`, `Pillar Estruturado`, `Diretor de Arte IA`, `Monitor de Regulação`, `Refinador de Skill`, `Sombra Jurídica`, `Adaptador de Audiência`, `Extrator PJe/FIRAC`, entre outros.

## Compliance e Segurança

O projeto prioriza a conformidade com a LGPD e a Resolução CNJ 615, utilizando memória local, anonimização de dados por demanda e chaves privadas para APIs de LLMs. Gates humanos são pontos cruciais de controle para garantir a ética e a precisão jurídica.

## Como Contribuir

Consulte o `CLAUDE.md` para diretrizes de desenvolvimento e o `runbook/` para o fluxo de trabalho. Em caso de dúvidas, entre em contato com a equipe de desenvolvimento.
