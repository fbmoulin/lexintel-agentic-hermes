# Tutorial de Deploy: Lex Intelligentia

Este guia detalha os passos para implantar o ecossistema Lex Intelligentia na sua máquina local ou servidor em produção.

## Opção 1: Instalação Rápida (Script Automatizado)

A forma mais rápida de rodar o projeto nativamente no Ubuntu/Linux ou macOS.

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/fbmoulin/lex-intelligentia-v2.git
   cd lex-intelligentia-v2
   ```

2. **Dê permissão e execute o instalador:**
   ```bash
   chmod +x runbook/install.sh
   ./runbook/install.sh
   ```
   *Este script instalará o Hermes Agent, o SQLite, as bibliotecas Python e copiará as skills para o diretório correto.*

3. **Configure as Chaves de API:**
   Abra o arquivo `.env` gerado e preencha suas chaves (Gemini, Anthropic, ElevenLabs, etc.).
   ```bash
   nano .env
   ```

4. **Inicie o sistema:**
   ```bash
   hermes chat
   ```
   Digite `/content-day` para testar o pipeline completo.

---

## Opção 2: Deploy Isolado (Docker Compose)

Ideal se você quiser isolar o ambiente ou rodar o n8n em conjunto.

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/fbmoulin/lex-intelligentia-v2.git
   cd lex-intelligentia-v2
   ```

2. **Configure o `.env`:**
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Suba os containers:**
   ```bash
   docker-compose up -d
   ```
   *Isso subirá o Hermes Agent em background e o n8n na porta 5678.*

4. **Acesse o Hermes no Docker:**
   ```bash
   docker exec -it lex-intelligentia-agent bash
   hermes chat
   ```

---

## Configuração do n8n (Publicação Automática)

O projeto está preparado para enviar o conteúdo finalizado para o n8n publicar nas redes sociais.

1. Acesse o n8n (se usou Docker: `http://localhost:5678`).
2. Crie um novo Workflow.
3. Adicione um nó **Webhook** (Método: POST, Path: `lex-publish`).
4. Copie a "Test URL" e cole no seu arquivo `.env` na variável `N8N_WEBHOOK_URL`.
5. No workflow do n8n, adicione os nós de destino (LinkedIn, Instagram, WordPress, etc.) conectando-os ao Webhook.
6. A skill `atomizador` enviará o JSON com os textos e mídias para este webhook.

---

## Checklist Pós-Deploy

- [ ] Arquivo `.env` preenchido com as chaves corretas.
- [ ] Comando `hermes skills list` exibe as 12 skills locais.
- [ ] Banco de dados `lex_intelligentia.db` foi criado na raiz do projeto.
- [ ] Cron jobs estão ativos (`hermes cron list`).
- [ ] Skills estão protegidas contra o Curator (`hermes curator status`).

Em caso de dúvidas, consulte o `RELATORIO_CONCLUSAO_PROJETO.md`.
