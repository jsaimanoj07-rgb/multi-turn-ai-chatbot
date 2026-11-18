"""Internship Task 1 — multi-turn chatbot with context window management."""

from __future__ import annotations

import os
import uuid
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))
API_TIMEOUT_MS = int(os.getenv("API_TIMEOUT_MS", "30000"))

SYSTEM_PROMPT = """
You are Byte, a friendly internship coding mentor for students.

Your job:
- Help the intern learn by explaining ideas in plain language.
- Keep replies short and practical (usually under 8 sentences).
- If they mention something from earlier in the chat, use that context.
- Prefer examples over lectures.
- Never reveal API keys or ask the user to paste secrets into chat.

Tone: encouraging, a bit witty, never condescending.
""".strip()

app = FastAPI(title="Byte Chatbot")
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory store: conversation_id -> list of {role, content}
conversations: dict[str, list[dict[str, str]]] = {}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    history_kept: int


def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Server is missing GEMINI_API_KEY. Add it to a .env file and restart.",
        )
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=API_TIMEOUT_MS),
    )


def trim_history(history: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep only the last N messages so we stay inside the context window."""
    if len(history) <= MAX_HISTORY_MESSAGES:
        return history
    return history[-MAX_HISTORY_MESSAGES:]


def to_gemini_contents(history: list[dict[str, str]]) -> list[types.Content]:
    contents: list[types.Content] = []
    for msg in history:
        role: Literal["user", "model"] = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part(text=msg["content"])])
        )
    return contents


def friendly_error(exc: Exception) -> str:
    text = str(exc).lower()
    if "timeout" in text or "timed out" in text:
        return "Byte took too long to reply. Check your network and try again."
    if "429" in text or "resource exhausted" in text or "quota" in text:
        return "The LLM API is rate-limited right now. Wait a minute and try again."
    if "api key" in text or "401" in text or "403" in text or "permission" in text:
        return "The API key looks invalid. Check GEMINI_API_KEY in your .env file."
    return "Byte could not reach the LLM API. Please try again in a moment."


@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    conversation_id = req.conversation_id or str(uuid.uuid4())
    history = conversations.setdefault(conversation_id, [])
    history.append({"role": "user", "content": req.message.strip()})

    window = trim_history(history)

    try:
        client = get_client()
        response = client.models.generate_content(
            model=MODEL,
            contents=to_gemini_contents(window),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )
        reply = (response.text or "").strip()
        if not reply:
            raise ValueError("empty model response")
    except HTTPException:
        history.pop()
        raise
    except Exception as exc:
        history.pop()
        raise HTTPException(status_code=502, detail=friendly_error(exc)) from exc

    history.append({"role": "assistant", "content": reply})
    conversations[conversation_id] = history
    return ChatResponse(
        conversation_id=conversation_id,
        reply=reply,
        history_kept=len(trim_history(history)),
    )


@app.post("/api/reset")
def reset(conversation_id: str | None = None) -> dict[str, str]:
    if conversation_id and conversation_id in conversations:
        del conversations[conversation_id]
    return {"status": "ok"}
