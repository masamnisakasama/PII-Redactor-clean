from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status":"healthy"}

@router.get("/v1/health")
def v1_health():
    return health()

@router.get("/capabilities")
def capabilities():
    return {
        "styles": ["box", "pixelate", "swap"],  # swap=オンライン顔変換
        "endpoints": ["/redact/replace","/detect/summary","/health","/v1/health","/capabilities"],
        "face_styles": ["synthetic","anime","cartoon","emoji","pixel","old","3d","blur"],
    }
