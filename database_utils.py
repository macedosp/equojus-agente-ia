import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "database/equojus.db"


def init_db():
    """Cria a tabela de casos no banco de dados com o novo schema."""
    import os
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Schema atualizado para refletir os dados extraídos pela IA
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS casos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        nome_usuario TEXT NOT NULL,
        cidade_estado TEXT,
        telefone_whatsapp TEXT,
        demanda TEXT NOT NULL,
        area_direito_inferida TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()


def add_case(dossie_data: dict):
    """Adiciona um novo caso ao banco de dados a partir de um dicionário."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now()

    try:
        cursor.execute("""
        INSERT INTO casos (timestamp, nome_usuario, cidade_estado, telefone_whatsapp, demanda, area_direito_inferida)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            dossie_data.get('nome_usuario'),
            dossie_data.get('cidade_estado'),
            dossie_data.get('telefone_whatsapp'),
            dossie_data.get('demanda'),
            dossie_data.get('area_direito_inferida')
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro de banco de dados ao adicionar caso: {e}")
        return False
    finally:
        conn.close()


def get_all_cases():
    """Busca todos os casos do banco de dados e retorna como um DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT * FROM casos ORDER BY timestamp DESC", conn)
        return df
    except Exception as e:
        print(f"Erro ao buscar casos: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
