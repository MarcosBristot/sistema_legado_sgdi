import sqlite3

conn = sqlite3.connect('demandas.db')
cursor = conn.cursor()

# Tabela de usuários (Card 1)
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    cargo TEXT DEFAULT 'comum',
    data_criacao TEXT NOT NULL
)
''')

# Tabela de demandas com FK para usuário criador (Card 5)
cursor.execute('''
CREATE TABLE IF NOT EXISTS demandas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    descricao TEXT,
    solicitante TEXT,
    data_criacao TEXT,
    prioridade TEXT DEFAULT 'Media',
    criado_por INTEGER,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id)
)
''')

# Tabela de comentários
cursor.execute('''
CREATE TABLE IF NOT EXISTS comentarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    demanda_id INTEGER,
    comentario TEXT,
    autor TEXT,
    data TEXT
)
''')

# Tabela de histórico de edições (Card 7)
cursor.execute('''
CREATE TABLE IF NOT EXISTS historico_edicoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    demanda_id INTEGER NOT NULL,
    usuario_id INTEGER,
    data TEXT NOT NULL,
    campo_alterado TEXT NOT NULL,
    valor_anterior TEXT,
    valor_novo TEXT,
    FOREIGN KEY (demanda_id) REFERENCES demandas(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
)
''')

conn.commit()
conn.close()

print("Banco de dados criado com sucesso!")
