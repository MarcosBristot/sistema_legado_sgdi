from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Definindo a Fronteira de Dados que conversamos
class DemandaCreate(BaseModel):
    titulo: str = Field(..., max_length=150, example="Sistema fora do ar")
    descricao: str = Field(..., example="Os usuários não conseguem fazer login desde as 10h.")
    solicitante: str = Field(..., example="Sistema ERP_Parceiro")
    prioridade: Optional[str] = Field("Media", pattern="^(Alta|Media|Baixa)$")
    # Não pedimos status nem ID, pois a API gera isso sozinha.

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
        from_attributes = True # Fundamental para o Pydantic entender o SQLAlchemy