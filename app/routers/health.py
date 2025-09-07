from fastapi import APIRouter
router = APIRouter(tags=["health"])
@router.get("/health")
def health(): return {"status":"healthy"}
@router.get("/v1/health")
def v1_health(): return health()
@router.get("/capabilities")
def caps(): return {"styles":["box"], "endpoints":["/redact/replace","/detect/summary","/health","/v1/health","/capabilities"]}
