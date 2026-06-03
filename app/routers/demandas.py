from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.Database import get_db
from app.models import DemandaModel, HistoricoEdicoesModel
from app.schemas.demandas import DemandaCreate, DemandaUpdate, DemandaResponse
from app.routers.auth import verificar_token, verificar_admin
from app.services.logger import registrar_log

router = APIRouter(prefix="/demandas", tags=["Gestão de Demandas"])


# ── GET / ─────────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[DemandaResponse], summary="Lista todas as demandas")
def listar_demandas(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_token)
):
    return db.query(DemandaModel).offset(skip).limit(limit).all()


# ── GET /{id} ─────────────────────────────────────────────────────────────────
@router.get("/{id}", response_model=DemandaResponse, summary="Busca demanda por ID")
def buscar_demanda(
    id: int,
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_token)
):
    demanda = db.query(DemandaModel).filter(DemandaModel.id == id).first()
    if not demanda:
        raise HTTPException(status_code=404, detail=f"Demanda {id} não encontrada.")
    return demanda


# ── POST / ────────────────────────────────────────────────────────────────────
@router.post("/", response_model=DemandaResponse, status_code=201, summary="Cria uma nova demanda")
def criar_demanda(
    demanda_in: DemandaCreate,
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_token)
):
    nova = DemandaModel(
        titulo=demanda_in.titulo,
        descricao=demanda_in.descricao,
        solicitante=demanda_in.solicitante,
        prioridade=demanda_in.prioridade,
        criado_por=usuario_atual["id"]
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    registrar_log(
        acao="CRIAR_DEMANDA",
        usuario_id=usuario_atual["id"],
        email=usuario_atual["email"],
        entidade="demanda",
        entidade_id=nova.id,
        detalhes=f"Via API | Prioridade: {nova.prioridade}",
        ip="api"
    )
    return nova


# ── PUT /{id} — qualquer usuário edita a própria, admin edita qualquer uma ───
@router.put("/{id}", response_model=DemandaResponse, summary="Edita uma demanda")
def editar_demanda(
    id: int,
    demanda_in: DemandaUpdate,
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_token)
):
    demanda = db.query(DemandaModel).filter(DemandaModel.id == id).first()
    if not demanda:
        raise HTTPException(status_code=404, detail=f"Demanda {id} não encontrada.")

    eh_admin = usuario_atual["cargo"] == "admin"
    eh_dono  = demanda.criado_por == usuario_atual["id"]
    if not eh_admin and not eh_dono:
        raise HTTPException(status_code=403, detail="Sem permissão para editar esta demanda.")

    agora = datetime.utcnow()
    campos = {
        "titulo":      (demanda.titulo,               demanda_in.titulo),
        "descricao":   (demanda.descricao,             demanda_in.descricao),
        "solicitante": (demanda.solicitante,           demanda_in.solicitante),
        "prioridade":  (demanda.prioridade,            demanda_in.prioridade),
        "status":      (demanda.status or "Aberta",    demanda_in.status),
    }
    for campo, (anterior, novo) in campos.items():
        if novo is not None and anterior != novo:
            db.add(HistoricoEdicoesModel(
                demanda_id=id,
                usuario_id=usuario_atual["id"],
                data=agora,
                campo_alterado=campo,
                valor_anterior=str(anterior),
                valor_novo=str(novo)
            ))
            setattr(demanda, campo, novo)

    # Atualiza data_conclusao se status mudou
    if demanda_in.status in ("Concluida", "Cancelada") and demanda.data_conclusao is None:
        demanda.data_conclusao = agora
    elif demanda_in.status == "Aberta":
        demanda.data_conclusao = None

    if demanda_in.prazo is not None:
        demanda.prazo = demanda_in.prazo

    db.commit()
    db.refresh(demanda)
    registrar_log(
        acao="EDITAR_DEMANDA",
        usuario_id=usuario_atual["id"],
        email=usuario_atual["email"],
        entidade="demanda",
        entidade_id=id,
        detalhes=f"Via API | Status: {demanda_in.status} | Prioridade: {demanda_in.prioridade}",
        ip="api"
    )
    return demanda


# ── PATCH /{id}/concluir ──────────────────────────────────────────────────────
@router.patch("/{id}/concluir", response_model=DemandaResponse, summary="Conclui uma demanda")
def concluir_demanda(
    id: int,
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_token)
):
    demanda = db.query(DemandaModel).filter(DemandaModel.id == id).first()
    if not demanda:
        raise HTTPException(status_code=404, detail=f"Demanda {id} não encontrada.")
    if demanda.status in ("Concluida", "Cancelada"):
        raise HTTPException(status_code=400, detail=f"Demanda já está {demanda.status}.")

    agora = datetime.utcnow()
    db.add(HistoricoEdicoesModel(
        demanda_id=id, usuario_id=usuario_atual["id"],
        data=agora, campo_alterado="status",
        valor_anterior=demanda.status or "Aberta", valor_novo="Concluida"
    ))
    demanda.status = "Concluida"
    demanda.data_conclusao = agora
    db.commit()
    db.refresh(demanda)
    registrar_log(
        acao="CONCLUIR_DEMANDA",
        usuario_id=usuario_atual["id"],
        email=usuario_atual["email"],
        entidade="demanda",
        entidade_id=id,
        ip="api"
    )
    return demanda


# ── PATCH /{id}/cancelar ──────────────────────────────────────────────────────
@router.patch("/{id}/cancelar", response_model=DemandaResponse, summary="Cancela uma demanda")
def cancelar_demanda(
    id: int,
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_token)
):
    demanda = db.query(DemandaModel).filter(DemandaModel.id == id).first()
    if not demanda:
        raise HTTPException(status_code=404, detail=f"Demanda {id} não encontrada.")

    eh_admin = usuario_atual["cargo"] == "admin"
    eh_dono  = demanda.criado_por == usuario_atual["id"]
    if not eh_admin and not eh_dono:
        raise HTTPException(status_code=403, detail="Sem permissão para cancelar esta demanda.")
    if demanda.status == "Cancelada":
        raise HTTPException(status_code=400, detail="Demanda já está Cancelada.")

    agora = datetime.utcnow()
    db.add(HistoricoEdicoesModel(
        demanda_id=id, usuario_id=usuario_atual["id"],
        data=agora, campo_alterado="status",
        valor_anterior=demanda.status or "Aberta", valor_novo="Cancelada"
    ))
    demanda.status = "Cancelada"
    demanda.data_conclusao = agora
    db.commit()
    db.refresh(demanda)
    registrar_log(
        acao="CANCELAR_DEMANDA",
        usuario_id=usuario_atual["id"],
        email=usuario_atual["email"],
        entidade="demanda",
        entidade_id=id,
        ip="api"
    )
    return demanda


# ── DELETE /{id} — somente admin ──────────────────────────────────────────────
@router.delete("/{id}", status_code=204, summary="Deleta uma demanda (somente admin)")
def deletar_demanda(
    id: int,
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_admin)
):
    demanda = db.query(DemandaModel).filter(DemandaModel.id == id).first()
    if not demanda:
        raise HTTPException(status_code=404, detail=f"Demanda {id} não encontrada.")

    db.delete(demanda)
    db.commit()
    registrar_log(
        acao="DELETAR_DEMANDA",
        usuario_id=usuario_atual["id"],
        email=usuario_atual["email"],
        entidade="demanda",
        entidade_id=id,
        detalhes="Deleção via API por admin",
        ip="api"
    )
    return


# ── PATCH /usuarios/{id}/cargo — promover/rebaixar usuário (somente admin) ───
@router.patch(
    "/usuarios/{id}/cargo",
    summary="Altera o cargo de um usuário (somente admin)",
    tags=["Administração"]
)
def alterar_cargo(
    id: int,
    cargo: str,
    db: Session = Depends(get_db),
    usuario_atual: dict = Depends(verificar_admin)
):
    if cargo not in ("admin", "comum"):
        raise HTTPException(status_code=400, detail="Cargo inválido. Use 'admin' ou 'comum'.")

    from app.models import UsuarioModel
    usuario = db.query(UsuarioModel).filter(UsuarioModel.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuário {id} não encontrado.")

    usuario.cargo = cargo
    db.commit()
    registrar_log(
        acao="ALTERAR_CARGO",
        usuario_id=usuario_atual["id"],
        email=usuario_atual["email"],
        entidade="usuario",
        entidade_id=id,
        detalhes=f"Novo cargo: {cargo}",
        ip="api"
    )
    return {"id": id, "nome": usuario.nome, "cargo": usuario.cargo}