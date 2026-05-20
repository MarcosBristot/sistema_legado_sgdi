import sqlite3
from sqlalchemy.orm import Session
from core.Database import SessionLocal, engine
from models import UsuarioModel, DemandaModel, ComentarioModel, Base

def migrar():
    print("Iniciando migração de dados...")
    
    # Garante que as tabelas existem no Postgres
    Base.metadata.create_all(bind=engine)
    
    # Conecta no SQLite legado
    conn_sqlite = sqlite3.connect('demandas.db')
    conn_sqlite.row_factory = sqlite3.Row
    cursor = conn_sqlite.cursor()

    db_postgres = SessionLocal()

    try:
        # 1. Migrar Usuários
        print("Migrando Usuários...")
        usuarios = cursor.execute("SELECT * FROM usuarios").fetchall()
        for u in usuarios:
            if not db_postgres.query(UsuarioModel).filter_by(email=u['email']).first():
                novo_user = UsuarioModel(
                    id=u['id'], nome=u['nome'], email=u['email'], 
                    senha_hash=u['senha_hash'], cargo=u['cargo'], 
                    data_criacao=u['data_criacao'] # SQLAlchemy converte string ISO para DateTime
                )
                db_postgres.add(novo_user)
        db_postgres.commit()

        # 2. Migrar Demandas
        print("Migrando Demandas...")
        demandas = cursor.execute("SELECT * FROM demandas").fetchall()
        for d in demandas:
            if not db_postgres.query(DemandaModel).filter_by(id=d['id']).first():
                nova_demanda = DemandaModel(
                    id=d['id'], titulo=d['titulo'], descricao=d['descricao'],
                    solicitante=d['solicitante'], prioridade=d['prioridade'],
                    status=d['status'], criado_por=d['criado_por'],
                    data_criacao=d['data_criacao'], data_conclusao=d['data_conclusao'], prazo=d['prazo']
                )
                db_postgres.add(nova_demanda)
        db_postgres.commit()

        print("✅ Migração concluída com sucesso!")
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        db_postgres.rollback()
    finally:
        db_postgres.close()
        conn_sqlite.close()

if __name__ == "__main__":
    migrar()