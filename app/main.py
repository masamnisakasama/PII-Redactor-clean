from fastapi import FastAPI
from app.routers.health import router as health
from app.routers.redact import router as redact
app = FastAPI(title="pii-redactor clean")
app.include_router(health)
app.include_router(redact)
