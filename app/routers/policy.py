from fastapi import APIRouter, Form
from app.rag.offline.policy import nl_to_policy as offline_nl2csv

router = APIRouter(prefix="/policy", tags=["policy"])

@router.post("/resolve")
def resolve_policy(
    text: str = Form(...),      # 例: "顔とメールを隠して"
    mode: str = Form("offline") # 今は 'offline' のみ
):
    if mode == "offline":
        csv = offline_nl2csv(text)
        return {"mode": "offline", "input": text, "policy": csv}
    return {"mode": mode, "input": text, "policy": ""}
