from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="Adhikar.ai Groq Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get your Groq API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

class ChatRequest(BaseModel):
    message: str
    mode: str = "general"

@app.post("/api/chat")
async def chat(chat_req: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(500, "GROQ_API_KEY not set")
    system_prompt = {
        "general": "You are Adhikar AI, assistant for Indian legal and insurance rights. Answer in simple English or Hinglish.",
        "insurance": "You are an IRDAI expert. Give actionable claim advice for Indian insurance policies.",
        "legal": "You are a lawyer. Explain IPC, CRPC, Consumer Protection Act sections clearly."
    }.get(chat_req.mode, "General assistant.")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",  # free and fast
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chat_req.message}
                ],
                "temperature": 0.3
            },
            timeout=30.0
        )
        if response.status_code != 200:
            raise HTTPException(503, f"Groq API error: {response.text}")
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return {"response": reply}

@app.get("/api/health")
async def health():
    return {"status": "ok", "backend": "Groq", "key_set": bool(GROQ_API_KEY)}
