import os
from typing import Optional, List, Dict, Any

import requests
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
AI_WEBHOOK_SECRET = os.getenv("AI_WEBHOOK_SECRET")  # optional simple auth

# TODO: replace with your own brand/system prompt
SYSTEM_PROMPT = (
    "Ты — бренд‑ассистент сети магазинов INTERTOP в Казахстане. "
    "Отвечай дружелюбно и по делу. Если вопрос не про INTERTOP, мягко верни в тему. "
    "Языки: русский/казахский/английский — отвечай на языке клиента."
)

OPENAI_URL = "https://api.openai.com/v1/responses"


class AIRequest(BaseModel):
    message: str
    contact_id: Optional[str] = None  # SendPulse contact_id (useful as safety_identifier)
    user_id: Optional[str] = None


app = FastAPI()


def _extract_output_text(resp_json: Dict[str, Any]) -> str:
    parts: List[str] = []
    for item in resp_json.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for c in item.get("content", []) or []:
            if c.get("type") == "output_text" and c.get("text"):
                parts.append(c["text"])
    return "".join(parts).strip()


def call_openai(message: str, safety_identifier: Optional[str]) -> str:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": OPENAI_MODEL,
        "input": message,
        "instructions": SYSTEM_PROMPT,
        "temperature": 0.25,
        "max_output_tokens": 350,
        "store": False,
    }
    if safety_identifier:
        payload["safety_identifier"] = safety_identifier

    r = requests.post(OPENAI_URL, headers=headers, json=payload, timeout=55)
    r.raise_for_status()
    data = r.json()
    text = _extract_output_text(data)
    return text or "Извините, не удалось сформировать ответ. Попробуйте ещё раз."


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ai")
def ai(req: AIRequest, x_ai_secret: Optional[str] = Header(default=None)):
    if AI_WEBHOOK_SECRET and x_ai_secret != AI_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="unauthorized")

    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="message is required")

    safety_id = req.contact_id or req.user_id
    reply = call_openai(msg, safety_identifier=str(safety_id) if safety_id else None)

    # Keep replies safely under SendPulse limits (and Telegram)
    if len(reply) > 3500:
        reply = reply[:3500] + "…"

    return {"reply": reply}
