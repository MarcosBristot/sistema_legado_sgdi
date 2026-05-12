import sqlite3

conn = sqlite3.connect('demandas.db')
cursor = conn.cursor()

# Tabela de usuários
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

# Tabela de demandas com status e data_conclusao
cursor.execute('''
CREATE TABLE IF NOT EXISTS demandas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    descricao TEXT,
    solicitante TEXT,
    data_criacao TEXT,
    prioridade TEXT DEFAULT 'Media',
    status TEXT DEFAULT 'Aberta',
    data_conclusao TEXT,
    prazo TEXT,
    criado_por INTEGER,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id)
)
''')

# Adicionar colunas se não existirem (migração)
try:
    cursor.execute("ALTER TABLE demandas ADD COLUMN status TEXT DEFAULT 'Aberta'")
except:
    pass
try:
    cursor.execute("ALTER TABLE demandas ADD COLUMN data_conclusao TEXT")
except:
    pass
try:
    cursor.execute("ALTER TABLE demandas ADD COLUMN prazo TEXT")
except:
    pass

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

# Tabela de histórico de edições
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

print("Banco de dados criado/atualizado com sucesso!")