from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
import os
from werkzeug.security import check_password_hash

from app.core.Database import get_db
from app.models import UsuarioModel

router = APIRouter(prefix="/auth", tags=["Segurança"])

SECRET_KEY = os.getenv("SECRET_KEY", "mude_esta_chave_no_arquivo_env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


@router.post("/token", summary="Gera um token de acesso JWT")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(UsuarioModel).filter(UsuarioModel.email == form_data.username).first()

    if not user or not check_password_hash(user.senha_hash, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expiracao = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dados_token = {
        "sub": user.email,
        "id": user.id,
        "cargo": user.cargo,   # ← cargo incluído no token
        "exp": expiracao
    }
    token_jwt = jwt.encode(dados_token, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": token_jwt, "token_type": "bearer"}


def verificar_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        usuario_id: int = payload.get("id")
        cargo: str = payload.get("cargo", "comum")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"email": email, "id": usuario_id, "cargo": cargo}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="O token expirou")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def verificar_admin(token_data: dict = Depends(verificar_token)):
    """Dependência que bloqueia acesso a não-admins."""
    if token_data.get("cargo") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return token_data