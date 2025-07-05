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
    Send a user prompt to the selected LLM backend and return the content.
    Supported backends: Ollama (default), Anthropic Cloud.
    The backend is selected via the LLM_BACKEND env var.
    """
    # Select LLM backend via LLM_BACKEND (default: ollama)
    backend = os.getenv('LLM_BACKEND', 'ollama').lower()
    if backend == 'anthropic':
        try:
            from anthropic import Client, HUMAN_PROMPT, AI_PROMPT
        except ModuleNotFoundError:
            raise RuntimeError(
                "Anthropic SDK is not installed; please install with `pip install anthropic>=3.0.0`"
            )

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise RuntimeError('ANTHROPIC_API_KEY is not set')
        try:
            client = Client(api_key=api_key)
        except TypeError:
            client = Client()
        full_prompt = HUMAN_PROMPT + prompt + AI_PROMPT
        try:
            response = client.completions.create(
                model=model,
                prompt=full_prompt,
                temperature=temperature,
                max_tokens_to_sample=2000,
            )
            return response.completion
        except Exception as e:
            err = str(e)
            # Fallback to the Anthropic Messages API for models that no longer support Completions
            if 'Please use the Messages API instead' in err:
                messages_payload = [{'role': 'user', 'content': prompt}]
                resp_msg = client.messages.create(
                    model=model,
                    messages=messages_payload,
                    temperature=temperature,
                    max_tokens=2000,
                )
                # Extract and concatenate text blocks from the response
                try:
                    blocks = resp_msg.content
                    text = ''
                    for block in blocks:
                        # Each block has .text for text content
                        if hasattr(block, 'text'):
                            text += block.text
                    return text
                except Exception:
                    return str(resp_msg)
            raise

    # Default to Ollama HTTP API
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