import sqlite3
import os

def setup_database():
    db_path = os.path.expanduser("~/.hermes/lex_intelligentia.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabela para memória de longo prazo (contexto jurídico)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS legal_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        value TEXT,
        category TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabela para logs de compliance
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS compliance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT,
        action TEXT,
        status TEXT,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Banco de dados inicializado em: {db_path}")

if __name__ == "__main__":
    setup_database()
