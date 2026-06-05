FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

# Instalar dependências
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar arquivos do projeto
COPY . /app/

# Instalar dependências Python
RUN pip3 install --no-cache-dir python-dotenv fpdf2 rich google-genai anthropic elevenlabs requests --break-system-packages

# Instalar Hermes Agent
RUN curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# Configurar o bashrc para carregar o hermes
RUN echo 'export PATH="$HOME/.hermes/bin:$PATH"' >> ~/.bashrc

# Copiar skills para o diretório do Hermes
RUN mkdir -p /root/.hermes/skills && cp -r /app/skills-conteudo/* /root/.hermes/skills/

# Script de entrada
COPY runbook/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
