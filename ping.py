"""Step 2 from the task: send one message and print the reply."""

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("Set GEMINI_API_KEY in a .env file first.")

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    contents="Reply with a one-sentence hello so I know the API works.",
)
print(response.text)
