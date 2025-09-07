from fastapi import FastAPI
from app.routers.health import router as health
from app.routers.redact import router as redact
from app.routers.diag import router as diag_router

app = FastAPI(title="PII Redactor", version="2")

app.include_router(diag_router)
app.include_router(health)
app.include_router(redact)
