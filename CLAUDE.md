# CLAUDE.md: Diretrizes de Governança para o Projeto Lex Intelligentia

Este documento estabelece as diretrizes e padrões que o agente Claude Code (e outros agentes de desenvolvimento) devem seguir ao interagir com o repositório do projeto Lex Intelligentia. O objetivo é garantir consistência, segurança, compliance e qualidade no desenvolvimento das skills e na manutenção da arquitetura.

## 1. Princípios Gerais

*   **Compliance by Design:** Todas as implementações devem considerar os requisitos de LGPD e Resolução CNJ 615 desde a concepção.
*   **Segurança Primeiro:** Priorizar a segurança em todas as etapas do desenvolvimento, especialmente no tratamento de dados sensíveis.
*   **Modularidade:** Manter as skills independentes e focadas em uma única responsabilidade.
*   **Clareza e Legibilidade:** O código e a documentação devem ser claros, concisos e fáceis de entender.
*   **Testabilidade:** Todas as novas funcionalidades e skills devem ser acompanhadas de testes automatizados.

## 2. Diretrizes para o Claude Code

### 2.1. Interação com o Repositório

*   **Localização de Arquivos:** O Claude Code deve sempre operar dentro do diretório `lex-intelligentia/`.
*   **Criação de Arquivos:** Novos arquivos devem ser criados nos diretórios apropriados (ex: `skills-conteudo/`, `tests/`, `docs/`).
*   **Modificação de Arquivos:** Antes de modificar qualquer arquivo existente, o Claude Code deve ler o conteúdo atual para entender o contexto e garantir que as alterações sejam incrementais e não disruptivas.
*   **Commits:** Cada conjunto de alterações lógicas deve ser encapsulado em um commit. As mensagens de commit devem ser claras e descritivas, seguindo o padrão `Tipo(Escopo): Descrição` (ex: `feat(skill-radar): Adiciona skill de radar preditivo`).

### 2.2. Desenvolvimento de Skills

*   **Estrutura `SKILL.md`:** Todas as skills devem seguir o formato `SKILL.md` com `frontmatter` YAML, conforme especificado no `AGENTS2.md` e no `spec_lex_intelligentia.md`.
*   **Linguagem:** Preferencialmente Python para a lógica das skills. Para scripts de automação de baixo nível, shell scripts são aceitáveis.
*   **Dependências:** Novas dependências Python devem ser adicionadas ao `requirements.txt` na raiz do projeto.
*   **Testes:** Para cada nova skill ou funcionalidade, um arquivo de teste correspondente deve ser criado em `tests/`.

### 2.3. Qualidade de Código

*   **Linting:** O código Python deve aderir aos padrões de estilo definidos pelo `flake8` ou `black`.
*   **Tipagem:** Utilizar type hints em Python para melhorar a legibilidade e a detecção de erros.
*   **Documentação:** Funções e classes devem ser documentadas com docstrings claras.

### 2.4. Segurança e Dados

*   **Dados Sensíveis:** O Claude Code **NUNCA** deve registrar dados de casos concretos ou informações sensíveis diretamente no código ou em logs públicos. Para testes, utilizar dados mockados ou anonimizados.
*   **Credenciais:** Credenciais de API ou acesso a sistemas externos (ex: PJe) devem ser gerenciadas via variáveis de ambiente ou um sistema de gerenciamento de segredos, e **NUNCA** hardcoded no repositório.

## 3. Fluxo de Trabalho para Novas Skills/Funcionalidades

1.  **Definição:** O objetivo da skill/funcionalidade é claramente definido no `spec_lex_intelligentia.md`.
2.  **Implementação:** O Claude Code implementa a skill (código Python, `SKILL.md`).
3.  **Testes:** O Claude Code cria testes unitários e de integração para a skill.
4.  **Revisão:** O código e a `SKILL.md` são submetidos para revisão (humana ou automatizada).
5.  **Integração:** Após aprovação, a skill é integrada ao orquestrador Hermes.

## 4. Autoridade e Exceções

*   **Regras Vinculativas:** As diretrizes neste `CLAUDE.md` são vinculativas para o Claude Code.
*   **Exceções:** Qualquer exceção a estas regras deve ser explicitamente aprovada por um gate humano e documentada.

