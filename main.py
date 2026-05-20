from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, demandas

# Inicialização do FastAPI com documentação Swagger customizada
app = FastAPI(
    title="API SGDI - Integração REST",
    description="API para comunicação de sistemas externos com o SGDI.",
    version="1.0.0",
    docs_url="/swagger",
    redoc_url=None,
)

# Configuração de CORS (Permite que outros sistemas chamem a API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Na produção, você restringe para os IPs parceiros
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# ESPAÇO PARA OS DEVS PLUGAREM AS ROTAS
# ==========================================
app.include_router(auth.router)
app.include_router(demandas.router)

@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "API SGDI Online e operante", "banco": "PostgreSQL configurado"}