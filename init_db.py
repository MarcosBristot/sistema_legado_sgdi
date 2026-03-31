import sqlite3

conn = sqlite3.connect('demandas.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS demandas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    descricao TEXT,
    solicitante TEXT,
    data_criacao TEXT,
    prioridade TEXT DEFAULT 'Media'
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS comentarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    demanda_id INTEGER,
    comentario TEXT,
    autor TEXT,
    data TEXT
)
''')

conn.commit()
conn.close()

print("Banco de dados criado com sucesso!")