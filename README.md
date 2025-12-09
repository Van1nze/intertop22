# SendPulse ↔ AI (OpenAI) webhook service

## What this is
A tiny FastAPI service for SendPulse chatbot **API Request** element.
SendPulse calls `POST /ai`, service returns JSON: `{ "reply": "..." }`.

## Environment variables (Render → Environment)
- `OPENAI_API_KEY` — your OpenAI key (keep it secret)
- `OPENAI_MODEL` — optional, default: `gpt-4.1-mini`
- `AI_WEBHOOK_SECRET` — optional shared secret. If set, SendPulse must send header `X-AI-SECRET`.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

## SendPulse flow (high level)
1. Add **Filter**: if `last_message` contains "оператор" → **Action → Open chat** (assign operator, pause bot automation).
2. Else → **API Request** (POST) to `https://<your-render>.onrender.com/ai`
   - Headers:
     - `Content-Type: application/json`
     - `X-AI-SECRET: <AI_WEBHOOK_SECRET>` (only if you set it)
   - Body example:
     ```json
     {"message":"{{last_message}}","contact_id":"{{contact_id}}"}
     ```
3. Next message element: output `{{$['reply']}}` (or save to variable and print it).

> Tip: add a button “🤖 Вернуться к боту” for users during operator mode.

## Security note
Do NOT hardcode tokens in code or commit them to GitHub. Rotate any leaked keys immediately.
