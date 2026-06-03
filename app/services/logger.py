from datetime import datetime
from app.core.Database import SessionLocal
from app.models import LogAuditoriaModel

def registrar_log(
    acao: str,
    email: str = None,
    usuario_id: int = None,
    entidade: str = None,
    entidade_id: int = None,
    detalhes: str = None,
    ip: str = None,
    status: str = "sucesso"
):
    """
    Registra um evento de auditoria no banco.
    Silencioso em caso de erro — log nunca deve quebrar a aplicação.
    """
    try:
        db = SessionLocal()
        log = LogAuditoriaModel(
            usuario_id=usuario_id,
            email=email,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            detalhes=detalhes,
            ip=ip,
            status=status,
            data=datetime.utcnow()
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"[LOG ERROR] Falha ao registrar log: {e}")
    finally:
        db.close()