from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.Database import get_db
from models import DemandaModel
from schemas.demandas import DemandaCreate, DemandaResponse
from routers.auth import verificar_token

router = APIRouter(prefix="/demandas", tags=["Gestão de Demandas"])

# ==========================================
# ÁREA DO DEV 2: LEITURA (GET)
# ==========================================

@router.get("/", response_model=List[DemandaResponse], summary="Lista todas as demandas")
def listar_demandas(
    skip: int = 0, 
    limit: int = 50, 
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_token) # <-- Cadeado de Segurança
):
    """Retorna lista paginada de demandas. Acesso restrito a usuários autenticados."""
    demandas = db.query(DemandaModel).offset(skip).limit(limit).all()
    return demandas


@router.get("/{id}", response_model=DemandaResponse, summary="Busca demanda por ID")
def buscar_demanda(
    id: int, 
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_token) # <-- Cadeado de Segurança
):
    """Retorna detalhes de uma demanda específica."""
    demanda = db.query(DemandaModel).filter(DemandaModel.id == id).first()
    if not demanda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Demanda {id} não encontrada."
        )
    return demanda


# ==========================================
# ÁREA DO DEV 3: ESCRITA (POST)
# ==========================================

@router.post("/", response_model=DemandaResponse, status_code=status.HTTP_201_CREATED, summary="Cria uma nova demanda")
def criar_demanda(
    demanda_in: DemandaCreate, 
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_token) # <-- Cadeado de Segurança
):
    """
    Cadastra uma nova demanda no banco de dados.
    O sistema externo não precisa enviar o status inicial (será 'Aberta' por padrão).
    """
    # Transforma o contrato de entrada (Pydantic) em modelo de banco (SQLAlchemy)
    nova_demanda = DemandaModel(
        titulo=demanda_in.titulo,
        descricao=demanda_in.descricao,
        solicitante=demanda_in.solicitante,
        prioridade=demanda_in.prioridade,
        criado_por=usuario_atual["id"] # Associa a demanda ao sistema/usuário logado
    )
    
    db.add(nova_demanda)
    db.commit()
    db.refresh(nova_demanda) # Puxa do banco o ID e as datas geradas automaticamente
    
    return nova_demanda