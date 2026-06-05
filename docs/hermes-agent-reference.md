# Referência Técnica — Hermes Agent (Documentação Oficial 2026)

## Estrutura de Skills (Padrão Oficial)

### Diretório Obrigatório
```
~/.hermes/skills/
├── <categoria>/
│   └── <nome-da-skill>/
│       ├── SKILL.md              # Obrigatório: instruções principais
│       ├── references/           # Opcional: docs adicionais
│       ├── templates/            # Opcional: formatos de saída
│       ├── scripts/              # Opcional: scripts auxiliares
│       └── assets/               # Opcional: arquivos suplementares
```

### Formato SKILL.md (Frontmatter YAML)
```yaml
---
name: nome-da-skill
description: "Descrição breve (aparece nos resultados de busca)"
version: 1.0.0
author: Nome do Autor
license: MIT
platforms: [macos, linux]          # Opcional
metadata:
  hermes:
    tags: [Categoria, Subcategoria, Keywords]
    category: nome-categoria
    related_skills: [outra-skill]
    requires_toolsets: [web]       # Opcional
    fallback_for_toolsets: [browser]  # Opcional
    config:
      - key: minha.config
        description: "O que controla"
        default: "valor-padrao"
        prompt: "Prompt de setup"
required_environment_variables:
  - name: MINHA_API_KEY
    prompt: "Chave da API"
    help: "Obtenha em https://exemplo.com"
    required_for: "Funcionalidade X"
---

# Título da Skill

Introdução breve.

## When to Use
Condições de ativação — quando o agente deve carregar esta skill?

## Quick Reference
Tabela de comandos comuns ou chamadas de API.

## Procedure
Instruções passo a passo que o agente segue.

## Pitfalls
Modos de falha conhecidos e como tratá-los.

## Verification
Como o agente confirma que funcionou.
```

### Progressive Disclosure (3 Níveis)
- **Level 0:** `skills_list()` → Lista compacta (~3k tokens)
- **Level 1:** `skill_view(name)` → Conteúdo completo do SKILL.md
- **Level 2:** `skill_view(name, path)` → Arquivo de referência específico

### Regras Importantes
1. Skills são carregadas sob demanda (zero tokens até uso)
2. Preferir stdlib Python, curl e ferramentas existentes do Hermes
3. Se dependência necessária, documentar instalação na skill
4. Manter SKILL.md conciso; mover detalhes para `references/`
5. Nunca transmitir dados sensíveis sem autorização
6. Skills podem ser invocadas via `/nome-da-skill` (slash command)

### External Skill Directories
```yaml
# Em ~/.hermes/config.yaml
skills:
  external_dirs:
    - /caminho/para/skills-compartilhadas
    - ~/projetos/minhas-skills
```

## Sistema de Memória

### Dois Arquivos
| Arquivo | Propósito | Limite |
|---------|-----------|--------|
| MEMORY.md | Notas pessoais do agente | 2.200 chars (~800 tokens) |
| USER.md | Perfil do usuário | 1.375 chars (~500 tokens) |

### Ações da Ferramenta `memory`
- `add` — Adicionar nova entrada
- `replace` — Substituir entrada existente (substring matching)
- `remove` — Remover entrada irrelevante

### Session Search
- Todas as sessões armazenadas em SQLite com FTS5
- Busca retorna mensagens reais do DB (sem resumo LLM)
- Pode encontrar coisas discutidas semanas atrás

## AGENTS.md (Context File)

### Propósito
- Arquivo de contexto no root do projeto
- Injetado automaticamente em toda sessão
- Contém: decisões de arquitetura, convenções de código, instruções específicas

### Descoberta
- Top-level `AGENTS.md` carregado no início da sessão
- Subdirectory `AGENTS.md` descobertos lazily durante tool calls
- Manter conciso (cada caractere conta contra token budget)

## Configuração (config.yaml)

### Localização
- `~/.hermes/config.yaml` — settings
- `~/.hermes/.env` — API keys apenas
- `~/.hermes/logs/` — logs

### Skills Config
```yaml
skills:
  external_dirs:
    - /caminho/externo
  config:
    minha-skill:
      setting1: valor1
```

## Arquitetura Core

### Loop Principal (`run_conversation()`)
- Síncrono com checks de interrupção
- Budget tracking e grace call
- Formato de mensagens: OpenAI (`system/user/assistant/tool`)
- Max iterations: 90 (padrão)

### Toolsets Disponíveis
- terminal, web, browser, execute_code, skills, memory, session_search
- Cada toolset pode ser habilitado/desabilitado por sessão

### Catálogo de Agentes (`agents.yaml`)
```yaml
agents:
  - id: meu-agente
    name: Nome do Agente
    implementation: tipo_implementacao
    system_prompt: "Prompt do sistema"
    skills: [skill1, skill2]
    tools: []
    capabilities: [cap1, cap2]
    config:
      supported_task_types: [tipo1]
      execution_mode: document
      max_pages: 5
```

## Boas Práticas (Oficiais)

1. **Ser específico** — Prompts vagos produzem resultados vagos
2. **Fornecer contexto** — Front-load com detalhes relevantes
3. **Usar context files** — AGENTS.md para instruções recorrentes
4. **Skills focadas** — Uma skill = uma tarefa específica
5. **Memória para fatos** — Skills para procedimentos
6. **Consolidar memória** — Quando acima de 80% da capacidade
7. **Não quebrar prompt cache** — Manter system prompt estável


## Novidades v0.15.0 (Velocity Release — Maio 2026)

### Skill Bundles
- `/<nome>` carrega múltiplas skills de uma vez
- Configure um bundle como `writing-day` e `/writing-day` ativa todas as skills do grupo
- Skills Hub agora tem health checks, freshness badge e watchdog cron

### Kanban Multi-Agent Platform
- Triage auto-decomposes uma tarefa em árvore de sub-tarefas
- `hermes kanban swarm` cria grafo Swarm v1 (root, parallel workers, gated verifier, gated synthesizer, shared blackboard)
- Per-task model overrides (modelos baratos para boilerplate, caros para tarefas difíceis)
- Scheduled start times, retry fingerprinting, stale-task detection

### Session Search Reconstruído
- Sem LLM, sem custo, 4.500× mais rápido
- Três modos: discovery, scroll, browse
- Busca em sessões passadas é gratuita e instantânea

### Segurança (Promptware Defense)
- Brainworm-class attacks bloqueados em três chokepoints
- Memória escaneada no load time
- Tool results recebem delimiter markers contra impersonação

### Auto-Discover de Skills Locais (Issue #4667 — Em Progresso)
- Proposta: auto-descobrir skills do diretório de trabalho no início da sessão
- Caminhos de descoberta (em ordem):
  1. `<project_root>/.hermes/skills/` — Hermes-native
  2. `<project_root>/.agents/skills/` — Agent-agnostic
  3. `<project_root>/.claude/skills/` — Interop com Claude Code/Codex/Cursor
- Read-only (skill_manage ainda escreve em ~/.hermes/skills/)
- Skills locais aparecem em `skills_list()` com tag `[project]`

## Padrão agentskills.io (Cross-Agent Compatibility)

### Campos Universais (Funcionam em Todos os Agentes)
| Campo | Claude Code | Codex CLI | Cursor | OpenClaw | Gemini CLI | Copilot |
|-------|-------------|-----------|--------|----------|------------|---------|
| name | Sim | Sim | Sim | Sim | Sim | Sim |
| description | Sim | Sim | Sim | Sim | Sim | Sim |
| when_to_use | Sim | Sim | Parcial | Sim | Sim | Parcial |
| allowed-tools | Sim | Não | Não | Sim | Não | Não |
| context: fork | Sim | Não | Não | Não | Não | Não |
| hooks | Sim | Não | Não | Não | Não | Não |

### Regra de Ouro
Se a skill usa apenas `name`, `description` e instruções em Markdown, funciona em TODOS os agentes.

## Boas Práticas de Authoring (Consolidadas)

1. **Nome = Pasta:** O `name` no frontmatter DEVE corresponder ao nome da pasta pai
2. **Description é Rei:** 1-3 frases. Primeira: o que faz. Segunda: quando usar (trigger phrases)
3. **Progressive Disclosure:** Manter SKILL.md enxuto; detalhes em `references/`
4. **Sem Dependências Externas:** Preferir stdlib Python, curl, ferramentas nativas do Hermes
5. **Foco Único:** Uma skill = uma tarefa bem definida (4 skills de 500 palavras > 1 de 2000)
6. **Exemplos Concretos:** Um exemplo vale mais que três parágrafos de explicação
7. **Limites Claros:** Dizer o que a skill NÃO deve fazer
8. **Passos Numerados:** Agentes seguem sequências numeradas com mais confiabilidade
9. **Testar com:** `hermes chat -q "/minha-skill ajude com X"`
10. **Bug Conhecido (#7390):** `prompt_builder.py` trunca SKILL.md em 2000 chars no parser YAML — manter frontmatter compacto
