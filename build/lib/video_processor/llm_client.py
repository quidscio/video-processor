"""
llm_client.py

Wrapper for calling the Ollama chat completion API (Claude Opus 4).
"""
import os
import requests

from .config import OLLAMA_URL

def load_template(name: str) -> str:
    """
    Load a prompt template from the prompts/ directory.
    """
    base = os.path.dirname(__file__)
    path = os.path.join(base, 'prompts', name)
    with open(path, encoding='utf-8') as f:
        return f.read()

def chat(prompt: str, model: str = 'claude-opus-4', temperature: float = 0.0) -> str:
    """
    Send a user prompt to the Ollama chat completions endpoint and return the content.
    """
    url = f"{OLLAMA_URL}/v1/chat/completions"
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': temperature,
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    try:
        return data['choices'][0]['message']['content']
    except Exception:
        raise RuntimeError(f"Unexpected response format from LLM: {data}")