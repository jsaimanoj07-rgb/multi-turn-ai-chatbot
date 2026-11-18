# Byte — Internship Task 1 Chatbot

A small Gemini-backed chatbot that keeps **multi-turn history**, trims the **context window**, and shows a clear error if the API fails.

## What it does

- `POST /api/chat` sends the user's message + conversation history to Google Gemini and returns the reply.
- History is stored **per conversation** in memory.
- Context management: only the **last 12 messages** are sent to the model (older turns are dropped).
- System prompt: Byte, a friendly internship coding mentor — not a generic assistant.
- Failures (timeout, rate limit, bad key, network) return a readable message in the UI.
- API key lives in `.env` and is ignored by git.

## Setup

1. Get a free Gemini key from [Google AI Studio](https://aistudio.google.com/apikey).
2. Copy the env file and paste your key (never commit `.env`):

```bash
copy .env.example .env
```

3. Create a venv and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

4. Confirm the API works:

```bash
python ping.py
```

5. Run the app:

```bash
uvicorn app:app --reload
```

Open http://127.0.0.1:8000

## Test a 5-turn conversation

Use the same chat window (don't click **New chat**):

1. "My name is Manoj and I'm building a Python chatbot."
2. "What language am I using?"
3. "What is my name?"
4. "Remind me what my project is."
5. "Give me one next step for this internship task."

Byte should remember your name, language, and project from earlier turns.

## Project layout

```
app.py              # FastAPI backend + history + truncation
ping.py             # one-shot API smoke test
static/index.html   # simple chat UI
.env.example        # key template (safe to commit)
.gitignore          # ignores .env
```
