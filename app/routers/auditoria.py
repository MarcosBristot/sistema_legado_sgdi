from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.Database import get_db
from app.models import LogAuditoriaModel
from app.routers.auth import verificar_admin
from app.schemas.auditoria import LogResponse

router = APIRouter(prefix="/audit", tags=["Auditoria"])


@router.get("/logs", response_model=List[LogResponse], summary="Lista logs de auditoria (somente admin)")
def listar_logs(
    skip: int = 0,
    limit: int = 100,
    email: Optional[str] = Query(None, description="Filtrar por e-mail"),
    acao: Optional[str] = Query(None, description="Filtrar por ação"),
    status: Optional[str] = Query(None, description="sucesso ou falha"),
    data_inicio: Optional[str] = Query(None, description="YYYY-MM-DD"),
    data_fim: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_admin)
):
    query = db.query(LogAuditoriaModel)

    if email:
        query = query.filter(LogAuditoriaModel.email.ilike(f"%{email}%"))
    if acao:
        query = query.filter(LogAuditoriaModel.acao == acao)
    if status:
        query = query.filter(LogAuditoriaModel.status == status)
    if data_inicio:
        query = query.filter(LogAuditoriaModel.data >= datetime.strptime(data_inicio, "%Y-%m-%d"))
    if data_fim:
        query = query.filter(LogAuditoriaModel.data <= datetime.strptime(data_fim, "%Y-%m-%d"))

    return query.order_by(LogAuditoriaModel.data.desc()).offset(skip).limit(limit).all()


@router.get("/logs/acoes", summary="Lista os tipos de ações registradas")
def listar_acoes(
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_admin)
):
    acoes = db.query(LogAuditoriaModel.acao).distinct().all()
    return [a[0] for a in acoes]


@router.get("/logs/resumo", summary="Resumo de eventos por ação (somente admin)")
def resumo_logs(
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_admin)
):
    from sqlalchemy import func
    resumo = db.query(
        LogAuditoriaModel.acao,
        func.count(LogAuditoriaModel.id).label("total"),
        func.sum(
            func.cast(LogAuditoriaModel.status == "falha", db.bind.dialect.name == "postgresql" and "int" or "integer")
        ).label("falhas")
    ).group_by(LogAuditoriaModel.acao).all()

    return [{"acao": r.acao, "total": r.total} for r in resumo]