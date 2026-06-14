
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
import pdfplumber
import tempfile
import os

# Load environment variables
load_dotenv()

# Environment Variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq Endpoint
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# FastAPI App
app = FastAPI(
    title="Adhikar.ai Groq Backend",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Model
class ChatRequest(BaseModel):
    message: str
    mode: str = "general"


# Root
@app.get("/")
async def root():
    return {
        "message": "Adhikar.ai Backend Running"
    }


# Health Check
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "backend": "Groq",
        "key_set": bool(GROQ_API_KEY)
    }


# Chat Endpoint
@app.post("/api/chat")
async def chat(chat_req: ChatRequest):

    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not found in .env"
        )

    system_prompt = {
        "general": (
            "You are Adhikar AI. Help users with legal, insurance, "
            "government schemes, consumer rights and general questions."
        ),
        "insurance": (
            "You are an insurance expert. Explain policy clauses, "
            "claim rejections and IRDAI processes."
        ),
        "legal": (
            "You are a legal assistant. Explain Indian laws "
            "in simple language."
        )
    }.get(chat_req.mode, "You are a helpful assistant.")

    async with httpx.AsyncClient() as client:

        response = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": chat_req.message
                    }
                ],
                "temperature": 0.3
            }
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text
            )

        data = response.json()

        return {
            "success": True,
            "response": data["choices"][0]["message"]["content"]
        }


# PDF Policy Analyzer
@app.post("/api/analyze-policy")
async def analyze_policy(file: UploadFile = File(...)):

    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not found in .env"
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(await file.read())
        temp_path = temp.name

    # Extract PDF Text
    extracted_text = ""

    try:
        with pdfplumber.open(temp_path) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"PDF extraction failed: {str(e)}"
        )

    # Prevent huge payloads
    extracted_text = extracted_text[:12000]

    prompt = f"""
Analyze the document and respond ONLY in this format:

SUMMARY:
...

IMPORTANT_CLAUSES:
...

RISKS:
...

RECOMMENDATIONS:
...

Document:

{extracted_text}
"""

    async with httpx.AsyncClient() as client:

        response = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Adhikar AI. "
                            "Analyze legal, insurance and policy documents. "
                            "Explain in simple English."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2
            }
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text
            )

        data = response.json()

        analysis = data["choices"][0]["message"]["content"]

        return {
            "success": True,
            "file_name": file.filename,
            "analysis": analysis
        }
