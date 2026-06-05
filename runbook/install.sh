#!/bin/bash
# ============================================================
# Lex Intelligentia — Setup Automatizado de Produção
# ============================================================
# Este script prepara o ambiente, instala o Hermes Agent,
# configura o banco de dados e ativa as skills.
# ============================================================

set -e

echo "🚀 Iniciando instalação do Lex Intelligentia..."

# 1. Instalar dependências de sistema
echo "📦 Instalando dependências de sistema..."
sudo apt-get update && sudo apt-get install -y sqlite3 python3-pip curl git

# 2. Instalar dependências Python
echo "🐍 Instalando dependências Python..."
sudo pip3 install python-dotenv fpdf2 rich google-genai anthropic elevenlabs requests

# 3. Instalar Hermes Agent
echo "🤖 Instalando Hermes Agent v0.15.0..."
if ! command -v hermes &> /dev/null; then
    curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
    source ~/.bashrc
else
    echo "✅ Hermes Agent já instalado."
fi

# 4. Configurar Banco de Dados
echo "🗄️ Inicializando banco de dados SQLite..."
python3 setup_db.py

# 5. Configurar Skills no Hermes
echo "🧠 Configurando Skills..."
mkdir -p ~/.hermes/skills
cp -r skills-conteudo/* ~/.hermes/skills/

# 6. Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "🔐 Criando arquivo .env a partir do .env.example..."
    cp .env.example .env
    echo "⚠️ AVISO: Preencha o arquivo .env com suas chaves de API antes de rodar."
fi

# 7. Executar setup de cron e pinagem
echo "⏰ Configurando automação (Cron Jobs e Pinagem)..."
chmod +x runbook/setup_cron_and_pin.sh
./runbook/setup_cron_and_pin.sh

echo "🎉 Instalação concluída com sucesso!"
echo "👉 Próximo passo: Edite o arquivo .env com suas chaves."
echo "👉 Depois, execute: hermes chat para iniciar."
