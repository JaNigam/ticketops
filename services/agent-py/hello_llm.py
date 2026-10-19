# hello_llm.py
import os
import requests


from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ["LLM_BASE_URL"].rstrip("/")
MODEL = os.environ.get("LLM_MODEL", "gemma4:e4b")

def ask(prompt: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/api/chat",
        headers={"ngrok-skip-browser-warning": "true"},  # skips ngrok's interstitial page
        json={
            "model": MODEL,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]

if __name__ == "__main__":
    print(ask("In one sentence, what is an AI agent?"))