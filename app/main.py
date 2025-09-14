# /app/main.py
from fastapi import FastAPI
from app.routers.health import router as health
from app.routers.redact import router as redact
from app.routers.diag import router as diag_router
from app.routers.rag import router as rag_router
from app.routers.policy import router as policy_router 
from app.routers.compose import router as compose_router

app = FastAPI(title="PII Redactor", version="2")

app.include_router(diag_router)
app.include_router(health)
app.include_router(redact)
app.include_router(rag_router)    
app.include_router(policy_router)
app.include_router(compose_router)