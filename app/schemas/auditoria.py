from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LogResponse(BaseModel):
    id:          int
    email:       Optional[str] = None
    usuario_id:  Optional[int] = None
    acao:        str
    entidade:    Optional[str] = None
    entidade_id: Optional[int] = None
    detalhes:    Optional[str] = None
    ip:          Optional[str] = None
    status:      str
    data:        datetime

    class Config:
        from_attributes = True