from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DemandaCreate(BaseModel):
    titulo: str = Field(..., max_length=150, example="Sistema fora do ar")
    descricao: str = Field(..., example="Usuários não conseguem fazer login.")
    solicitante: str = Field(..., example="Sistema ERP_Parceiro")
    prioridade: Optional[str] = Field("Media", pattern="^(Alta|Media|Baixa)$")

class DemandaUpdate(BaseModel):
    titulo: Optional[str] = Field(None, max_length=150)
    descricao: Optional[str] = None
    solicitante: Optional[str] = None
    prioridade: Optional[str] = Field(None, pattern="^(Alta|Media|Baixa)$")
    status: Optional[str] = Field(None, pattern="^(Aberta|Concluida|Cancelada)$")
    prazo: Optional[datetime] = None

class DemandaResponse(BaseModel):
    id: int
    titulo: str
    descricao: str
    solicitante: str
    prioridade: str
    status: str
    data_criacao: datetime
    prazo: Optional[datetime] = None

    class Config:
        from_attributes = True