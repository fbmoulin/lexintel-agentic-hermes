#!/bin/bash
# Inicializar banco se não existir
if [ ! -f /app/lex_intelligentia.db ]; then
    python3 /app/setup_db.py
fi

# Iniciar o Hermes em modo daemon (se suportado, caso contrário manter container vivo)
# O Hermes roda os cron jobs em background se configurado
tail -f /dev/null
